"""Field-level validation rules (row-based)."""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

from validator_oop.core.constants import (
    ALLOWED_TIP_OBJEKTA,
    DATA_OBJECT_MAPPING,
    FORMULA_REF,
    KEY_PATTERN,
    LABELA_CHECKBOX_ALLOWED,
    LABELA_DATETIME_OBJECT_TYPES,
    LABELA_DATUM_CAS_VALUE,
    LABELA_KODA_TYPES,
    LABELA_MASS_TYPES,
    LABELA_NAZIV_OPREME_VALUE,
    REQUIRED_KEY_TIME_TYPES,
    REQUIRED_KEY_TYPES,
    STANDARD_TIP_PODATKA,
    TIP_PODATKA_POSEBNOSTI,
    TIP_PODATKA_POSEBNOSTIMON,
    VALIDATION_EXCLUDED_COLUMNS,
)
from validator_oop.core.error import Severity
from validator_oop.core.shared_context import _is_usable_zavihek_name
from validator_oop.rules import RowRule, RuleContext, register
from validator_oop.utils import (
    coerce_str,
    extract_unit_token,
    extract_unit_token_near_number,
    is_step_number_column,
    looks_like_number_with_commas,
    norm_control_name,
    norm_text,
)

# Additional local constants not in core/constants.py
FORMULA_OBJECT_TYPES: frozenset[str] = frozenset({"formula", "formula0", "formula1"})
# masa1, masa_2, … niso veljavni tipi; številka sodi v Ključ preverjanja.
_MASA_NUMBERED_TIP_RE = re.compile(r"^masa[\s_\-.]?\d+$")
# Zavihek recepture: monolit1, monolit2, ... (brez presledkov, številka obvezna).
_MONOLIT_ZAVIHEK_RE = re.compile(r"monolit\d+")
# Pri crta mora biti zapolnjen št. Koraka (tudi okrajšava št. Kor.);
# Tip podatka/Tip objekta sta identifikatorja vrstice.
# Zavihek sme biti prazen ali koda monolita (monolit1, monolit2, ...).
CRTA_ALLOWED_NON_EMPTY_COLUMNS: frozenset[str] = frozenset({
    "št. Koraka",
    "Tip podatka",
    "Tip objekta",
})
ZAVIHEK_COLUMN = "Zavihek"
NASLOV_ALLOWED_NON_EMPTY_COLUMNS: frozenset[str] = frozenset({
    "št. Koraka",
    "Navodilo",
    "Tip podatka",
    "Tip objekta",
})


def _cell_is_nonempty(value: object) -> bool:
    if value is None:
        return False
    try:
        import pandas as pd
        if pd.isna(value):
            return False
    except (ImportError, TypeError, ValueError):
        pass
    return bool(str(value).strip())


def _is_allowed_monolit_zavihek(value: object) -> bool:
    """True, če je Zavihek prazen ali koda monolita (monolit1, monolit2, ...)."""
    if not _cell_is_nonempty(value):
        return True
    return norm_text(coerce_str(value)).startswith("monolit")


def _row_columns(row: Mapping[str, object], context: RuleContext) -> list[str]:
    shared = context.shared
    if shared:
        return list(
            shared.columns
            or [k for k in row.keys() if k not in VALIDATION_EXCLUDED_COLUMNS]
        )
    return [k for k in row.keys() if k not in VALIDATION_EXCLUDED_COLUMNS]


def _find_step_column(
    row: Mapping[str, object], columns: Sequence[str]
) -> tuple[str, object]:
    """Vrni ime stolpca številke koraka in njegovo vrednost (vključno z okrajšavami)."""
    candidates: list[tuple[str, object]] = []
    seen: set[str] = set()
    for column in list(columns) + [str(key) for key in row.keys()]:
        if column in seen or not is_step_number_column(column):
            continue
        seen.add(column)
        candidates.append((column, row.get(column)))
    for column, value in candidates:
        if _cell_is_nonempty(value):
            return column, value
    if candidates:
        return candidates[0]
    return "št. Koraka", row.get("št. Koraka")


