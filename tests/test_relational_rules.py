"""Tests for relational validation rules.

This module tests DuplicateKeyRule, MassOwnerRule, TimePairRule, and KeyNumberingRule.
"""

from __future__ import annotations

from typing import Any

import pytest

from validator_oop.core.error import Severity
from validator_oop.core.shared_context import SharedContextBuilder
from validator_oop.rules.builtin.relational import (
    DuplicateKeyRule,
    KeyNumberingRule,
    MassOwnerRule,
    OwnerMassPairRule,
    ReproKolicinaOwnerRule,
    TehtnicaMasaPairRule,
    TehtnicaVrednostFromFormulaRule,
    TimeOrderRule,
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
        assert "KEY_DUP_CHEM" in error_codes

    def test_duplicate_kemikalija_key_grouped_across_tabs(self, rule: DuplicateKeyRule) -> None:
        """Isti podvojen ključ v več zavihkih je ena napaka, ki našteje zavihke."""
        rows = [
            {"Zavihek": "monolit1", "Ključ preverjanja": "EtOH1", "Tip podatka": "kemikalija"},
            {"Zavihek": "monolit1", "Ključ preverjanja": "EtOH1", "Tip podatka": "kemikalija"},
            {"Zavihek": "monolit2", "Ključ preverjanja": "EtOH1", "Tip podatka": "kemikalija"},
            {"Zavihek": "monolit2", "Ključ preverjanja": "EtOH1", "Tip podatka": "kemikalija"},
            {"Zavihek": "monolit3", "Ključ preverjanja": "razt_5", "Tip podatka": "raztopina"},
            {"Zavihek": "monolit3", "Ključ preverjanja": "razt_5", "Tip podatka": "raztopina"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        chem = [e for e in errors if e.code == "KEY_DUP_CHEM"]
        sol = [e for e in errors if e.code == "KEY_DUP_SOL"]
        assert len(chem) == 1
        assert "v zavihkih 'monolit1', 'monolit2'" in chem[0].message
        assert len(sol) == 1
        assert "v zavihku 'monolit3'" in sol[0].message

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
        assert "KEY_DUP_SOL" in error_codes

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
        assert "KEY_DUP_MASS" in error_codes

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
        assert "KEY_DUP_MASS" not in error_codes

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
        assert "KEY_DUP_MASS_SECTION" in error_codes

    def test_masa_same_key_in_sections_grouped_across_tabs(self, rule: DuplicateKeyRule) -> None:
        """Isti ključ mase v več razdelkih na več zavihkih je ena napaka."""
        rows = [
            {"Zavihek": "monolit1", "Tip objekta": "naslov", "Tip podatka": "", "Ključ preverjanja": ""},
            {"Zavihek": "", "Tip objekta": "", "Tip podatka": "masa", "Ključ preverjanja": "razt_8"},
            {"Zavihek": "", "Tip objekta": "naslov", "Tip podatka": "", "Ključ preverjanja": ""},
            {"Zavihek": "", "Tip objekta": "", "Tip podatka": "masa", "Ključ preverjanja": "razt_8"},
            {"Zavihek": "monolit2", "Tip objekta": "naslov", "Tip podatka": "", "Ključ preverjanja": ""},
            {"Zavihek": "", "Tip objekta": "", "Tip podatka": "masa", "Ključ preverjanja": "razt_8"},
            {"Zavihek": "", "Tip objekta": "naslov", "Tip podatka": "", "Ključ preverjanja": ""},
            {"Zavihek": "", "Tip objekta": "", "Tip podatka": "masa", "Ključ preverjanja": "razt_8"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "Tip objekta", "Tip podatka", "Ključ preverjanja"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        section_errors = [e for e in errors if e.code == "KEY_DUP_MASS_SECTION"]
        assert len(section_errors) == 1
        assert "v zavihkih 'monolit1', 'monolit2'" in section_errors[0].message

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
        assert "KEY_DUP_MASS_SECTION" not in error_codes
        assert "KEY_DUP_MASS" not in error_codes

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
        assert "KEY_DUP_TIME_START" not in error_codes
        assert "KEY_DUP_TIME_END" not in error_codes


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

        no_owner_errors = [e for e in errors if e.code == "PAIR_MASS_WITHOUT_OWNER"]
        assert len(no_owner_errors) == 0

    def test_masa_with_monomerna_owner(self, rule: MassOwnerRule) -> None:
        """Masa with monomerna (or numbered variant) as owner passes."""
        for owner_tip in ("monomerna", "monomerna1"):
            rows = [
                {"Ključ preverjanja": "SMM1", "Tip podatka": owner_tip},
                {"Ključ preverjanja": "SMM1", "Tip podatka": "masa"},
            ]
            builder = SharedContextBuilder(row_offset=2)
            columns = ["Ključ preverjanja", "Tip podatka"]
            ctx = builder.build(rows, columns)
            rule.set_shared_context(ctx)
            errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
            no_owner_errors = [e for e in errors if e.code == "PAIR_MASS_WITHOUT_OWNER"]
            assert len(no_owner_errors) == 0, owner_tip

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
        assert "PAIR_MASS_WITHOUT_OWNER" in error_codes

    def test_razt_numbered_keys_are_compared_in_full(self, rule: MassOwnerRule) -> None:
        """razt6 and razt7 stay distinct; a later razt7 must not claim the razt6 mass."""
        rows = [
            {"Ključ preverjanja": "razt6", "Tip podatka": "raztopina"},
            {"Ključ preverjanja": "razt7", "Tip podatka": "raztopina"},
            {"Ključ preverjanja": "razt7", "Tip podatka": "masa"},
            {"Ključ preverjanja": "razt6", "Tip podatka": "masa"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        codes = [e.code for e in errors]
        assert "PAIR_MASS_SECTION_MISMATCH" not in codes
        assert "PAIR_MASS_WITHOUT_OWNER" not in codes

    def test_other_keys_still_match_on_base_without_trailing_number(
        self, rule: MassOwnerRule
    ) -> None:
        """EtOH1 / EtOH2 still share a base, so the mass must copy the nearest owner key."""
        rows = [
            {"Ključ preverjanja": "EtOH1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "EtOH2", "Tip podatka": "masa"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        mismatch = [e for e in errors if e.code == "PAIR_MASS_SECTION_MISMATCH"]
        assert len(mismatch) == 1
        assert "EtOH1" in mismatch[0].message


class TestOwnerMassPairRule:
    """Tests for OwnerMassPairRule."""

    @pytest.fixture
    def rule(self) -> OwnerMassPairRule:
        return OwnerMassPairRule()

    def _run(self, rule: OwnerMassPairRule, rows: list[dict[str, Any]]):
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        return rule.run(rows, sheet_name="Sheet1", row_offset=2)

    def test_kemikalija_with_masa_passes(self, rule: OwnerMassPairRule) -> None:
        rows = [
            {"Ključ preverjanja": "NaCl1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "NaCl1", "Tip podatka": "masa"},
        ]
        assert [e.code for e in self._run(rule, rows)] == []

    def test_raztopina_with_masa_passes(self, rule: OwnerMassPairRule) -> None:
        rows = [
            {"Ključ preverjanja": "raz1", "Tip podatka": "raztopina"},
            {"Ključ preverjanja": "raz1", "Tip podatka": "masa"},
        ]
        assert [e.code for e in self._run(rule, rows)] == []

    def test_kemikalija_without_masa_raises(self, rule: OwnerMassPairRule) -> None:
        rows = [{"Ključ preverjanja": "NaCl1", "Tip podatka": "kemikalija"}]
        errors = self._run(rule, rows)
        assert "PAIR_CHEM_WITHOUT_MASS" in [e.code for e in errors]

    def test_raztopina_without_masa_raises(self, rule: OwnerMassPairRule) -> None:
        rows = [{"Ključ preverjanja": "raz1", "Tip podatka": "raztopina"}]
        errors = self._run(rule, rows)
        assert "PAIR_SOL_WITHOUT_MASS" in [e.code for e in errors]

    def test_raztopina_with_volumen_instead_of_masa_raises(self, rule: OwnerMassPairRule) -> None:
        rows = [
            {"Ključ preverjanja": "raz1", "Tip podatka": "raztopina"},
            {"Ključ preverjanja": "raz1", "Tip podatka": "volumen"},
        ]
        codes = [e.code for e in self._run(rule, rows)]
        assert "PAIR_SOL_WITHOUT_MASS" in codes
        assert "PAIR_VOLUME_NOT_ALLOWED" in codes

    def test_volumen_same_key_forbidden_even_if_masa_exists(
        self, rule: OwnerMassPairRule
    ) -> None:
        rows = [
            {"Ključ preverjanja": "raz1", "Tip podatka": "raztopina"},
            {"Ključ preverjanja": "raz1", "Tip podatka": "masa"},
            {"Ključ preverjanja": "raz1", "Tip podatka": "volumen"},
        ]
        codes = [e.code for e in self._run(rule, rows)]
        assert "PAIR_VOLUME_NOT_ALLOWED" in codes
        assert "PAIR_SOL_WITHOUT_MASS" not in codes

    def test_standalone_volumen_other_key_allowed(self, rule: OwnerMassPairRule) -> None:
        rows = [
            {"Ključ preverjanja": "raz1", "Tip podatka": "raztopina"},
            {"Ključ preverjanja": "raz1", "Tip podatka": "masa"},
            {"Ključ preverjanja": "padec_tlaka", "Tip podatka": "volumen"},
        ]
        assert [e.code for e in self._run(rule, rows)] == []

    def test_dh2o_volumen_with_raztopina_allowed(self, rule: OwnerMassPairRule) -> None:
        rows = [
            {"Ključ preverjanja": "dH2O_1", "Tip podatka": "raztopina"},
            {"Ključ preverjanja": "dH2O_1", "Tip podatka": "volumen"},
        ]
        codes = [e.code for e in self._run(rule, rows)]
        assert "PAIR_VOLUME_NOT_ALLOWED" not in codes
        assert "PAIR_SOL_WITHOUT_MASS" not in codes
        assert "PAIR_WATER_WITHOUT_VOLUME" not in codes

    def test_dh2o_standalone_volumen_allowed(self, rule: OwnerMassPairRule) -> None:
        rows = [{"Ključ preverjanja": "dH2O", "Tip podatka": "volumen"}]
        assert [e.code for e in self._run(rule, rows)] == []

    def test_dh2o_raztopina_without_volumen_raises(self, rule: OwnerMassPairRule) -> None:
        rows = [{"Ključ preverjanja": "dH2O_1", "Tip podatka": "raztopina"}]
        errors = self._run(rule, rows)
        assert "PAIR_WATER_WITHOUT_VOLUME" in [e.code for e in errors]
        assert "PAIR_SOL_WITHOUT_MASS" not in [e.code for e in errors]

    def test_masa_on_other_tab_is_not_pair(self, rule: OwnerMassPairRule) -> None:
        rows = [
            {"Ključ preverjanja": "raz1", "Tip podatka": "raztopina", "Zavihek": "A"},
            {"Ključ preverjanja": "raz1", "Tip podatka": "masa", "Zavihek": "B"},
        ]
        errors = self._run(rule, rows)
        assert "PAIR_SOL_WITHOUT_MASS" in [e.code for e in errors]


class TestReproKolicinaOwnerRule:
    """Tests for ReproKolicinaOwnerRule."""

    @pytest.fixture
    def rule(self) -> ReproKolicinaOwnerRule:
        return ReproKolicinaOwnerRule()

    def _run(self, rule: ReproKolicinaOwnerRule, rows: list[dict[str, Any]]):
        builder = SharedContextBuilder(row_offset=2)
        ctx = builder.build(rows, ["Ključ preverjanja", "Tip podatka"])
        rule.set_shared_context(ctx)
        return rule.run(rows, sheet_name="Sheet1", row_offset=2)

    def test_kolicina_with_matching_repro_passes(self, rule: ReproKolicinaOwnerRule) -> None:
        rows = [
            {"Ključ preverjanja": "telo_samec_V4", "Tip podatka": "repro"},
            {"Ključ preverjanja": "telo_samec_V4", "Tip podatka": "kolicina"},
        ]
        errors = self._run(rule, rows)
        assert [e.code for e in errors] == []

    def test_two_kolicina_rows_after_repro_pass(self, rule: ReproKolicinaOwnerRule) -> None:
        rows = [
            {"Ključ preverjanja": "oring", "Tip podatka": "repro"},
            {"Ključ preverjanja": "oring", "Tip podatka": "kolicina"},
            {"Ključ preverjanja": "oring", "Tip podatka": "kolicina"},
        ]
        errors = self._run(rule, rows)
        assert [e.code for e in errors] == []

    def test_kolicina_key_mismatch_raises_error(self, rule: ReproKolicinaOwnerRule) -> None:
        rows = [
            {"Ključ preverjanja": "telo_samec_V4", "Tip podatka": "repro"},
            {"Ključ preverjanja": "telo_V4", "Tip podatka": "kolicina"},
        ]
        errors = self._run(rule, rows)
        mismatch = [e for e in errors if e.code == "PAIR_KOLICINA_KEY_MISMATCH"]
        assert len(mismatch) == 1
        assert "telo_samec_V4" in mismatch[0].message

    def test_kolicina_without_repro_raises_error(self, rule: ReproKolicinaOwnerRule) -> None:
        rows = [
            {"Ključ preverjanja": "telo_V4", "Tip podatka": "kolicina"},
        ]
        errors = self._run(rule, rows)
        assert "PAIR_KOLICINA_WITHOUT_OWNER" in [e.code for e in errors]

    def test_empty_kolicina_key_with_repro_raises_mismatch(
        self, rule: ReproKolicinaOwnerRule
    ) -> None:
        rows = [
            {"Ključ preverjanja": "frita_V4", "Tip podatka": "repro"},
            {"Ključ preverjanja": "", "Tip podatka": "kolicina"},
        ]
        errors = self._run(rule, rows)
        assert "PAIR_KOLICINA_KEY_MISMATCH" in [e.code for e in errors]

    def test_repro_on_other_tab_is_not_owner(self, rule: ReproKolicinaOwnerRule) -> None:
        rows = [
            {"Ključ preverjanja": "oring", "Tip podatka": "repro", "Zavihek": "A"},
            {"Ključ preverjanja": "oring", "Tip podatka": "kolicina", "Zavihek": "B"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        ctx = builder.build(rows, ["Ključ preverjanja", "Tip podatka", "Zavihek"])
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "PAIR_KOLICINA_WITHOUT_OWNER" in [e.code for e in errors]

    def test_paketni_monolit_with_kolicina_paketnimonolit_passes(
        self, rule: ReproKolicinaOwnerRule
    ) -> None:
        rows = [
            {"Ključ preverjanja": "paketni", "Tip podatka": "monolit"},
            {"Ključ preverjanja": "paketnimonolit", "Tip podatka": "kolicina"},
        ]
        errors = self._run(rule, rows)
        assert [e.code for e in errors] == []

    def test_kolicina_paketnimonolit_without_paketni_monolit_raises_error(
        self, rule: ReproKolicinaOwnerRule
    ) -> None:
        rows = [
            {"Ključ preverjanja": "drugi", "Tip podatka": "monolit"},
            {"Ključ preverjanja": "paketnimonolit", "Tip podatka": "kolicina"},
        ]
        errors = self._run(rule, rows)
        assert "PAIR_KOLICINA_WITHOUT_OWNER" in [e.code for e in errors]


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

        time_errors = [e for e in errors if "PAIR_TIME" in e.code]
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
        assert "PAIR_TIME_WITHOUT_END" in error_codes

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
        assert "PAIR_TIME_WITHOUT_START" in error_codes

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
        assert "KEY_DUP_TIME_PAIR" in error_codes

    def test_duplicate_time_key_grouped_across_tabs(self, rule: TimePairRule) -> None:
        """Isti ponovljen časovni ključ v več zavihkih je ena napaka."""
        rows = [
            {"Zavihek": "monolit1", "Ključ preverjanja": "crpanje", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "crpanje", "Tip podatka": "datumcaskonec"},
            {"Zavihek": "monolit4", "Ključ preverjanja": "crpanje_3", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "crpanje_3", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "monolit7", "Ključ preverjanja": "crpanje_3", "Tip podatka": "datumcaszacetek"},
            {"Zavihek": "", "Ključ preverjanja": "crpanje_3", "Tip podatka": "datumcaszacetek"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Zavihek", "Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        dup = [e for e in errors if e.code == "KEY_DUP_TIME_PAIR"]
        assert len(dup) == 1
        assert "v zavihkih 'monolit4', 'monolit7'" in dup[0].message
        assert "monolit1" not in dup[0].message

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
        assert "KEY_DUP_TIME_PAIR" in error_codes
        assert "PAIR_TIME_WITHOUT_END" in error_codes

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
        assert "KEY_DUP_TIME_PAIR" not in error_codes
        assert "PAIR_TIME_WITHOUT_END" not in error_codes
        assert "PAIR_TIME_WITHOUT_START" not in error_codes

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
        assert "KEY_DUP_TIME_PAIR" not in error_codes


class TestTimeOrderRule:
    """Tests for TimeOrderRule."""

    @pytest.fixture
    def rule(self) -> TimeOrderRule:
        return TimeOrderRule()

    def test_start_before_end_passes(self, rule: TimeOrderRule) -> None:
        rows = [
            {"Ključ preverjanja": "T1", "Tip podatka": "datumcaszacetek", "št. Koraka": "10"},
            {"Ključ preverjanja": "T1", "Tip podatka": "datumcaskonec", "št. Koraka": "20"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka", "št. Koraka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "PAIR_TIME_ORDER"] == []

    def test_start_after_end_warns(self, rule: TimeOrderRule) -> None:
        rows = [
            {"Ključ preverjanja": "T1", "Tip podatka": "datumcaszacetek", "št. Koraka": "30"},
            {"Ključ preverjanja": "T1", "Tip podatka": "datumcaskonec", "št. Koraka": "20"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka", "št. Koraka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        order_errors = [e for e in errors if e.code == "PAIR_TIME_ORDER"]
        assert len(order_errors) == 1
        assert order_errors[0].severity == Severity.WARNING

    def test_equal_steps_warns(self, rule: TimeOrderRule) -> None:
        rows = [
            {"Ključ preverjanja": "T1", "Tip podatka": "datumcaszacetek", "št. Koraka": "15"},
            {"Ključ preverjanja": "T1", "Tip podatka": "datumcaskonec", "št. Koraka": "15"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka", "št. Koraka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "PAIR_TIME_ORDER" for e in errors)


class TestKeyNumberingRule:
    """Tests for KeyNumberingRule."""

    @pytest.fixture
    def rule(self) -> KeyNumberingRule:
        """Create a KeyNumberingRule instance."""
        return KeyNumberingRule()

    def test_chemical_key_without_underscore_suffix_no_numbering_error(
        self, rule: KeyNumberingRule
    ) -> None:
        """Ključi brez pripone _N (npr. H2SO4) ne sprožijo oštevilčenja."""
        rows = [
            {"Ključ preverjanja": "H2SO4", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "NaCl", "Tip podatka": "raztopina"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Ključ preverjanja", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        num_errors = [e for e in errors if e.code.startswith("KEY_NUM")]
        assert len(num_errors) == 0

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
        assert "KEY_NUM_NOT_FROM_ONE" in error_codes

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
        assert "KEY_NUM_GAP" in error_codes

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
        assert "KEY_NUM_DUPLICATE_BASE" in error_codes


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
        assert [e for e in errors if e.code == "CONTROL_SCALE_WITHOUT_MASS"] == []

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
        assert "CONTROL_SCALE_WITHOUT_MASS" in [e.code for e in errors]


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
        assert "SCALE_VALUE_TOO_HIGH" in [e.code for e in errors]

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
        assert "SCALE_VALUE_TOO_LOW" in [e.code for e in errors]

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
        assert "SCALE_VALUE_TOO_LOW" not in [e.code for e in errors]

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

