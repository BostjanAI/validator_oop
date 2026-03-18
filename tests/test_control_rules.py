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

        unknown_errors = [e for e in errors if e.code == "KONTROLA_NEZNAN"]
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
        assert "KONTROLA_NEZNAN" in error_codes

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

        unknown_errors = [e for e in errors if e.code == "KONTROLA_NEZNAN"]
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

        context_errors = [e for e in errors if e.code == "KONTROLA_NAPACEN_KONTEKST"]
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
        assert "KONTROLA_NAPACEN_KONTEKST" not in error_codes


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
        assert "KONTROLA_ZAHTEVANO_PRAZNO" in error_codes

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
        assert "KONTROLA_ZAHTEVANO_PRAZNO" not in error_codes


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
        assert "KONTROLA_INTERVAL_NI_STEVILO" in error_codes

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
        assert "KONTROLA_INTERVAL_VRSTA" in error_codes


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

        zakleni_errors = [e for e in errors if "ZAKLENI" in e.code]
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
        assert "ZAKLENI_P1_KORAK_MANJKA" in error_codes

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
        assert "ZAKLENI_PAR1_FORMAT" in error_codes


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

        combo_errors = [e for e in errors if e.code == "ZAKLENI_POGOJ_P1P2"]
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
        assert [e for e in errors if e.code == "ZAKLENI_KLJUC_PODVOJEN"] == []

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
        dup = [e for e in errors if e.code == "ZAKLENI_KLJUC_PODVOJEN"]
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
        dup = [e for e in errors if e.code == "ZAKLENI_KLJUC_PODVOJEN"]
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
        dup = [e for e in errors if e.code == "ZAKLENI_KLJUC_PODVOJEN"]
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

        expected = [e for e in errors if e.code == "KONTROLA_PRICAKOVANO_MANJKA"]
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
        assert [e for e in errors if e.code == "KONTROLA_PRICAKOVANO_MANJKA"] == []


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
        assert "ZAKLENI_P1_MANJKA_ZA_POGOJ" in error_codes

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
        assert [e for e in errors if e.code == "ZAKLENI_P1_MANJKA_ZA_POGOJ"] == []

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
        inverse_errors = [e for e in errors if e.code == "ZAKLENI_P1_MANJKA_ZA_POGOJ"]
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
        inverse_errors = [e for e in errors if e.code == "ZAKLENI_P1_MANJKA_ZA_POGOJ"]
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
        assert "ALIOB_PARAM_DA_NE" in [e.code for e in errors]

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
        assert "CHECKBOX_STANJE" in [e.code for e in errors]

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
        assert [e for e in errors if e.code in {"ALIOB_PARAM_DA_NE", "CHECKBOX_STANJE"}] == []


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
        assert "KONTROLA_INTERVAL_CILJ_P1" in [e.code for e in errors]

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
        assert "KONTROLA_INTERVAL_PM_P2" not in [e.code for e in errors]

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
        assert "KONTROLA_INTERVAL_PM_P2" in [e.code for e in errors]

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
        assert "KONTROLA_INTERVAL_PM_P2" not in [e.code for e in errors]


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

        checkbox_errors = [e for e in errors if "KONTROLA_ZAKLENI" in e.code]
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
        assert "KONTROLA_ALIOB_NE_DOVOLJENA" not in [e.code for e in errors]


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
        assert "KONTROLA_CAS_MIN" in error_codes

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
        assert "KONTROLA_CAS_VRSTA" in error_codes


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
        assert "KONTROLA_CAS_ZAHTEVANA" in error_codes

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
        assert "KONTROLA_CAS_ZAHTEVANA" not in [e.code for e in errors]

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
        assert "KONTROLA_CAS_ZAHTEVANA" in [e.code for e in errors]

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
        assert "KONTROLA_CAS_ZAHTEVANA" not in error_codes


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
        assert "KONTROLA_INTERVAL_ZAHTEVANA" in error_codes

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
        assert "KONTROLA_INTERVAL_ZAHTEVANA" not in [e.code for e in errors]

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
        assert "KONTROLA_INTERVAL_ZAHTEVANA" in [e.code for e in errors]

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
        assert "KONTROLA_INTERVAL_ZAHTEVANA" not in error_codes

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
        assert "KONTROLA_INTERVAL_ZAHTEVANA" not in [e.code for e in errors]

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
        assert "KONTROLA_INTERVAL_ZAHTEVANA" not in [e.code for e in errors]

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
        assert "KONTROLA_INTERVAL_ZAHTEVANA" not in [e.code for e in errors]


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
        assert "KONTROLA_ALIOBKLJUKAN_ZAHTEVANA" in [e.code for e in errors]

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
        assert "KONTROLA_ALIOBKLJUKAN_ZAHTEVANA" not in [e.code for e in errors]

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
        assert "KONTROLA_ALIOBKLJUKAN_ZAHTEVANA" not in [e.code for e in errors]

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
        assert "KONTROLA_ALIOBKLJUKAN_ZAHTEVANA" in [e.code for e in errors]

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
        assert "KONTROLA_ALIOBKLJUKAN_ZAHTEVANA" not in [e.code for e in errors]


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
        assert "KONTROLA_ALIPRAVAVLOGAKODA_ZAHTEVANA" in [e.code for e in errors]

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
        assert "KONTROLA_ALIPRAVAVLOGAKODA_ZAHTEVANA" not in [e.code for e in errors]


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
        assert "KONTROLA_MONOLIT_VELJAVNOST_ZAHTEVANA" in codes
        assert "KONTROLA_MONOLIT_USTREZNOST_ZAHTEVANA" in codes

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
        assert "KONTROLA_MONOLIT_VELJAVNOST_ZAHTEVANA" in codes
        assert "KONTROLA_MONOLIT_USTREZNOST_ZAHTEVANA" not in codes

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
        assert "KONTROLA_MONOLIT_VELJAVNOST_ZAHTEVANA" not in codes
        assert "KONTROLA_MONOLIT_USTREZNOST_ZAHTEVANA" not in codes