def _is_allowed_non_empty_column(column: str, allowed: frozenset[str]) -> bool:
    if column in allowed or column in VALIDATION_EXCLUDED_COLUMNS:
        return True
    return is_step_number_column(column)


@register
class ObjectTypeRule(RowRule):
    """Validate 'Tip objekta' column."""

    name = "tip_objekta_rule"
    description = "Tip objekta mora biti zapolnjen in med dovoljenimi vrednostmi."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if not tip_obj:
            yield self.build_error(
                "Tip objekta ne sme biti prazen.",
                context=context,
                column="Tip objekta",
                code="OBJECT_TYPE_EMPTY",
            )
            return

        if tip_obj not in ALLOWED_TIP_OBJEKTA:
            yield self.build_error(
                f"Neznan Tip objekta: '{tip_obj}'.",
                context=context,
                column="Tip objekta",
                code="OBJECT_TYPE_UNKNOWN",
            )


@register
class MasaTipPodatkaRule(RowRule):
    """Tip podatka for mass must be exactly 'masa' (masa1 is invalid)."""

    name = "masa_tip_podatka_rule"
    description = (
        "Tip podatka za maso mora biti točno 'masa'; oštevilčene vrednosti "
        "(npr. masa1) niso veljavne."
    )

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        if not tip_data or tip_data == "masa":
            return
        if _MASA_NUMBERED_TIP_RE.fullmatch(tip_data):
            yield self.build_error(
                f"Tip podatka mora biti 'masa', vrednost '{tip_data_raw}' ni veljavna.",
                context=context,
                column="Tip podatka",
                code="DATA_TYPE_MASA_INVALID",
            )


def _is_monolit_zavihek_code(value: object) -> bool:
    """True, če je vrednost točno koda zavihka monolita (monolit1, monolit2, ...)."""
    text = coerce_str(value).strip()
    if not _is_usable_zavihek_name(text):
        return False
    return _MONOLIT_ZAVIHEK_RE.fullmatch(norm_text(text)) is not None


@register
class PosebnostiTipPodatkaRule(RowRule):
    """Tip podatka posebnosti mora ustrezati zavihku v isti vrstici."""

    name = "posebnosti_tip_podatka_rule"
    description = (
        "Če je v isti vrstici v stolpcu Zavihek vpisano monolit1, monolit2, …, "
        "mora biti Tip podatka 'posebnostimon'; sicer 'posebnosti'."
    )

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        if tip_data not in {TIP_PODATKA_POSEBNOSTI, TIP_PODATKA_POSEBNOSTIMON}:
            return

        zavihek_raw = coerce_str(row.get(ZAVIHEK_COLUMN, ""))
        if _is_monolit_zavihek_code(zavihek_raw):
            if tip_data == TIP_PODATKA_POSEBNOSTIMON:
                return
            yield self.build_error(
                "V isti vrstici je v stolpcu 'Zavihek' vpisano "
                f"'{zavihek_raw.strip()}', zato mora biti Tip podatka "
                f"'{TIP_PODATKA_POSEBNOSTIMON}' (najdeno: '{tip_data_raw}').",
                context=context,
                column="Tip podatka",
                code="DATA_TYPE_POSEBNOSTIMON_REQUIRED",
            )
            return

        if tip_data == TIP_PODATKA_POSEBNOSTI:
            return
        yield self.build_error(
            "V isti vrstici stolpec 'Zavihek' ni 'monolit1', 'monolit2', …, "
            f"zato mora biti Tip podatka '{TIP_PODATKA_POSEBNOSTI}' "
            f"(najdeno: '{tip_data_raw}').",
            context=context,
            column="Tip podatka",
            code="DATA_TYPE_POSEBNOSTI_REQUIRED",
        )


