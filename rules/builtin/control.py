"""Control-related validation rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from validator_oop.core.constants import ALLOWED_CONTROLS_NORMALIZED, NUMERIC_TOKEN_RE
from validator_oop.core.error import Severity
from validator_oop.rules import RowRule, RuleContext, SheetRule, register
from validator_oop.utils import (
    base_key_no_trailing_number,
    coerce_str,
    decimals_from_eps,
    derive_decimal_step_from_text,
    eq_with_decimals,
    extract_unit_token,
    has_only_comma_separated_ints,
    is_equipment_row,
    is_equipment_tip,
    max_decimals,
    norm_control_name,
    norm_text,
    parse_checkbox_state,
    parse_navodilo_inequality,
    parse_navodilo_interval,
    parse_navodilo_pm,
    parse_navodilo_single,
    parse_time_lower_bound_from_navodilo,
    parse_time_range_from_navodilo,
)

# Use the normalized set from constants
ALLOWED_CONTROLS_NS = ALLOWED_CONTROLS_NORMALIZED

# Subset of controls that have a simple, fixed data-type context.
# More complex context rules (monolit, raztopina, oprema, ...) are implemented
# explicitly in ControlContextRule to mirror MES_validator.py.
SPECIFIC_TYPE_CONTROLS = {
    "kontrolaveljavnostikemikalije": {"kemikalija"},
    "kontrolaustreznostikemikalije": {"kemikalija"},
    "kontrolamase": {"masa"},
    "kontrolaembalaze": {"embalaza"},
    "kontrolaprazneembalaze": {"embalaza"},
}

EQUIPMENT_TYPES = {"tehtnica", "termometer", "kopel", "ph_meter", "sušilnik", "susilnik", "vak_sušilnik", "vak_susilnik"}
INPUT_OBJECT_TYPES = {"edit", "spustniseznam", "izberidatumcas", "gumbdatumcas", "memo"}

EXPECTED_CONTROLS = {
    "kemikalija": [["kontrolaveljavnostikemikalije"], ["kontrolaustreznostikemikalije"]],
    "masa": [["kontrolamase", "kontrolainterval", "kontrolarazlika"]],
    "embalaza": [["kontrolaembalaze", "kontrolaprazneembalaze"]],
    "datumcaskonec": [["kontrolacasa"]],
    "tehtnica": [["kontrolaveljavnostiopreme"], ["kontrolaustreznostiopreme"]],
    "termometer": [["kontrolaveljavnostiopreme"]],
    "kopel": [["kontrolaveljavnostiopreme"]],
    "ph_meter": [["kontrolaveljavnostiopreme"]],
    "sušilnik": [["kontrolaveljavnostiopreme"]],
    "susilnik": [["kontrolaveljavnostiopreme"]],
    "vak_sušilnik": [["kontrolaveljavnostiopreme"]],
    "vak_susilnik": [["kontrolaveljavnostiopreme"]],
    "monolit": [["kontrolaveljavnostimonolita"], ["kontrolaustreznostimonolita"]],
    "raztopina": [["kontrolaveljavnostiraztopine"], ["kontrolaustreznostiraztopine"]],
}

ZAKLENI_CONTROL = "zaklenipolja"
ALIOB_CONTROL = "aliobstajapogoj"
# Labela za checkbox: samo kljukica → zahteva aliObkljukan; kljukica/prazno → aliObkljukan ne sme biti
LABELA_DA_KLJUKICA = "da (kljukica)"
LABELA_DA_NE = "da (kljukica)/ne (prazno)"

# Tip objekta, pri katerih se zahtevata kontrolaInterval / kontrolaCasa ob številčnem intervalu
TIP_OBJEKTA_REQUIRE_INTERVAL_OR_CASA = frozenset({"edit", "formula", "formula0", "formula1"})


def _extract_control_number(column_name: str) -> int | None:
    match = re.findall(r"\d+", column_name)
    if not match:
        return None
    try:
        return int(match[0])
    except ValueError:
        return None


@dataclass(slots=True)
class ControlInstance:
    name_ns: str
    raw_name: str
    column: str
    ctrl_number: int | None
    param1_column: str | None
    param2_column: str | None


def _get_present_controls(row: Mapping[str, object], shared) -> list[ControlInstance]:
    if not shared:
        return []
    controls: list[ControlInstance] = []
    for column in shared.control_columns:
        raw = coerce_str(row.get(column, ""))
        if not raw:
            continue
        ctrl_number = _extract_control_number(column)
        param1_col = shared.param1_columns.get(ctrl_number) if ctrl_number is not None else None
        param2_col = shared.param2_columns.get(ctrl_number) if ctrl_number is not None else None
        controls.append(
            ControlInstance(
                name_ns=norm_control_name(raw),
                raw_name=raw,
                column=column,
                ctrl_number=ctrl_number,
                param1_column=param1_col,
                param2_column=param2_col,
            )
        )
    return controls


def _has_control(controls: Sequence[ControlInstance], name: str) -> bool:
    target = norm_control_name(name)
    return any(ctrl.name_ns == target for ctrl in controls)


def _get_control(controls: Sequence[ControlInstance], name: str) -> list[ControlInstance]:
    target = norm_control_name(name)
    return [ctrl for ctrl in controls if ctrl.name_ns == target]


def _navodilo_has_numeric_interval(navodilo: str) -> bool:
    """Return True if Navodilo contains a numeric range/±/inequality expression."""
    if not navodilo:
        return False
    # Normaliziraj posebne znake
    nav_clean = navodilo.replace("â‰¤", "≤").replace("â‰¥", "≥")

    a, b, _, _ = parse_navodilo_interval(nav_clean)
    if a is not None and b is not None:
        return True

    xpm, tpm, _, _ = parse_navodilo_pm(nav_clean)
    if xpm is not None and tpm is not None:
        return True

    op, xi, _, _ = parse_navodilo_inequality(nav_clean)
    if op and xi is not None:
        return True

    return False


@register
class UnknownControlsRule(RowRule):
    """Ensure every control is part of the allowed list."""

    name = "unknown_controls_rule"
    description = "Kontrole morajo biti iz znanega nabora."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []
        errors = []
        for control in _get_present_controls(row, shared):
            if control.name_ns not in ALLOWED_CONTROLS_NS:
                errors.append(
                    self.build_error(
                        f"Neznano ime kontrole: '{control.raw_name}'.",
                        context=context,
                        column=control.column,
                        code="KONTROLA_NEZNAN",
                    )
                )
        return errors


@register
class ControlContextRule(RowRule):
    """Validate that controls are placed on appropriate data/object types."""

    name = "control_context_rule"
    description = "Kontrole morajo biti na ustreznih tipih podatka/objekta."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        navodilo = coerce_str(row.get("Navodilo", ""))
        navodilo_clean = navodilo.replace("â‰¤", "≤").replace("â‰¥", "≥")
        nav_n = norm_text(navodilo)
        key_here = coerce_str(row.get("Ključ preverjanja", ""))
        label_value_raw = coerce_str(row.get("Labela", ""))
        label_value = norm_text(label_value_raw)
        controls = _get_present_controls(row, shared)
        present_names_ns = {ctrl.name_ns for ctrl in controls}
        is_hplc_pump = bool(re.search(r"hplc\s*[-–]?\s*(?:č|c)rpalka\b", nav_n))
        is_hplc_pump = bool(re.search(r"hplc\s*[-–]?\s*(?:č|c)rpalka\b", nav_n))
        is_hplc_pump = bool(re.search(r"hplc\s*[-–]?\s*(?:č|c)rpalka\b", nav_n))

        errors = []
        sensitive_ctrls_ns = {
            # Oprema (kemikalija in raztopina zahtevata samo polje 'koda', glej spodaj)
            "kontrolaveljavnostiopreme",
            "kontrolaustreznostiopreme",
            "kontrolaustreznostiopremeizmase",
        }
        for control in controls:
            name_ns = control.name_ns

            if name_ns not in ALLOWED_CONTROLS_NS:
                errors.append(
                    self.build_error(
                        f"Neznano ime kontrole: '{control.raw_name}'.",
                        context=context,
                        column=control.column,
                        code="KONTROLA_NEZNAN",
                    )
                )
                continue

            allowed_types = SPECIFIC_TYPE_CONTROLS.get(name_ns)
            if allowed_types and tip_data not in allowed_types:
                errors.append(
                    self.build_error(
                        f"Kontrola '{control.raw_name}' ni dovoljena na tipu '{tip_data}'.",
                        context=context,
                        column=control.column,
                        code="KONTROLA_NAPACEN_KONTEKST",
                    )
                )
                continue

            if name_ns in {"aliobkljukan", "aliniobkljukan"} and tip_obj != "checkbox":
                errors.append(
                    self.build_error(
                        f"Kontrola '{control.raw_name}' je smiselna le na checkbox poljih.",
                        context=context,
                        column=control.column,
                        code="KONTROLA_NAPACEN_KONTEKST",
                    )
                )
                continue

            # Kontrole za opremo so dovoljene na spustnem seznamu ali polju 'koda'.
            # (Kemikalija in raztopina zahtevata samo polje 'koda' – glej bloke spodaj.)
            if name_ns in sensitive_ctrls_ns:
                is_koda_field = label_value == "koda"
                if not (tip_obj == "spustniseznam" or is_koda_field):
                    errors.append(
                        self.build_error(
                            (
                                f"Kontrola '{control.raw_name}' je dovoljena samo na spustnem seznamu "
                                f"ali polju 'koda'. Trenutni Tip objekta='"
                                f"{coerce_str(row.get('Tip objekta', '')).strip()}', "
                                f"Labela='{label_value_raw.strip()}'."
                            ),
                            context=context,
                            column=control.column,
                            code="KONTROLA_NAPACEN_KONTEKST",
                        )
                    )
                    continue

            equipment_ctrls_ns = {
                "kontrolaveljavnostiopreme",
                "kontrolaustreznostiopreme",
                "kontrolaustreznostiopremeizmase",
            }

            def equipment_context_ok() -> bool:
                if is_equipment_tip(tip_data_raw):
                    return True
                if key_here and key_here in shared.equipment_keys:
                    return True
                return False

            if name_ns in equipment_ctrls_ns:
                if is_hplc_pump:
                    continue
                if not equipment_context_ok():
                    tip_podatka_current = coerce_str(row.get("Tip podatka", "")).strip()
                    errors.append(
                        self.build_error(
                            (
                                f"Kontrola '{control.raw_name}' mora biti na opremi ali povezani vrstici (isti ključ kot oprema). "
                                f"Trenutno: Tip podatka='{tip_podatka_current}'"
                            ),
                            context=context,
                            column=control.column,
                            code="KONTROLA_NAPACEN_KONTEKST",
                        )
                    )
                continue

            if name_ns in {"kontrolaveljavnostikemikalije", "kontrolaustreznostikemikalije"}:
                if not tip_data.startswith("kemikalija"):
                    errors.append(
                        self.build_error(
                            f"Kontrola '{control.raw_name}' je na polju, ki ni 'kemikalija'.",
                            context=context,
                            column=control.column,
                            code="KONTROLA_NAPACEN_KONTEKST",
                        )
                    )
                    continue
                # Dovoljeno samo polje 'koda' (brez spustnega seznama).
                if label_value != "koda":
                    errors.append(
                        self.build_error(
                            (
                                f"Kontrola '{control.raw_name}' je dovoljena samo na polju 'koda'. "
                                f"Trenutni Tip objekta='{coerce_str(row.get('Tip objekta', '')).strip()}', "
                                f"Labela='{label_value_raw.strip()}'."
                            ),
                            context=context,
                            column=control.column,
                            code="KONTROLA_NAPACEN_KONTEKST",
                        )
                    )
                    continue

            if name_ns in {"kontrolaveljavnostimonolita", "kontrolaustreznostimonolita"} and not tip_data.startswith(
                "monolit"
            ):
                errors.append(
                    self.build_error(
                        f"Kontrola '{control.raw_name}' je na polju, ki ni 'monolit'.",
                        context=context,
                        column=control.column,
                        code="KONTROLA_NAPACEN_KONTEKST",
                    )
                )
                continue

            if name_ns in {"kontrolaveljavnostiraztopine", "kontrolaustreznostiraztopine"}:
                if not tip_data.startswith("raztopina"):
                    errors.append(
                        self.build_error(
                            f"Kontrola '{control.raw_name}' je na polju, ki ni 'raztopina'.",
                            context=context,
                            column=control.column,
                            code="KONTROLA_NAPACEN_KONTEKST",
                        )
                    )
                    continue
                # Dovoljeno samo polje 'koda' (brez spustnega seznama).
                if label_value != "koda":
                    errors.append(
                        self.build_error(
                            (
                                f"Kontrola '{control.raw_name}' je dovoljena samo na polju 'koda'. "
                                f"Trenutni Tip objekta='{coerce_str(row.get('Tip objekta', '')).strip()}', "
                                f"Labela='{label_value_raw.strip()}'."
                            ),
                            context=context,
                            column=control.column,
                            code="KONTROLA_NAPACEN_KONTEKST",
                        )
                    )
                    continue

                # Validacija Param1 za raztopine
                if not key_here:
                    errors.append(
                        self.build_error(
                            "Kontrola raztopine brez ključa v vrstici.",
                            context=context,
                            column="Ključ preverjanja",
                            code="RAZTOPINA_KLJUC_MANJKA",
                        )
                    )
                else:
                    key_base = base_key_no_trailing_number(key_here)
                    
                    # Validacija Param1
                    param1_col = control.param1_column
                    if not param1_col:
                        errors.append(
                            self.build_error(
                                "Kontrola raztopine brez baze ključa (Param1).",
                                context=context,
                                column=control.column,
                                code="RAZTOPINA_P1_MANJKA",
                            )
                        )
                    else:
                        param1_value = coerce_str(row.get(param1_col, "")).strip()
                        if param1_value:
                            # Param1 mora biti enak bazi ključa (brez številke na koncu)
                            if param1_value != key_base:
                                errors.append(
                                    self.build_error(
                                        "Param1 ne ustreza bazi ključa",
                                        context=context,
                                        column=param1_col,
                                        code="RAZTOPINA_P1_BAZA",
                                    )
                                )
                    
                    # Validacija Param2 (če obstaja)
                    param2_col = control.param2_column
                    if param2_col:
                        param2_value = coerce_str(row.get(param2_col, "")).strip()
                        if param2_value:
                            # Param2 mora biti enak bazi ključa (brez številke na koncu)
                            if param2_value != key_base:
                                errors.append(
                                    self.build_error(
                                        "Param2 ne ustreza bazi ključa",
                                        context=context,
                                        column=param2_col,
                                        code="RAZTOPINA_P2_BAZA",
                                    )
                                )
                continue

            if name_ns == "kontrolacasa" and tip_data != "datumcaskonec":
                errors.append(
                    self.build_error(
                        "Kontrola 'kontrolaCasa' naj bo na zaključnem času (datumcaskonec).",
                        context=context,
                        column=control.column,
                        code="KONTROLA_NAPACEN_KONTEKST",
                    )
                )
                continue

        return errors


@register
class RequiredControlsRule(RowRule):
    """Rules about required/forbidden combinations (empty field controls)."""

    name = "required_controls_rule"
    description = "Kontrola praznih polj glede na tip objekta."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        controls = _get_present_controls(row, shared)

        errors = []
        has_empty_control = _has_control(controls, "kontrolapraznopolje")
        has_lock_control = _has_control(controls, ZAKLENI_CONTROL)

        # Ne zahtevaj kontrolaPraznoPolje, če so vse kontrolne kolone že zasedene (npr. vse 4)
        all_control_slots_used = len(controls) == len(shared.control_columns) if shared.control_columns else False
        if (
            tip_obj in INPUT_OBJECT_TYPES
            and not has_empty_control
            and not has_lock_control
            and not all_control_slots_used
        ):
            errors.append(
                self.build_error(
                    "Manjka kontrola 'kontrolaPraznoPolje' pri vnosnem polju.",
                    context=context,
                    column="(Kontrole)",
                    code="KONTROLA_ZAHTEVANO_PRAZNO",
                )
            )

        if tip_obj == "checkbox" and has_empty_control and not has_lock_control:
            errors.append(
                self.build_error(
                    "Checkbox ne sme imeti 'kontrolaPraznoPolje'.",
                    context=context,
                    column="(Kontrole)",
                    code="KONTROLA_CHECKBOX_PRAZNO",
                )
            )

        # Pri zaklenipolja na checkbox ne sme biti kontrolapraznopolje
        if tip_obj == "checkbox" and has_lock_control and has_empty_control:
            errors.append(
                self.build_error(
                    "Pri 'zaklenipolja' na checkbox ne sme biti kontrola 'kontrolaPraznoPolje'.",
                    context=context,
                    column="(Kontrole)",
                    code="KONTROLA_ZAKLENI_BREZ_PRAZNO",
                )
            )
        return errors


@register
class ExpectedControlsRule(RowRule):
    """Warn when recommended controls are missing."""

    name = "expected_controls_rule"
    description = "Opozorila za priporočene kontrole glede na tip podatka."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        navodilo = coerce_str(row.get("Navodilo", ""))
        nav_n = norm_text(navodilo)
        label_value = coerce_str(row.get("Labela", ""))
        vrednost = coerce_str(row.get("Vrednost", ""))
        controls = _get_present_controls(row, shared)
        present_names_ns = {ctrl.name_ns for ctrl in controls}
        is_hplc_pump = bool(re.search(r"hplc\s*[-–]?\s*(?:č|c)rpalka\b", nav_n))

        def warn_if_missing_any(one_of: list[str], label: str) -> None:
            if any(_has_control(controls, ctrl_name) for ctrl_name in one_of):
                return

            message = f"{label} manjka: pričakovana vsaj ena od {one_of}"
            if label.startswith("Oprema –"):
                tip_current = tip_data_raw.strip()
                if tip_current:
                    if " manjka:" in message:
                        pref, rest = message.split(" manjka:", 1)
                        message = f"{pref} za opremo '{tip_current}' manjka:{rest}"
            errors.append(
                self.build_error(
                    message,
                    context=context,
                    column="(Kontrole)",
                    code="KONTROLA_PRICAKOVANO_MANJKA",
                    severity=Severity.WARNING,
                )
            )

        errors = []
        tip_n = tip_data

        if tip_n == "kemikalija":
            for needed in [["kontrolaveljavnostikemikalije"], ["kontrolaustreznostikemikalije"]]:
                warn_if_missing_any(needed, "Kemikalija – pričakovane kontrole")

        if tip_n == "masa":
            porabljan_word = bool(re.search(r"\bporablj\w*\b", nav_n, flags=re.IGNORECASE))
            volume_number_present = bool(re.search(r"\d+(?:[.,]\d+)?\s*(?:ml|l)\b", navodilo, flags=re.IGNORECASE))
            has_concentration = bool(re.search(r"\b(?:mg|g)\s*/\s*ml\b", nav_n, flags=re.IGNORECASE))
            label_unit_token = extract_unit_token(label_value)
            nav_unit_token = extract_unit_token(navodilo)
            any_volume_unit = (label_unit_token in {"ml", "l"}) or (nav_unit_token in {"ml", "l"})
            concentration_implies_volume = has_concentration and any_volume_unit
            no_numeric_in_navodilo = not bool(NUMERIC_TOKEN_RE.search(nav_n))
            vrednost_has_number = bool(NUMERIC_TOKEN_RE.search(vrednost))
            masa_is_exception = (
                porabljan_word
                or volume_number_present
                or concentration_implies_volume
                or no_numeric_in_navodilo
            ) and (not vrednost_has_number)
            if not masa_is_exception:
                warn_if_missing_any(
                    ["kontrolamase", "kontrolainterval", "kontrolarazlika"],
                    "Masa – pričakovane kontrole",
                )

        if tip_n == "embalaza":
            for needed in [["kontrolaembalaze"], ["kontrolaprazneembalaze"]]:
                warn_if_missing_any(needed, "Embalaža – pričakovana kontrola")

        if is_equipment_row(tip_data_raw, present_names_ns) and not is_hplc_pump:
            warn_if_missing_any(["kontrolaveljavnostiopreme"], "Oprema – pričakovana kontrola veljavnosti")
            if tip_n == "tehtnica":
                # Zahteva kontrolaustreznostiopreme samo, če obstaja masa z enakim ključem
                key_here = coerce_str(row.get("Ključ preverjanja", ""))
                masa_keys = shared.get_keys_for_type("masa")
                if key_here and key_here in masa_keys:
                    warn_if_missing_any(["kontrolaustreznostiopreme"], "Oprema – pričakovana kontrola ustreznosti")

        if tip_n.startswith("monolit"):
            warn_if_missing_any(["kontrolaveljavnostimonolita"], "Monolit – pričakovana kontrola veljavnosti")
            warn_if_missing_any(["kontrolaustreznostimonolita"], "Monolit – pričakovana kontrola ustreznosti")

        if tip_n.startswith("raztopina"):
            warn_if_missing_any(["kontrolaveljavnostiraztopine"], "Raztopina – pričakovana kontrola veljavnosti")
            warn_if_missing_any(["kontrolaustreznostiraztopine"], "Raztopina – pričakovana kontrola ustreznosti")

        return errors


@register
class ZakleniParamRule(RowRule):
    """Validate Param1 for zaklenipolja controls."""

    name = "zakleni_param_rule"
    description = "Param1 pri 'zaklenipolja' mora biti seznam korakov."

    INT_LIST_PATTERN = re.compile(r"^\s*\d+(?:\s*,\s*\d+)*\s*$")

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        controls = _get_present_controls(row, shared)
        zakleni_controls = _get_control(controls, ZAKLENI_CONTROL)
        if not zakleni_controls:
            return []

        errors = []
        for control in zakleni_controls:
            param_col = control.param1_column
            value = coerce_str(row.get(param_col or "", ""))
            if not value:
                continue
            if "#" in value:
                errors.append(
                    self.build_error(
                        "Param1 vsebuje Excel napako.",
                        context=context,
                        column=param_col or control.column,
                        code="ZAKLENI_PAR1_EXCEL_NAPAKA",
                    )
                )
                continue
            if not self.INT_LIST_PATTERN.fullmatch(value):
                errors.append(
                    self.build_error(
                        "Param1 mora biti seznam celih števil, ločenih z vejicami (npr. 12, 13, 14).",
                        context=context,
                        column=param_col or control.column,
                        code="ZAKLENI_PAR1_FORMAT",
                    )
                )
                continue

            # Interpret Param1 as list of step numbers
            require_pogoj = not shared.extra.get(
                "bypass_zakleni_require_pogoj_for_param1_steps",
                True,
            )
            for token in value.split(","):
                step = int(token.strip())
                if step not in shared.existing_steps:
                    errors.append(
                        self.build_error(
                            f"Korak {step} iz Param1 ne obstaja v tabeli.",
                            context=context,
                            column=param_col or control.column,
                            code="ZAKLENI_P1_KORAK_MANJKA",
                        )
                    )
                elif require_pogoj and "aliobstajapogoj" not in shared.step_to_controls.get(step, set()):
                    errors.append(
                        self.build_error(
                            f"Korak {step} mora imeti kontrolo 'aliObstajaPogoj'.",
                            context=context,
                            column=param_col or control.column,
                            code="ZAKLENI_P1_BREZ_POGOJA",
                        )
                    )
        return errors


@register
class AliObstajaPogojCombinationRule(RowRule):
    """Validate Param1/Param2 combinations for aliObstajaPogoj."""

    name = "aliobstajapogoj_combo_rule"
    description = "Param1/Param2 kombinacije morajo slediti pravilom zakleniPolja."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        controls = _get_present_controls(row, shared)
        ali_controls = _get_control(controls, ALIOB_CONTROL)
        if not ali_controls:
            return []

        step_token = coerce_str(row.get("št. Koraka", ""))
        try:
            step_here = int(step_token)
        except ValueError:
            step_here = None

        if step_here is None:
            return []

        step_keys = shared.keys_by_zakleni_step.get(step_here, set())
        all_zakleni = shared.all_zakleni_keys
        param1_columns = shared.param1_columns
        param2_columns = shared.param2_columns
        ali_locations = shared.ali_pogoj_step_locations

        if not step_keys:
            return []

        present_pairs: list[tuple[str, int | None]] = []
        for ctrl in ali_controls:
            ctrl_number = ctrl.ctrl_number
            if ctrl_number is None:
                continue
            p1_col = ctrl.param1_column or param1_columns.get(ctrl_number)
            p2_col = ctrl.param2_column or param2_columns.get(ctrl_number)
            p1_value = coerce_str(row.get(p1_col or "", ""))
            p2_value = coerce_str(row.get(p2_col or "", ""))
            if not p1_value or not p2_value:
                continue
            try:
                parsed_p2 = int(float(p2_value.replace(",", ".")))
            except Exception:
                parsed_p2 = None
            for key in [token.strip() for token in p1_value.split(",") if token.strip()]:
                present_pairs.append((key, parsed_p2))

        if not present_pairs:
            return []

        invalid: list[tuple[str, int | None]] = []
        for key, p2_val in present_pairs:
            if p2_val is None:
                invalid.append((key, p2_val))
                continue
            if key in step_keys:
                if p2_val != 0:
                    invalid.append((key, p2_val))
            elif key in all_zakleni:
                if p2_val != 1:
                    invalid.append((key, p2_val))
            else:
                invalid.append((key, p2_val))

        if not invalid:
            return []

        # Če so vsi neveljavni pari (key, 1) z key v step_keys, je vzrok odvečni koraki v zaklenipolja Param1 – napako poroča ZakleniParam1OdvecniKorakiRule
        if all(
            p2_val == 1 and key in step_keys for key, p2_val in invalid
        ):
            return []

        used_keys = sorted({key for key, _ in present_pairs if key})
        combos: list[str] = []
        for key in used_keys:
            if key in step_keys:
                combos.append(f"(Param1='{key}', Param2=0)")
            elif key in all_zakleni:
                combos.append(f"(Param1='{key}', Param2=1)")
        msg_tail = ", ".join(combos) if combos else "(ni definiranih kombinacij)"
        row_hint, col_hint = ali_locations.get(step_here, (None, None))
        target_context = context.with_row(row_hint) if row_hint else context
        column = col_hint or ali_controls[0].column or "(Kontrole)"

        return [
            self.build_error(
                "Korak iz Param1 nima zahtevane kombinacije Param1/Param2 za 'aliObstajaPogoj'. "
                f"Možne kombinacije: {msg_tail}",
                context=target_context,
                column=column,
                code="ZAKLENI_POGOJ_P1P2",
            )
        ]


@register
class ZakleniParam1OdvecniKorakiRule(RowRule):
    """Report on zaklenipolja row when Param1 contains steps that have aliObstajaPogoj with same key and Param2=1 (odvečni koraki)."""

    name = "zaklenipolja_param1_odvecni_koraki_rule"
    description = "Pri zaklenipolja v Param1 ne smejo biti koraki, kjer ima ta korak aliObstajaPogoj s tem ključem in Param2=1."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        controls = _get_present_controls(row, shared)
        if not _has_control(controls, ZAKLENI_CONTROL):
            return []

        key_here = coerce_str(row.get("Ključ preverjanja", "")).strip()
        if not key_here:
            return []

        step_key_param2 = getattr(shared, "step_key_param2", {})
        if not step_key_param2:
            return []

        for ctrl in _get_control(controls, ZAKLENI_CONTROL):
            p1_col = ctrl.param1_column
            if not p1_col:
                continue
            p1_val = coerce_str(row.get(p1_col, ""))
            if not p1_val or not has_only_comma_separated_ints(p1_val):
                continue
            odvecni: list[int] = []
            for tok in p1_val.split(","):
                tok = tok.strip()
                if not tok:
                    continue
                try:
                    ref_step = int(tok)
                    if step_key_param2.get((ref_step, key_here)) == 1:
                        odvecni.append(ref_step)
                except ValueError:
                    pass
            if odvecni:
                odvecni_str = ", ".join(str(s) for s in sorted(odvecni))
                yield self.build_error(
                    f"Pri zaklenipolja v Param1 so odvečni koraki: {odvecni_str}.",
                    context=context,
                    column=p1_col,
                    code="ZAKLENI_P1_ODVECNI_KORAKI",
                )
            break  # only one zaklenipolja per row
        return


@register
class ZakleniUniqueKeyRule(SheetRule):
    """Ensure each 'zaklenipolja' control has a unique 'Ključ preverjanja' in the recipe."""

    name = "zaklenipolja_unique_key_rule"
    description = "Vsaka kontrola 'zaklenipolja' mora imeti unikaten ključ preverjanja."

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        errors = []
        tab_by_row = shared.tab_by_row
        
        # Grupiraj ključe po zavihku: tab -> key -> [(row_idx, column)]
        key_locations_by_tab: dict[str, dict[str, list[tuple[int, str]]]] = {}

        for row_idx, row in enumerate(rows, start=row_offset):
            controls = _get_present_controls(row, shared)
            zakleni_controls = _get_control(controls, ZAKLENI_CONTROL)
            if not zakleni_controls:
                continue

            key = coerce_str(row.get("Ključ preverjanja", "")).strip()
            if not key:
                # Don't enforce uniqueness for missing keys here (handled by other rules if needed)
                continue

            tab = tab_by_row.get(row_idx, "")
            key_locations_by_tab.setdefault(tab, {}).setdefault(key, []).append(
                (row_idx, "Ključ preverjanja")
            )

        # Preveri podvojenost znotraj vsakega zavihka
        for tab, key_locations in key_locations_by_tab.items():
            for key, locs in key_locations.items():
                if len(locs) <= 1:
                    continue
                row_list = ", ".join(str(r) for r, _ in locs)
                tab_info = f" v zavihku '{tab}'" if tab else ""
                for row_idx, col_name in locs:
                    errors.append(
                        self.build_error(
                            f"Kontrola 'zaklenipolja' ima podvojen ključ preverjanja '{key}'{tab_info}. "
                            f"Pojavitve (vrstice): {row_list}.",
                            context=context.with_row(row_idx),
                            column=col_name,
                            code="ZAKLENI_KLJUC_PODVOJEN",
                        )
                    )

        return errors


@register
class ZakleniInverseRule(SheetRule):
    """Every aliObstajaPogoj step must appear in some zaklenipolja Param1."""

    name = "zakleni_inverse_rule"
    description = "Koraki z 'aliObstajaPogoj' morajo biti navedeni pri 'zaklenipolja'."

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        # Tab-aware: the same step numbers repeat per tab, so we must validate
        # 'aliObstajaPogoj' vs 'zaklenipolja Param1' within each tab separately.
        locations_by_tab = getattr(shared, "ali_pogoj_step_locations_by_tab", {})
        param1_steps_by_tab = getattr(shared, "zakleni_param1_steps_by_tab", {})

        errors = []
        for tab in sorted(locations_by_tab.keys()):
            step_locations = locations_by_tab.get(tab, {})
            zakleni_steps = param1_steps_by_tab.get(tab, set())
            for step in sorted(step_locations.keys()):
                if step in zakleni_steps:
                    continue
                for row_index, column in step_locations.get(step, []):
                    errors.append(
                        self.build_error(
                            f"Korak {step} ima 'aliObstajaPogoj', vendar ni naveden v Param1 pri 'zaklenipolja'.",
                            context=context.with_row(row_index),
                            column=column,
                            code="ZAKLENI_P1_MANJKA_ZA_POGOJ",
                        )
                    )
        return errors


@register
class ZakleniCheckboxRule(RowRule):
    """Handle zaklenipolja/aliObstajaPogoj + checkbox; Labela DA/NE forbids aliObkljukan."""

    name = "zakleni_checkbox_rule"
    description = "Pri 'zaklenipolja' na checkboxu 'aliObkljukan' ne sme biti. Pri checkboxu z 'DA (kljukica)/NE (prazno)' tudi 'aliObkljukan' ne sme biti."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        controls = _get_present_controls(row, shared)
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
        labela_norm = norm_text(coerce_str(row.get("Labela", "")))

        errors = []
        has_aliobkljukan = _has_control(controls, "aliobkljukan")

        # Na checkboxu: če je zaklenipolja, aliObkljukan ne sme biti
        if tip_data == "checkbox" and has_aliobkljukan:
            if _has_control(controls, ZAKLENI_CONTROL):
                errors.append(
                    self.build_error(
                        "Pri 'zaklenipolja' na checkboxu ni dovoljena kontrola 'aliObkljukan'.",
                        context=context,
                        column="(Kontrole)",
                        code="KONTROLA_ZAKLENI_BREZ_ALIOB",
                    )
                )

        # Pri checkboxu z Labela 'DA (kljukica)/NE (prazno)' aliObkljukan ne sme biti
        if has_aliobkljukan and (labela_norm == LABELA_DA_NE or "/ne (prazno)" in labela_norm):
            errors.append(
                self.build_error(
                    "Pri checkboxu z 'DA (kljukica)/NE (prazno)' ni dovoljena kontrola 'aliObkljukan'.",
                    context=context,
                    column="(Kontrole)",
                    code="KONTROLA_CHECKBOX_DA_NE_BREZ_ALIOB",
                )
            )

        # Pri zaklenipolja na checkbox ne sme biti kontrolapraznopolje
        if (
            tip_obj == "checkbox"
            and _has_control(controls, ZAKLENI_CONTROL)
            and _has_control(controls, "kontrolapraznopolje")
        ):
            errors.append(
                self.build_error(
                    "Pri 'zaklenipolja' na checkbox ne sme biti kontrola 'kontrolaPraznoPolje'.",
                    context=context,
                    column="(Kontrole)",
                    code="KONTROLA_ZAKLENI_BREZ_PRAZNO",
                )
            )
        return errors


@register
class AliObkljukanParamRule(RowRule):
    """Validate aliObkljukan parameters and checkbox state."""

    name = "aliobkljukan_param_rule"
    description = "ALI Obkljukan parametri morajo biti DA/NE in skladni s stanjem checkboxa."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        controls = _get_present_controls(row, shared)
        ali_controls = _get_control(controls, "aliobkljukan")
        if not ali_controls:
            return []

        key = coerce_str(row.get("Ključ preverjanja", ""))
        checkbox_state = shared.checkbox_states.get(key)

        errors = []
        for control in ali_controls:
            param_value = norm_text(coerce_str(row.get(control.param1_column or "", "")))
            if param_value not in {"da", "ne"}:
                errors.append(
                    self.build_error(
                        "aliObkljukan zahteva Param1 = 'DA' ali 'NE'.",
                        context=context,
                        column=control.param1_column or control.column,
                        code="ALIOB_PARAM_DA_NE",
                    )
                )
                continue
            expected_state = 1 if param_value == "da" else 0
            if checkbox_state is not None and checkbox_state != expected_state:
                errors.append(
                    self.build_error(
                        f"Checkbox '{key}' pričakovan '{param_value.upper()}', najdeno: {'DA' if checkbox_state == 1 else 'NE'}.",
                        context=context,
                        column=control.column,
                        code="CHECKBOX_STANJE",
                    )
                )
        return errors


@register
class KontrolaIntervalParamRule(RowRule):
    """Basic numeric validation for kontrolaInterval."""

    name = "kontrola_interval_param_rule"
    description = "Parametri kontrolaInterval morajo biti numerični in pravilnega vrstnega reda."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        controls = _get_present_controls(row, shared)
        # Support both "kontrolainterval" and "kontrolaintervala" variants
        interval_controls = _get_control(controls, "kontrolainterval") + _get_control(controls, "kontrolaintervala")
        if not interval_controls:
            return []

        errors = []
        for control in interval_controls:
            p1 = coerce_str(row.get(control.param1_column or "", ""))
            p2 = coerce_str(row.get(control.param2_column or "", ""))
            if not p1 and not p2:
                errors.append(
                    self.build_error(
                        "kontrolaInterval potrebuje vsaj en parameter (min ali max).",
                        context=context,
                        column=control.param1_column or control.column,
                        code="KONTROLA_INTERVAL_PARAMETRI",
                    )
                )
                continue

            p1_val = self._parse_number(p1)
            p2_val = self._parse_number(p2)
            if p1 and p1_val is None:
                errors.append(
                    self.build_error(
                        f"Param1 '{p1}' ni številčna vrednost.",
                        context=context,
                        column=control.param1_column or control.column,
                        code="KONTROLA_INTERVAL_NI_STEVILO",
                    )
                )
            if p2 and p2_val is None:
                errors.append(
                    self.build_error(
                        f"Param2 '{p2}' ni številčna vrednost.",
                        context=context,
                        column=control.param2_column or control.column,
                        code="KONTROLA_INTERVAL_NI_STEVILO",
                    )
                )
            if p1_val is not None and p2_val is not None and p2_val <= p1_val:
                errors.append(
                    self.build_error(
                        "Param2 (max) mora biti večji od Param1 (min).",
                        context=context,
                        column=control.param2_column or control.column,
                        code="KONTROLA_INTERVAL_VRSTA",
                    )
                )
        return errors

    def _parse_number(self, value: str) -> float | None:
        if not value:
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None


@register
class KontrolaIntervalAdvancedRule(RowRule):
    """Advanced interpretation of kontrolaInterval vs Navodilo."""

    name = "kontrola_interval_advanced_rule"
    description = "Parametri kontrolaInterval morajo slediti navodilom (>, <, ±)."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        controls = _get_present_controls(row, shared)
        # Support both "kontrolainterval" and "kontrolaintervala" variants
        interval_controls = _get_control(controls, "kontrolainterval") + _get_control(controls, "kontrolaintervala")
        if not interval_controls:
            return []

        navodilo = coerce_str(row.get("Navodilo", ""))
        # Normaliziraj posebne znake (enako kot v ControlContextRule)
        navodilo_clean = navodilo.replace("â‰¤", "≤").replace("â‰¥", "≥")
        a, b, unit_range, step_ab = parse_navodilo_interval(navodilo_clean)
        xpm, tpm, unit_pm, step_pm = parse_navodilo_pm(navodilo_clean)
        op, xi, unit_ineq, step_in = parse_navodilo_inequality(navodilo_clean)
        if op is None:
            simple_match = re.search(r"(>=|<=|>|<|≥|≤)\s*(\d+(?:[.,]\d+)?)", navodilo_clean)
            if simple_match:
                raw_op = simple_match.group(1)
                if raw_op in (">=", "≥"):
                    op = ">="
                elif raw_op in ("<=", "≤"):
                    op = "<="
                else:
                    op = raw_op
                xi = float(simple_match.group(2).replace(",", "."))
                step_in = step_in or derive_decimal_step_from_text(navodilo)
        errors = []

        for control in interval_controls:
            p1_raw = coerce_str(row.get(control.param1_column or "", ""))
            p2_raw = coerce_str(row.get(control.param2_column or "", ""))
            p1_val = self._parse_number(p1_raw)
            p2_val = self._parse_number(p2_raw)
            p1_is_num = p1_val is not None
            p2_is_num = p2_val is not None

            def fmt(value: float | None, raw: str, decimals: int) -> str:
                if value is None:
                    return raw or ""
                return f"{value:.{decimals}f}"

            def pm_next_step_from_tolerance(tolerance: float) -> float:
                """Return next-step increment from last non-zero decimal in tolerance.

                Examples:
                - 0.20 -> 0.1
                - 0.14 -> 0.01
                - 0.032 -> 0.001
                """
                if tolerance <= 0:
                    return 1.0
                s = f"{tolerance:.12f}".rstrip("0").rstrip(".")
                if "." not in s:
                    return 1.0
                frac = s.split(".", 1)[1]
                for pos in range(len(frac), 0, -1):
                    if frac[pos - 1] != "0":
                        return 10 ** (-pos)
                return 1.0

            # 1) Neenačbe (>, >=, <, <=) – enako kot v MES_validator.py
            if op and xi is not None:
                eps = step_in if step_in is not None else derive_decimal_step_from_text(navodilo)
                d_exact = decimals_from_eps(eps)
                # Vsaj toliko decimalk kot jih narekuje korak, plus vse iz dejanskih vrednosti
                d_fmt = max(d_exact, max_decimals(xi, p1_val, p2_val, xi - eps, xi + eps))

                if op == ">":
                    # Strogo večje: Param1 mora biti ENAK xi, Param2 ≥ xi + eps
                    if not (p1_is_num and eq_with_decimals(p1_val, xi, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param1 mora biti {xi:.{d_fmt}f} – spodnja meja iz navodila {navodilo}. "
                                    f"(meja = {xi:.{d_fmt}f}) Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param1_column or control.column,
                                code="KONTROLA_INTERVAL_CILJ_P1",
                            )
                        )
                    if not (p2_is_num and round(p2_val, d_exact) >= round(xi + eps, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param2 mora biti ≥ {xi + eps:.{d_fmt}f} – zgornja meja iz navodila {navodilo}. "
                                    f"({xi:.{d_fmt}f} + x = {xi + eps:.{d_fmt}f}) Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param2_column or control.column,
                                code="KONTROLA_INTERVAL_CILJ_P2_MIN",
                            )
                        )
                elif op == ">=":
                    # Večje ali enako: Param1 = xi − eps, Param2 ≥ xi + eps
                    expected_p1 = xi - eps
                    if not (p1_is_num and eq_with_decimals(p1_val, expected_p1, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param1 mora biti {expected_p1:.{d_fmt}f} – (meja − korak) iz navodila {navodilo}. "
                                    f"({xi:.{d_fmt}f} − x = {expected_p1:.{d_fmt}f}) Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param1_column or control.column,
                                code="KONTROLA_INTERVAL_CILJ_P1",
                            )
                        )
                    if not (p2_is_num and round(p2_val, d_exact) >= round(xi + eps, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param2 mora biti ≥ {xi + eps:.{d_fmt}f} – zgornja meja iz navodila {navodilo}. "
                                    f"({xi:.{d_fmt}f} + x = {xi + eps:.{d_fmt}f}) Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param2_column or control.column,
                                code="KONTROLA_INTERVAL_CILJ_P2_MIN",
                            )
                        )
                elif op in (">", ">=", "<", "<="):
                    # Za preostale primere (<, <=) je p1 omejen zgoraj, p2 spodaj
                    if not (p1_is_num and round(p1_val, d_exact) <= round(xi - eps, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param1 mora biti ≤ {xi - eps:.{d_fmt}f} – iz navodila {navodilo}. "
                                    f"({xi:.{d_fmt}f} − x = {xi - eps:.{d_fmt}f}) Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param1_column or control.column,
                                code="KONTROLA_INTERVAL_CILJ_P1_MAX",
                            )
                        )
                    if op == "<":
                        # Strogo manjše: Param2 > xi + eps
                        comparison_ok = p2_is_num and p2_val > xi + eps
                        severity = "CTRL_INTERVAL_TARGET_P2_STRICT"
                        requirement_text = f"> {xi + eps:.{d_fmt}f}"
                    else:  # "<="
                        # Manjše ali enako: Param2 ≥ xi + eps
                        comparison_ok = p2_is_num and p2_val >= xi + eps
                        severity = "CTRL_INTERVAL_TARGET_P2_EXACT"
                        requirement_text = f"≥ {xi + eps:.{d_fmt}f}"
                    if not comparison_ok:
                        errors.append(
                            self.build_error(
                                (
                                    f"Param2 mora biti {requirement_text} – zgornja meja iz navodila {navodilo}. "
                                    f"({xi:.{d_fmt}f} + x = {xi + eps:.{d_fmt}f}) Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param2_column or control.column,
                                code=severity,
                            )
                        )
                continue

            # 2) ± notation
            if xpm is not None and tpm is not None:
                eps = step_pm if step_pm is not None else derive_decimal_step_from_text(navodilo)
                d_exact = decimals_from_eps(eps)
                
                # Preverimo, ali je tolerance decimalna (< 1) ali cela (>= 1)
                is_decimal_tolerance = tpm < 1.0
                
                if is_decimal_tolerance:
                    # Za decimalne tolerance (npr. 0.1) uporabljamo zaokroževalno logiko
                    # Določimo natančnost meritve iz tolerance (npr. 0.1 → 1 decimalno mesto)
                    # Uporabimo step_pm za določitev natančnosti tolerance (ne xpm)
                    # step_pm je izračunan iz max(d1, d2), kjer sta d1 in d2 decimalni mesti iz x in t
                    # Vendar moramo uporabiti natančnost tolerance (d2), ne max(d1, d2)
                    # Zato poiščimo najmanjši d, kjer je 10^(-d) enak tolerance
                    d_measurement = None
                    for d in range(0, 12):
                        step = 10 ** (-d)
                        if abs(tpm - step) < 1e-12:
                            d_measurement = d
                            break
                    # Če ni natančnega ujemanja, poiščimo najmanjši d, kjer je 10^(-d) <= tpm
                    if d_measurement is None:
                        for d in range(0, 12):
                            step = 10 ** (-d)
                            if tpm >= step:
                                d_measurement = d
                                break
                    if d_measurement is None:
                        d_measurement = d_exact
                    # Normaliziramo tolerance na to natančnost (samo za potence 10)
                    # Za tpm = 0.1: tpm_normalized = 0.1
                    # Za tpm = 0.5: tpm_normalized = 0.5 (ne 0.1!)
                    # Preverimo, ali je tpm potenca 10
                    is_power_of_10 = False
                    for d in range(0, 12):
                        step = 10 ** (-d)
                        if abs(tpm - step) < 1e-12:
                            is_power_of_10 = True
                            break
                    
                    if is_power_of_10:
                        tpm_normalized = 10 ** (-d_measurement) if d_measurement > 0 else 1.0
                    else:
                        # Če ni potenca 10, uporabimo tpm neposredno
                        tpm_normalized = tpm
                        # Določimo d_measurement iz tpm
                        d_measurement = decimals_from_eps(tpm) if tpm > 0 else d_exact
                    
                    # Za decimalne tolerance: left_req je spodnja meja intervala
                    # left_req = xpm - tpm (brez zaokroževanja xpm)
                    left_req = xpm - tpm_normalized
                    right_req = xpm + tpm_normalized
                    
                    # Param1 mora biti left_req - tolerance_zmanjšana_za_eno_decimalko
                    # Logika:
                    # 1. Najprej odštejemo toleranco od xpm: left_req = xpm - tpm (to je spodnja meja intervala)
                    # 2. Za Param1 od left_req odštejemo še tolerance, vendar zmanjšano za eno decimalko
                    # Primer: 8.0 ± 0.4
                    #         - Najprej: 8.0 - 0.4 = 7.6 (left_req, spodnja meja)
                    #         - Tolerance 0.4 ima 1 decimalno mesto, zmanjšamo za eno decimalko: 0.4 → 0.1
                    #         - Param1: 7.6 - 0.1 = 7.5 ✓
                    # Primer: 6.50 ± 0.10
                    #         - Najprej: 6.50 - 0.10 = 6.40 (left_req, spodnja meja)
                    #         - Tolerance 0.10 je potenca 10, uporabimo polno tolerance: 0.10
                    #         - Param1: 6.40 - 0.10 = 6.30 ✓
                    if is_power_of_10:
                        # Za tolerance, ki so potenca 10, odštejemo polno tolerance
                        param1_required = left_req - tpm_normalized
                        param2_step = tpm_normalized
                        param2_target = right_req + param2_step
                    else:
                        high_res_step = (10 * step_pm) if step_pm is not None else None
                        is_high_res_zero_tail = False
                        if (
                            step_pm is not None
                            and step_pm < 0.01
                            and high_res_step is not None
                            and high_res_step > 0
                        ):
                            # Uporabi "coarse" korak samo za tolerance tipa 0.140 (zadnja decimala je 0).
                            ratio = tpm_normalized / high_res_step
                            is_high_res_zero_tail = abs(ratio - round(ratio)) < 1e-9

                        if is_high_res_zero_tail:
                            # 14.010 ± 0.140: Param1 = xpm - (tpm + 0.01), Param2 = xpm + (tpm + 0.01)
                            offset_pm = tpm_normalized + high_res_step
                            param1_required = xpm - offset_pm
                        else:
                            # 8.0 ± 0.4, 2.00 ± 0.20 in 3.180 ± 0.032
                            tpm_decimals = decimals_from_eps(tpm_normalized)
                            if tpm_decimals == 1:
                                param1_required = left_req - tpm_normalized / 4
                            else:
                                param1_required = left_req - tpm_normalized / 10
                        # Param2 je vedno naslednji korak nad zgornjo mejo, določen z zadnjo
                        # neničelno decimalko tolerance (npr. 0.14 -> +0.01, 0.20 -> +0.1).
                        param2_step = pm_next_step_from_tolerance(tpm_normalized)
                        param2_target = right_req + param2_step
                    d_fmt = max_decimals(left_req, right_req, param1_required, p1_val, p2_val)
                    
                    # Za Param1: vrednost mora biti tako, da se zaokroži na param1_required
                    # Primer: 6.50 ± 0.10 → left_req = 6.40, param1_required = 6.30 (tolerance je potenca 10)
                    # 6.30 → zaokroži na 6.30 → veljavno (✓)
                    # 6.34 → zaokroži na 6.30 → veljavno (✓) - znotraj tolerance zaokroževanja
                    # 6.25 → zaokroži na 6.30 → veljavno (✓)
                    # 6.20 → zaokroži na 6.20 → neveljavno (✗) - premalo
                    # Primer: 8.0 ± 0.4 → left_req = 7.6, param1_required = 7.5 (tolerance ni potenca 10, uporabimo tpm/4)
                    # Validacija: vrednost mora biti znotraj param1_required ± tpm/4 = 7.5 ± 0.1 = [7.4, 7.6]
                    # 7.5 → znotraj [7.4, 7.6] → veljavno (✓)
                    # 7.4 → znotraj [7.4, 7.6] → veljavno (✓)
                    # 7.6 → znotraj [7.4, 7.6] → veljavno (✓)
                    # 7.2 → zunaj [7.4, 7.6] → neveljavno (✗) - premalo
                    # 7.7 → zunaj [7.4, 7.6] → neveljavno (✗) - preveč
                    p1_valid = False
                    if p1_is_num:
                        if is_power_of_10:
                            # Za tolerance, ki so potenca 10, uporabimo zaokroževalno logiko
                            p1_rounded_to_tolerance = round(p1_val / tpm_normalized) * tpm_normalized
                            # Preverimo, ali se ujema z param1_required
                            if eq_with_decimals(p1_rounded_to_tolerance, param1_required, d_measurement):
                                p1_valid = True
                        else:
                            # Za tolerance, ki niso potenca 10, preverimo, ali je vrednost znotraj param1_required ± tpm/4
                            tolerance_range = tpm_normalized / 4
                            if abs(p1_val - param1_required) <= tolerance_range:
                                p1_valid = True
                    
                    if not p1_valid:
                        errors.append(
                            self.build_error(
                                (
                                    f"Param1 mora biti {param1_required:.{d_fmt}f} – iz {xpm:.{d_fmt}f} ± {tpm:.{d_fmt}f}. "
                                    f"Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param1_column or control.column,
                                code="KONTROLA_INTERVAL_PM_P1",
                            )
                        )
                    
                    # Param2: območje okoli param2_target (right_req + step); npr. 5.5±0.1 → param2_target=5.7
                    p2_valid = False
                    if p2_is_num:
                        if is_power_of_10:
                            half = param2_step / 2
                            lo = param2_target - half
                            hi = param2_target + half - 1e-12
                            if lo <= p2_val <= hi:
                                p2_valid = True
                        else:
                            tolerance_range = tpm_normalized / 4
                            if abs(p2_val - param2_target) <= tolerance_range:
                                p2_valid = True
                    
                    if not p2_valid:
                        msg_target = f"{param2_target:.{d_fmt}f} (naslednja vrednost nad zgornjo dovoljeno mejo {right_req:.{d_fmt}f})"
                        errors.append(
                            self.build_error(
                                (
                                    f"Param2 mora biti {msg_target} – iz {xpm:.{d_fmt}f} ± {tpm:.{d_fmt}f}. "
                                    f"Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param2_column or control.column,
                                code="KONTROLA_INTERVAL_PM_P2",
                            )
                        )
                else:
                    # Za cele tolerance (>= 1) uporabljamo logiko odvisno od tega, ali ima xpm decimalna mesta
                    left_req = xpm - tpm
                    right_req = xpm + tpm
                    
                    # Preverimo, ali ima xpm decimalna mesta
                    # Če je xpm celo število (npr. 90), odštejemo 1
                    # Če xpm ima decimalna mesta (npr. 90.0), odštejemo 0.1
                    # Uporabimo eps za določitev decimalnih mest - če je eps < 1, ima xpm decimalna mesta
                    # Ali pa preverimo, ali je xpm celo število
                    xpm_is_integer = abs(xpm - round(xpm)) < 1e-10
                    # Preverimo tudi eps - če je eps decimalna vrednost (npr. 0.1), ima xpm decimalna mesta
                    eps_is_decimal = eps < 1.0
                    
                    # Če je xpm celo število IN eps ni decimalna vrednost, odštejemo 1
                    # Sicer odštejemo 0.1
                    if xpm_is_integer and not eps_is_decimal:
                        # xpm je celo število (npr. 90) in eps ni decimalna → odštejemo 1
                        param1_required = left_req - 1
                    else:
                        # xpm ima decimalna mesta (npr. 90.0) ali eps je decimalna → odštejemo 0.1
                        param1_required = left_req - 0.1
                    
                    # Za Param2 uporabimo enako logiko kot za Param1, vendar prištejemo namesto odštejemo
                    # Če je xpm celo število IN eps ni decimalna vrednost, prištejemo 1
                    # Sicer prištejemo 0.1
                    if xpm_is_integer and not eps_is_decimal:
                        # xpm je celo število (npr. 20) in eps ni decimalna → prištejemo 1
                        param2_required = right_req + 1
                    else:
                        # xpm ima decimalna mesta (npr. 20.0) ali eps je decimalna → prištejemo 0.1
                        param2_required = right_req + 0.1
                    
                    # Primer: 20 ± 1
                    #         - Najprej: 20 - 1 = 19 (left_req, spodnja meja), 20 + 1 = 21 (right_req, zgornja meja)
                    #         - xpm nima decimalnih mest, odštejemo 1 za Param1, prištejemo 1 za Param2
                    #         - Param1: 19 - 1 = 18, Param2: 21 + 1 = 22 ✓
                    # Primer: 90 ± 2
                    #         - Najprej: 90 - 2 = 88 (left_req), 90 + 2 = 92 (right_req)
                    #         - xpm nima decimalnih mest, odštejemo 1 za Param1, prištejemo 1 za Param2
                    #         - Param1: 88 - 1 = 87, Param2: 92 + 1 = 93 ✓
                    # Primer: 90.0 ± 2
                    #         - Najprej: 90.0 - 2 = 88.0 (left_req), 90.0 + 2 = 92.0 (right_req)
                    #         - xpm ima decimalna mesta, odštejemo 0.1 za Param1, prištejemo 0.1 za Param2
                    #         - Param1: 88.0 - 0.1 = 87.9, Param2: 92.0 + 0.1 = 92.1 ✓
                    
                    d_fmt = max_decimals(left_req, right_req, param1_required, param2_required, p1_val, p2_val)
                    if not (p1_is_num and eq_with_decimals(p1_val, param1_required, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param1 mora biti {param1_required:.{d_fmt}f} – iz {xpm:.{d_fmt}f} ± {tpm:.{d_fmt}f}. "
                                    f"Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param1_column or control.column,
                                code="KONTROLA_INTERVAL_PM_P1",
                            )
                        )
                    if not (p2_is_num and eq_with_decimals(p2_val, param2_required, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param2 mora biti {param2_required:.{d_fmt}f} – iz {xpm:.{d_fmt}f} ± {tpm:.{d_fmt}f}. "
                                    f"Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param2_column or control.column,
                                code="KONTROLA_INTERVAL_PM_P2",
                            )
                        )
                continue

            # 3) Range a-b
            if a is not None and b is not None:
                eps = step_ab if step_ab is not None else derive_decimal_step_from_text(navodilo)
                d_exact = decimals_from_eps(eps)
                lower = a - eps
                upper = b + eps
                d_fmt = max_decimals(a, b, lower, upper, p1_val, p2_val)

                if not (p1_is_num and eq_with_decimals(p1_val, lower, d_exact)):
                    errors.append(
                        self.build_error(
                                (
                                    f"Param1 mora biti {lower:.{d_fmt}f} – spodnja meja iz navodila {navodilo}. "
                                    f"({a:.{d_fmt}f} − x = {lower:.{d_fmt}f}) Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                            context=context,
                            column=control.param1_column or control.column,
                            code="KONTROLA_INTERVAL_P1_MEJA",
                        )
                    )
                if not (p2_is_num and eq_with_decimals(p2_val, upper, d_exact)):
                    errors.append(
                        self.build_error(
                                (
                                    f"Param2 mora biti {upper:.{d_fmt}f} – zgornja meja iz navodila {navodilo}. "
                                    f"({b:.{d_fmt}f} + x = {upper:.{d_fmt}f}) Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                                ),
                            context=context,
                            column=control.param2_column or control.column,
                            code="KONTROLA_INTERVAL_P2_MEJA",
                        )
                    )
                continue

        return errors

    def _parse_number(self, value: str) -> float | None:
        if not value:
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None


@register
class KontrolaCasaRule(RowRule):
    """Validate kontrolaCasa parameters and time matching."""

    name = "kontrola_casa_rule"
    description = "kontrolaCasa mora imeti pravilne parametre (sekunde) in slediti navodilom."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        controls = _get_present_controls(row, shared)
        casa_controls = _get_control(controls, "kontrolacasa")
        if not casa_controls:
            return []

        errors = []
        navodilo = coerce_str(row.get("Navodilo", ""))

        for control in casa_controls:
            p1 = coerce_str(row.get(control.param1_column or "", ""))
            p2 = coerce_str(row.get(control.param2_column or "", ""))

            p1_num = self._parse_number(p1)
            p2_num = self._parse_number(p2)

            # Basic validation
            if not p1:
                errors.append(
                    self.build_error(
                        "kontrolaCasa zahteva Param1 (min trajanje v sekundah).",
                        context=context,
                        column=control.param1_column or control.column,
                        code="KONTROLA_CAS_MIN",
                    )
                )
            elif p1_num is None:
                errors.append(
                    self.build_error(
                        f"kontrolaCasa Param1 '{p1}' ni številčna (sekunde).",
                        context=context,
                        column=control.param1_column or control.column,
                        code="KONTROLA_CAS_MIN_NI_STEVILO",
                    )
                )

            if p2 and p2_num is None:
                errors.append(
                    self.build_error(
                        f"kontrolaCasa Param2 '{p2}' ni številčna (sekunde).",
                        context=context,
                        column=control.param2_column or control.column,
                        code="KONTROLA_CAS_MAX_NI_STEVILO",
                    )
                )

            if p1_num is not None and p2_num is not None and p2_num < p1_num:
                errors.append(
                    self.build_error(
                        "kontrolaCasa Param2 (max) < Param1 (min).",
                        context=context,
                        column=control.param2_column or control.column,
                        code="KONTROLA_CAS_VRSTA",
                        severity=Severity.WARNING,
                    )
                )

            # Compare with time from navodilo
            errors.extend(
                self._validate_time_from_navodilo(
                    navodilo, p1_num, p2_num, control, context
                )
            )

        return errors

    def _validate_time_from_navodilo(
        self,
        navodilo: str,
        p1_num: float | None,
        p2_num: float | None,
        control: ControlInstance,
        context: RuleContext,
    ) -> list:
        """Validate Param1/Param2 against time expressions in navodilo."""
        errors = []

        # Parse inequality from navodilo
        op, xi, unit, _ = parse_navodilo_inequality(navodilo)

        if op and xi is not None:
            # Convert to seconds
            xi_seconds = self._convert_to_seconds(xi, unit)
            if xi_seconds is None:
                return errors

            if op in (">", ">=") and p1_num is not None:
                target_p1 = xi_seconds - 10.0  # 10 seconds tolerance
                if abs(p1_num - target_p1) > 1e-6:
                    errors.append(
                        self.build_error(
                            f"kontrolaCasa: Param1 mora biti {target_p1:.0f} s (iz navodila −10 s). "
                            f"Trenutno: {p1_num:.0f} s",
                            context=context,
                            column=control.param1_column or control.column,
                            code="KONTROLA_CAS_P1_NAVODILO",
                        )
                    )

            if op == "<=" and p2_num is not None:
                target_p2 = xi_seconds + 10.0
                if abs(p2_num - target_p2) > 1e-6:
                    errors.append(
                        self.build_error(
                            f"kontrolaCasa: Param2 mora biti {target_p2:.0f} s (iz navodila +10 s). "
                            f"Trenutno: {p2_num:.0f} s",
                            context=context,
                            column=control.param2_column or control.column,
                            code="KONTROLA_CAS_P2_NAVODILO",
                        )
                    )

            return errors

        # Parse time range from navodilo
        min_sec, max_sec = parse_time_range_from_navodilo(navodilo)
        if min_sec is not None and max_sec is not None:
            target_p1 = min_sec - 10.0
            target_p2 = max_sec + 10.0

            if p1_num is not None and abs(p1_num - target_p1) > 1e-6:
                errors.append(
                    self.build_error(
                        f"kontrolaCasa: Param1 mora biti {target_p1:.0f} s (min −10 s). "
                        f"Trenutno: {p1_num:.0f} s",
                        context=context,
                        column=control.param1_column or control.column,
                        code="KONTROLA_CAS_P1_NAVODILO",
                    )
                )

            if p2_num is not None and abs(p2_num - target_p2) > 1e-6:
                errors.append(
                    self.build_error(
                        f"kontrolaCasa: Param2 mora biti {target_p2:.0f} s (max +10 s). "
                        f"Trenutno: {p2_num:.0f} s",
                        context=context,
                        column=control.param2_column or control.column,
                        code="KONTROLA_CAS_P2_NAVODILO",
                    )
                )

        return errors

    def _convert_to_seconds(self, value: float, unit: str | None) -> float | None:
        """Convert time value to seconds based on unit."""
        if unit is None:
            # Default to hours
            return value * 3600.0

        u = unit.lower()
        if u in {"min", "minute", "minuta", "minuti", "minut"}:
            return value * 60.0
        if u in {"h", "hour", "hours", "ura", "ure", "ur"}:
            return value * 3600.0
        if u in {"d", "dan", "dni", "dnevi", "dneh", "dnevih", "day", "days"}:
            return value * 86400.0

        return value * 3600.0  # Default to hours

    def _parse_number(self, value: str) -> float | None:
        if not value:
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None


@register
class DatumCasKonecKontrolaCasaRequiredRule(RowRule):
    """Require kontrolaCasa on all datumcaskonec rows."""

    name = "datumcaskonec_kontrolacasa_required_rule"
    description = "Za tip podatka 'datumcasKonec' je obvezna kontrola 'kontrolaCasa'."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        if tip_data != "datumcaskonec":
            return []

        # Zahteva kontrolacasa samo pri Tip objekta edit/formula/formula0/formula1
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj not in TIP_OBJEKTA_REQUIRE_INTERVAL_OR_CASA:
            return []

        controls = _get_present_controls(row, shared)
        if _has_control(controls, "kontrolacasa"):
            return []

        return [
            self.build_error(
                "Manjka kontrola 'kontrolaCasa' pri tipu podatka 'datumcasKonec'.",
                context=context,
                column="(Kontrole)",
                code="KONTROLA_CAS_ZAHTEVANA",
            )
        ]


@register
class NavodiloIntervalKontrolaIntervalRequiredRule(RowRule):
    """Require kontrolaInterval when Navodilo contains numeric intervals (≥, range, ±)."""

    name = "navodilo_interval_kontrolainterval_required_rule"
    description = "Če Navodilo vsebuje številčni interval (≥, razpon, ±), je obvezna kontrola 'kontrolaInterval'."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        navodilo = coerce_str(row.get("Navodilo", ""))
        if not _navodilo_has_numeric_interval(navodilo):
            return []

        # Pri datumcaskonec je časovni interval pokrit s kontrolacasa, kontrolainterval ni obvezen
        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        if tip_data == "datumcaskonec":
            return []

        # Zahteva kontrolainterval samo pri Tip objekta edit/formula/formula0/formula1
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj not in TIP_OBJEKTA_REQUIRE_INTERVAL_OR_CASA:
            return []

        # Pri checkbox in pri Labela "koda" kontrolaInterval ni obvezna
        if tip_obj == "checkbox":
            return []
        labela_norm = norm_text(coerce_str(row.get("Labela", "")))
        if labela_norm == "koda":
            return []

        controls = _get_present_controls(row, shared)
        has_interval_ctrl = _has_control(controls, "kontrolainterval") or _has_control(
            controls, "kontrolaintervala"
        )
        if has_interval_ctrl:
            return []

        return [
            self.build_error(
                "Navodilo vsebuje številčni interval, vendar manjka kontrola 'kontrolaInterval'.",
                context=context,
                column="(Kontrole)",
                code="KONTROLA_INTERVAL_ZAHTEVANA",
            )
        ]


@register
class CheckboxAliObkljukanRequiredRule(RowRule):
    """Require aliObkljukan when Tip podatka is checkbox and Labela = 'DA (kljukica)' (samo kljukica).
    Ne zahtevaj, če je Labela 'DA (kljukica)/NE (prazno)' ali če je prisotna zaklenipolja.
    """

    name = "checkbox_aliobkljukan_required_rule"
    description = "Pri tipu 'checkbox' in Labela 'DA (kljukica)' je obvezna kontrola 'aliObkljukan'. Pri checkboxu z 'DA (kljukica)/NE (prazno)' ali pri zaklenipolja 'aliObkljukan' ne sme biti."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        if tip_data != "checkbox":
            return []

        labela_norm = norm_text(coerce_str(row.get("Labela", "")))
        # Zahtevamo aliObkljukan samo, če je Labela natančno "DA (kljukica)" (samo kljukica, brez "/NE (prazno)")
        if labela_norm != LABELA_DA_KLJUKICA:
            return []

        controls = _get_present_controls(row, shared)
        if _has_control(controls, ZAKLENI_CONTROL):
            return []
        if _has_control(controls, "aliobkljukan"):
            return []

        return [
            self.build_error(
                "Manjka kontrola 'aliObkljukan' pri checkboxu z Labela 'DA (kljukica)' (obvezna, če ni kontrole 'zaklenipolja').",
                context=context,
                column="(Kontrole)",
                code="KONTROLA_ALIOBKLJUKAN_ZAHTEVANA",
            )
        ]


@register
class ZaposleniAliPravavlogaKodaRequiredRule(RowRule):
    """Require alipravavlogakoda when Tip podatka is zaposleni."""

    name = "zaposleni_alipravavlogakoda_required_rule"
    description = "Za tip podatka 'zaposleni' je obvezna kontrola 'aliPravavlogaKoda'."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        if tip_data != "zaposleni":
            return []

        controls = _get_present_controls(row, shared)
        if _has_control(controls, "alipravavlogakoda"):
            return []

        return [
            self.build_error(
                "Manjka kontrola 'aliPravavlogaKoda' pri tipu podatka 'zaposleni'.",
                context=context,
                column="(Kontrole)",
                code="KONTROLA_ALIPRAVAVLOGAKODA_ZAHTEVANA",
            )
        ]


@register
class MonolitControlsRequiredRule(RowRule):
    """Require kontrolaveljavnostimonolita and kontrolaustreznostimonolita when Tip podatka is monolit/monolit1/monolit2/..."""

    name = "monolit_controls_required_rule"
    description = "Za tip podatka 'monolit' (monolit1, monolit2, ...) sta obvezni kontrole 'kontrolaVeljavnostiMonolita' in 'kontrolaUstreznostiMonolita'."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        if not tip_data.startswith("monolit"):
            return []

        controls = _get_present_controls(row, shared)
        errors = []

        if not _has_control(controls, "kontrolaveljavnostimonolita"):
            errors.append(
                self.build_error(
                    "Manjka kontrola 'kontrolaVeljavnostiMonolita' pri tipu podatka 'monolit'.",
                    context=context,
                    column="(Kontrole)",
                    code="KONTROLA_MONOLIT_VELJAVNOST_ZAHTEVANA",
                )
            )
        if not _has_control(controls, "kontrolaustreznostimonolita"):
            errors.append(
                self.build_error(
                    "Manjka kontrola 'kontrolaUstreznostiMonolita' pri tipu podatka 'monolit'.",
                    context=context,
                    column="(Kontrole)",
                    code="KONTROLA_MONOLIT_USTREZNOST_ZAHTEVANA",
                )
            )
        return errors


@register
class MasaKontrolaMaseBrezVrednostiRule(RowRule):
    """Disallow 'kontrolaMase' when Vrednost is empty for type 'masa'."""

    name = "masa_kontrolamase_brez_vrednosti_rule"
    description = "Pri tipu podatka 'masa' kontrola 'kontrolaMase' ni dovoljena, če je stolpec 'Vrednost' prazen."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        if tip_data != "masa":
            return []

        vrednost = coerce_str(row.get("Vrednost", "")).strip()
        if vrednost:
            return []

        controls = _get_present_controls(row, shared)
        if not _has_control(controls, "kontrolamase"):
            return []

        return [
            self.build_error(
                "Pri tipu podatka 'masa' kontrola 'kontrolaMase' ni dovoljena, če je stolpec 'Vrednost' prazen.",
                context=context,
                column="(Kontrole)",
                code="KONTROLA_MASA_BREZ_VREDNOSTI",
            )
        ]

