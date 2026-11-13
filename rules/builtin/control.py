"""Control-related validation rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence

from validator_oop.core.constants import (
    ALLOWED_CONTROLS_NORMALIZED,
    EXCEL_ERROR_TOKENS,
    NUMERIC_TOKEN_RE,
)
from validator_oop.core.error import Severity
from validator_oop.rules import RowRule, RuleContext, SheetRule, register
from validator_oop.utils import (
    coerce_str,
    decimal_places_of_first_number,
    decimals_from_eps,
    derive_decimal_step_from_text,
    extract_unit_token,
    is_equipment_row,
    is_equipment_tip,
    max_decimals,
    norm_control_name,
    norm_text,
    parse_checkbox_state,
    inequality_is_column_volume,
    parse_navodilo_inequality,
    parse_navodilo_interval,
    parse_navodilo_pm,
    parse_navodilo_single,
    match_navodilo_pm,
    parse_time_lower_bound_from_navodilo,
    parse_time_range_from_navodilo,
)

# Use the normalized set from constants
ALLOWED_CONTROLS_NS = ALLOWED_CONTROLS_NORMALIZED

# Subset of controls that have a simple, fixed data-type context.
# More complex context rules (monolit, raztopina, oprema, ...) are implemented
# explicitly in ControlContextRule to mirror MES_validator.py.
# Kontrole kemikalije in raztopine so pokrite z ChemicalSolutionControlsRule
# (obvezen par kontrol + točen tip podatka).
SPECIFIC_TYPE_CONTROLS = {
    "kontrolamase": {"masa"},
    "kontrolaembalaze": {"embalaza"},
    "kontrolaprazneembalaze": {"embalaza"},
}

EQUIPMENT_TYPES = {"tehtnica", "termometer", "kopel", "ph_meter", "sušilnik", "susilnik", "vak_sušilnik", "vak_susilnik", "naprava", "avtoklav"}
INPUT_OBJECT_TYPES = {"edit", "spustniseznam", "izberidatumcas", "gumbdatumcas", "memo"}
EMPTY_CONTROL_FORBIDDEN_OBJECT_TYPES = {"checkbox", "naslov", "crta"}

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
    "naprava": [["kontrolaveljavnostiopreme"]],
    "avtoklav": [["kontrolaveljavnostiopreme"]],
    "monolit": [["kontrolaveljavnostimonolita"], ["kontrolaustreznostimonolita"]],
    "raztopina": [["kontrolaveljavnostiraztopine"], ["kontrolaustreznostiraztopine"]],
    "repro": [["kontrolaveljavnostirepro"], ["kontrolaustreznostirepro"]],
}

ZAKLENI_CONTROL = "zaklenipolja"
ALIOB_CONTROL = "aliobstajapogoj"
INTERVAL_CONTROL_NAMES = ("kontrolainterval", "kontrolaintervala")
# Stolpec 'Kontrola 1' je rezerviran samo za te kontrole; ostale gredo v Kontrola 2+.
RESERVED_CONTROL_COLUMN_NUMBER = 1
RESERVED_FIRST_COLUMN_CONTROLS = frozenset({ZAKLENI_CONTROL, ALIOB_CONTROL, "aliobstajapogoj_ali"})
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


@dataclass(slots=True)
class NumericNavodiloParse:
    raw: str
    clean: str
    range_min: float | None
    range_max: float | None
    range_step: float | None
    pm_center: float | None
    pm_tolerance: float | None
    pm_step: float | None
    inequality_op: str | None
    inequality_value: float | None
    inequality_step: float | None
    pm_center_text: str | None = None
    pm_tolerance_text: str | None = None

    def has_numeric_interval(self) -> bool:
        return (
            (self.range_min is not None and self.range_max is not None)
            or (self.pm_center is not None and self.pm_tolerance is not None)
            or (self.inequality_op is not None and self.inequality_value is not None)
        )


@dataclass(slots=True)
class ControlContextState:
    row: Mapping[str, object]
    shared: Any
    tip_data_raw: str
    tip_data: str
    tip_obj: str
    navodilo_norm: str
    key_here: str
    label_value_raw: str
    label_value: str
    controls: list[ControlInstance]
    present_names_ns: set[str]
    is_hplc_pump: bool


def _normalize_navodilo_text(navodilo: str) -> str:
    return navodilo.replace("â‰¤", "≤").replace("â‰¥", "≥")


def _parse_number(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _decimal_eq(raw: str, target: float, d_exact: int) -> bool:
    """Primerja surovo vrednost iz Excel celice z pričakovano mejo brez napak plavajoče vejice.

    Namesto round(float, d) == round(float, d) (ki pri vrednostih kot 4.95 vrne
    napačen rezultat: round(4.95, 1) = 5.0) primerja Decimal reprezentaciji,
    ki temeljita na dejansko vpisanem nizu in formatiranem pričakovanem nizu.

    Kot varnostni mehanizem se pri majhnih razlikah (< 1e-9) vrednosti sprejmejo kot enake.
    To pokrije primere, kjer Excel formula vrne float z napako plavajoče vejice
    (npr. 3.340000000001 namesto 3.34), ki jo Excel sicer prikaže zaokroženo na 2 decimalki,
    openpyxl pa jo prebere z dodatno natančnostjo. Razlika mora biti bistveno manjša od
    najmanjšega koraka (eps ≥ 0.01), zato lažnih negativov ni.

    Primer: _decimal_eq("4.95", 5.0, 1) → Decimal('4.95') == Decimal('5.0') → False ✓
            _decimal_eq("5.0",  5.0, 1) → Decimal('5.0')  == Decimal('5.0') → True  ✓
            _decimal_eq("4.85", 4.9, 1) → Decimal('4.85') == Decimal('4.9') → False ✓
            _decimal_eq("3.340000000001", 3.34, 2) → abs diff < 1e-9 → True ✓
    """
    try:
        raw_dec = Decimal(raw.replace(",", "."))
        target_dec = Decimal(f"{target:.{d_exact}f}")
        if raw_dec == target_dec:
            return True
        # Fallback: sprejmi vrednosti z mikroskopsko razliko (napaka plavajoče vejice iz formulnih celic)
        return abs(raw_dec - target_dec) < Decimal("1e-9")
    except InvalidOperation:
        return False


def _decimal_places_stripped(value: Decimal) -> int:
    """Število decimalnih mest po odstranitvi trailing zeros (6.40 → 1)."""
    exponent = value.normalize().as_tuple().exponent
    if isinstance(exponent, int) and exponent < 0:
        return -exponent
    return 0


def _round_half_up(value: Decimal, decimals: int) -> Decimal:
    quant = Decimal(1) if decimals <= 0 else Decimal(10) ** -decimals
    return value.quantize(quant, rounding=ROUND_HALF_UP)


def _pm_rounding_band(lower: Decimal, upper: Decimal, d_round: int) -> tuple[Decimal, Decimal]:
    """Dovoljeni numerični pas za Param1/Param2 pri ± (ne samo zaokrožena vrednost).

    Za 6.50 ± 0.10: interval [6.40, 6.60], korak 0.1 → [6.34, 6.65].
    6.34 in 6.65 sta OK; 6.33 in 6.66 sta napaki.
    """
    step = Decimal(1) if d_round <= 0 else Decimal(10) ** -d_round
    fine = Decimal(10) ** -(d_round + 1)
    lo_r = _round_half_up(lower, d_round)
    hi_r = _round_half_up(upper, d_round)
    return lo_r - (step / 2) - fine, hi_r + (step / 2)


def _rounds_into_pm_interval(raw: str, lower: Decimal, upper: Decimal, d_round: int) -> bool:
    """True, če je raw v pasu [_pm_rounding_band]."""
    try:
        raw_dec = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return False
    lo, hi = _pm_rounding_band(lower, upper, d_round)
    return lo <= raw_dec <= hi


def _pm_param_matches(
    raw: str,
    is_num: bool,
    required: float,
    d_eq: int,
    lower: Decimal | None,
    upper: Decimal | None,
    d_round: int | None,
) -> bool:
    """Kanonska meja ali vrednost v numeričnem pasu okoli [x−t, x+t] (npr. 6.34–6.65)."""
    if not is_num:
        return False
    if _decimal_eq(raw, required, d_eq):
        return True
    if lower is None or upper is None or d_round is None:
        return False
    return _rounds_into_pm_interval(raw, lower, upper, d_round)


def _range_param_band(lower: Decimal, upper: Decimal, d_round: int) -> tuple[Decimal, Decimal]:
    """Dovoljeni pas Param1/Param2 pri razponu a–b, kjer bi bil a−eps enak 0.

    Za 0.01–0.30: [0.004, 0.305]. Param1 0.004 je prag pod meritvijo 0.005;
    Param2 0.305 je prag nad zadnjo meritvijo 0.304.
    Sicer (npr. 0.18–0.22, 47.5–52.5) veljata kanonska a−eps / b+eps na istih decimalkah.
    """
    step = Decimal(1) if d_round <= 0 else Decimal(10) ** -d_round
    fine = Decimal(10) ** -(d_round + 1)
    lo_r = _round_half_up(lower, d_round)
    hi_r = _round_half_up(upper, d_round)
    return lo_r - (step / 2) - fine, hi_r + (step / 2)


def _integer_range_one_decimal_match(raw: str, bound: float, *, is_lower: bool) -> bool:
    """Celo število v razponu beremo tudi kot N.0 (korak 0.1).

    Zapis ``45 - 51`` je zato veljaven kot ``45`` (Param1 ``44``) in kot ``45.0``
    (Param1 ``44.9``). Končne ničle se v navodilu včasih ne prikažejo.
    """
    whole = Decimal(int(round(bound)))
    target = whole - Decimal("0.1") if is_lower else whole + Decimal("0.1")
    return _decimal_eq(raw, float(target), 1)


def _range_param_matches(
    raw: str,
    is_num: bool,
    required: float | None,
    d_eq: int,
    bound_lo: Decimal,
    bound_hi: Decimal,
    d_round: int,
) -> bool:
    """Vrednost v [_range_param_band]; kanonski a−eps / b+eps le, če je required v pasu ali pri celih številih."""
    if not is_num:
        return False
    if required is not None and _decimal_eq(raw, required, d_eq):
        return True
    try:
        raw_dec = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return False
    lo, hi = _range_param_band(bound_lo, bound_hi, d_round)
    return lo <= raw_dec <= hi


def _parse_numeric_navodilo(navodilo: str) -> NumericNavodiloParse:
    navodilo_clean = _normalize_navodilo_text(navodilo)
    range_min, range_max, range_unit, range_step = parse_navodilo_interval(navodilo_clean)
    pm_match = match_navodilo_pm(navodilo_clean)
    pm_center, pm_tolerance, _, pm_step = parse_navodilo_pm(navodilo_clean)
    pm_center_text = pm_match.group("x") if pm_match else None
    pm_tolerance_text = pm_match.group("t") if pm_match else None
    inequality_op, inequality_value, _, inequality_step = parse_navodilo_inequality(navodilo_clean)

    if inequality_op is None:
        simple_match = re.search(r"(>=|<=|>|<|≥|≤)\s*(\d+(?:[.,]\d+)?)", navodilo_clean)
        if simple_match:
            raw_op = simple_match.group(1)
            if raw_op in (">=", "≥"):
                inequality_op = ">="
            elif raw_op in ("<=", "≤"):
                inequality_op = "<="
            else:
                inequality_op = raw_op
            inequality_value = float(simple_match.group(2).replace(",", "."))
            inequality_step = inequality_step or derive_decimal_step_from_text(navodilo)

    # "≥ 10 - 11 CV (≥ 4000 - 4400 mL)" is a closed range, not an unbounded ≥.
    # If the inequality value is one of the range endpoints, keep the range and drop ≥/<.
    if (
        range_min is not None
        and range_max is not None
        and inequality_op is not None
        and inequality_value is not None
        and (
            abs(inequality_value - range_min) < 1e-9
            or abs(inequality_value - range_max) < 1e-9
        )
    ):
        inequality_op = None
        inequality_value = None
        inequality_step = None

    # "≥ 3 CV (120000 - 340000 mL)" is the mL range, not an open ≥ 3.
    if (
        inequality_op is not None
        and range_min is not None
        and range_max is not None
        and range_unit in {"ml", "l", "ul"}
        and inequality_is_column_volume(navodilo_clean)
    ):
        inequality_op = None
        inequality_value = None
        inequality_step = None

    return NumericNavodiloParse(
        raw=navodilo,
        clean=navodilo_clean,
        range_min=range_min,
        range_max=range_max,
        range_step=range_step,
        pm_center=pm_center,
        pm_tolerance=pm_tolerance,
        pm_step=pm_step,
        pm_center_text=pm_center_text,
        pm_tolerance_text=pm_tolerance_text,
        inequality_op=inequality_op,
        inequality_value=inequality_value,
        inequality_step=inequality_step,
    )


def _get_present_controls(row: Mapping[str, object], shared) -> list[ControlInstance]:
    if not shared:
        return []
    controls: list[ControlInstance] = []
    for column in shared.control_columns:
        raw = coerce_str(row.get(column, ""))
        if not raw:
            continue
        ctrl_number = shared.control_numbers.get(column)
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


def _get_interval_controls(controls: Sequence[ControlInstance]) -> list[ControlInstance]:
    interval_controls: list[ControlInstance] = []
    for name in INTERVAL_CONTROL_NAMES:
        interval_controls.extend(_get_control(controls, name))
    return interval_controls


# Oznaka v Navodilu: meje iz navodila se ne primerjajo s Param1/Param2.
# Obveznost kontrole in preverjanje, da sta parametra številki v pravem vrstnem redu, ostaneta.
_INFO_NAVODILO_RE = re.compile(r"\(\s*info\b", re.IGNORECASE)


def _navodilo_is_info(navodilo: str) -> bool:
    """True, če Navodilo vsebuje oklepaj, ki se začne z info: (info), (info.) ali (info 3.0 - 5.5)."""
    if not navodilo:
        return False
    return _INFO_NAVODILO_RE.search(navodilo) is not None


def _navodilo_has_numeric_interval(navodilo: str) -> bool:
    """Return True if Navodilo contains a numeric range/±/inequality expression."""
    if not navodilo:
        return False
    return _parse_numeric_navodilo(navodilo).has_numeric_interval()


def _make_control_context_state(row: Mapping[str, object], shared) -> ControlContextState:
    tip_data_raw = coerce_str(row.get("Tip podatka", ""))
    navodilo = coerce_str(row.get("Navodilo", ""))
    controls = _get_present_controls(row, shared)
    navodilo_norm = norm_text(navodilo)
    return ControlContextState(
        row=row,
        shared=shared,
        tip_data_raw=tip_data_raw,
        tip_data=norm_text(tip_data_raw),
        tip_obj=norm_text(coerce_str(row.get("Tip objekta", ""))),
        navodilo_norm=navodilo_norm,
        key_here=coerce_str(row.get("Ključ preverjanja", "")),
        label_value_raw=coerce_str(row.get("Labela", "")),
        label_value=norm_text(coerce_str(row.get("Labela", ""))),
        controls=controls,
        present_names_ns={ctrl.name_ns for ctrl in controls},
        is_hplc_pump=bool(re.search(r"hplc\s*[-–]?\s*(?:č|c)rpalka\b", navodilo_norm)),
    )


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
                        code="CTRL_UNKNOWN",
                    )
                )
        return errors


@register
class ControlColumnOneReservedRule(RowRule):
    """Kontrola 1 je rezervirana za 'zaklenipolja' in 'aliObstajaPogoj'."""

    name = "control_column_one_reserved_rule"
    description = (
        "Stolpec 'Kontrola 1' je rezerviran za 'zaklenipolja' in 'aliObstajaPogoj'; "
        "vse ostale kontrole morajo biti v 'Kontrola 2' ali naprej."
    )

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []
        errors = []
        for control in _get_present_controls(row, shared):
            if control.ctrl_number != RESERVED_CONTROL_COLUMN_NUMBER:
                continue
            if control.name_ns in RESERVED_FIRST_COLUMN_CONTROLS:
                continue
            if control.name_ns not in ALLOWED_CONTROLS_NS:
                # Neznano ime že javi UnknownControlsRule (CTRL_UNKNOWN).
                continue
            errors.append(
                self.build_error(
                    f"Kontrola '{control.raw_name}' ne sme biti v stolpcu 'Kontrola 1' – "
                    "ta je rezerviran za 'zaklenipolja' in 'aliObstajaPogoj'. "
                    "Premaknite jo v 'Kontrola 2' ali naprej.",
                    context=context,
                    column=control.column,
                    code="CTRL_COL1_RESERVED",
                )
            )
        return errors


@register
class ExcelErrorTokenRule(RowRule):
    """Detect Excel error tokens in formula-related input cells."""

    name = "excel_error_token_rule"
    description = "Excel napake (#REF!, #N/A, ...) v Vrednost in Param stolpcih niso dovoljene."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        target_columns: list[str] = []
        if "Vrednost" in row:
            target_columns.append("Vrednost")

        for control in _get_present_controls(row, shared):
            if control.param1_column and control.param1_column not in target_columns:
                target_columns.append(control.param1_column)
            if control.param2_column and control.param2_column not in target_columns:
                target_columns.append(control.param2_column)

        errors = []
        for column in target_columns:
            token = self._find_excel_error_token(row.get(column))
            if not token:
                continue
            errors.append(
                self.build_error(
                    f"Celica vsebuje Excel napako '{token}'.",
                    context=context,
                    column=column,
                    code="EXCEL_ERROR_TOKEN",
                )
            )
        return errors

    @staticmethod
    def _find_excel_error_token(value: object) -> str | None:
        text = coerce_str(value).strip().upper()
        if not text:
            return None
        for token in EXCEL_ERROR_TOKENS:
            if token in text:
                return token
        return None


@register
class ControlContextRule(RowRule):
    """Validate that controls are placed on appropriate data/object types."""

    name = "control_context_rule"
    description = "Kontrole morajo biti na ustreznih tipih podatka/objekta."

    SENSITIVE_EQUIPMENT_CONTROLS = frozenset(
        {
            "kontrolaveljavnostiopreme",
            "kontrolaustreznostiopreme",
            "kontrolaustreznostiopremeizmase",
        }
    )
    EQUIPMENT_CONTEXT_CONTROLS = SENSITIVE_EQUIPMENT_CONTROLS
    KEMIKALIJA_CONTROLS = frozenset({"kontrolaveljavnostikemikalije", "kontrolaustreznostikemikalije"})
    MONOLIT_CONTROLS = frozenset({"kontrolaveljavnostimonolita", "kontrolaustreznostimonolita"})
    RAZTOPINA_CONTROLS = frozenset({"kontrolaveljavnostiraztopine", "kontrolaustreznostiraztopine"})
    CHECKBOX_ONLY_CONTROLS = frozenset({"aliobkljukan", "aliniobkljukan"})

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []
        state = _make_control_context_state(row, shared)

        errors = []
        for control in state.controls:
            validation_error = (
                self._validate_known_control(control, context)
                or self._validate_specific_type_control(control, state, context)
                or self._validate_checkbox_only_control(control, state, context)
                or self._validate_equipment_field_constraint(control, state, context)
                or self._validate_equipment_context(control, state, context)
                or self._validate_kemikalija_context(control, state, context)
                or self._validate_monolit_context(control, state, context)
                or self._validate_raztopina_context(control, state, context)
                or self._validate_aliisto_context(control, state, context)
                or self._validate_kontrolacasa_context(control, state, context)
            )
            if validation_error is not None:
                if isinstance(validation_error, list):
                    errors.extend(validation_error)
                else:
                    errors.append(validation_error)
        return errors

    def _build_invalid_context_error(
        self,
        message: str,
        context: RuleContext,
        column: str,
    ):
        return self.build_error(
            message,
            context=context,
            column=column,
            code="CTRL_INVALID_CONTEXT",
        )

    def _validate_known_control(self, control: ControlInstance, context: RuleContext):
        if control.name_ns in ALLOWED_CONTROLS_NS:
            return None
        return self.build_error(
            f"Neznano ime kontrole: '{control.raw_name}'.",
            context=context,
            column=control.column,
            code="CTRL_UNKNOWN",
        )

    def _validate_specific_type_control(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        allowed_types = SPECIFIC_TYPE_CONTROLS.get(control.name_ns)
        if not allowed_types or state.tip_data in allowed_types:
            return None
        return self._build_invalid_context_error(
            f"Kontrola '{control.raw_name}' ni dovoljena na tipu '{state.tip_data}'.",
            context=context,
            column=control.column,
        )

    def _validate_checkbox_only_control(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        if control.name_ns not in self.CHECKBOX_ONLY_CONTROLS or state.tip_obj == "checkbox":
            return None
        return self._build_invalid_context_error(
            f"Kontrola '{control.raw_name}' je smiselna le na checkbox poljih.",
            context=context,
            column=control.column,
        )

    def _validate_equipment_field_constraint(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        if control.name_ns not in self.SENSITIVE_EQUIPMENT_CONTROLS:
            return None
        is_koda_field = state.label_value == "koda"
        if state.tip_obj == "spustniseznam" or is_koda_field:
            return None
        if control.name_ns == "kontrolaustreznostiopremeizmase" and state.tip_obj == "klictehtnice1":
            return None
        return self._build_invalid_context_error(
            (
                f"Kontrola '{control.raw_name}' je dovoljena samo na spustnem seznamu "
                f"ali polju 'koda'. Trenutni Tip objekta='"
                f"{coerce_str(state.row.get('Tip objekta', '')).strip()}', "
                f"Labela='{state.label_value_raw.strip()}'."
            ),
            context=context,
            column=control.column,
        )

    def _equipment_context_ok(self, state: ControlContextState) -> bool:
        if is_equipment_tip(state.tip_data_raw):
            return True
        if state.key_here and state.key_here in state.shared.equipment_keys:
            return True
        return False

    def _validate_equipment_context(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        if control.name_ns not in self.EQUIPMENT_CONTEXT_CONTROLS or state.is_hplc_pump:
            return None
        if self._equipment_context_ok(state):
            return None
        return self._build_invalid_context_error(
            (
                f"Kontrola '{control.raw_name}' mora biti na opremi ali povezani vrstici (isti ključ kot oprema). "
                f"Trenutno: Tip podatka='{coerce_str(state.row.get('Tip podatka', '')).strip()}'"
            ),
            context=context,
            column=control.column,
        )

    def _validate_kemikalija_context(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        if control.name_ns not in self.KEMIKALIJA_CONTROLS:
            return None
        # Tip podatka preverja ChemicalSolutionControlsRule.
        if state.tip_data != "kemikalija":
            return None
        if state.label_value == "koda":
            return None
        return self._build_invalid_context_error(
            (
                f"Kontrola '{control.raw_name}' je dovoljena samo na polju 'koda'. "
                f"Trenutni Tip objekta='{coerce_str(state.row.get('Tip objekta', '')).strip()}', "
                f"Labela='{state.label_value_raw.strip()}'."
            ),
            context=context,
            column=control.column,
        )

    def _validate_monolit_context(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        if control.name_ns not in self.MONOLIT_CONTROLS or state.tip_data.startswith("monolit"):
            return None
        return self._build_invalid_context_error(
            f"Kontrola '{control.raw_name}' je na polju, ki ni 'monolit'.",
            context=context,
            column=control.column,
        )

    def _validate_raztopina_context(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        if control.name_ns not in self.RAZTOPINA_CONTROLS:
            return None
        # Tip podatka preverja ChemicalSolutionControlsRule.
        if state.tip_data != "raztopina":
            return None
        if state.label_value != "koda":
            return self._build_invalid_context_error(
                (
                    f"Kontrola '{control.raw_name}' je dovoljena samo na polju 'koda'. "
                    f"Trenutni Tip objekta='{coerce_str(state.row.get('Tip objekta', '')).strip()}', "
                    f"Labela='{state.label_value_raw.strip()}'."
                ),
                context=context,
                column=control.column,
            )
        return self._validate_raztopina_params(control, state, context)

    def _validate_raztopina_params(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        errors = []
        if not state.key_here:
            errors.append(
                self.build_error(
                    "Kontrola raztopine brez ključa v vrstici.",
                    context=context,
                    column="Ključ preverjanja",
                    code="SOLUTION_KEY_MISSING",
                )
            )
            return errors

        param1_col = control.param1_column
        if not param1_col:
            errors.append(
                self.build_error(
                    "Kontrola raztopine brez Param1.",
                    context=context,
                    column=control.column,
                    code="SOLUTION_P1_MISSING",
                )
            )
        return errors or None

    def _validate_aliisto_context(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        if control.name_ns != "aliisto":
            return None
        if (
            state.tip_data.startswith("raztopina")
            or state.tip_data.startswith("kemikalija")
            or is_equipment_tip(state.tip_data_raw)
        ):
            return None
        return self._build_invalid_context_error(
            (
                f"Kontrola '{control.raw_name}' je dovoljena samo pri tipu podatka "
                f"'raztopina', 'kemikalija' ali oprema."
            ),
            context=context,
            column=control.column,
        )

    def _validate_kontrolacasa_context(
        self,
        control: ControlInstance,
        state: ControlContextState,
        context: RuleContext,
    ):
        if control.name_ns != "kontrolacasa" or state.tip_data == "datumcaskonec":
            return None
        return self._build_invalid_context_error(
            "Kontrola 'kontrolaCasa' naj bo na zaključnem času (datumcaskonec).",
            context=context,
            column=control.column,
        )


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
                    code="CTRL_REQUIRED_EMPTY",
                )
            )

        if (
            tip_obj in EMPTY_CONTROL_FORBIDDEN_OBJECT_TYPES
            and has_empty_control
            and not (tip_obj == "checkbox" and has_lock_control)
        ):
            if tip_obj == "checkbox":
                message = "Checkbox ne sme imeti 'kontrolaPraznoPolje'."
                code = "CTRL_CHECKBOX_EMPTY"
            else:
                message = f"Tip objekta '{tip_obj}' ne sme imeti 'kontrolaPraznoPolje'."
                code = "CTRL_EMPTY_NOT_ALLOWED"
            errors.append(
                self.build_error(
                    message,
                    context=context,
                    column="(Kontrole)",
                    code=code,
                )
            )

        # Pri zaklenipolja na checkbox ne sme biti kontrolapraznopolje
        if tip_obj == "checkbox" and has_lock_control and has_empty_control:
            errors.append(
                self.build_error(
                    "Pri 'zaklenipolja' na checkbox ne sme biti kontrola 'kontrolaPraznoPolje'.",
                    context=context,
                    column="(Kontrole)",
                    code="CTRL_LOCK_EMPTY_NOT_ALLOWED",
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
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        navodilo = coerce_str(row.get("Navodilo", ""))
        nav_n = norm_text(navodilo)
        label_value = coerce_str(row.get("Labela", ""))
        vrednost = coerce_str(row.get("Vrednost", ""))
        controls = _get_present_controls(row, shared)
        present_names_ns = {ctrl.name_ns for ctrl in controls}
        is_hplc_pump = bool(re.search(r"hplc\s*[-–]?\s*(?:č|c)rpalka\b", nav_n))
        errors = []
        self._append_expected_for_kemikalija(errors, controls, tip_data, tip_data_raw, context)
        self._append_expected_for_masa(errors, controls, tip_data, navodilo, nav_n, label_value, vrednost, tip_data_raw, context)
        self._append_expected_for_embalaza(errors, controls, tip_data, tip_data_raw, context)
        self._append_expected_for_equipment(
            errors,
            controls,
            tip_data,
            tip_data_raw,
            tip_obj,
            norm_text(label_value),
            present_names_ns,
            is_hplc_pump,
            coerce_str(row.get("Ključ preverjanja", "")),
            shared,
            context,
        )
        self._append_expected_for_monolit(errors, controls, tip_data, tip_data_raw, context)
        self._append_expected_for_raztopina(errors, controls, tip_data, tip_data_raw, context)
        self._append_expected_for_repro(errors, controls, tip_data, tip_data_raw, context)
        return errors

    def _warn_if_missing_any(
        self,
        errors: list,
        controls: Sequence[ControlInstance],
        one_of: list[str],
        label: str,
        tip_data_raw: str,
        context: RuleContext,
    ) -> None:
        if any(_has_control(controls, ctrl_name) for ctrl_name in one_of):
            return

        message = f"{label} manjka: pričakovana vsaj ena od {one_of}"
        if label.startswith("Oprema –"):
            tip_current = tip_data_raw.strip()
            if tip_current and " manjka:" in message:
                pref, rest = message.split(" manjka:", 1)
                message = f"{pref} za opremo '{tip_current}' manjka:{rest}"
        errors.append(
            self.build_error(
                message,
                context=context,
                column="(Kontrole)",
                code="CTRL_EXPECTED_MISSING",
                severity=Severity.WARNING,
            )
        )

    def _append_expected_for_kemikalija(
        self,
        errors: list,
        controls: Sequence[ControlInstance],
        tip_data: str,
        tip_data_raw: str,
        context: RuleContext,
    ) -> None:
        if tip_data != "kemikalija":
            return
        for needed in [["kontrolaveljavnostikemikalije"], ["kontrolaustreznostikemikalije"]]:
            self._warn_if_missing_any(errors, controls, needed, "Kemikalija – pričakovane kontrole", tip_data_raw, context)

    def _is_masa_exception(self, navodilo: str, nav_n: str, label_value: str, vrednost: str) -> bool:
        porabljan_word = bool(re.search(r"\bporablj\w*\b", nav_n, flags=re.IGNORECASE))
        volume_number_present = bool(re.search(r"\d+(?:[.,]\d+)?\s*(?:ml|l)\b", navodilo, flags=re.IGNORECASE))
        has_concentration = bool(re.search(r"\b(?:mg|g)\s*/\s*ml\b", nav_n, flags=re.IGNORECASE))
        label_unit_token = extract_unit_token(label_value)
        nav_unit_token = extract_unit_token(navodilo)
        any_volume_unit = (label_unit_token in {"ml", "l"}) or (nav_unit_token in {"ml", "l"})
        concentration_implies_volume = has_concentration and any_volume_unit
        no_numeric_in_navodilo = not bool(NUMERIC_TOKEN_RE.search(nav_n))
        vrednost_has_number = bool(NUMERIC_TOKEN_RE.search(vrednost))
        return (
            porabljan_word
            or volume_number_present
            or concentration_implies_volume
            or no_numeric_in_navodilo
        ) and (not vrednost_has_number)

    def _append_expected_for_masa(
        self,
        errors: list,
        controls: Sequence[ControlInstance],
        tip_data: str,
        navodilo: str,
        nav_n: str,
        label_value: str,
        vrednost: str,
        tip_data_raw: str,
        context: RuleContext,
    ) -> None:
        if tip_data != "masa" or self._is_masa_exception(navodilo, nav_n, label_value, vrednost):
            return
        self._warn_if_missing_any(
            errors,
            controls,
            ["kontrolamase", "kontrolainterval", "kontrolarazlika"],
            "Masa – pričakovane kontrole",
            tip_data_raw,
            context,
        )

    def _append_expected_for_embalaza(
        self,
        errors: list,
        controls: Sequence[ControlInstance],
        tip_data: str,
        tip_data_raw: str,
        context: RuleContext,
    ) -> None:
        if tip_data != "embalaza":
            return
        for needed in [["kontrolaembalaze"], ["kontrolaprazneembalaze"]]:
            self._warn_if_missing_any(errors, controls, needed, "Embalaža – pričakovana kontrola", tip_data_raw, context)

    def _append_expected_for_equipment(
        self,
        errors: list,
        controls: Sequence[ControlInstance],
        tip_data: str,
        tip_data_raw: str,
        tip_obj: str,
        label_value: str,
        present_names_ns: set[str],
        is_hplc_pump: bool,
        key_here: str,
        shared: Any,
        context: RuleContext,
    ) -> None:
        if not is_equipment_row(tip_data_raw, tuple(present_names_ns)) or is_hplc_pump:
            return

        requires_equipment_validity = tip_obj == "spustniseznam" or label_value == "koda"
        if requires_equipment_validity:
            self._warn_if_missing_any(
                errors,
                controls,
                ["kontrolaveljavnostiopreme"],
                "Oprema – pričakovana kontrola veljavnosti",
                tip_data_raw,
                context,
            )
        if tip_data != "tehtnica":
            return
        masa_keys = shared.get_keys_with_value_for_type("masa")
        if key_here and key_here in masa_keys:
            self._warn_if_missing_any(
                errors,
                controls,
                ["kontrolaustreznostiopreme"],
                "Oprema – pričakovana kontrola ustreznosti",
                tip_data_raw,
                context,
            )

    def _append_expected_for_monolit(
        self,
        errors: list,
        controls: Sequence[ControlInstance],
        tip_data: str,
        tip_data_raw: str,
        context: RuleContext,
    ) -> None:
        if not tip_data.startswith("monolit"):
            return
        self._warn_if_missing_any(
            errors, controls, ["kontrolaveljavnostimonolita"], "Monolit – pričakovana kontrola veljavnosti", tip_data_raw, context
        )
        self._warn_if_missing_any(
            errors, controls, ["kontrolaustreznostimonolita"], "Monolit – pričakovana kontrola ustreznosti", tip_data_raw, context
        )

    def _append_expected_for_raztopina(
        self,
        errors: list,
        controls: Sequence[ControlInstance],
        tip_data: str,
        tip_data_raw: str,
        context: RuleContext,
    ) -> None:
        if not tip_data.startswith("raztopina"):
            return
        self._warn_if_missing_any(
            errors, controls, ["kontrolaveljavnostiraztopine"], "Raztopina – pričakovana kontrola veljavnosti", tip_data_raw, context
        )
        self._warn_if_missing_any(
            errors, controls, ["kontrolaustreznostiraztopine"], "Raztopina – pričakovana kontrola ustreznosti", tip_data_raw, context
        )

    def _append_expected_for_repro(
        self,
        errors: list,
        controls: Sequence[ControlInstance],
        tip_data: str,
        tip_data_raw: str,
        context: RuleContext,
    ) -> None:
        if not (tip_data == "repro" or tip_data == "reproodpis"):
            return
        for needed, label in (
            (["kontrolaveljavnostirepro"], "Repro – pričakovana kontrola veljavnosti"),
            (["kontrolaustreznostirepro"], "Repro – pričakovana kontrola ustreznosti"),
        ):
            self._warn_if_missing_any(errors, controls, needed, label, tip_data_raw, context)


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
                        code="LOCK_P1_EXCEL_ERROR",
                    )
                )
                continue
            if not self.INT_LIST_PATTERN.fullmatch(value):
                errors.append(
                    self.build_error(
                        "Param1 mora biti seznam celih števil, ločenih z vejicami (npr. 12, 13, 14).",
                        context=context,
                        column=param_col or control.column,
                        code="LOCK_P1_FORMAT",
                    )
                )
                continue

            # Interpret Param1 as list of step numbers
            require_pogoj = not shared.extra.get(
                "bypass_zakleni_require_pogoj_for_param1_steps",
                False,
            )
            zakleni_checkbox_steps = getattr(shared, "zakleni_checkbox_steps", set())
            for token in value.split(","):
                step = int(token.strip())
                if step not in shared.existing_steps:
                    errors.append(
                        self.build_error(
                            f"Korak {step} iz Param1 ne obstaja v tabeli.",
                            context=context,
                            column=param_col or control.column,
                            code="LOCK_P1_STEP_MISSING",
                        )
                    )
                elif (
                    require_pogoj
                    and step not in zakleni_checkbox_steps
                    and "aliobstajapogoj" not in shared.step_to_controls.get(step, set())
                ):
                    errors.append(
                        self.build_error(
                            f"Korak {step} mora imeti kontrolo 'aliObstajaPogoj'.",
                            context=context,
                            column=param_col or control.column,
                            code="LOCK_P1_WITHOUT_CONDITION",
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

        # Param2=1 pri ključu, ki je v Param1 istega zaklenipolja, je dovoljeno (ne javimo napake).
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
                code="LOCK_CONDITION_P1P2",
            )
        ]


_ZAKLENI_INT_LIST_RE = re.compile(r"^\s*\d+(?:\s*,\s*\d+)*\s*$")
_SEPARATOR_OBJECT_TYPES = frozenset({"crta", "naslov"})


@dataclass(slots=True)
class _ZakleniLocker:
    row_idx: int
    step: int | None
    key: str
    locked_steps: set[int] | None


@dataclass(slots=True)
class _AliobParam1Hit:
    row_idx: int
    param1_col: str
    keys: list[str]


def _parse_step_token(row: Mapping[str, object]) -> int | None:
    token = coerce_str(row.get("št. Koraka", "")).strip()
    if not token:
        return None
    try:
        return int(token)
    except ValueError:
        return None


def _parse_zakleni_locked_steps(value: object) -> set[int] | None:
    raw = coerce_str(value).strip()
    if not raw or raw.startswith("=") or not _ZAKLENI_INT_LIST_RE.fullmatch(raw):
        return None
    return {int(tok.strip()) for tok in raw.split(",") if tok.strip()}


def _parse_aliob_param1_keys(value: object) -> list[str] | None:
    raw = coerce_str(value).strip()
    if not raw or raw.startswith("="):
        return None
    keys = [tok.strip() for tok in raw.split(",") if tok.strip()]
    return keys or None


def _unique_lockers(lockers: Sequence[_ZakleniLocker]) -> list[_ZakleniLocker]:
    by_row: dict[int, _ZakleniLocker] = {}
    for locker in lockers:
        by_row.setdefault(locker.row_idx, locker)
    return list(by_row.values())


def _cluster_zakleni_rows(
    tab_rows: Sequence[tuple[int, Mapping[str, object]]],
    zakleni_by_row: Mapping[int, _ZakleniLocker],
) -> dict[int, list[_ZakleniLocker]]:
    """Map each zaklenipolja row to its contiguous DA/NE (or similar) cluster."""
    clusters: list[list[_ZakleniLocker]] = []
    current: list[_ZakleniLocker] = []

    def close_current() -> None:
        nonlocal current
        if current:
            clusters.append(current)
            current = []

    for row_idx, row in tab_rows:
        if row_idx in zakleni_by_row:
            current.append(zakleni_by_row[row_idx])
            continue
        tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
        if tip_obj in _SEPARATOR_OBJECT_TYPES:
            continue
        close_current()
    close_current()

    cluster_by_row: dict[int, list[_ZakleniLocker]] = {}
    for cluster in clusters:
        for locker in cluster:
            cluster_by_row[locker.row_idx] = cluster
    return cluster_by_row


def _expand_lock_sklop(
    owners: Sequence[_ZakleniLocker],
    zakleni_by_step: Mapping[int, _ZakleniLocker],
    cluster_by_row: Mapping[int, Sequence[_ZakleniLocker]],
) -> list[_ZakleniLocker]:
    """Owners plus paired zaklenipolja (listed in Param1 or adjacent in the same cluster)."""
    by_row: dict[int, _ZakleniLocker] = {}

    def add(locker: _ZakleniLocker) -> None:
        by_row[locker.row_idx] = locker

    for owner in owners:
        add(owner)
        if owner.locked_steps:
            for listed_step in owner.locked_steps:
                sibling = zakleni_by_step.get(listed_step)
                if sibling is not None:
                    add(sibling)
        for mate in cluster_by_row.get(owner.row_idx, ()):
            add(mate)
    return list(by_row.values())


@register
class AliObstajaPogojParam1Rule(SheetRule):
    """Param1 at aliObstajaPogoj must match the zaklenipolja sklop that locks this step."""

    name = "aliobstajapogoj_param1_rule"
    description = (
        "Pri 'aliObstajaPogoj' mora biti Param1 ključ sklopa 'zaklenipolja', ki ta korak "
        "zaklene (ključ vrstice, ki korak navaja v Param1, ali parni ključ, npr. sst_4 "
        "namesto sst_3), in ne sme biti podvojen med različnimi sklopi zaklepanja."
    )

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

        tab_by_row = shared.tab_by_row
        rows_by_tab: dict[str, list[tuple[int, Mapping[str, object]]]] = {}
        for row_idx, row in enumerate(rows, start=row_offset):
            tab = tab_by_row.get(row_idx, "")
            rows_by_tab.setdefault(tab, []).append((row_idx, row))

        errors: list = []
        for tab_rows in rows_by_tab.values():
            errors.extend(self._evaluate_tab(tab_rows, context, shared))
        return errors

    def _evaluate_tab(
        self,
        tab_rows: Sequence[tuple[int, Mapping[str, object]]],
        context: RuleContext,
        shared,
    ) -> list:
        lockers_by_step: dict[int, list[_ZakleniLocker]] = {}
        zakleni_by_row: dict[int, _ZakleniLocker] = {}
        zakleni_by_step: dict[int, _ZakleniLocker] = {}
        aliob_rows: list[tuple[int, Mapping[str, object], list[ControlInstance]]] = []

        for row_idx, row in tab_rows:
            controls = _get_present_controls(row, shared)
            zakleni_ctrls = _get_control(controls, ZAKLENI_CONTROL)
            ali_ctrls = _get_control(controls, ALIOB_CONTROL)

            if zakleni_ctrls:
                key = coerce_str(row.get("Ključ preverjanja", "")).strip()
                locker_step = _parse_step_token(row)
                locked: set[int] | None = None
                for ctrl in zakleni_ctrls:
                    locked = _parse_zakleni_locked_steps(row.get(ctrl.param1_column or "", ""))
                    break
                locker = _ZakleniLocker(
                    row_idx=row_idx,
                    step=locker_step,
                    key=key,
                    locked_steps=locked,
                )
                zakleni_by_row[row_idx] = locker
                if locker_step is not None:
                    zakleni_by_step[locker_step] = locker
                if locked:
                    for locked_step in locked:
                        lockers_by_step.setdefault(locked_step, []).append(locker)

            if ali_ctrls:
                aliob_rows.append((row_idx, row, ali_ctrls))

        cluster_by_row = _cluster_zakleni_rows(tab_rows, zakleni_by_row)

        errors: list = []
        key_to_group_hits: dict[str, dict[frozenset[int], list[_AliobParam1Hit]]] = {}

        for row_idx, row, ali_ctrls in aliob_rows:
            step = _parse_step_token(row)
            if step is None:
                continue
            owners = _unique_lockers(lockers_by_step.get(step, []))
            if not owners:
                continue

            sklop = _expand_lock_sklop(owners, zakleni_by_step, cluster_by_row)
            allowed = {item.key for item in sklop if item.key}
            group_id = frozenset(item.row_idx for item in sklop)
            keys_label = " ali ".join(item.key for item in sklop if item.key)

            for ctrl in ali_ctrls:
                p1_col = ctrl.param1_column or ctrl.column or "(Kontrole)"
                parsed = _parse_aliob_param1_keys(row.get(ctrl.param1_column or "", ""))
                if parsed is None:
                    continue
                unique_keys = list(dict.fromkeys(parsed))
                hit = _AliobParam1Hit(row_idx=row_idx, param1_col=p1_col, keys=unique_keys)
                for key in unique_keys:
                    if allowed and key not in allowed:
                        expected = keys_label or "(manjka ključ)"
                        errors.append(
                            self.build_error(
                                f"Param1 pri 'aliObstajaPogoj' mora biti {expected}, ne '{key}'.",
                                context=context.with_row(row_idx),
                                column=p1_col,
                                code="LOCK_CONDITION_P1_LOCK_KEY",
                            )
                        )
                    key_to_group_hits.setdefault(key, {}).setdefault(group_id, []).append(hit)

        for key, groups in key_to_group_hits.items():
            if len(groups) <= 1:
                continue
            first_group_id = min(groups, key=lambda gid: min(gid) if gid else 0)
            first_row = min(hit.row_idx for hit in groups[first_group_id])
            reported_rows: set[int] = set()
            for group_id, hits in groups.items():
                if group_id == first_group_id:
                    continue
                for hit in hits:
                    if hit.row_idx in reported_rows:
                        continue
                    reported_rows.add(hit.row_idx)
                    errors.append(
                        self.build_error(
                            f"Param1 '{key}' pri kontroli 'aliObstajaPogoj' je podvojen – "
                            "isti ključ je že uporabljen pri drugem sklopu 'zaklenipolja' "
                            f"(prva pojavitev: vrstica {first_row}).",
                            context=context.with_row(hit.row_idx),
                            column=hit.param1_col,
                            code="LOCK_CONDITION_P1_DUPLICATE",
                        )
                    )
        return errors


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
                            code="LOCK_KEY_DUPLICATE",
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
                            code="LOCK_P1_MISSING_FOR_CONDITION",
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
                        code="CTRL_LOCK_ALIOB_NOT_ALLOWED",
                    )
                )

        # Pri checkboxu z Labela 'DA (kljukica)/NE (prazno)' aliObkljukan ne sme biti
        if has_aliobkljukan and (labela_norm == LABELA_DA_NE or "/ne (prazno)" in labela_norm):
            errors.append(
                self.build_error(
                    "Pri checkboxu z 'DA (kljukica)/NE (prazno)' ni dovoljena kontrola 'aliObkljukan'.",
                    context=context,
                    column="(Kontrole)",
                    code="CTRL_CHECKBOX_DANE_ALIOB_NOT_ALLOWED",
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
                    code="CTRL_LOCK_EMPTY_NOT_ALLOWED",
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
                        code="ALIOB_PARAM_CHECK",
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
                        code="CHECKBOX_STATE",
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
        interval_controls = _get_interval_controls(controls)
        if not interval_controls:
            return []

        errors = []
        for control in interval_controls:
            p1 = coerce_str(row.get(control.param1_column or "", ""))
            p2 = coerce_str(row.get(control.param2_column or "", ""))
            if not p1:
                errors.append(
                    self.build_error(
                        "kontrolaInterval potrebuje Param1 (spodnjo mejo).",
                        context=context,
                        column=control.param1_column or control.column,
                        code="CTRL_INTERVAL_PARAMS",
                    )
                )
            if not p2:
                errors.append(
                    self.build_error(
                        "kontrolaInterval potrebuje Param2 (zgornjo mejo).",
                        context=context,
                        column=control.param2_column or control.column,
                        code="CTRL_INTERVAL_PARAMS",
                    )
                )
            if not p1 or not p2:
                continue

            p1_val = _parse_number(p1)
            p2_val = _parse_number(p2)
            if p1 and p1_val is None:
                errors.append(
                    self.build_error(
                        f"Param1 '{p1}' ni številčna vrednost.",
                        context=context,
                        column=control.param1_column or control.column,
                        code="CTRL_INTERVAL_NOT_NUMBER",
                    )
                )
            if p2 and p2_val is None:
                errors.append(
                    self.build_error(
                        f"Param2 '{p2}' ni številčna vrednost.",
                        context=context,
                        column=control.param2_column or control.column,
                        code="CTRL_INTERVAL_NOT_NUMBER",
                    )
                )
            if p1_val is not None and p2_val is not None and p2_val <= p1_val:
                errors.append(
                    self.build_error(
                        "Param2 (max) mora biti večji od Param1 (min).",
                        context=context,
                        column=control.param2_column or control.column,
                        code="CTRL_INTERVAL_RANGE",
                    )
                )
        return errors


@register
class KontrolaIntervalAdvancedRule(RowRule):
    """Advanced interpretation of kontrolaInterval vs Navodilo."""

    name = "kontrola_interval_advanced_rule"
    description = "Parametri kontrolaInterval morajo slediti navodilom (>, <, ±)."

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        navodilo_raw = coerce_str(row.get("Navodilo", ""))
        if _navodilo_is_info(navodilo_raw):
            return []

        controls = _get_present_controls(row, shared)
        interval_controls = _get_interval_controls(controls)
        if not interval_controls:
            return []

        navodilo_parse = _parse_numeric_navodilo(navodilo_raw)
        navodilo = navodilo_parse.raw
        errors = []

        for control in interval_controls:
            p1_raw = coerce_str(row.get(control.param1_column or "", ""))
            p2_raw = coerce_str(row.get(control.param2_column or "", ""))
            p1_val = _parse_number(p1_raw)
            p2_val = _parse_number(p2_raw)
            p1_is_num = p1_val is not None
            p2_is_num = p2_val is not None

            def fmt(value: float | None, raw: str, decimals: int) -> str:
                if value is None:
                    return raw or ""
                return f"{value:.{decimals}f}"

            # 1) Neenačbe (>, >=, <, <=) – enako kot v MES_validator.py
            if navodilo_parse.inequality_op and navodilo_parse.inequality_value is not None:
                op = navodilo_parse.inequality_op
                xi = navodilo_parse.inequality_value
                eps = (
                    navodilo_parse.inequality_step
                    if navodilo_parse.inequality_step is not None
                    else derive_decimal_step_from_text(navodilo)
                )
                d_exact = decimals_from_eps(eps)
                # Vsaj toliko decimalk kot jih narekuje korak, plus vse iz dejanskih vrednosti
                d_fmt = max(d_exact, max_decimals(xi, p1_val, p2_val, xi - eps, xi + eps))

                if op == ">":
                    # Strogo večje: Param1 mora biti ENAK xi, Param2 ≥ xi + eps
                    if not (p1_is_num and _decimal_eq(p1_raw, xi, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param1 mora biti {xi:.{d_fmt}f} – spodnja meja iz navodila {navodilo}. "
                                    f"(meja = {xi:.{d_fmt}f}) Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param1_column or control.column,
                                code="CTRL_INTERVAL_TARGET_P1",
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
                                code="CTRL_INTERVAL_TARGET_P2_MIN",
                            )
                        )
                elif op == ">=":
                    # Večje ali enako: Param1 = xi − eps, Param2 ≥ xi + eps
                    expected_p1 = xi - eps
                    if not (p1_is_num and _decimal_eq(p1_raw, expected_p1, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param1 mora biti {expected_p1:.{d_fmt}f} – (meja − korak) iz navodila {navodilo}. "
                                    f"({xi:.{d_fmt}f} − x = {expected_p1:.{d_fmt}f}) Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param1_column or control.column,
                                code="CTRL_INTERVAL_TARGET_P1",
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
                                code="CTRL_INTERVAL_TARGET_P2_MIN",
                            )
                        )
                elif op in ("<", "<="):
                    # Manjše / manjše ali enako:
                    # Param1 je spodnja meja – ni določena z navodilom, mora biti ≤ xi − eps
                    # Param2 je zgornja meja:
                    #   <  (strogo): Param2 = xi        (MES zavrne vrednosti ≥ xi)
                    #   <= (vključno): Param2 = xi + eps (MES zavrne vrednosti > xi)
                    if not (p1_is_num and round(p1_val, d_exact) <= round(xi - eps, d_exact)):
                        errors.append(
                            self.build_error(
                                (
                                    f"Param1 mora biti ≤ {xi - eps:.{d_fmt}f} – iz navodila {navodilo}. "
                                    f"Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param1_column or control.column,
                                code="CTRL_INTERVAL_TARGET_P1_MAX",
                            )
                        )
                    if op == "<":
                        # Strogo manjše: Param2 = xi (MES: zavrni če vrednost >= Param2)
                        p2_required = xi
                        p2_ok = p2_is_num and _decimal_eq(p2_raw, p2_required, d_exact)
                        p2_msg = f"{p2_required:.{d_fmt}f}"
                    else:  # "<="
                        # Manjše ali enako: Param2 = xi + eps (MES: zavrni če vrednost > xi)
                        p2_required = xi + eps
                        p2_ok = p2_is_num and _decimal_eq(p2_raw, p2_required, d_exact)
                        p2_msg = f"{p2_required:.{d_fmt}f}"
                    if not p2_ok:
                        errors.append(
                            self.build_error(
                                (
                                    f"Param2 mora biti {p2_msg} – zgornja meja iz navodila {navodilo}. "
                                    f"Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                                ),
                                context=context,
                                column=control.param2_column or control.column,
                                code="CTRL_INTERVAL_TARGET_P2",
                            )
                        )
                continue

            # 2) ± notation – Možnost A: eps iz natančnosti xpm (decimalna mesta ciljne vrednosti)
            if navodilo_parse.pm_center is not None and navodilo_parse.pm_tolerance is not None:
                xpm = navodilo_parse.pm_center
                tpm = navodilo_parse.pm_tolerance
                # Za ± uporabljamo decimalke tolerance (t), ne decimalke sredine (x).
                # Tako npr. "8 ± 0.4" vedno zahteva Param1=7.5 in Param2=8.5.
                # Float xpm/tpm izgubi trailing zeros, zato decimalke beremo iz surovega besedila v Navodilu.
                x_text = navodilo_parse.pm_center_text
                t_text = navodilo_parse.pm_tolerance_text
                left_dec: Decimal | None = None
                right_dec: Decimal | None = None
                d_round: int | None = None
                if x_text and t_text:
                    d_tol = decimal_places_of_first_number(t_text) or 0
                    try:
                        x_dec = Decimal(x_text.replace(",", "."))
                        t_dec = Decimal(t_text.replace(",", "."))
                        left_dec = x_dec - t_dec
                        right_dec = x_dec + t_dec
                        d_round = max(
                            _decimal_places_stripped(left_dec),
                            _decimal_places_stripped(right_dec),
                        )
                    except InvalidOperation:
                        left_dec = None
                        right_dec = None
                        d_round = None
                else:
                    # Fallback: step_pm je definiran kot korak iz max(decimalk(x), decimalk(t))
                    d_tol = decimals_from_eps(navodilo_parse.pm_step) if navodilo_parse.pm_step is not None else 0

                eps_pm = 10 ** (-d_tol) if d_tol > 0 else 1.0

                left_req = xpm - tpm
                right_req = xpm + tpm
                param1_required = left_req - eps_pm
                param2_required = right_req + eps_pm

                d_fmt = max_decimals(left_req, right_req, param1_required, param2_required, p1_val, p2_val)
                # Sporočilo kaže kanonski Param (npr. 24.0 ± 0.5 → 23.4 / 24.6), ne roba pasu (23.44 / 24.55).
                p1_msg_target = f"{param1_required:.{d_tol}f}"
                p2_msg_target = f"{param2_required:.{d_tol}f}"

                if not _pm_param_matches(
                    p1_raw, p1_is_num, param1_required, d_tol, left_dec, right_dec, d_round
                ):
                    errors.append(
                        self.build_error(
                            (
                                f"Param1 mora biti {p1_msg_target} – iz {xpm:.{d_fmt}f} ± {tpm:.{d_fmt}f}. "
                                f"Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                            ),
                            context=context,
                            column=control.param1_column or control.column,
                            code="CTRL_INTERVAL_PM_P1",
                        )
                    )
                if not _pm_param_matches(
                    p2_raw, p2_is_num, param2_required, d_tol, left_dec, right_dec, d_round
                ):
                    errors.append(
                        self.build_error(
                            (
                                f"Param2 mora biti {p2_msg_target} – iz {xpm:.{d_fmt}f} ± {tpm:.{d_fmt}f}. "
                                f"Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                            ),
                            context=context,
                            column=control.param2_column or control.column,
                            code="CTRL_INTERVAL_PM_P2",
                        )
                    )
                continue

            # 3) Range a-b
            if navodilo_parse.range_min is not None and navodilo_parse.range_max is not None:
                a = navodilo_parse.range_min
                b = navodilo_parse.range_max
                eps = (
                    navodilo_parse.range_step
                    if navodilo_parse.range_step is not None
                    else derive_decimal_step_from_text(navodilo)
                )
                d_exact = decimals_from_eps(eps)
                lower = a - eps
                upper = b + eps
                d_fmt = max_decimals(a, b, lower, upper, p1_val, p2_val)
                a_dec = Decimal(f"{a:.{d_exact}f}")
                b_dec = Decimal(f"{b:.{d_exact}f}")
                canonical_lo = Decimal(f"{lower:.{d_exact}f}")
                # Extra decimal MES band only when a−eps is 0 (0.01–0.30 → 0.004 / 0.305).
                # Otherwise keep a−eps / b+eps at the interval's decimals (0.18–0.22 → 0.17).
                use_fine_band = d_exact >= 2 and canonical_lo == 0
                if use_fine_band:
                    band_lo, band_hi = _range_param_band(a_dec, b_dec, d_exact)
                    d_hint = max(d_exact + 1, d_fmt, 0)
                    p1_required: float | None = lower
                    p2_required: float | None = upper
                    if Decimal(f"{lower:.{d_exact}f}") < band_lo:
                        p1_required = None
                    if Decimal(f"{upper:.{d_exact}f}") > band_hi:
                        p2_required = None
                    p1_ok = _range_param_matches(
                        p1_raw, p1_is_num, p1_required, d_exact, a_dec, b_dec, d_exact
                    )
                    p2_ok = _range_param_matches(
                        p2_raw, p2_is_num, p2_required, d_exact, a_dec, b_dec, d_exact
                    )
                    p1_msg_target = f"{band_lo:.{d_hint}f}"
                    p2_msg_target = f"{band_hi:.{d_hint}f}"
                else:
                    p1_ok = p1_is_num and _decimal_eq(p1_raw, lower, d_exact)
                    p2_ok = p2_is_num and _decimal_eq(p2_raw, upper, d_exact)
                    p1_msg_target = f"{lower:.{d_exact}f}"
                    p2_msg_target = f"{upper:.{d_exact}f}"
                    # Cela števila: 45 in 45.0 sta isti zapis (ničla se včasih ne prikaže).
                    if d_exact == 0:
                        if p1_is_num and _integer_range_one_decimal_match(
                            p1_raw, a, is_lower=True
                        ):
                            p1_ok = True
                        if p2_is_num and _integer_range_one_decimal_match(
                            p2_raw, b, is_lower=False
                        ):
                            p2_ok = True
                        if not p1_ok:
                            alt_p1 = Decimal(int(round(a))) - Decimal("0.1")
                            p1_msg_target = f"{p1_msg_target} ali {alt_p1:.1f}"
                        if not p2_ok:
                            alt_p2 = Decimal(int(round(b))) + Decimal("0.1")
                            p2_msg_target = f"{p2_msg_target} ali {alt_p2:.1f}"

                if not p1_ok:
                    errors.append(
                        self.build_error(
                                (
                                    f"Param1 mora biti {p1_msg_target} – iz navodila {navodilo}. "
                                    f"Trenutno v recepturi: {fmt(p1_val, p1_raw, d_fmt)}"
                                ),
                            context=context,
                            column=control.param1_column or control.column,
                            code="CTRL_INTERVAL_P1_BOUND",
                        )
                    )
                if not p2_ok:
                    errors.append(
                        self.build_error(
                                (
                                    f"Param2 mora biti {p2_msg_target} – iz navodila {navodilo}. "
                                    f"Trenutno v recepturi: {fmt(p2_val, p2_raw, d_fmt)}"
                                ),
                            context=context,
                            column=control.param2_column or control.column,
                            code="CTRL_INTERVAL_P2_BOUND",
                        )
                    )
                continue

        return errors


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

            p1_num = _parse_number(p1)
            p2_num = _parse_number(p2)

            # Basic validation
            if not p1:
                errors.append(
                    self.build_error(
                        "kontrolaCasa zahteva Param1 (min trajanje v sekundah).",
                        context=context,
                        column=control.param1_column or control.column,
                        code="CTRL_CASA_MIN",
                    )
                )
            elif p1_num is None:
                errors.append(
                    self.build_error(
                        f"kontrolaCasa Param1 '{p1}' ni številčna (sekunde).",
                        context=context,
                        column=control.param1_column or control.column,
                        code="CTRL_CASA_MIN_NOT_NUMBER",
                    )
                )

            if p2 and p2_num is None:
                errors.append(
                    self.build_error(
                        f"kontrolaCasa Param2 '{p2}' ni številčna (sekunde).",
                        context=context,
                        column=control.param2_column or control.column,
                        code="CTRL_CASA_MAX_NOT_NUMBER",
                    )
                )

            if p1_num is not None and p2_num is not None and p2_num < p1_num:
                errors.append(
                    self.build_error(
                        "kontrolaCasa Param2 (max) < Param1 (min).",
                        context=context,
                        column=control.param2_column or control.column,
                        code="CTRL_CASA_RANGE",
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
                            code="CTRL_CASA_P1_INSTRUCTION",
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
                            code="CTRL_CASA_P2_INSTRUCTION",
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
                        code="CTRL_CASA_P1_INSTRUCTION",
                    )
                )

            if p2_num is not None and abs(p2_num - target_p2) > 1e-6:
                errors.append(
                    self.build_error(
                        f"kontrolaCasa: Param2 mora biti {target_p2:.0f} s (max +10 s). "
                        f"Trenutno: {p2_num:.0f} s",
                        context=context,
                        column=control.param2_column or control.column,
                        code="CTRL_CASA_P2_INSTRUCTION",
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
                code="CTRL_CASA_REQUIRED",
            )
        ]


@register
class NavodiloIntervalKontrolaIntervalRequiredRule(RowRule):
    """Require kontrolaInterval or kontrolarazlika when Navodilo contains numeric intervals (≥, range, ±)."""

    name = "navodilo_interval_kontrolainterval_required_rule"
    description = "Če Navodilo vsebuje številčni interval (≥, razpon, ±), je obvezna kontrola 'kontrolaInterval' ali 'kontrolarazlika'."

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
        if _get_interval_controls(controls) or _has_control(controls, "kontrolarazlika"):
            return []

        return [
            self.build_error(
                "Navodilo vsebuje številčni interval, vendar manjka kontrola 'kontrolaInterval' ali 'kontrolarazlika'.",
                context=context,
                column="(Kontrole)",
                code="CTRL_INTERVAL_REQUIRED",
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
                code="CTRL_ALIOBKLJUKAN_REQUIRED",
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
                code="CTRL_ALIPRAVAVLOGAKODA_REQUIRED",
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
                    code="CTRL_MONOLIT_VALIDITY_REQUIRED",
                )
            )
        if not _has_control(controls, "kontrolaustreznostimonolita"):
            errors.append(
                self.build_error(
                    "Manjka kontrola 'kontrolaUstreznostiMonolita' pri tipu podatka 'monolit'.",
                    context=context,
                    column="(Kontrole)",
                    code="CTRL_MONOLIT_SUITABILITY_REQUIRED",
                )
            )
        return errors


@dataclass(frozen=True, slots=True)
class _ControlPairSpec:
    """Par kontrol (veljavnost + ustreznost), ki velja samo za en tip podatka."""

    tip_podatka: str
    validity: str
    validity_label: str
    validity_code: str
    suitability: str
    suitability_label: str
    suitability_code: str
    type_code: str
    param1_code: str
    param2_code: str
    # True: Param1 mora biti prazen; False: Param1 mora biti pri obeh kontrolah enak.
    param1_must_be_empty: bool


_CONTROL_PAIR_SPECS: tuple[_ControlPairSpec, ...] = (
    _ControlPairSpec(
        tip_podatka="kemikalija",
        validity="kontrolaveljavnostikemikalije",
        validity_label="kontrolaVeljavnostiKemikalije",
        validity_code="CTRL_KEMIKALIJA_VALIDITY_REQUIRED",
        suitability="kontrolaustreznostikemikalije",
        suitability_label="kontrolaUstreznostiKemikalije",
        suitability_code="CTRL_KEMIKALIJA_SUITABILITY_REQUIRED",
        type_code="CTRL_KEMIKALIJA_TYPE_REQUIRED",
        param1_code="CTRL_KEMIKALIJA_PARAM1_NOT_EMPTY",
        param2_code="CTRL_KEMIKALIJA_PARAM2_NOT_EMPTY",
        param1_must_be_empty=True,
    ),
    _ControlPairSpec(
        tip_podatka="raztopina",
        validity="kontrolaveljavnostiraztopine",
        validity_label="kontrolaVeljavnostiRaztopine",
        validity_code="CTRL_RAZTOPINA_VALIDITY_REQUIRED",
        suitability="kontrolaustreznostiraztopine",
        suitability_label="kontrolaUstreznostiRaztopine",
        suitability_code="CTRL_RAZTOPINA_SUITABILITY_REQUIRED",
        type_code="CTRL_RAZTOPINA_TYPE_REQUIRED",
        param1_code="CTRL_RAZTOPINA_PARAM1_MISMATCH",
        param2_code="CTRL_RAZTOPINA_PARAM2_NOT_EMPTY",
        param1_must_be_empty=False,
    ),
)


@register
class ChemicalSolutionControlsRule(RowRule):
    """Kemikalija/raztopina: kontroli veljavnosti in ustreznosti sta obvezni skupaj, tip podatka je točen."""

    name = "chemical_solution_controls_rule"
    description = (
        "Če je v vrstici kontrola 'kontrolaVeljavnostiKemikalije' ali 'kontrolaUstreznostiKemikalije', "
        "morata biti prisotni obe, tip podatka pa mora biti 'kemikalija'. "
        "Enako velja za 'kontrolaVeljavnostiRaztopine' in 'kontrolaUstreznostiRaztopine' ter tip 'raztopina'."
    )

    def evaluate(self, row: Mapping[str, object], context: RuleContext) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        tip_data_raw = coerce_str(row.get("Tip podatka", ""))
        tip_data = norm_text(tip_data_raw)
        controls = _get_present_controls(row, shared)

        errors = []
        for spec in _CONTROL_PAIR_SPECS:
            validity = _get_control(controls, spec.validity)
            suitability = _get_control(controls, spec.suitability)
            present = validity + suitability
            if not present:
                continue

            if not validity:
                errors.append(
                    self.build_error(
                        f"Manjka kontrola '{spec.validity_label}': kontroli '{spec.validity_label}' in "
                        f"'{spec.suitability_label}' morata biti v vrstici obe.",
                        context=context,
                        column="(Kontrole)",
                        code=spec.validity_code,
                    )
                )
            if not suitability:
                errors.append(
                    self.build_error(
                        f"Manjka kontrola '{spec.suitability_label}': kontroli '{spec.validity_label}' in "
                        f"'{spec.suitability_label}' morata biti v vrstici obe.",
                        context=context,
                        column="(Kontrole)",
                        code=spec.suitability_code,
                    )
                )

            if tip_data != spec.tip_podatka:
                shown = tip_data_raw.strip() or "(prazno)"
                errors.append(
                    self.build_error(
                        f"Kontroli '{spec.validity_label}' in '{spec.suitability_label}' sta dovoljeni samo "
                        f"pri tipu podatka '{spec.tip_podatka}'. Trenutno: Tip podatka='{shown}'.",
                        context=context,
                        column=present[0].column,
                        code=spec.type_code,
                    )
                )

            errors.extend(self._check_params(row, spec, validity, suitability, context))
        return errors

    def _check_params(
        self,
        row: Mapping[str, object],
        spec: _ControlPairSpec,
        validity: Sequence[ControlInstance],
        suitability: Sequence[ControlInstance],
        context: RuleContext,
    ) -> list:
        errors = []
        present = list(validity) + list(suitability)

        # Param2 mora biti pri obeh kontrolah vedno prazen.
        for control in present:
            if not control.param2_column:
                continue
            value = coerce_str(row.get(control.param2_column, "")).strip()
            if value:
                errors.append(
                    self.build_error(
                        f"Param2 pri kontroli '{control.raw_name}' mora biti prazen. Trenutno: '{value}'.",
                        context=context,
                        column=control.param2_column,
                        code=spec.param2_code,
                    )
                )

        if spec.param1_must_be_empty:
            for control in present:
                if not control.param1_column:
                    continue
                value = coerce_str(row.get(control.param1_column, "")).strip()
                if value:
                    errors.append(
                        self.build_error(
                            f"Param1 pri kontroli '{control.raw_name}' mora biti prazen. Trenutno: '{value}'.",
                            context=context,
                            column=control.param1_column,
                            code=spec.param1_code,
                        )
                    )
            return errors

        # Raztopina: Param1 mora biti pri veljavnosti in ustreznosti enak.
        if validity and suitability:
            v_ctrl, s_ctrl = validity[0], suitability[0]
            v_val = coerce_str(row.get(v_ctrl.param1_column or "", "")).strip()
            s_val = coerce_str(row.get(s_ctrl.param1_column or "", "")).strip()
            if v_val != s_val:
                errors.append(
                    self.build_error(
                        f"Param1 pri '{v_ctrl.raw_name}' ('{v_val}') in '{s_ctrl.raw_name}' "
                        f"('{s_val}') mora biti enak.",
                        context=context,
                        column=s_ctrl.param1_column or s_ctrl.column,
                        code=spec.param1_code,
                    )
                )

        errors.extend(self._check_navodilo_label(row, suitability, context))
        return errors

    def _check_navodilo_label(
        self,
        row: Mapping[str, object],
        suitability: Sequence[ControlInstance],
        context: RuleContext,
    ) -> list:
        """Navodilo mora vsebovati točno oznako raztopine (Param1 pri kontrolaUstreznostiRaztopine)."""
        for control in suitability:
            if not control.param1_column:
                continue
            label = coerce_str(row.get(control.param1_column, "")).strip()
            # Prazen Param1 ali neizračunana formula: oznake ni mogoče primerjati.
            if not label or label.startswith("="):
                continue
            navodilo = coerce_str(row.get("Navodilo", "")).strip()
            if navodilo.startswith("="):
                continue
            if _navodilo_has_label(navodilo, label):
                continue
            shown = navodilo or "(prazno)"
            return [
                self.build_error(
                    f"Navodilo mora vsebovati točno oznako raztopine '{label}' (kot na nalepki; "
                    f"Param1 pri '{control.raw_name}'). Trenutno: '{shown}'.",
                    context=context,
                    column="Navodilo",
                    code="CTRL_RAZTOPINA_NAVODILO_LABEL",
                )
            ]
        return []


def _navodilo_has_label(navodilo: str, label: str) -> bool:
    """True, če Navodilo vsebuje oznako natančno (razlikuje velike/male črke) kot samostojen niz.

    Oznaka ne sme biti del daljše oznake (npr. ``1M-NaOH`` v ``1M-NaOH-PL``)
    ali zapisa števila (``5M-NaOH`` v ``0.5M-NaOH``).
    """
    if not navodilo or not label:
        return False
    pattern = rf"(?<![\w\-.]){re.escape(label)}(?![\w\-]|\.\d)"
    return re.search(pattern, navodilo) is not None


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
                code="CTRL_MASS_WITHOUT_VALUE",
            )
        ]