@register
class DataObjectCompatibilityRule(RowRule):
    """Validate compatibility between 'Tip podatka' and 'Tip objekta'."""

    name = "data_object_compatibility"
    description = "Tip podatka mora imeti ustrezen Tip objekta."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        errors = []

        if tip_data not in STANDARD_TIP_PODATKA:
            return errors

        if tip_data == "masa" and tip_obj in FORMULA_OBJECT_TYPES:
            errors.append(
                self.build_error(
                    "Pri tipu podatka 'masa' Tip objekta ne sme biti 'formula', 'formula0' ali 'formula1'.",
                    context=context,
                    column="Tip objekta",
                    code="OBJECT_TYPE_MISMATCH",
                )
            )
            return errors

        allowed_objects = DATA_OBJECT_MAPPING.get(tip_data)
        if allowed_objects and tip_obj and tip_obj not in allowed_objects:
            allowed_str = ", ".join(sorted(allowed_objects))
            errors.append(
                self.build_error(
                    f"'{tip_data_raw}' zahteva Tip objekta {allowed_str}, najdeno: '{tip_obj}'.",
                    context=context,
                    column="Tip objekta",
                    code="OBJECT_TYPE_MISMATCH",
                )
            )
        return errors


@register
class LabelRequirementsRule(RowRule):
    """Validate label requirements (koda, oprema, datum/čas, enote)."""

    name = "label_requirements"
    description = "Pravila za 'Labela' glede na Tip podatka (koda, oprema, datum/čas, enote)."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        errors = []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        labela_raw = coerce_str(row.get("Labela", ""))
        labela_norm = norm_text(labela_raw)
        navodilo_raw = coerce_str(row.get("Navodilo", ""))

        if not tip_data:
            return errors

        if tip_data in LABELA_KODA_TYPES and labela_norm != "koda":
            errors.append(
                self.build_error(
                    f"Za tip podatka '{tip_data}' mora biti Labela = 'koda'.",
                    context=context,
                    column="Labela",
                    code="LABEL_MUST_BE_KODA",
                )
            )
        elif tip_obj == "spustniseznam" and labela_norm != LABELA_NAZIV_OPREME_VALUE:
            errors.append(
                self.build_error(
                    "Pri tipu objekta 'spustniseznam' mora biti Labela = 'naziv opreme'.",
                    context=context,
                    column="Labela",
                    code="LABEL_MUST_BE_NAZIV_OPREME",
                )
            )
        elif tip_obj in LABELA_DATETIME_OBJECT_TYPES and labela_norm != LABELA_DATUM_CAS_VALUE:
            errors.append(
                self.build_error(
                    f"Pri tipu objekta '{tip_obj}' mora biti Labela = 'datum/čas'.",
                    context=context,
                    column="Labela",
                    code="LABEL_MUST_BE_DATUM_CAS",
                )
            )
        elif tip_data in LABELA_MASS_TYPES:
            label_unit = extract_unit_token(labela_raw)
            if not label_unit:
                errors.append(
                    self.build_error(
                        "Za tip podatka 'masa' mora Labela vsebovati enoto (npr. g, mL, kg).",
                        context=context,
                        column="Labela",
                        code="LABEL_MUST_BE_UNIT",
                    )
                )

        # Try to extract unit near number first, fallback to any unit if not found
        label_unit = extract_unit_token_near_number(labela_raw)
        if not label_unit:
            label_unit = extract_unit_token(labela_raw)
        
        nav_unit = extract_unit_token_near_number(navodilo_raw)
        if not nav_unit:
            nav_unit = extract_unit_token(navodilo_raw)
        
        # Skip unit mismatch check if Navodilo doesn't contain a number with unit
        # This handles cases like "Masa H2SO4 iz založne raztopine za ta korak"
        # where the unit might be extracted incorrectly
        if nav_unit:
            # Check if Navodilo actually contains a number followed by this unit
            # If not, it's likely a false positive (e.g., "h" from "H2SO4" or similar)
            import re
            from validator_oop.core.constants import NUMERIC_TOKEN_RE
            
            # Check if there's a number near the unit in Navodilo
            # Look for pattern like "number unit" or "number  unit"
            unit_pattern = re.compile(rf"\d+(?:[.,]\d+)?\s+{re.escape(nav_unit)}\b", re.IGNORECASE)
            if not unit_pattern.search(navodilo_raw):
                # Unit found but not near a number - likely false positive
                nav_unit = None
        
        if label_unit and nav_unit and label_unit != nav_unit:
            errors.append(
                self.build_error(
                    f"Enota v 'Labela' ({label_unit}) se ne ujema z enoto v 'Navodilo' ({nav_unit}).",
                    context=context,
                    column="Labela",
                    code="UNIT_MISMATCH",
                )
            )

        return errors


