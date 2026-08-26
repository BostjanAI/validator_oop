"""Tests for control validation rules.

This module tests control-related rules like UnknownControlsRule,
ControlContextRule, ZakleniParamRule, and others.
"""

from __future__ import annotations

from typing import Any

import pytest

from validator_oop.core.shared_context import SharedContextBuilder
from validator_oop.core.error import Severity
from validator_oop.rules.builtin.control import (
    AliObkljukanParamRule,
    AliObstajaPogojCombinationRule,
    CheckboxAliObkljukanRequiredRule,
    ControlContextRule,
    DatumCasKonecKontrolaCasaRequiredRule,
    ExcelErrorTokenRule,
    ExpectedControlsRule,
    KontrolaCasaRule,
    KontrolaIntervalAdvancedRule,
    KontrolaIntervalParamRule,
    MonolitControlsRequiredRule,
    NavodiloIntervalKontrolaIntervalRequiredRule,
    RequiredControlsRule,
    UnknownControlsRule,
    ZakleniUniqueKeyRule,
    ZakleniCheckboxRule,
    ZakleniInverseRule,
    ZakleniParamRule,
    ZaposleniAliPravavlogaKodaRequiredRule,
)


class TestUnknownControlsRule:
    """Tests for UnknownControlsRule."""

    @pytest.fixture
    def rule(self) -> UnknownControlsRule:
        """Create an UnknownControlsRule instance."""
        return UnknownControlsRule()

    def test_known_controls(self, rule: UnknownControlsRule) -> None:
        """Test that known controls pass validation."""
        rows = [
            {"Kontrola-1": "kontrolaIntervala", "Kontrola-2": "zaklenipolja"},
            {"Kontrola-1": "aliObstajaPogoj", "Kontrola-2": ""},
            {"Kontrola-1": "kontrolaCasa", "Kontrola-2": "aliObkljukan"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        unknown_errors = [e for e in errors if e.code == "CTRL_UNKNOWN"]
        assert len(unknown_errors) == 0

    def test_unknown_control(self, rule: UnknownControlsRule) -> None:
        """Test that unknown controls raise errors."""
        rows = [
            {"Kontrola-1": "neznanaKontrola", "Kontrola-2": ""},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "CTRL_UNKNOWN" in error_codes

    def test_case_insensitive(self, rule: UnknownControlsRule) -> None:
        """Test that control name matching is case-insensitive."""
        rows = [
            {"Kontrola-1": "KONTROLAINTERVALA", "Kontrola-2": ""},
            {"Kontrola-1": "ZakleniPolja", "Kontrola-2": ""},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        unknown_errors = [e for e in errors if e.code == "CTRL_UNKNOWN"]
        assert len(unknown_errors) == 0


class TestControlContextRule:
    """Tests for ControlContextRule."""

    @pytest.fixture
    def rule(self) -> ControlContextRule:
        """Create a ControlContextRule instance."""
        return ControlContextRule()

    def test_valid_control_context(self, rule: ControlContextRule) -> None:
        """Test that controls in valid context pass."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "kemijski",
                "Kontrola-1": "kontrolaIntervala",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        context_errors = [e for e in errors if e.code == "CTRL_INVALID_CONTEXT"]
        assert len(context_errors) == 0

    def test_control_on_naslov(self, rule: ControlContextRule) -> None:
        """Test that controls on naslov rows do not raise CTRL_BAD_CONTEXT errors.

        The original MES_validator.py does not forbid controls on 'naslov' rows
        explicitly; our OOP implementation mirrors that behavior.
        """
        rows = [
            {
                "Tip objekta": "naslov",
                "Tip podatka": "",
                "Kontrola-1": "kontrolaIntervala",  # Control on naslov
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        # There should be no CTRL_BAD_CONTEXT solely because of 'naslov'
        assert "CTRL_INVALID_CONTEXT" not in error_codes

    @pytest.mark.parametrize(
        "tip_podatka",
        [
            "raztopina",
            "raztopina1",
            "kemikalija",
            "kemikalija2",
            "tehtnica",
            "termometer",
            "kopel",
            "ph_meter",
            "sušilnik",
            "vak_sušilnik",
            "merilnik",
            "naprava",
            "avtoklav",
            "pipeta",
            "konduktometer",
        ],
    )
    def test_aliisto_allowed_on_raztopina_kemikalija_or_oprema(
        self, rule: ControlContextRule, tip_podatka: str
    ) -> None:
        """aliIsto je dovoljena pri raztopina/kemikalija (tudi s pripono) in pri opremi."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": tip_podatka,
                "Kontrola-1": "aliIsto",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert not any(e.code == "CTRL_INVALID_CONTEXT" for e in errors)

    def test_aliisto_forbidden_on_other_tip(self, rule: ControlContextRule) -> None:
        """aliIsto na tipu masa mora javiti KONTROLA_NAPACEN_KONTEKST."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "masa",
                "Kontrola-1": "aliIsto",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        bad = [e for e in errors if e.code == "CTRL_INVALID_CONTEXT"]
        assert len(bad) == 1

    def test_kontrolaustreznostiopremeizmase_allowed_on_klictehtnice1(
        self, rule: ControlContextRule
    ) -> None:
        """kontrolaustreznostiopremeizmase je dovoljena na klicu tehtnice (masa), ne le na kodi/spustnem seznamu."""
        rows = [
            {
                "Tip objekta": "spustniseznam",
                "Tip podatka": "tehtnica",
                "Labela": "koda",
                "Ključ preverjanja": "T1",
            },
            {
                "Tip objekta": "klictehtnice1",
                "Tip podatka": "masa",
                "Labela": "g",
                "Ključ preverjanja": "T1",
                "Kontrola-1": "kontrolaUstreznostiOpremeIzMase",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Labela", "Ključ preverjanja", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        field_errors = [
            e
            for e in errors
            if e.code == "CTRL_INVALID_CONTEXT"
            and "spustnem seznamu" in (e.message or "")
        ]
        assert not field_errors

    def test_kemikalija_control_requires_labela_koda(self, rule: ControlContextRule) -> None:
        """Kemikalija kontrola je dovoljena samo na polju 'koda'."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "kemikalija",
                "Labela": "naziv",
                "Kontrola-1": "kontrolaVeljavnostiKemikalije",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Labela", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "CTRL_INVALID_CONTEXT" for e in errors)

    def test_equipment_control_rejects_non_equipment_context(self, rule: ControlContextRule) -> None:
        """Oprema kontrola na nepovezani ne-oprema vrstici mora javiti napako."""
        rows = [
            {
                "Tip objekta": "spustniseznam",
                "Tip podatka": "kemikalija",
                "Labela": "koda",
                "Ključ preverjanja": "K1",
                "Kontrola-1": "kontrolaVeljavnostiOpreme",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Labela", "Ključ preverjanja", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "CTRL_INVALID_CONTEXT" for e in errors)

    def test_raztopina_control_reports_param_base_mismatch(self, rule: ControlContextRule) -> None:
        """Raztopina kontrola mora preveriti skladnost Param1 s bazo ključa."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "raztopina1",
                "Labela": "koda",
                "Ključ preverjanja": "RAZTOPINA_2",
                "Kontrola-1": "kontrolaVeljavnostiRaztopine",
                "Kontrola-1: Par 1": "NAPACNA_BAZA",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = [
            "Tip objekta",
            "Tip podatka",
            "Labela",
            "Ključ preverjanja",
            "Kontrola-1",
            "Kontrola-1: Par 1",
        ]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "SOLUTION_P1_BASE" for e in errors)


class TestExcelErrorTokenRule:
    """Tests for ExcelErrorTokenRule."""

    @pytest.fixture
    def rule(self) -> ExcelErrorTokenRule:
        """Create an ExcelErrorTokenRule instance."""
        return ExcelErrorTokenRule()

    def test_reports_ref_error_in_aliisto_param1(self, rule: ExcelErrorTokenRule) -> None:
        """aliIsto mora javiti napako pri #REF! v Param1."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "raztopina",
                "Kontrola-1": "aliIsto",
                "Kontrola-1: Par 1": "#REF!",
                "Vrednost": "OK",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Kontrola-1", "Kontrola-1: Par 1", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Receptura", row_offset=2)
        assert "EXCEL_ERROR_TOKEN" in [e.code for e in errors]
        assert any(e.column == "Kontrola-1: Par 1" for e in errors if e.code == "EXCEL_ERROR_TOKEN")

    def test_reports_ref_error_in_zakleni_param1(self, rule: ExcelErrorTokenRule) -> None:
        """zaklenipolja mora javiti napako pri #REF! v Param1."""
        rows = [
            {
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "#REF!",
                "Vrednost": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Receptura", row_offset=2)
        assert "EXCEL_ERROR_TOKEN" in [e.code for e in errors]

    def test_reports_other_excel_error_token(self, rule: ExcelErrorTokenRule) -> None:
        """Pravilo mora zaznati tudi druge obstoječe Excel error tokene."""
        rows = [
            {
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "#N/A",
                "Kontrola-1: Par 2": "10",
                "Vrednost": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Receptura", row_offset=2)
        assert "EXCEL_ERROR_TOKEN" in [e.code for e in errors]
        assert any("N/A" in e.message for e in errors if e.code == "EXCEL_ERROR_TOKEN")

    def test_no_error_for_valid_values(self, rule: ExcelErrorTokenRule) -> None:
        """Veljavne vrednosti ne smejo sprožiti napake."""
        rows = [
            {
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "1",
                "Kontrola-1: Par 2": "2",
                "Vrednost": "=A1+A2",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Receptura", row_offset=2)
        assert "EXCEL_ERROR_TOKEN" not in [e.code for e in errors]


class TestRequiredControlsRule:
    """Tests for RequiredControlsRule."""

    @pytest.fixture
    def rule(self) -> RequiredControlsRule:
        """Create a RequiredControlsRule instance."""
        return RequiredControlsRule()

    def test_input_field_with_empty_control(self, rule: RequiredControlsRule) -> None:
        """Test that input fields with kontrolaPraznoPolje pass."""
        rows = [
            {
                "Tip objekta": "edit",
                "Kontrola-1": "kontrolaPraznoPolje",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        required_errors = [e for e in errors if "CTRL_REQUIRED" in e.code]
        assert len(required_errors) == 0

    def test_input_field_missing_empty_control(self, rule: RequiredControlsRule) -> None:
        """Test that input fields without kontrolaPraznoPolje raise errors."""
        rows = [
            {
                "Tip objekta": "edit",
                "Kontrola-1": "",  # Missing kontrolaPraznoPolje
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "CTRL_REQUIRED_EMPTY" in error_codes

    def test_input_field_all_four_controls_used_no_empty_required(
        self, rule: RequiredControlsRule
    ) -> None:
        """Če so vse 4 kontrolne kolone zasedene, se ne zahteva kontrolaPraznoPolje."""
        rows = [
            {
                "Tip objekta": "edit",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-2": "kontrolaCasa",
                "Kontrola-3": "kontrolaMase",
                "Kontrola-4": "kontrolaVeljavnostiKemikalije",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = [
            "Tip objekta",
            "Kontrola-1",
            "Kontrola-2",
            "Kontrola-3",
            "Kontrola-4",
        ]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "CTRL_REQUIRED_EMPTY" not in error_codes

    def test_checkbox_with_empty_control_forbidden(self, rule: RequiredControlsRule) -> None:
        rows = [
            {
                "Tip objekta": "checkbox",
                "Kontrola-1": "kontrolaPraznoPolje",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert "CTRL_CHECKBOX_EMPTY" in [e.code for e in errors]

    @pytest.mark.parametrize("tip_obj", ["naslov", "crta"])
    def test_naslov_crta_with_empty_control_forbidden(
        self, rule: RequiredControlsRule, tip_obj: str
    ) -> None:
        rows = [
            {
                "Tip objekta": tip_obj,
                "Kontrola-1": "kontrolaPraznoPolje",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert "CTRL_EMPTY_NOT_ALLOWED" in [e.code for e in errors]
        assert "CTRL_REQUIRED_EMPTY" not in [e.code for e in errors]

    @pytest.mark.parametrize("tip_obj", ["naslov", "crta"])
    def test_naslov_crta_without_empty_control_ok(
        self, rule: RequiredControlsRule, tip_obj: str
    ) -> None:
        rows = [{"Tip objekta": tip_obj, "Kontrola-1": ""}]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert "CTRL_EMPTY_NOT_ALLOWED" not in [e.code for e in errors]
        assert "CTRL_REQUIRED_EMPTY" not in [e.code for e in errors]


class TestKontrolaIntervalParamRule:
    """Tests for KontrolaIntervalParamRule."""

    @pytest.fixture
    def rule(self) -> KontrolaIntervalParamRule:
        """Create a KontrolaIntervalParamRule instance."""
        return KontrolaIntervalParamRule()

    def test_valid_interval_params(self, rule: KontrolaIntervalParamRule) -> None:
        """Test that valid interval parameters pass."""
        rows = [
            {
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "10",
                "Kontrola-1: Par 2": "100",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        interval_errors = [e for e in errors if "CTRL_INTERVAL" in e.code]
        assert len(interval_errors) == 0

    def test_interval_non_numeric_param(self, rule: KontrolaIntervalParamRule) -> None:
        """Test that non-numeric interval params raise errors."""
        rows = [
            {
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "abc",  # Not numeric
                "Kontrola-1: Par 2": "100",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "CTRL_INTERVAL_NOT_NUMBER" in error_codes

    def test_interval_wrong_order(self, rule: KontrolaIntervalParamRule) -> None:
        """Test that interval with min > max raises an error."""
        rows = [
            {
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "100",  # Min
                "Kontrola-1: Par 2": "10",  # Max < Min
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "CTRL_INTERVAL_RANGE" in error_codes

    def test_interval_requires_both_params_without_numeric_navodilo(
        self, rule: KontrolaIntervalParamRule
    ) -> None:
        """Par1 in Par2 sta obvezna tudi brez številčnega intervala v Navodilu."""
        rows = [
            {
                "Navodilo": "Vnesite temperaturo",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "",
                "Kontrola-1: Par 2": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert "CTRL_INTERVAL_PARAMS" in [e.code for e in errors]

    def test_interval_with_params_without_numeric_navodilo_ok(
        self, rule: KontrolaIntervalParamRule
    ) -> None:
        """kontrolaInterval z obema mejama je dovoljen brez intervala v Navodilu."""
        rows = [
            {
                "Navodilo": "Vnesite temperaturo",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "10",
                "Kontrola-1: Par 2": "100",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        interval_errors = [e for e in errors if e.code.startswith("CTRL_INTERVAL")]
        assert interval_errors == []


class TestZakleniParamRule:
    """Tests for ZakleniParamRule."""

    @pytest.fixture
    def rule(self) -> ZakleniParamRule:
        """Create a ZakleniParamRule instance."""
        return ZakleniParamRule()

    def test_valid_zakleni_param(self, rule: ZakleniParamRule) -> None:
        """Test that valid zaklenipolja params pass."""
        rows = [
            {"št. Koraka": "1", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "KEY_1", "Kontrola-1: Par 2": "1"},
            {"št. Koraka": "2", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "KEY_2", "Kontrola-1: Par 2": "1"},
            {
                "št. Koraka": "3",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "1,2",  # References existing steps with aliObstajaPogoj
                "Kontrola-1: Par 2": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        zakleni_errors = [e for e in errors if "LOCK" in e.code]
        assert len(zakleni_errors) == 0

    def test_zakleni_missing_step(self, rule: ZakleniParamRule) -> None:
        """Test that zaklenipolja referencing non-existent step raises error."""
        rows = [
            {"št. Koraka": "1", "Kontrola-1": "", "Kontrola-1: Par 1": ""},
            {
                "št. Koraka": "2",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "1,99",  # Step 99 doesn't exist
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "LOCK_P1_STEP_MISSING" in error_codes

    def test_zakleni_invalid_format(self, rule: ZakleniParamRule) -> None:
        """Test that zaklenipolja with invalid format raises error."""
        rows = [
            {
                "št. Koraka": "1",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "not,valid,format",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "LOCK_P1_FORMAT" in error_codes

    def test_zakleni_param1_step_without_pogoj_raises_error(
        self, rule: ZakleniParamRule
    ) -> None:
        """Param1 must list steps that have aliObstajaPogoj (except checkbox zaklenipolja steps)."""
        rows = [
            {
                "št. Koraka": "5",
                "Tip objekta": "checkbox",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "6,7",
            },
            {
                "št. Koraka": "6",
                "Tip objekta": "checkbox",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "5,7",
            },
            {
                "št. Koraka": "7",
                "Tip objekta": "checkbox",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "5,6,27",
            },
            {"št. Koraka": "27", "Tip objekta": "edit", "Kontrola-1": ""},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        ctx.extra["bypass_zakleni_require_pogoj_for_param1_steps"] = False
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        without = [e for e in errors if e.code == "LOCK_P1_WITHOUT_CONDITION"]

        assert len(without) == 1
        assert without[0].row_index == 4
        assert "27" in without[0].message

    def test_zakleni_param1_checkbox_steps_exempt_from_pogoj_requirement(
        self, rule: ZakleniParamRule
    ) -> None:
        """Other checkbox zaklenipolja steps in Param1 do not require aliObstajaPogoj."""
        rows = [
            {
                "št. Koraka": "5",
                "Tip objekta": "checkbox",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "6,7",
            },
            {
                "št. Koraka": "6",
                "Tip objekta": "checkbox",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "5,7",
            },
            {
                "št. Koraka": "7",
                "Tip objekta": "checkbox",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "5,6",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        ctx.extra["bypass_zakleni_require_pogoj_for_param1_steps"] = False
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LOCK_P1_WITHOUT_CONDITION"] == []


class TestAliObstajaPogojCombinationRule:
    """Tests for AliObstajaPogojCombinationRule."""

    @pytest.fixture
    def rule(self) -> AliObstajaPogojCombinationRule:
        """Create an AliObstajaPogojCombinationRule instance."""
        return AliObstajaPogojCombinationRule()

    def test_valid_combination(self, rule: AliObstajaPogojCombinationRule) -> None:
        """Test that valid aliObstajaPogoj combinations pass."""
        # Step 2 is referenced by zaklenipolja at step 1, so Param2 should be 0 when step is in keys_by_zakleni_step
        rows = [
            {
                "št. Koraka": "1",
                "Ključ preverjanja": "ZAKLENI_KEY",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "2",  # References step 2
                "Kontrola-1: Par 2": "",
            },
            {
                "št. Koraka": "2",
                "Ključ preverjanja": "KEY_2",
                "Kontrola-1": "aliObstajaPogoj",
                "Kontrola-1: Par 1": "ZAKLENI_KEY",  # References the key from zaklenipolja
                "Kontrola-1: Par 2": "0",  # Expected value when step is in keys_by_zakleni_step
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Ključ preverjanja", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        combo_errors = [e for e in errors if e.code == "LOCK_CONDITION_P1P2"]
        assert len(combo_errors) == 0


class TestZakleniUniqueKeyRule:
    """Tests for ZakleniUniqueKeyRule."""

    @pytest.fixture
    def rule(self) -> ZakleniUniqueKeyRule:
        """Create a ZakleniUniqueKeyRule instance."""
        return ZakleniUniqueKeyRule()

    def test_unique_keys_pass(self, rule: ZakleniUniqueKeyRule) -> None:
        """Each zaklenipolja row must have a unique Ključ preverjanja."""
        rows = [
            {"št. Koraka": "1", "Ključ preverjanja": "Z1", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "2"},
            {"št. Koraka": "2", "Ključ preverjanja": "Z2", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "3"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Ključ preverjanja", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LOCK_KEY_DUPLICATE"] == []

    def test_duplicate_key_errors(self, rule: ZakleniUniqueKeyRule) -> None:
        """Duplicate Ključ preverjanja among zaklenipolja rows should raise an error per occurrence."""
        rows = [
            {"št. Koraka": "1", "Ključ preverjanja": "Z1", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "2"},
            {"št. Koraka": "2", "Ključ preverjanja": "Z1", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "3"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Ključ preverjanja", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        dup = [e for e in errors if e.code == "LOCK_KEY_DUPLICATE"]
        assert len(dup) == 2
        assert {e.row_index for e in dup} == {2, 3}

    def test_duplicate_key_same_tab_raises_error(self, rule: ZakleniUniqueKeyRule) -> None:
        """Duplicate Ključ preverjanja on same tab should raise an error."""
        rows = [
            {"Zavihek": "Tab1", "št. Koraka": "1", "Ključ preverjanja": "Z1", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "2"},
            {"Zavihek": "", "št. Koraka": "2", "Ključ preverjanja": "Z1", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "3"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "št. Koraka", "Ključ preverjanja", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        dup = [e for e in errors if e.code == "LOCK_KEY_DUPLICATE"]
        assert len(dup) == 2

    def test_same_key_different_tabs_no_error(self, rule: ZakleniUniqueKeyRule) -> None:
        """Same Ključ preverjanja on different tabs should NOT raise an error."""
        rows = [
            # Tab1 has Z1
            {"Zavihek": "Tab1", "št. Koraka": "1", "Ključ preverjanja": "Z1", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "2"},
            # Tab2 also has Z1 - this is allowed on different tab
            {"Zavihek": "Tab2", "št. Koraka": "2", "Ključ preverjanja": "Z1", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "3"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "št. Koraka", "Ključ preverjanja", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        dup = [e for e in errors if e.code == "LOCK_KEY_DUPLICATE"]
        assert len(dup) == 0


class TestExpectedControlsRule:
    """Tests for ExpectedControlsRule."""

    @pytest.fixture
    def rule(self) -> ExpectedControlsRule:
        """Create an ExpectedControlsRule instance."""
        return ExpectedControlsRule()

    def test_kemikalija_missing_controls_warns(self, rule: ExpectedControlsRule) -> None:
        """Kemikalija without recommended controls should emit warnings."""
        rows = [
            {
                "Tip podatka": "kemikalija",
                "Kontrola-1": "",
                "Kontrola-2": "",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        expected = [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"]
        assert len(expected) == 2  # two recommended control groups for kemikalija
        assert all(e.severity == Severity.WARNING for e in expected)

    def test_kemikalija_with_controls_no_warning(self, rule: ExpectedControlsRule) -> None:
        """Kemikalija with recommended controls should not warn."""
        rows = [
            {
                "Tip podatka": "kemikalija",
                "Kontrola-1": "kontrolaVeljavnostiKemikalije",
                "Kontrola-2": "kontrolaUstreznostiKemikalije",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"] == []

    def test_repro_missing_controls_warns(self, rule: ExpectedControlsRule) -> None:
        rows = [{"Tip podatka": "repro", "Kontrola-1": "", "Kontrola-2": ""}]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        expected = [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"]
        assert len(expected) == 2
        assert all(e.severity == Severity.WARNING for e in expected)

    def test_repro_with_controls_no_warning(self, rule: ExpectedControlsRule) -> None:
        rows = [
            {
                "Tip podatka": "repro",
                "Kontrola-1": "kontrolaVeljavnostiRepro",
                "Kontrola-2": "kontrolaUstreznostiRepro",
            }
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"] == []

    def test_reproodpis_missing_controls_warns(self, rule: ExpectedControlsRule) -> None:
        rows = [{"Tip podatka": "reproodpis", "Kontrola-1": "", "Kontrola-2": ""}]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        expected = [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"]
        assert len(expected) == 2

    def test_tehtnica_without_masa_value_does_not_require_ustreznost(self, rule: ExpectedControlsRule) -> None:
        """Tehtnica should not require oprema suitability if matching masa has empty Vrednost."""
        rows = [
            {
                "Tip podatka": "masa",
                "Ključ preverjanja": "K1",
                "Vrednost": "",
                "Kontrola-1": "kontrolaMase",
            },
            {
                "Tip podatka": "tehtnica",
                "Ključ preverjanja": "K1",
                "Vrednost": "TEH-KLA",
                "Kontrola-1": "kontrolaVeljavnostiOpreme",
                "Kontrola-2": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        expected = [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"]
        assert not any("Oprema – pričakovana kontrola ustreznosti" in e.message for e in expected)

    def test_tehtnica_with_masa_value_requires_ustreznost(self, rule: ExpectedControlsRule) -> None:
        """Tehtnica should require oprema suitability if matching masa has non-empty Vrednost."""
        rows = [
            {
                "Tip podatka": "masa",
                "Ključ preverjanja": "K1",
                "Vrednost": "10 g",
                "Kontrola-1": "kontrolaMase",
            },
            {
                "Tip podatka": "tehtnica",
                "Ključ preverjanja": "K1",
                "Vrednost": "TEH-KLA",
                "Kontrola-1": "kontrolaVeljavnostiOpreme",
                "Kontrola-2": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        expected = [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"]
        assert any("Oprema – pričakovana kontrola ustreznosti" in e.message for e in expected)

    def test_masa_porabljan_without_value_is_exception(self, rule: ExpectedControlsRule) -> None:
        """Masa z navodilom 'porabljan...' in prazno Vrednost ne zahteva priporocenih kontrol."""
        rows = [
            {
                "Tip podatka": "masa",
                "Navodilo": "porabljana kolicina",
                "Vrednost": "",
                "Kontrola-1": "",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Navodilo", "Vrednost", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"] == []

    def test_tehtnica_missing_validity_includes_equipment_name(self, rule: ExpectedControlsRule) -> None:
        """Warning for oprema should include concrete equipment type in message."""
        rows = [
            {
                "Tip podatka": "tehtnica",
                "Tip objekta": "spustniseznam",
                "Ključ preverjanja": "K1",
                "Vrednost": "TEH-KLA",
                "Kontrola-1": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Tip objekta", "Ključ preverjanja", "Vrednost", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        expected = [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"]
        assert any("za opremo 'tehtnica'" in e.message for e in expected)

    def test_equipment_without_dropdown_or_koda_does_not_require_validity(self, rule: ExpectedControlsRule) -> None:
        """Oprema brez spustnega seznama in brez Labela 'koda' ne zahteva kontrole veljavnosti."""
        rows = [
            {
                "Tip podatka": "termometer",
                "Tip objekta": "edit",
                "Labela": "naziv opreme",
                "Kontrola-1": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Tip objekta", "Labela", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        expected = [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"]
        assert not any("Oprema – pričakovana kontrola veljavnosti" in e.message for e in expected)

    def test_equipment_with_label_koda_requires_validity(self, rule: ExpectedControlsRule) -> None:
        """Oprema z Labela 'koda' zahteva kontrolo veljavnosti tudi brez spustnega seznama."""
        rows = [
            {
                "Tip podatka": "termometer",
                "Tip objekta": "edit",
                "Labela": "koda",
                "Kontrola-1": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Tip objekta", "Labela", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        expected = [e for e in errors if e.code == "CTRL_EXPECTED_MISSING"]
        assert any("Oprema – pričakovana kontrola veljavnosti" in e.message for e in expected)


class TestZakleniInverseRule:
    """Tests for ZakleniInverseRule."""

    @pytest.fixture
    def rule(self) -> ZakleniInverseRule:
        """Create a ZakleniInverseRule instance."""
        return ZakleniInverseRule()

    def test_missing_in_zakleni_param1_errors(self, rule: ZakleniInverseRule) -> None:
        """Step with aliObstajaPogoj must appear in some zaklenipolja Param1."""
        rows = [
            {"št. Koraka": "1", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
            {"št. Koraka": "2", "Kontrola-1": "", "Kontrola-1: Par 1": "", "Kontrola-1: Par 2": ""},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "LOCK_P1_MISSING_FOR_CONDITION" in error_codes

    def test_present_in_zakleni_param1_no_error(self, rule: ZakleniInverseRule) -> None:
        """If zaklenipolja Param1 lists the aliObstajaPogoj step, no inverse error."""
        rows = [
            {"št. Koraka": "1", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
            {"št. Koraka": "2", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "1", "Kontrola-1: Par 2": ""},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LOCK_P1_MISSING_FOR_CONDITION"] == []

    def test_missing_in_zakleni_param1_reports_per_tab(self, rule: ZakleniInverseRule) -> None:
        """Same step on multiple tabs should raise an error on each tab."""
        rows = [
            {"Zavihek": "Tab1", "št. Koraka": "38", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
            {"Zavihek": "Tab2", "št. Koraka": "38", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
            {"Zavihek": "Tab3", "št. Koraka": "38", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
            {"Zavihek": "Tab4", "št. Koraka": "38", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "št. Koraka", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        inverse_errors = [e for e in errors if e.code == "LOCK_P1_MISSING_FOR_CONDITION"]
        assert len(inverse_errors) == 4

    def test_missing_in_zakleni_param1_reports_only_for_missing_tabs(self, rule: ZakleniInverseRule) -> None:
        """If one tab references the step in zaklenipolja Param1, only other tabs should error."""
        rows = [
            {"Zavihek": "Tab1", "št. Koraka": "38", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
            {"Zavihek": "Tab1", "št. Koraka": "1", "Ključ preverjanja": "ZK1", "Kontrola-1": "zaklenipolja", "Kontrola-1: Par 1": "38"},
            {"Zavihek": "Tab2", "št. Koraka": "38", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
            {"Zavihek": "Tab3", "št. Koraka": "38", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
            {"Zavihek": "Tab4", "št. Koraka": "38", "Kontrola-1": "aliObstajaPogoj", "Kontrola-1: Par 1": "X", "Kontrola-1: Par 2": "1"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = [
            "Zavihek",
            "št. Koraka",
            "Ključ preverjanja",
            "Kontrola-1",
            "Kontrola-1: Par 1",
            "Kontrola-1: Par 2",
        ]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        inverse_errors = [e for e in errors if e.code == "LOCK_P1_MISSING_FOR_CONDITION"]
        assert len(inverse_errors) == 3


class TestAliObkljukanParamRule:
    """Tests for AliObkljukanParamRule."""

    @pytest.fixture
    def rule(self) -> AliObkljukanParamRule:
        """Create an AliObkljukanParamRule instance."""
        return AliObkljukanParamRule()

    def test_param_must_be_da_ne(self, rule: AliObkljukanParamRule) -> None:
        """Param1 must be DA/NE for aliObkljukan."""
        rows = [
            {"Tip objekta": "checkbox", "Ključ preverjanja": "CB1", "Vrednost": "1", "Kontrola-1": "aliObkljukan", "Kontrola-1: Par 1": "MOGOČE"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Ključ preverjanja", "Vrednost", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "ALIOB_PARAM_CHECK" in [e.code for e in errors]

    def test_param_must_match_checkbox_state(self, rule: AliObkljukanParamRule) -> None:
        """DA/NE must match checkbox state derived from Vrednost."""
        rows = [
            {"Tip objekta": "checkbox", "Ključ preverjanja": "CB1", "Vrednost": "1", "Kontrola-1": "aliObkljukan", "Kontrola-1: Par 1": "NE"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Ključ preverjanja", "Vrednost", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CHECKBOX_STATE" in [e.code for e in errors]

    def test_valid_param_matches_state(self, rule: AliObkljukanParamRule) -> None:
        """Valid DA for checked checkbox should pass."""
        rows = [
            {"Tip objekta": "checkbox", "Ključ preverjanja": "CB1", "Vrednost": "1", "Kontrola-1": "aliObkljukan", "Kontrola-1: Par 1": "DA"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Ključ preverjanja", "Vrednost", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code in {"ALIOB_PARAM_CHECK", "CHECKBOX_STATE"}] == []


class TestKontrolaIntervalAdvancedRule:
    """Tests for KontrolaIntervalAdvancedRule."""

    @pytest.fixture
    def rule(self) -> KontrolaIntervalAdvancedRule:
        """Create a KontrolaIntervalAdvancedRule instance."""
        return KontrolaIntervalAdvancedRule()

    def test_inequality_strict_greater(self, rule: KontrolaIntervalAdvancedRule) -> None:
        """For '> 10', Param1 must be 10 and Param2 must be >= 11 (eps=1)."""
        rows = [
            {
                "Navodilo": "> 10",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "10",
                "Kontrola-1: Par 2": "11",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code.startswith("CTRL_INTERVAL_TARGET_")] == []

    def test_inequality_strict_greater_wrong_param1(self, rule: KontrolaIntervalAdvancedRule) -> None:
        """Wrong Param1 for '> 10' should raise CTRL_INTERVAL_TARGET_P1_EXACT."""
        rows = [
            {
                "Navodilo": "> 10",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "9",
                "Kontrola-1: Par 2": "11",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_TARGET_P1" in [e.code for e in errors]

    def test_gte_prefix_on_volume_range_rejects_too_high_param2(
        self, rule: KontrolaIntervalAdvancedRule
    ) -> None:
        """'≥ 10 - 11 CV (≥ 4000 - 4400 mL)' is a range: Param2 must be 4401, not an open ≥ 4000."""
        rows = [
            {
                "Navodilo": "Prečrpano ≥ 10 - 11 CV dH2O (≥ 4000 - 4400 mL)",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "3999",
                "Kontrola-1: Par 2": "8801",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_P2_BOUND" in [e.code for e in errors]

    def test_gte_prefix_on_volume_range_accepts_open_interval_bounds(
        self, rule: KontrolaIntervalAdvancedRule
    ) -> None:
        """Open interval for 4000–4400 mL is Param1=3999 and Param2=4401."""
        rows = [
            {
                "Navodilo": "Prečrpano ≥ 10 - 11 CV dH2O (≥ 4000 - 4400 mL)",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "3999",
                "Kontrola-1: Par 2": "4401",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code.startswith("CTRL_INTERVAL_")] == []

    def test_inequality_gte_double_value_navodilo_accepts_correct_params(
        self, rule: KontrolaIntervalAdvancedRule
    ) -> None:
        """For navodilo with two values like '≥ 5 MVS (≥ 3.35 L)', Param1=3.34 and Param2=3.36 must be valid."""
        rows = [
            {
                "Navodilo": "Prečrpano ≥ 5 MVS 80 % v/v EtOH (≥ 3.35 L)",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "3.34",
                "Kontrola-1: Par 2": "3.36",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code.startswith("CTRL_INTERVAL_TARGET_")] == []

    def test_inequality_gte_fp_noise_in_param1_accepts_as_correct(
        self, rule: KontrolaIntervalAdvancedRule
    ) -> None:
        """Param1 with tiny floating-point noise (e.g. formula cell) must not raise a false positive."""
        rows = [
            {
                "Navodilo": "≥ 3.35 L",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "3.340000000001",
                "Kontrola-1: Par 2": "3.36",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "CTRL_INTERVAL_TARGET_P1"] == []

    def test_inequality_less_equal_with_spaced_decimal_uses_correct_step(
        self, rule: KontrolaIntervalAdvancedRule
    ) -> None:
        """For '<= 2 .0', Param2 should be 2.1 (not 3.0)."""
        rows = [
            {
                "Navodilo": "T (NB) (≤ 2 .0) (info)",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "1.9",
                "Kontrola-1: Par 2": "2.3",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        target_p2_errors = [e for e in errors if e.code == "CTRL_INTERVAL_TARGET_P2"]
        assert len(target_p2_errors) == 1
        assert "Param2 mora biti 2.1" in target_p2_errors[0].message
        assert "Param2 mora biti 3.0" not in target_p2_errors[0].message

    def test_pm_tolerance_high_resolution_param2_accepts_3213(self, rule: KontrolaIntervalAdvancedRule) -> None:
        """For 3.180 ± 0.032, Param2=3.213 must be valid."""
        rows = [
            {
                "Navodilo": "3.180 ± 0.032",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "3.140",
                "Kontrola-1: Par 2": "3.213",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_PM_P2" not in [e.code for e in errors]

    def test_pm_tolerance_high_resolution_param2_rejects_3222(self, rule: KontrolaIntervalAdvancedRule) -> None:
        """For 3.180 ± 0.032, Param2=3.222 must be invalid."""
        rows = [
            {
                "Navodilo": "3.180 ± 0.032",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "3.140",
                "Kontrola-1: Par 2": "3.222",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_PM_P2" in [e.code for e in errors]

    def test_pm_tolerance_integer_center_accepts_7_5_8_5(self, rule: KontrolaIntervalAdvancedRule) -> None:
        """For 8 ± 0.4, Param1=7.5 and Param2=8.5 must be valid."""
        rows = [
            {
                "Navodilo": "8 ± 0.4",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "7.5",
                "Kontrola-1: Par 2": "8.5",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_PM_P1" not in [e.code for e in errors]
        assert "CTRL_INTERVAL_PM_P2" not in [e.code for e in errors]

    def test_pm_tolerance_integer_center_rejects_wrong_param1(self, rule: KontrolaIntervalAdvancedRule) -> None:
        """For 8 ± 0.4, Param1=6.6 and Param2=8.5 must be invalid."""
        rows = [
            {
                "Navodilo": "8 ± 0.4",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "6.6",
                "Kontrola-1: Par 2": "8.5",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_PM_P1" in [e.code for e in errors]

    def test_pm_tolerance_14_01_014_param2_accepts_14160(self, rule: KontrolaIntervalAdvancedRule) -> None:
        """For 14.01 +/- 0.14, Param2=14.160 must be valid."""
        rows = [
            {
                "Navodilo": "14.01 +/- 0.14",
                "Kontrola-1": "kontrolaIntervala",
                "Kontrola-1: Par 1": "13.835",
                "Kontrola-1: Par 2": "14.160",
            }
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_PM_P2" not in [e.code for e in errors]


class TestZakleniCheckboxRule:
    """Tests for ZakleniCheckboxRule."""

    @pytest.fixture
    def rule(self) -> ZakleniCheckboxRule:
        """Create a ZakleniCheckboxRule instance."""
        return ZakleniCheckboxRule()

    def test_zakleni_with_checkbox(self, rule: ZakleniCheckboxRule) -> None:
        """Test that zaklenipolja with checkbox passes."""
        rows = [
            {
                "št. Koraka": "1",
                "Tip objekta": "checkbox",
                "Ključ preverjanja": "CHECK_KEY",
                "Vrednost": "1",
            },
            {
                "št. Koraka": "2",
                "Tip objekta": "edit",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "1",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Ključ preverjanja", "Vrednost", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        checkbox_errors = [e for e in errors if "CTRL_LOCK" in e.code]
        assert len(checkbox_errors) == 0

    def test_aliobstajapogoj_with_aliobkljukan_on_checkbox_no_error(
        self, rule: ZakleniCheckboxRule
    ) -> None:
        """Pri checkboxu je aliObkljukan dovoljen tudi skupaj z aliObstajaPogoj."""
        rows = [
            {
                "Tip podatka": "checkbox",
                "Tip objekta": "checkbox",
                "Labela": "DA (kljukica)",
                "Kontrola-1": "aliObstajaPogoj",
                "Kontrola-2": "aliObkljukan",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Tip objekta", "Labela", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_ALIOB_NOT_ALLOWED" not in [e.code for e in errors]


class TestKontrolaCasaRule:
    """Tests for KontrolaCasaRule."""

    @pytest.fixture
    def rule(self) -> KontrolaCasaRule:
        """Create a KontrolaCasaRule instance."""
        return KontrolaCasaRule()

    def test_valid_kontrola_casa(self, rule: KontrolaCasaRule) -> None:
        """Test that valid kontrolaCasa configuration passes."""
        rows = [
            {
                "Kontrola-1": "kontrolaCasa",
                "Kontrola-1: Par 1": "10",  # Min time
                "Kontrola-1: Par 2": "60",  # Max time
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        casa_errors = [e for e in errors if "CTRL_CASA" in e.code]
        assert len(casa_errors) == 0

    def test_kontrola_casa_missing_min(self, rule: KontrolaCasaRule) -> None:
        """Test that kontrolaCasa without min time raises error."""
        rows = [
            {
                "Kontrola-1": "kontrolaCasa",
                "Kontrola-1: Par 1": "",  # Missing min
                "Kontrola-1: Par 2": "60",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "CTRL_CASA_MIN" in error_codes

    def test_kontrola_casa_wrong_order(self, rule: KontrolaCasaRule) -> None:
        """Test that kontrolaCasa with min > max raises error."""
        rows = [
            {
                "Kontrola-1": "kontrolaCasa",
                "Kontrola-1: Par 1": "100",  # Min
                "Kontrola-1: Par 2": "10",  # Max < Min
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Kontrola-1", "Kontrola-1: Par 1", "Kontrola-1: Par 2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "CTRL_CASA_RANGE" in error_codes


class TestDatumCasKonecKontrolaCasaRequiredRule:
    """Tests for DatumCasKonecKontrolaCasaRequiredRule."""

    @pytest.fixture
    def rule(self) -> DatumCasKonecKontrolaCasaRequiredRule:
        """Create a DatumCasKonecKontrolaCasaRequiredRule instance."""
        return DatumCasKonecKontrolaCasaRequiredRule()

    def test_datumcaskonec_missing_kontrolacasa_raises_error(
        self, rule: DatumCasKonecKontrolaCasaRequiredRule
    ) -> None:
        """Tip podatka datumcaskonec z Tip objekta edit brez kontrolaCasa mora javljati napako."""
        rows = [
            {
                "Tip podatka": "datumcasKonec",
                "Tip objekta": "edit",
                "Kontrola-1": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CTRL_CASA_REQUIRED" in error_codes

    def test_datumcaskonec_tip_objekta_not_edit_no_error(
        self, rule: DatumCasKonecKontrolaCasaRequiredRule
    ) -> None:
        """Pri Tip objekta različnem od edit/formula/formula0/formula1 (npr. izberidatumcas) kontrolaCasa ni obvezna."""
        rows = [
            {
                "Tip podatka": "datumcasKonec",
                "Tip objekta": "izberidatumcas",
                "Kontrola-1": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_CASA_REQUIRED" not in [e.code for e in errors]

    @pytest.mark.parametrize("tip_objekta", ["formula", "formula0", "formula1"])
    def test_datumcaskonec_formula_tip_objekta_requires_kontrolacasa(
        self, rule: DatumCasKonecKontrolaCasaRequiredRule, tip_objekta: str
    ) -> None:
        """Pri Tip objekta formula/formula0/formula1 brez kontrolaCasa se zahteva napaka."""
        rows = [
            {
                "Tip podatka": "datumcasKonec",
                "Tip objekta": tip_objekta,
                "Kontrola-1": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_CASA_REQUIRED" in [e.code for e in errors]

    def test_datumcaskonec_with_kontrolacasa_no_error(
        self, rule: DatumCasKonecKontrolaCasaRequiredRule
    ) -> None:
        """Tip podatka datumcaskonec z kontrolaCasa ne sme javljati napake CTRL_CASA_REQUIRED."""
        rows = [
            {
                "Tip podatka": "datumcasKonec",
                "Kontrola-1": "kontrolaCasa",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CTRL_CASA_REQUIRED" not in error_codes


class TestNavodiloIntervalKontrolaIntervalRequiredRule:
    """Tests for NavodiloIntervalKontrolaIntervalRequiredRule."""

    @pytest.fixture
    def rule(self) -> NavodiloIntervalKontrolaIntervalRequiredRule:
        """Create a NavodiloIntervalKontrolaIntervalRequiredRule instance."""
        return NavodiloIntervalKontrolaIntervalRequiredRule()

    @pytest.mark.parametrize(
        "navodilo",
        [
            "≥ 4 h",
            ">= 4 h",
            "3 - 6",
            "57.5 ± 3.0",
            "14.01 +/- 0.14",
        ],
    )
    def test_navodilo_with_interval_without_kontrolainterval_raises_error(
        self, rule: NavodiloIntervalKontrolaIntervalRequiredRule, navodilo: str
    ) -> None:
        """Če Navodilo vsebuje interval, Tip objekta je edit in kontrolaInterval manjka, se javi napaka."""
        rows = [
            {
                "Navodilo": navodilo,
                "Tip objekta": "edit",
                "Kontrola-1": "",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CTRL_INTERVAL_REQUIRED" in error_codes

    def test_navodilo_with_interval_tip_objekta_not_edit_no_error(
        self, rule: NavodiloIntervalKontrolaIntervalRequiredRule
    ) -> None:
        """Pri Tip objekta različnem od edit/formula/formula0/formula1 kontrolaInterval ni obvezna."""
        rows = [
            {
                "Navodilo": "3 - 6",
                "Tip objekta": "izberidatumcas",
                "Kontrola-1": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_REQUIRED" not in [e.code for e in errors]

    @pytest.mark.parametrize("tip_objekta", ["formula", "formula0", "formula1"])
    def test_navodilo_with_interval_formula_tip_objekta_requires_kontrolainterval(
        self, rule: NavodiloIntervalKontrolaIntervalRequiredRule, tip_objekta: str
    ) -> None:
        """Pri Tip objekta formula/formula0/formula1 in intervalu v Navodilu brez kontrolaInterval se javi napaka."""
        rows = [
            {
                "Navodilo": "3 - 6",
                "Tip objekta": tip_objekta,
                "Kontrola-1": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Tip objekta", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_REQUIRED" in [e.code for e in errors]

    def test_navodilo_with_interval_and_kontrolainterval_no_error(
        self, rule: NavodiloIntervalKontrolaIntervalRequiredRule
    ) -> None:
        """Če Navodilo vsebuje interval in je prisotna kontrolaInterval, napake ne sme biti."""
        rows = [
            {
                "Navodilo": "3 - 6",
                "Kontrola-1": "kontrolaIntervala",
            },
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CTRL_INTERVAL_REQUIRED" not in error_codes

    def test_datumcaskonec_with_interval_no_kontrolainterval_no_error(
        self, rule: NavodiloIntervalKontrolaIntervalRequiredRule
    ) -> None:
        """Pri tipu datumcaskonec s časovnim intervalom v Navodilu kontrolaInterval ni obvezna (pokriva kontrolacasa)."""
        rows = [
            {
                "Tip podatka": "datumcasKonec",
                "Navodilo": "≥ 4 h",
                "Kontrola-1": "kontrolaCasa",
                "Kontrola-2": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Navodilo", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_REQUIRED" not in [e.code for e in errors]

    def test_checkbox_with_interval_no_kontrolainterval_no_error(
        self, rule: NavodiloIntervalKontrolaIntervalRequiredRule
    ) -> None:
        """Pri tipu objekta checkbox s številčnim intervalom v Navodilu kontrolaInterval ni obvezna."""
        rows = [
            {
                "Navodilo": "3 - 6",
                "Tip objekta": "checkbox",
                "Labela": "DA (kljukica)",
                "Kontrola-1": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Tip objekta", "Labela", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_REQUIRED" not in [e.code for e in errors]

    def test_labela_koda_with_interval_no_kontrolainterval_no_error(
        self, rule: NavodiloIntervalKontrolaIntervalRequiredRule
    ) -> None:
        """Pri Labela 'koda' s številčnim intervalom v Navodilu kontrolaInterval ni obvezna."""
        rows = [
            {
                "Navodilo": "3 - 6",
                "Tip objekta": "edit",
                "Labela": "koda",
                "Kontrola-1": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Navodilo", "Tip objekta", "Labela", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_INTERVAL_REQUIRED" not in [e.code for e in errors]


class TestCheckboxAliObkljukanRequiredRule:
    """Tests for CheckboxAliObkljukanRequiredRule."""

    @pytest.fixture
    def rule(self) -> CheckboxAliObkljukanRequiredRule:
        """Create a CheckboxAliObkljukanRequiredRule instance."""
        return CheckboxAliObkljukanRequiredRule()

    def test_checkbox_missing_aliobkljukan_raises_error(
        self, rule: CheckboxAliObkljukanRequiredRule
    ) -> None:
        """Tip podatka checkbox z Labela 'DA (kljukica)' brez aliObkljukan mora javljati napako."""
        rows = [
            {
                "Tip podatka": "checkbox",
                "Labela": "DA (kljukica)",
                "Kontrola-1": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Labela", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_ALIOBKLJUKAN_REQUIRED" in [e.code for e in errors]

    def test_checkbox_with_aliobkljukan_no_error(
        self, rule: CheckboxAliObkljukanRequiredRule
    ) -> None:
        """Tip podatka checkbox z Labela 'DA (kljukica)' in aliObkljukan ne sme javljati napake."""
        rows = [
            {
                "Tip podatka": "checkbox",
                "Labela": "DA (kljukica)",
                "Kontrola-1": "aliObkljukan",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Labela", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_ALIOBKLJUKAN_REQUIRED" not in [e.code for e in errors]

    def test_checkbox_with_zaklenipolja_no_aliobkljukan_no_error(
        self, rule: CheckboxAliObkljukanRequiredRule
    ) -> None:
        """Checkbox z zaklenipolja ne zahteva aliObkljukan; napaka se ne sme javiti."""
        rows = [
            {
                "Tip podatka": "checkbox",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-2": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_ALIOBKLJUKAN_REQUIRED" not in [e.code for e in errors]

    def test_checkbox_with_aliobstajapogoj_no_aliobkljukan_raises_error(
        self, rule: CheckboxAliObkljukanRequiredRule
    ) -> None:
        """Checkbox z aliObstajaPogoj še vedno zahteva aliObkljukan."""
        rows = [
            {
                "Tip podatka": "checkbox",
                "Labela": "DA (kljukica)",
                "Kontrola-1": "aliObstajaPogoj",
                "Kontrola-2": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Labela", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_ALIOBKLJUKAN_REQUIRED" in [e.code for e in errors]

    def test_checkbox_with_aliobstajapogoj_and_aliobkljukan_no_error(
        self, rule: CheckboxAliObkljukanRequiredRule
    ) -> None:
        """Checkbox z aliObstajaPogoj in aliObkljukan je veljaven."""
        rows = [
            {
                "Tip podatka": "checkbox",
                "Labela": "DA (kljukica)",
                "Kontrola-1": "aliObstajaPogoj",
                "Kontrola-2": "aliObkljukan",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Labela", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_ALIOBKLJUKAN_REQUIRED" not in [e.code for e in errors]


class TestZaposleniAliPravavlogaKodaRequiredRule:
    """Tests for ZaposleniAliPravavlogaKodaRequiredRule."""

    @pytest.fixture
    def rule(self) -> ZaposleniAliPravavlogaKodaRequiredRule:
        """Create a ZaposleniAliPravavlogaKodaRequiredRule instance."""
        return ZaposleniAliPravavlogaKodaRequiredRule()

    def test_zaposleni_missing_alipravavlogakoda_raises_error(
        self, rule: ZaposleniAliPravavlogaKodaRequiredRule
    ) -> None:
        """Tip podatka zaposleni brez aliPravavlogaKoda mora javljati napako."""
        rows = [
            {
                "Tip podatka": "zaposleni",
                "Kontrola-1": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_ALIPRAVAVLOGAKODA_REQUIRED" in [e.code for e in errors]

    def test_zaposleni_with_alipravavlogakoda_no_error(
        self, rule: ZaposleniAliPravavlogaKodaRequiredRule
    ) -> None:
        """Tip podatka zaposleni z aliPravavlogaKoda ne sme javljati napake."""
        rows = [
            {
                "Tip podatka": "zaposleni",
                "Kontrola-1": "aliPravavlogaKoda",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "CTRL_ALIPRAVAVLOGAKODA_REQUIRED" not in [e.code for e in errors]


class TestMonolitControlsRequiredRule:
    """Tests for MonolitControlsRequiredRule."""

    @pytest.fixture
    def rule(self) -> MonolitControlsRequiredRule:
        """Create a MonolitControlsRequiredRule instance."""
        return MonolitControlsRequiredRule()

    @pytest.mark.parametrize("tip_podatka", ["monolit", "monolit1", "monolit2"])
    def test_monolit_missing_both_controls_raises_both_errors(
        self, rule: MonolitControlsRequiredRule, tip_podatka: str
    ) -> None:
        """Tip podatka monolit/monolit1/monolit2 brez obeh kontrol mora javiti obe napaki."""
        rows = [{"Tip podatka": tip_podatka, "Kontrola-1": "", "Kontrola-2": ""}]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        codes = [e.code for e in errors]
        assert "CTRL_MONOLIT_VALIDITY_REQUIRED" in codes
        assert "CTRL_MONOLIT_SUITABILITY_REQUIRED" in codes

    def test_monolit_missing_veljavnost_only_raises_one_error(
        self, rule: MonolitControlsRequiredRule
    ) -> None:
        """Monolit z ustreznostjo brez veljavnosti javi samo KONTROLA_MONOLIT_VELJAVNOST_ZAHTEVANA."""
        rows = [
            {
                "Tip podatka": "monolit",
                "Kontrola-1": "kontrolaUstreznostiMonolita",
                "Kontrola-2": "",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        codes = [e.code for e in errors]
        assert "CTRL_MONOLIT_VALIDITY_REQUIRED" in codes
        assert "CTRL_MONOLIT_SUITABILITY_REQUIRED" not in codes

    def test_monolit_with_both_controls_no_error(
        self, rule: MonolitControlsRequiredRule
    ) -> None:
        """Monolit z obema kontrolama ne sme javljati napak."""
        rows = [
            {
                "Tip podatka": "monolit1",
                "Kontrola-1": "kontrolaVeljavnostiMonolita",
                "Kontrola-2": "kontrolaUstreznostiMonolita",
            },
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        codes = [e.code for e in errors]
        assert "CTRL_MONOLIT_VALIDITY_REQUIRED" not in codes
        assert "CTRL_MONOLIT_SUITABILITY_REQUIRED" not in codes

