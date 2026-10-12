"""Matrix and regression tests for critical control-rule edge cases."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pytest  # pyright: ignore[reportMissingImports]

from validator_oop.core.shared_context import SharedContextBuilder
from validator_oop.rules.builtin.control import (
    DatumCasKonecKontrolaCasaRequiredRule,
    ExcelErrorTokenRule,
    KontrolaIntervalParamRule,
    NavodiloIntervalKontrolaIntervalRequiredRule,
)

CONTROL_SLOTS = (1, 2, 3, 4)


def _control_slot_columns(slot: int) -> tuple[str, str, str]:
    return (
        f"Kontrola-{slot}",
        f"Kontrola-{slot}: Par 1",
        f"Kontrola-{slot}: Par 2",
    )


def _run_rule(
    rule: Any,
    rows: Sequence[Mapping[str, object]],
    columns: Sequence[str],
) -> list[Any]:
    materialized_rows = [dict(row) for row in rows]
    materialized_columns = list(columns)
    context = SharedContextBuilder(row_offset=2).build(materialized_rows, materialized_columns)
    rule.set_shared_context(context)
    return rule.run(materialized_rows, sheet_name="Receptura", row_offset=2)


@pytest.fixture(
    params=[
        pytest.param(
            {
                "rule_cls": ExcelErrorTokenRule,
                "row": {
                    "Kontrola-3": "kontrolaIntervala",
                    "Kontrola-3: Par 1": "1",
                    "Kontrola-3: Par 2": "#REF!",
                    "Vrednost": "",
                },
                "columns": ["Kontrola-3", "Kontrola-3: Par 1", "Kontrola-3: Par 2", "Vrednost"],
                "expected_code": "EXCEL_ERROR_TOKEN",
                "expected_column": "Kontrola-3: Par 2",
            },
            id="excel-error-in-param2-slot3",
        ),
        pytest.param(
            {
                "rule_cls": KontrolaIntervalParamRule,
                "row": {
                    "Navodilo": "3 - 6",
                    "Kontrola-4": "kontrolaIntervala",
                    "Kontrola-4: Par 1": "",
                    "Kontrola-4: Par 2": "",
                },
                "columns": ["Navodilo", "Kontrola-4", "Kontrola-4: Par 1", "Kontrola-4: Par 2"],
                "expected_code": "CTRL_INTERVAL_PARAMS",
                "expected_column": "Kontrola-4: Par 1",
            },
            id="empty-interval-params-slot4",
        ),
        pytest.param(
            {
                "rule_cls": NavodiloIntervalKontrolaIntervalRequiredRule,
                "row": {
                    "Tip objekta": "edit",
                    "Navodilo": "14.01 +/- 0.14",
                    "Kontrola-4": "kontrolaIntervala",
                },
                "columns": ["Tip objekta", "Navodilo", "Kontrola-4"],
                "expected_missing_code": "CTRL_INTERVAL_REQUIRED",
            },
            id="slot4-interval-satisfies-required-rule",
        ),
    ]
)
def control_regression_case(request: pytest.FixtureRequest) -> dict[str, Any]:
    return request.param


@pytest.mark.regression
def test_control_regression_cases(control_regression_case: dict[str, Any]) -> None:
    """Regression fixture set for previously fragile control-slot combinations."""
    rule = control_regression_case["rule_cls"]()
    errors = _run_rule(
        rule,
        [control_regression_case["row"]],
        control_regression_case["columns"],
    )
    error_codes = [error.code for error in errors]

    expected_missing_code = control_regression_case.get("expected_missing_code")
    if expected_missing_code is not None:
        assert expected_missing_code not in error_codes
        return

    expected_code = control_regression_case["expected_code"]
    assert expected_code in error_codes
    expected_column = control_regression_case.get("expected_column")
    if expected_column is not None:
        assert any(error.column == expected_column for error in errors if error.code == expected_code)


@pytest.mark.smoke
@pytest.mark.parametrize("slot", CONTROL_SLOTS)
@pytest.mark.parametrize("control_name", ["kontrolaInterval", "kontrolaIntervala", "kontrolarazlika"])
def test_navodilo_interval_requirement_is_satisfied_by_any_control_slot(
    slot: int, control_name: str
) -> None:
    control_col, _, _ = _control_slot_columns(slot)
    row = {
        "Tip objekta": "edit",
        "Navodilo": "3 - 6",
        control_col: control_name,
    }
    errors = _run_rule(
        NavodiloIntervalKontrolaIntervalRequiredRule(),
        [row],
        ["Tip objekta", "Navodilo", control_col],
    )
    assert "CTRL_INTERVAL_REQUIRED" not in [error.code for error in errors]


@pytest.mark.regression
@pytest.mark.parametrize(
    "navodilo",
    [
        ">= 4 h",
        "T (NB) (≤ 2 .0) (info)",
        "14.01 +/- 0.14",
    ],
)
def test_navodilo_interval_requirement_detects_supported_numeric_forms(navodilo: str) -> None:
    row = {
        "Tip objekta": "edit",
        "Navodilo": navodilo,
        "Kontrola-1": "",
    }
    errors = _run_rule(
        NavodiloIntervalKontrolaIntervalRequiredRule(),
        [row],
        ["Tip objekta", "Navodilo", "Kontrola-1"],
    )
    assert "CTRL_INTERVAL_REQUIRED" in [error.code for error in errors]


@pytest.mark.parametrize("slot", CONTROL_SLOTS)
def test_kontrola_interval_reports_missing_params_in_any_control_slot(slot: int) -> None:
    control_col, param1_col, param2_col = _control_slot_columns(slot)
    row = {
        "Navodilo": "3 - 6",
        control_col: "kontrolaIntervala",
        param1_col: "",
        param2_col: "",
    }
    errors = _run_rule(
        KontrolaIntervalParamRule(),
        [row],
        ["Navodilo", control_col, param1_col, param2_col],
    )
    assert "CTRL_INTERVAL_PARAMS" in [error.code for error in errors]


@pytest.mark.parametrize("slot", CONTROL_SLOTS)
def test_kontrola_interval_requires_both_params_without_numeric_navodilo(slot: int) -> None:
    control_col, param1_col, param2_col = _control_slot_columns(slot)
    row = {
        "Navodilo": "Vnesite temperaturo",
        control_col: "kontrolaIntervala",
        param1_col: "",
        param2_col: "",
    }
    errors = _run_rule(
        KontrolaIntervalParamRule(),
        [row],
        ["Navodilo", control_col, param1_col, param2_col],
    )
    assert "CTRL_INTERVAL_PARAMS" in [error.code for error in errors]


@pytest.mark.parametrize("slot", CONTROL_SLOTS)
def test_kontrola_interval_reports_non_numeric_param2_in_any_control_slot(slot: int) -> None:
    control_col, param1_col, param2_col = _control_slot_columns(slot)
    row = {
        control_col: "kontrolaIntervala",
        param1_col: "10",
        param2_col: "abc",
    }
    errors = _run_rule(
        KontrolaIntervalParamRule(),
        [row],
        [control_col, param1_col, param2_col],
    )
    assert "CTRL_INTERVAL_NOT_NUMBER" in [error.code for error in errors]


@pytest.mark.parametrize(
    ("slot", "token_column"),
    [
        pytest.param(1, "param1", id="slot1-param1"),
        pytest.param(2, "param2", id="slot2-param2"),
        pytest.param(3, "param1", id="slot3-param1"),
        pytest.param(4, "param2", id="slot4-param2"),
    ],
)
def test_excel_error_token_rule_covers_param_columns_across_control_slots(
    slot: int, token_column: str
) -> None:
    control_col, param1_col, param2_col = _control_slot_columns(slot)
    row = {
        control_col: "kontrolaIntervala",
        param1_col: "#N/A" if token_column == "param1" else "10",
        param2_col: "#REF!" if token_column == "param2" else "20",
        "Vrednost": "",
    }
    errors = _run_rule(
        ExcelErrorTokenRule(),
        [row],
        [control_col, param1_col, param2_col, "Vrednost"],
    )
    assert "EXCEL_ERROR_TOKEN" in [error.code for error in errors]


@pytest.mark.smoke
@pytest.mark.parametrize("slot", CONTROL_SLOTS)
def test_datumcaskonec_requirement_is_satisfied_by_kontrolacasa_in_any_slot(slot: int) -> None:
    control_col, _, _ = _control_slot_columns(slot)
    row = {
        "Tip podatka": "datumcasKonec",
        "Tip objekta": "formula1",
        control_col: "kontrolaCasa",
    }
    errors = _run_rule(
        DatumCasKonecKontrolaCasaRequiredRule(),
        [row],
        ["Tip podatka", "Tip objekta", control_col],
    )
    assert "CTRL_CASA_REQUIRED" not in [error.code for error in errors]