@register
class CheckboxLabelaRule(RowRule):
    """Za Tip objekta checkbox preveri, da je Labela 'DA (kljukica)' ali 'DA (kljukica)/NE (prazno)'."""

    name = "checkbox_labela_rule"
    description = "Pri tipu objekta 'checkbox' mora biti Labela 'DA (kljukica)' ali 'DA (kljukica)/NE (prazno)'."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj != "checkbox":
            return

        labela_raw = coerce_str(row.get("Labela", ""))
        labela_norm = norm_text(labela_raw)
        if not labela_norm:
            yield self.build_error(
                "Pri tipu objekta 'checkbox' mora biti Labela zapolnjena: 'DA (kljukica)' ali 'DA (kljukica)/NE (prazno)'.",
                context=context,
                column="Labela",
                code="LABEL_CHECKBOX_FORMAT",
            )
            return

        if labela_norm not in LABELA_CHECKBOX_ALLOWED:
            allowed_str = "', '".join(sorted(LABELA_CHECKBOX_ALLOWED))
            yield self.build_error(
                f"Pri tipu objekta 'checkbox' mora biti Labela ena od: '{allowed_str}'. Najdeno: '{labela_raw.strip()}'.",
                context=context,
                column="Labela",
                code="LABEL_CHECKBOX_FORMAT",
            )


@register
class CrtaEmptyColumnsRule(RowRule):
    """Pri tipu objekta crta mora biti zapolnjen št. Koraka; ostali stolpci prazni.

    Izjema: stolpec Zavihek sme biti prazen ali koda monolita (monolit1, monolit2, ...).
    """

    name = "crta_empty_columns_rule"
    description = (
        "Pri tipu objekta 'crta' mora biti 'št. Koraka' zapolnjen; ostali stolpci prazni "
        "(Zavihek sme biti prazen ali monolit1, monolit2, ...)."
    )

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj != "crta":
            return

        columns = _row_columns(row, context)
        step_col, step_val = _find_step_column(row, columns)
        if not _cell_is_nonempty(step_val):
            yield self.build_error(
                f"Pri tipu objekta 'crta' mora biti stolpec '{step_col}' zapolnjen.",
                context=context,
                column=step_col,
                code="CRTA_STEP_EMPTY",
            )

        for column in columns:
            if _is_allowed_non_empty_column(column, CRTA_ALLOWED_NON_EMPTY_COLUMNS):
                continue
            if column == ZAVIHEK_COLUMN and _is_allowed_monolit_zavihek(row.get(column)):
                continue
            if not _cell_is_nonempty(row.get(column)):
                continue
            yield self.build_error(
                f"Pri tipu objekta 'crta' mora biti stolpec '{column}' prazen.",
                context=context,
                column=column,
                code="CRTA_COLUMN_NOT_EMPTY",
            )


