"""Tests for relational validation rules.

This module tests DuplicateKeyRule, MassOwnerRule, TimePairRule, and KeyNumberingRule.
"""

from __future__ import annotations

from typing import Any

import pytest

from validator_oop.core.shared_context import SharedContextBuilder
from validator_oop.rules.builtin.relational import (
    DuplicateKeyRule,
    KeyNumberingRule,
    MassOwnerRule,
    TehtnicaMasaPairRule,
    TehtnicaVrednostFromFormulaRule,
    TimePairRule,
)


class TestDuplicateKeyRule:
    """Tests for DuplicateKeyRule."""

    @pytest.fixture
    def rule(self) -> DuplicateKeyRule:
        """Create a DuplicateKeyRule instance."""
        return DuplicateKeyRule()

    def test_no_duplicates(self, rule: DuplicateKeyRule) -> None:
        """Test that unique keys pass validation."""
        rows = [
            {"Ključ preverjanja": "KEY_1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_2", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_3", "Tip podatka": "kemikalija"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        dup_errors = [e for e in errors if "KEY_DUP" in e.code]
        assert len(dup_errors) == 0

    def test_duplicate_kemikalija_key(self, rule: DuplicateKeyRule) -> None:
        """Test that duplicate kemikalija keys raise errors."""
        rows = [
            {"Ključ preverjanja": "KEY_1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_2", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_1", "Tip podatka": "kemikalija"},  # Duplicate
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KEY_DUP_KEM" in error_codes

    def test_duplicate_raztopina_key(self, rule: DuplicateKeyRule) -> None:
        """Test that duplicate raztopina keys raise errors."""
        rows = [
            {"Ključ preverjanja": "RAZT_1", "Tip podatka": "raztopina"},
            {"Ključ preverjanja": "RAZT_1", "Tip podatka": "raztopina"},  # Duplicate
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KEY_DUP_RAZT" in error_codes

    def test_duplicate_masa_key(self, rule: DuplicateKeyRule) -> None:
        """Test that duplicate masa keys raise errors."""
        rows = [
            {"Ključ preverjanja": "MASA_1", "Tip podatka": "masa"},
            {"Ključ preverjanja": "MASA_1", "Tip podatka": "masa"},  # Duplicate
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_MASA" in error_codes

    def test_duplicate_masa_water_keys_allowed(self, rule: DuplicateKeyRule) -> None:
        """Multiple masa with water base (dH2O_1, dH2O_2) without kemikalija/raztopina are allowed."""
        rows = [
            {"Ključ preverjanja": "dH2O_1", "Tip podatka": "masa"},
            {"Ključ preverjanja": "dH2O_2", "Tip podatka": "masa"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_MASA" not in error_codes

    def test_masa_same_key_in_different_sections_raises(self, rule: DuplicateKeyRule) -> None:
        """Same masa key in more than one section raises KEY_DUP_MASA_SECTIONS."""
        rows = [
            {"Tip objekta": "naslov", "Tip podatka": "", "Ključ preverjanja": ""},  # section 1
            {"Tip objekta": "", "Tip podatka": "masa", "Ključ preverjanja": "EtOH1"},
            {"Tip objekta": "naslov", "Tip podatka": "", "Ključ preverjanja": ""},  # section 2
            {"Tip objekta": "", "Tip podatka": "masa", "Ključ preverjanja": "EtOH1"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Ključ preverjanja"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_MASA_RAZD" in error_codes

    def test_masa_same_key_same_section_allowed(self, rule: DuplicateKeyRule) -> None:
        """Same masa key multiple times in the same section is allowed (no KEY_DUP_MASA_SECTIONS)."""
        rows = [
            {"Tip objekta": "naslov", "Tip podatka": "", "Ključ preverjanja": ""},
            {"Tip objekta": "", "Tip podatka": "kemikalija", "Ključ preverjanja": "EtOH1"},
            {"Tip objekta": "", "Tip podatka": "masa", "Ključ preverjanja": "EtOH1"},
            {"Tip objekta": "", "Tip podatka": "masa", "Ključ preverjanja": "EtOH1"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka", "Ključ preverjanja"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_MASA_RAZD" not in error_codes
        assert "KLJUC_PODVOJEN_MASA" not in error_codes

    def test_same_key_different_types(self, rule: DuplicateKeyRule) -> None:
        """Test that same key in different types doesn't raise duplicate error."""
        rows = [
            {"Ključ preverjanja": "KEY_1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_1", "Tip podatka": "raztopina"},  # Same key, different type
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        # Should not have duplicate errors (different types)
        dup_errors = [e for e in errors if "KEY_DUP" in e.code]
        assert len(dup_errors) == 0

    def test_duplicate_datumcas_keys_are_handled_by_time_pair_rule(self, rule: DuplicateKeyRule) -> None:
        """DuplicateKeyRule should not report datumcas duplicates."""
        rows = [
            {"Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},
            {"Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},  # Duplicate
            {"Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaskonec"},  # Matching end
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_CAS_ZAC" not in error_codes
        assert "KLJUC_PODVOJEN_CAS_KONEC" not in error_codes


class TestMassOwnerRule:
    """Tests for MassOwnerRule."""

    @pytest.fixture
    def rule(self) -> MassOwnerRule:
        """Create a MassOwnerRule instance."""
        return MassOwnerRule()

    def test_masa_with_owner(self, rule: MassOwnerRule) -> None:
        """Test that masa with a valid owner passes."""
        # The masa key must also exist in kemikalija or raztopina
        rows = [
            {"Ključ preverjanja": "SHARED_KEY", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "SHARED_KEY", "Tip podatka": "masa"},  # Same key exists in kemikalija
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        no_owner_errors = [e for e in errors if e.code == "PAR_MASA_BREZ_LASTNIKA"]
        assert len(no_owner_errors) == 0

    def test_masa_without_owner(self, rule: MassOwnerRule) -> None:
        """Test that masa without an owner raises an error."""
        rows = [
            {"Ključ preverjanja": "ORPHAN_MASA", "Tip podatka": "masa"},  # No owner
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "PAR_MASA_BREZ_LASTNIKA" in error_codes


class TestTimePairRule:
    """Tests for TimePairRule."""

    @pytest.fixture
    def rule(self) -> TimePairRule:
        """Create a TimePairRule instance."""
        return TimePairRule()

    def test_complete_time_pair(self, rule: TimePairRule) -> None:
        """Test that complete time pairs pass validation."""
        rows = [
            {"Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},
            {"Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaskonec"},  # Same key, matching pair
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        time_errors = [e for e in errors if "PAR_CAS" in e.code]
        assert len(time_errors) == 0

    def test_time_start_without_end(self, rule: TimePairRule) -> None:
        """Test that time start without end raises an error."""
        rows = [
            {"Ključ preverjanja": "TIME_START", "Tip podatka": "datumcaszacetek"},
            # Missing datumcaskonec with same key
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "PAR_CAS_BREZ_KONCA" in error_codes

    def test_time_end_without_start(self, rule: TimePairRule) -> None:
        """Test that time end without start raises an error."""
        rows = [
            {"Ključ preverjanja": "TIME_END", "Tip podatka": "datumcaskonec"},
            # Missing datumcaszacetek with same key
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "PAR_CAS_BREZ_ZACETKA" in error_codes

    def test_duplicate_key_same_tab_raises_error(self, rule: TimePairRule) -> None:
        """Same exact time key repeated on the same tab raises duplicate error."""
        rows = [
            {"Zavihek": "Tab1", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaskonec"},
            # Duplicate pair on same tab
            {"Zavihek": "", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaskonec"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_CAS_PAR" in error_codes

    def test_duplicate_start_key_without_end_still_raises_duplicate_error(self, rule: TimePairRule) -> None:
        """Repeated start key should be duplicate even when matching end is missing."""
        rows = [
            {"Zavihek": "Tab1", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_CAS_PAR" in error_codes
        assert "PAR_CAS_BREZ_KONCA" in error_codes

    def test_distinct_numbered_time_keys_are_not_treated_as_duplicates(self, rule: TimePairRule) -> None:
        """crpanje and crpanje1 must be treated as different exact keys."""
        rows = [
            {"Zavihek": "monolit1", "Ključ preverjanja": "crpanje", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "crpanje", "Tip podatka": "datumcaskonec"},
            {"Zavihek": "", "Ključ preverjanja": "crpanje1", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "crpanje1", "Tip podatka": "datumcaskonec"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_CAS_PAR" not in error_codes
        assert "PAR_CAS_BREZ_KONCA" not in error_codes
        assert "PAR_CAS_BREZ_ZACETKA" not in error_codes

    def test_same_key_different_tabs_no_error(self, rule: TimePairRule) -> None:
        """Test that same time pair key on different tabs does NOT raise an error."""
        rows = [
            # Tab1 has TIME_KEY
            {"Zavihek": "Tab1", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaskonec"},
            # Tab2 also has TIME_KEY - this is allowed on different tab
            {"Zavihek": "Tab2", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "TIME_KEY", "Tip podatka": "datumcaskonec"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_PODVOJEN_CAS_PAR" not in error_codes


class TestKeyNumberingRule:
    """Tests for KeyNumberingRule."""

    @pytest.fixture
    def rule(self) -> KeyNumberingRule:
        """Create a KeyNumberingRule instance."""
        return KeyNumberingRule()

    def test_valid_key_numbering(self, rule: KeyNumberingRule) -> None:
        """Test that valid key numbering passes."""
        rows = [
            {"Ključ preverjanja": "KEY_1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_2", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_3", "Tip podatka": "kemikalija"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        num_errors = [e for e in errors if "KEY_NUM" in e.code]
        assert len(num_errors) == 0

    def test_key_numbering_not_starting_at_one(self, rule: KeyNumberingRule) -> None:
        """Test that key numbering not starting at 1 raises an error."""
        rows = [
            {"Ključ preverjanja": "KEY_2", "Tip podatka": "kemikalija"},  # Starts at 2
            {"Ključ preverjanja": "KEY_3", "Tip podatka": "kemikalija"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_NUM_NE_1" in error_codes

    def test_key_numbering_gap(self, rule: KeyNumberingRule) -> None:
        """Test that gaps in key numbering raise errors."""
        rows = [
            {"Ključ preverjanja": "KEY_1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_2", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_5", "Tip podatka": "kemikalija"},  # Gap: 3, 4 missing
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_NUM_PRESLEDEK" in error_codes

    def test_bare_key_and_numbered_key(self, rule: KeyNumberingRule) -> None:
        """Test that using both bare key and numbered key raises warning."""
        # Need bare key (KEY) plus KEY_1 and KEY_2 to trigger the warning
        # because the rule checks: bare_present[base] and len(numbers) > 1
        rows = [
            {"Ključ preverjanja": "KEY", "Tip podatka": "kemikalija"},  # Bare key (number=0 → treated as 1)
            {"Ključ preverjanja": "KEY_1", "Tip podatka": "kemikalija"},  # KEY_1
            {"Ključ preverjanja": "KEY_2", "Tip podatka": "kemikalija"},  # KEY_2 (now len(numbers) > 1)
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KLJUC_NUM_PODVOJEN_BASE" in error_codes


class TestTehtnicaMasaPairRule:
    """Tests for TehtnicaMasaPairRule."""

    @pytest.fixture
    def rule(self) -> TehtnicaMasaPairRule:
        """Create a TehtnicaMasaPairRule instance."""
        return TehtnicaMasaPairRule()

    def test_tehtnica_with_matching_masa_allows_control(self, rule: TehtnicaMasaPairRule) -> None:
        """If masa with same key exists, kontrolaustreznostiopreme is allowed."""
        rows = [
            {"Tip podatka": "masa", "Ključ preverjanja": "K1", "Vrednost": "5"},
            {"Tip podatka": "tehtnica", "Ključ preverjanja": "K1", "Kontrola-1": "kontrolaUstreznostiOpreme"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "KONTROLA_TEHTNICA_BREZ_MASE"] == []

    def test_tehtnica_without_masa_forbids_control(self, rule: TehtnicaMasaPairRule) -> None:
        """If no masa exists for key, kontrolaustreznostiopreme must not be present."""
        rows = [
            {"Tip podatka": "tehtnica", "Ključ preverjanja": "K1", "Kontrola-1": "kontrolaUstreznostiOpreme"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Kontrola-1"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "KONTROLA_TEHTNICA_BREZ_MASE" in [e.code for e in errors]


class TestTehtnicaVrednostFromFormulaRule:
    """Tests for TehtnicaVrednostFromFormulaRule (numeric masa fallback)."""

    @pytest.fixture
    def rule(self) -> TehtnicaVrednostFromFormulaRule:
        """Create a TehtnicaVrednostFromFormulaRule instance."""
        return TehtnicaVrednostFromFormulaRule()

    def test_masa_high_requires_teh_kla(self, rule: TehtnicaVrednostFromFormulaRule) -> None:
        """When masa >= 10, tehtnica Vrednost must be TEH-KLA."""
        rows = [
            {"Tip podatka": "masa", "Ključ preverjanja": "K1", "Vrednost": "12"},
            {"Tip podatka": "tehtnica", "Ključ preverjanja": "K1", "Vrednost": "TEH-ANA"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "TEHTNICA_VREDNOST_PREVISOKA" in [e.code for e in errors]

    def test_masa_high_allows_teh_kla_and_ana_combo(self, rule: TehtnicaVrednostFromFormulaRule) -> None:
        """When masa >= 10, allowed values are TEH-KLA or 'TEH-KLA, TEH-ANA'."""
        rows = [
            {"Tip podatka": "masa", "Ključ preverjanja": "K1", "Vrednost": "12"},
            {"Tip podatka": "tehtnica", "Ključ preverjanja": "K1", "Vrednost": "TEH-KLA, TEH-ANA"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code.startswith("TEHTNICA_VREDNOST_INVALID_")] == []

    def test_masa_low_allows_teh_ana_variants(self, rule: TehtnicaVrednostFromFormulaRule) -> None:
        """When masa < 10, allowed values are TEH-ANA or 'TEH-KLA, TEH-ANA'."""
        rows = [
            {"Tip podatka": "masa", "Ključ preverjanja": "K1", "Vrednost": "5", "Labela": "g"},
            {"Tip podatka": "tehtnica", "Ključ preverjanja": "K1", "Vrednost": "TEH-KLA"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost", "Labela"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "TEHTNICA_VREDNOST_PRENIZKA" in [e.code for e in errors]

    def test_masa_low_in_kg_does_not_raise_error(self, rule: TehtnicaVrednostFromFormulaRule) -> None:
        """When masa < 10 in kg, low-mass tehtnica restriction should not apply."""
        rows = [
            {"Tip podatka": "masa", "Ključ preverjanja": "K1", "Vrednost": "5", "Labela": "kg"},
            {"Tip podatka": "tehtnica", "Ključ preverjanja": "K1", "Vrednost": "TEH-KLA"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost", "Labela"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "TEHTNICA_VREDNOST_PRENIZKA" not in [e.code for e in errors]

    def test_valid_values_pass(self, rule: TehtnicaVrednostFromFormulaRule) -> None:
        """Valid combinations should pass."""
        rows = [
            {"Tip podatka": "masa", "Ključ preverjanja": "K1", "Vrednost": "12"},
            {"Tip podatka": "tehtnica", "Ključ preverjanja": "K1", "Vrednost": "TEH-KLA"},
            {"Tip podatka": "masa", "Ključ preverjanja": "K2", "Vrednost": "5"},
            {"Tip podatka": "tehtnica", "Ključ preverjanja": "K2", "Vrednost": "TEH-ANA"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code.startswith("TEHTNICA_VREDNOST_INVALID_")] == []

