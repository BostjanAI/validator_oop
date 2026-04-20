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
    LABELA_KODA_TYPES,
    STANDARD_TIP_PODATKA,
    VALIDATION_EXCLUDED_COLUMNS,
)
from validator_oop.core.error import Severity
from validator_oop.rules import RowRule, RuleContext, register
from validator_oop.utils import (
    coerce_str,
    extract_unit_token,
    extract_unit_token_near_number,
    looks_like_number_with_commas,
    norm_control_name,
    norm_text,
)

# Additional local constants not in core/constants.py
REQUIRED_KEY_TYPES: frozenset[str] = frozenset({"kemikalija", "raztopina", "masa", "tehtnica"})
FORMULA_OBJECT_TYPES: frozenset[str] = frozenset({"formula", "formula0", "formula1"})


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
    """Validate label requirements (koda in unit matching)."""

    name = "label_requirements"
    description = "Pravila za 'Labela' (koda in enote)."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        errors = []

        tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
        labela_raw = coerce_str(row.get("Labela", ""))
        labela_norm = norm_text(labela_raw)
        navodilo_raw = coerce_str(row.get("Navodilo", ""))

        if tip_data in LABELA_KODA_TYPES and labela_norm != "koda":
            errors.append(
                self.build_error(
                    f"Za tip podatka '{tip_data}' mora biti Labela = 'koda'.",
                    context=context,
                    column="Labela",
                    code="LABEL_MUST_BE_KODA",
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
class KeyValidationRule(RowRule):
    """Validate 'Ključ preverjanja'."""

    name = "key_validation"
    description = "Preveri format ključa in obveznost za določene tipe."

    def _find_invalid_char(self, key: str) -> str | None:
        """Poišče prvi nedovoljen znak v ključu in vrne njegov opis."""
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-.")
        char_descriptions = {
            " ": "presledek",
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
            if char not in allowed_chars:
                return char_descriptions.get(char, f"znak '{char}'")
        return None

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        errors = []
        key = coerce_str(row.get("Ključ preverjanja", ""))
        tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))

        if key and not KEY_PATTERN.fullmatch(key):
            invalid_char_desc = self._find_invalid_char(key)
            if invalid_char_desc:
                error_msg = f"Ključ preverjanja '{key}' vsebuje nedovoljen {invalid_char_desc}."
            else:
                error_msg = f"Ključ preverjanja '{key}' vsebuje nedovoljene znake. Dovoljeni so samo: črke (A-Z, a-z), številke (0-9), podčrtaj (_), vezaj (-) in pika (.)."
            
            errors.append(
                self.build_error(
                    error_msg,
                    context=context,
                    column="Ključ preverjanja",
                    code="KEY_INVALID_FORMAT",
                )
            )

        if tip_data in REQUIRED_KEY_TYPES and not key:
            errors.append(
                self.build_error(
                    "Za tipe 'kemikalija', 'raztopina', 'masa' in 'tehtnica' mora biti nastavljen 'Ključ preverjanja'.",
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
    description = "Formulska polja morajo začeti z '=' in vsebovati sklice."

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
    """Preveri, da vrednosti v vseh stolpcih (razen Navodilo in Labela) ne vsebujejo presledkov."""

    name = "no_spaces_rule"
    description = "V vseh stolpcih in vrsticah ne sme biti presledkov (izjemi: Navodilo, Labela)."

    # Stolpci, kjer so presledki vedno dovoljeni
    EXCLUDED_COLUMNS: frozenset[str] = frozenset({"Navodilo", "Labela"})

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
            if not raw.strip():
                continue
            if " " in raw:
                yield self.build_error(
                    f"Vrednost v stolpcu '{column}' vsebuje presledek (ni dovoljeno).",
                    context=context,
                    column=column,
                    code="SPACE_NOT_ALLOWED",
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
    description = "Koraki, na katere se formula sklicuje (v stolpcu Vrednost), morajo imeti Tip objekta 'edit', 'formula', 'formula0' ali 'formula1'."

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