@register
class NaslovEmptyColumnsRule(RowRule):
    """Pri naslovu morata biti zapolnjena št. Koraka in Navodilo; ostali stolpci prazni.

    Izjema: stolpec Zavihek sme biti prazen ali koda monolita (monolit1, monolit2, ...).
    """

    name = "naslov_empty_columns_rule"
    description = (
        "Pri naslovu morata biti zapolnjena 'št. Koraka' in 'Navodilo'; ostali stolpci prazni "
        "(Zavihek sme biti prazen ali monolit1, monolit2, ...)."
    )

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
        if tip_obj != "naslov" and tip_data != "naslov":
            return

        columns = _row_columns(row, context)
        step_col, step_val = _find_step_column(row, columns)
        if not _cell_is_nonempty(step_val):
            yield self.build_error(
                f"Pri naslovu mora biti stolpec '{step_col}' zapolnjen.",
                context=context,
                column=step_col,
                code="NASLOV_STEP_EMPTY",
            )
        if not _cell_is_nonempty(row.get("Navodilo")):
            yield self.build_error(
                "Pri naslovu mora biti stolpec 'Navodilo' zapolnjen.",
                context=context,
                column="Navodilo",
                code="NASLOV_NAVODILO_EMPTY",
            )

        for column in columns:
            if _is_allowed_non_empty_column(column, NASLOV_ALLOWED_NON_EMPTY_COLUMNS):
                continue
            if column == ZAVIHEK_COLUMN and _is_allowed_monolit_zavihek(row.get(column)):
                continue
            if not _cell_is_nonempty(row.get(column)):
                continue
            yield self.build_error(
                f"Pri naslovu mora biti stolpec '{column}' prazen "
                "(dovoljena sta le 'št. Koraka' in 'Navodilo').",
                context=context,
                column=column,
                code="NASLOV_COLUMN_NOT_EMPTY",
            )


@register
class SpustniseznamVrednostRule(RowRule):
    """Pri spustnem seznamu mora biti stolpec Vrednost zapolnjen z oznako šifranta."""

    name = "spustniseznam_vrednost_rule"
    description = "Pri tipu objekta 'spustniseznam' mora biti stolpec 'Vrednost' zapolnjen."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj != "spustniseznam":
            return

        vrednost = coerce_str(row.get("Vrednost", "")).strip()
        if not vrednost:
            yield self.build_error(
                "Pri tipu objekta 'spustniseznam' mora biti stolpec 'Vrednost' zapolnjen (oznaka šifranta, npr. HPLC, tehtnica).",
                context=context,
                column="Vrednost",
                code="SPUSTNISEZNAM_VREDNOST_EMPTY",
            )


@register
class KeyValidationRule(RowRule):
    """Validate 'Ključ preverjanja'."""

    name = "key_validation"
    description = "Preveri format ključa in obveznost za določene tipe."

    @staticmethod
    def _key_raw(row: Mapping[str, object]) -> str:
        """Vrednost ključa brez strip (za zaznavo presledkov na začetku/koncu)."""
        value = row.get("Ključ preverjanja", "")
        if value is None:
            return ""
        try:
            import pandas as pd
            if pd.isna(value):
                return ""
        except (ImportError, TypeError, ValueError):
            pass
        return str(value)

    @staticmethod
    def _has_edge_space(key: str) -> bool:
        return bool(key) and (key[0] == " " or key[-1] == " ")

    def _find_invalid_char(self, key: str) -> str | None:
        """Poišče prvi nedovoljen znak v ključu in vrne njegov opis."""
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-.")
        char_descriptions = {
            ",": "vejica",
            ";": "podpičje",
            ":": "dvopičje",
            "!": "klicaj",
            "?": "vprašaj",
            "@": "znak @",
            "#": "znak #",
            "$": "znak $",
            "%": "znak %",
            "&": "znak &",
            "*": "znak *",
            "+": "znak +",
            "=": "znak =",
            "(": "oklepaj (",
            ")": "oklepaj )",
            "[": "oklepaj [",
            "]": "oklepaj ]",
            "{": "oklepaj {",
            "}": "oklepaj }",
            "<": "znak <",
            ">": "znak >",
            "/": "znak /",
            "\\": "znak \\",
            "|": "znak |",
            "^": "znak ^",
            "~": "znak ~",
            "`": "znak `",
            "\"": "narekovaj",
            "'": "apostrof",
            "\t": "tabulator",
            "\n": "nova vrstica",
            "\r": "vrnitev kazalca",
        }
        
        for char in key:
            if char == " ":
                continue
            if char not in allowed_chars:
                return char_descriptions.get(char, f"znak '{char}'")
        return None

    @staticmethod
    def _requires_key(row: Mapping[str, object]) -> tuple[bool, str]:
        tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))

        if tip_data in REQUIRED_KEY_TYPES:
            return True, tip_data
        if tip_data in REQUIRED_KEY_TIME_TYPES:
            return True, tip_data
        return False, ""

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        errors = []
        key_raw = self._key_raw(row)
        key = key_raw.strip()

        if key_raw and self._has_edge_space(key_raw):
            errors.append(
                self.build_error(
                    f"Ključ preverjanja '{key_raw}' vsebuje presledek na začetku ali koncu.",
                    context=context,
                    column="Ključ preverjanja",
                    code="KEY_INVALID_FORMAT",
                )
            )
        elif key and not KEY_PATTERN.fullmatch(key):
            invalid_char_desc = self._find_invalid_char(key)
            if invalid_char_desc:
                error_msg = f"Ključ preverjanja '{key}' vsebuje nedovoljen {invalid_char_desc}."
                errors.append(
                    self.build_error(
                        error_msg,
                        context=context,
                        column="Ključ preverjanja",
                        code="KEY_INVALID_FORMAT",
                    )
                )
            elif " " not in key:
                errors.append(
                    self.build_error(
                        f"Ključ preverjanja '{key}' vsebuje nedovoljene znake. "
                        "Dovoljeni so samo: črke (A-Z, a-z), številke (0-9), podčrtaj (_), vezaj (-) in pika (.).",
                        context=context,
                        column="Ključ preverjanja",
                        code="KEY_INVALID_FORMAT",
                    )
                )

        requires_key, type_label = self._requires_key(row)
        if requires_key and not key:
            errors.append(
                self.build_error(
                    (
                        f"Za tip podatka '{type_label}' mora biti nastavljen 'Ključ preverjanja'."
                    ),
                    context=context,
                    column="Ključ preverjanja",
                    code="KEY_REQUIRED",
                )
            )

        return errors


@register
class FormulaSyntaxRule(RowRule):
    """Validate syntax of formula objects."""

    name = "formula_syntax"
    description = "Formulska polja morajo začeti z '=' in vsebovati sklice, brez zapisa '&$'."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj not in FORMULA_OBJECT_TYPES:
            return []

        value = coerce_str(row.get("Vrednost", ""))
        errors = []

        if not value.startswith("="):
            errors.append(
                self.build_error(
                    "Pri formulskih objektih mora 'Vrednost' začeti z '=' in uporabljati $korake (npr. =$12+$13).",
                    context=context,
                    column="Vrednost",
                    code="FORMULA_SYNTAX",
                )
            )
        if "$" not in value:
            errors.append(
                self.build_error(
                    "Formula ne vsebuje sklica na korake (npr. $12). Preveri sklice.",
                    context=context,
                    column="Vrednost",
                    code="FORMULA_NO_REFERENCE",
                    severity=self.severity if self.severity != Severity.INFO else None,
                )
            )
        if "&$" in value:
            errors.append(
                self.build_error(
                    "Formula vsebuje nedovoljen zapis '&$'. "
                    "Sklic na korak zapišite kot '\"$\"&' in celico s številko koraka "
                    "(npr. \"$\"&C12).",
                    context=context,
                    column="Vrednost",
                    code="FORMULA_AMPERSAND_DOLLAR",
                )
            )

        return errors


@register
class CommaNumberRule(RowRule):
    """Disallow decimal commas outside of explicitly permitted columns."""

    name = "comma_number_rule"
    description = "Decimalna pika je privzeta; vejice niso dovoljene (razen izjem)."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        allowed_columns = {"Navodilo"}
        if shared:
            allowed_columns.update(self._allowed_param_columns(row, shared))
            columns = shared.columns or [
                k for k in row.keys() if k not in VALIDATION_EXCLUDED_COLUMNS
            ]
        else:
            columns = [k for k in row.keys() if k not in VALIDATION_EXCLUDED_COLUMNS]

        errors = []
        for column in columns:
            if column in allowed_columns:
                continue
            value = coerce_str(row.get(column, ""))
            if not looks_like_number_with_commas(value):
                continue
            errors.append(
                self.build_error(
                    f"Vrednost v '{column}' vsebuje vejico v številu (ni dovoljeno). Uporabi decimalno piko.",
                    context=context,
                    column=column,
                    code="COMMA_NOT_ALLOWED",
                )
            )
        return errors

    def _allowed_param_columns(
        self,
        row: Mapping[str, object],
        shared,
    ) -> set[str]:
        allowed: set[str] = set()
        for ctrl_col in shared.control_columns:
            ctrl_val = coerce_str(row.get(ctrl_col, ""))
            if not ctrl_val:
                continue
            ctrl_name = norm_control_name(ctrl_val)
            if ctrl_name not in {"zaklenipolja", "aliobstajapogoj"}:
                continue
            ctrl_num = self._extract_control_number(ctrl_col)
            if ctrl_num is None:
                continue
            param_col = shared.param1_columns.get(ctrl_num)
            if param_col:
                allowed.add(param_col)
        return allowed

    @staticmethod
    def _extract_control_number(column_name: str) -> int | None:
        match = re.findall(r"\d+", column_name)
        if not match:
            return None
        try:
            return int(match[0])
        except ValueError:
            return None


@register
class NoSpacesRule(RowRule):
    """Preveri presledke v vmesnosti vrednosti (robni presledki niso prepovedani)."""

    name = "no_spaces_rule"
    description = (
        "V vseh stolpcih ne sme biti presledkov v vmesnosti vrednosti "
        "(izjemi: Navodilo, Labela, Vrednost, Ključ preverjanja)."
    )

    # Stolpci, kjer so presledki vedno dovoljeni
    EXCLUDED_COLUMNS: frozenset[str] = frozenset(
        {"Navodilo", "Labela", "Vrednost", "Ključ preverjanja"}
    )

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if shared:
            columns = shared.columns or [
                k for k in row.keys() if k not in VALIDATION_EXCLUDED_COLUMNS
            ]
        else:
            columns = [k for k in row.keys() if k not in VALIDATION_EXCLUDED_COLUMNS]

        for column in columns:
            if column in self.EXCLUDED_COLUMNS:
                continue
            value = row.get(column)
            if value is None:
                continue
            try:
                import pandas as pd
                if pd.isna(value):
                    continue
            except (ImportError, TypeError, ValueError):
                pass
            raw = str(value)
            inner = raw.strip()
            if not inner:
                continue
            if " " in inner:
                if column == "Zavihek":
                    message = (
                        "Vrednost v stolpcu 'Zavihek' vsebuje presledek (ni dovoljeno). "
                        "Popravite to celico — presledek ne odpira novega zavihka."
                    )
                else:
                    message = f"Vrednost v stolpcu '{column}' vsebuje presledek (ni dovoljeno)."
                yield self.build_error(
                    message,
                    context=context,
                    column=column,
                    code="SPACE_NOT_ALLOWED",
                )


_RANGE_DASH_RE = re.compile(r"(?P<before>[ \u00a0\t]*)(?P<dash>[–—-])(?P<after>[ \u00a0\t]*)")
_RANGE_LEFT_DASH_RE = re.compile(r"\d[^\s\d–—-]{0,8}$")
_RANGE_LEFT_HYPHEN_RE = re.compile(r"(?<![\w\-.,/])\d+(?:[.,]\d+)?$")
_RANGE_RIGHT_RE = re.compile(r"\d")
_RANGE_RIGHT_HYPHEN_RE = re.compile(r"\d+(?:[.,]\d+)?(?![\d\-/]|[.,]\d)")


def find_range_dash_spacing_problems(text: str) -> list[str]:
    """Vrni zapise razponov (npr. ``4000–4400``), ki nimajo presledka pred in za pomišljajem.

    Razpon je: število, pomišljaj (``–``, ``—``) ali vezaj (``-``) in število.
    Pri vezaju se upoštevajo samo samostojna števila (ne ``7647-14-5``, ``2026-01-01``
    ali ``A-1-2``). Pravilen zapis je ``4000 – 4400`` (en presledek pred in za).
    """
    problems: list[str] = []
    for match in _RANGE_DASH_RE.finditer(text):
        dash = match.group("dash")
        left = text[: match.start()]
        right = text[match.end():]
        if dash == "-":
            if not _RANGE_LEFT_HYPHEN_RE.search(left) or not _RANGE_RIGHT_HYPHEN_RE.match(right):
                continue
        else:
            if not _RANGE_LEFT_DASH_RE.search(left) or not _RANGE_RIGHT_RE.match(right):
                continue
        if len(match.group("before")) == 1 and len(match.group("after")) == 1:
            continue
        left_token = re.search(r"\S+$", left)
        right_token = re.match(r"\S+", right)
        problems.append(
            f"{left_token.group(0) if left_token else ''}"
            f"{match.group('before')}{dash}{match.group('after')}"
            f"{right_token.group(0) if right_token else ''}"
        )
    return problems


@register
class NavodiloRangeDashSpacingRule(RowRule):
    """Razpon v stolpcu Navodilo (npr. 4000 – 4400) mora imeti presledek pred in za pomišljajem."""

    name = "navodilo_range_dash_spacing_rule"
    description = (
        "V stolpcu 'Navodilo' mora biti pri razponu (npr. 4000 – 4400) "
        "presledek pred pomišljajem in za njim."
    )

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        navodilo = row.get("Navodilo")
        if not _cell_is_nonempty(navodilo):
            return
        problems = find_range_dash_spacing_problems(coerce_str(navodilo))
        if not problems:
            return
        examples = ", ".join(f"'{p}'" for p in dict.fromkeys(problems))
        yield self.build_error(
            "V stolpcu 'Navodilo' mora biti pri razponu presledek pred pomišljajem in za njim "
            f"(npr. 4000 – 4400). Najdeno: {examples}.",
            context=context,
            column="Navodilo",
            code="NAVODILO_RANGE_DASH_SPACING",
        )


@register
class FormulaReferenceRule(RowRule):
    """Ensure formulas reference existing steps."""

    name = "formula_reference_rule"
    description = "Formule se lahko sklicujejo le na obstoječe korake."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj not in FORMULA_OBJECT_TYPES:
            return []

        shared = context.shared
        if not shared or not shared.existing_steps:
            return []

        value = coerce_str(row.get("Vrednost", ""))
        if not value:
            return []

        missing_steps: set[int] = set()
        for match in FORMULA_REF.finditer(value):
            try:
                step = int(match.group(1))
            except ValueError:
                continue
            if step not in shared.existing_steps:
                missing_steps.add(step)

        for step in sorted(missing_steps):
            yield self.build_error(
                f"Formula se sklicuje na neobstoječi korak ${step}.",
                context=context,
                column="Vrednost",
                code="FORMULA_INVALID_REFERENCE",
            )


@register
class FormulaStepEditLabelaRule(RowRule):
    """Ensure formula-referenced steps have an allowed object type."""

    name = "formula_step_edit_labela_rule"
    description = "Koraki, na katere se formula sklicuje (v stolpcu Vrednost), morajo imeti Tip objekta 'edit', 'formula', 'formula0', 'formula1' ali 'klictehtnice1'."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj not in FORMULA_OBJECT_TYPES:
            return []

        shared = context.shared
        if not shared or not shared.existing_steps:
            return []

        value = coerce_str(row.get("Vrednost", ""))
        if not value or not value.strip().startswith("="):
            return []

        invalid_steps: set[int] = set()
        for match in FORMULA_REF.finditer(value):
            try:
                step = int(match.group(1))
            except ValueError:
                continue
            if step not in shared.existing_steps:
                continue  # formula_reference_rule handles missing steps
            if step not in shared.step_allowed_for_formula_ref:
                invalid_steps.add(step)

        for step in sorted(invalid_steps):
            yield self.build_error(
                f"Korak ${step}, na katerega se formula sklicuje, ni pravilen!",
                context=context,
                column="Vrednost",
                code="FORMULA_STEP_INVALID_TYPE",
            )

