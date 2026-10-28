"""Tests for field validation rules.

This module tests ObjectTypeRule, DataObjectCompatibilityRule, LabelRequirementsRule,
KeyValidationRule, FormulaSyntaxRule, CommaNumberRule, NoSpacesRule, and FormulaReferenceRule.
"""

from __future__ import annotations

from typing import Any

import pytest

from validator_oop.core.shared_context import SharedContextBuilder
from validator_oop.rules.builtin.field import (
    CheckboxLabelaRule,
    CommaNumberRule,
    CrtaEmptyColumnsRule,
    DataObjectCompatibilityRule,
    FormulaReferenceRule,
    FormulaStepEditLabelaRule,
    FormulaSyntaxRule,
    KeyValidationRule,
    LabelRequirementsRule,
    MasaTipPodatkaRule,
    NaslovEmptyColumnsRule,
    NavodiloRangeDashSpacingRule,
    PosebnostiTipPodatkaRule,
    NoSpacesRule,
    ObjectTypeRule,
    SpustniseznamVrednostRule,
)


class TestObjectTypeRule:
    """Tests for ObjectTypeRule."""

    @pytest.fixture
    def rule(self) -> ObjectTypeRule:
        """Create an ObjectTypeRule instance."""
        return ObjectTypeRule()

    def test_valid_object_type(self, rule: ObjectTypeRule) -> None:
        """Test that valid object types pass validation."""
        rows = [
            {"Tip objekta": "edit", "št. Koraka": "1"},
            {"Tip objekta": "checkbox", "št. Koraka": "2"},
            {"Tip objekta": "naslov", "št. Koraka": "3"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert len(errors) == 0

    def test_empty_object_type(self, rule: ObjectTypeRule) -> None:
        """Test that empty object type raises an error."""
        rows = [
            {"Tip objekta": "", "št. Koraka": "1"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "OBJECT_TYPE_EMPTY" in error_codes

    def test_unknown_object_type(self, rule: ObjectTypeRule) -> None:
        """Test that unknown object type raises an error."""
        rows = [
            {"Tip objekta": "unknown_type", "št. Koraka": "1"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "OBJECT_TYPE_UNKNOWN" in error_codes

    def test_case_insensitive(self, rule: ObjectTypeRule) -> None:
        """Test that object type validation is case-insensitive."""
        rows = [
            {"Tip objekta": "EDIT", "št. Koraka": "1"},
            {"Tip objekta": "CheckBox", "št. Koraka": "2"},
            {"Tip objekta": "NASLOV", "št. Koraka": "3"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert len(errors) == 0


class TestMasaTipPodatkaRule:
    """Tests for MasaTipPodatkaRule."""

    @pytest.fixture
    def rule(self) -> MasaTipPodatkaRule:
        return MasaTipPodatkaRule()

    def test_masa_is_valid(self, rule: MasaTipPodatkaRule) -> None:
        rows = [{"Tip podatka": "masa", "Tip objekta": "edit"}]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert errors == []

    @pytest.mark.parametrize("tip_podatka", ["masa1", "Masa1", "masa_1", "masa 2", "masa.3"])
    def test_numbered_masa_is_invalid(
        self, rule: MasaTipPodatkaRule, tip_podatka: str
    ) -> None:
        rows = [{"Tip podatka": tip_podatka, "Tip objekta": "edit"}]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e.code for e in errors] == ["DATA_TYPE_MASA_INVALID"]
        assert "mora biti 'masa'" in errors[0].message

    @pytest.mark.parametrize("tip_podatka", ["masakonec", "summasa", "volumen", "raztopina"])
    def test_other_types_are_not_flagged(
        self, rule: MasaTipPodatkaRule, tip_podatka: str
    ) -> None:
        rows = [{"Tip podatka": tip_podatka, "Tip objekta": "edit"}]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert errors == []


class TestPosebnostiTipPodatkaRule:
    """Tests for PosebnostiTipPodatkaRule."""

    @pytest.fixture
    def rule(self) -> PosebnostiTipPodatkaRule:
        return PosebnostiTipPodatkaRule()

    def _run(self, rule: PosebnostiTipPodatkaRule, rows: list[dict[str, Any]]) -> list:
        columns = list(rows[0].keys()) if rows else []
        shared = SharedContextBuilder(row_offset=2).build(rows, columns)
        rule.set_shared_context(shared)
        return rule.run(rows, sheet_name="Sheet1", row_offset=2)

    def test_without_zavihek_posebnosti_is_valid(self, rule: PosebnostiTipPodatkaRule) -> None:
        rows = [
            {"Zavihek": "", "Tip podatka": "posebnosti"},
            {"Zavihek": "", "Tip podatka": "kemikalija"},
        ]
        errors = self._run(rule, rows)
        assert errors == []

    def test_without_zavihek_posebnostimon_is_error(self, rule: PosebnostiTipPodatkaRule) -> None:
        rows = [{"Zavihek": "", "Tip podatka": "posebnostimon"}]
        errors = self._run(rule, rows)
        assert [e.code for e in errors] == ["DATA_TYPE_POSEBNOSTI_REQUIRED"]
        assert all(e.column == "Tip podatka" for e in errors)
        assert "posebnosti" in errors[0].message

    def test_monolit_on_other_row_does_not_require_posebnostimon(
        self, rule: PosebnostiTipPodatkaRule
    ) -> None:
        rows = [
            {"Zavihek": "monolit1", "Tip podatka": "naslov"},
            {"Zavihek": "", "Tip podatka": "posebnosti"},
            {"Zavihek": "", "Tip podatka": "masa"},
        ]
        assert self._run(rule, rows) == []

    def test_posebnostimon_on_other_row_than_monolit_is_error(
        self, rule: PosebnostiTipPodatkaRule
    ) -> None:
        rows = [
            {"Zavihek": "monolit1", "Tip podatka": "naslov"},
            {"Zavihek": "", "Tip podatka": "posebnostimon"},
        ]
        errors = self._run(rule, rows)
        assert [e.code for e in errors] == ["DATA_TYPE_POSEBNOSTI_REQUIRED"]
        assert errors[0].row_index == 3

    @pytest.mark.parametrize("zavihek", ["monolit2", "Monolit3", " monolit10 "])
    def test_monolit_code_on_same_row_requires_posebnostimon(
        self, rule: PosebnostiTipPodatkaRule, zavihek: str
    ) -> None:
        rows = [{"Zavihek": zavihek, "Tip podatka": "posebnostimon"}]
        assert self._run(rule, rows) == []

        rows = [{"Zavihek": zavihek, "Tip podatka": "posebnosti"}]
        errors = self._run(rule, rows)
        assert [e.code for e in errors] == ["DATA_TYPE_POSEBNOSTIMON_REQUIRED"]
        assert errors[0].row_index == 2

    @pytest.mark.parametrize(
        "zavihek", ["=B2", "mono lit1", " ", "monolit", "monolit_1", "monolitx", "zavihek1", "abc"]
    )
    def test_other_zavihek_values_require_posebnosti(
        self, rule: PosebnostiTipPodatkaRule, zavihek: str
    ) -> None:
        rows = [{"Zavihek": zavihek, "Tip podatka": "posebnosti"}]
        assert self._run(rule, rows) == []

        rows = [{"Zavihek": zavihek, "Tip podatka": "posebnostimon"}]
        errors = self._run(rule, rows)
        assert [e.code for e in errors] == ["DATA_TYPE_POSEBNOSTI_REQUIRED"]


class TestCrtaEmptyColumnsRule:
    """Tests for CrtaEmptyColumnsRule."""

    @pytest.fixture
    def rule(self) -> CrtaEmptyColumnsRule:
        """Create a CrtaEmptyColumnsRule instance."""
        return CrtaEmptyColumnsRule()

    def test_crta_row_with_empty_columns_passes(self, rule: CrtaEmptyColumnsRule) -> None:
        """Veljavna vrstica crta z praznimi stolpci ne sme sprožiti napake."""
        rows = [
            {
                "št. Koraka": "5",
                "Tip podatka": "crta",
                "Tip objekta": "crta",
                "Navodilo": "",
                "Ključ preverjanja": "",
                "Vrednost": "",
                "Labela": "",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert len(errors) == 0

    def test_crta_row_with_abbreviated_step_column_passes(
        self, rule: CrtaEmptyColumnsRule
    ) -> None:
        """Okrajšava št. Kor. je številka koraka in sme (mora) biti zapolnjena."""
        rows = [
            {
                "št. Kor.": "5",
                "Tip podatka": "crta",
                "Tip objekta": "crta",
                "Navodilo": "",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "CRTA_COLUMN_NOT_EMPTY"] == []
        assert [e for e in errors if e.code == "CRTA_STEP_EMPTY"] == []

    def test_crta_row_with_wrapped_step_column_passes(
        self, rule: CrtaEmptyColumnsRule
    ) -> None:
        """Prelomljena glava št. Kor.\\naka se obravnava kot št. Koraka."""
        rows = [
            {
                "št. Kor.\naka": "5",
                "Tip objekta": "crta",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "CRTA_COLUMN_NOT_EMPTY"] == []
        assert [e for e in errors if e.code == "CRTA_STEP_EMPTY"] == []

    def test_crta_row_without_step_fails(self, rule: CrtaEmptyColumnsRule) -> None:
        """Pri crta mora biti št. Koraka zapolnjen."""
        rows = [
            {
                "št. Koraka": "",
                "Tip podatka": "crta",
                "Tip objekta": "crta",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "CRTA_STEP_EMPTY" for e in errors)

    def test_crta_row_with_zavihek_fails(self, rule: CrtaEmptyColumnsRule) -> None:
        """Zavihek pri tipu objekta crta ne sme vsebovati formule ali druge kode."""
        rows = [
            {
                "Zavihek": "=B42",
                "št. Koraka": "5",
                "Tip podatka": "crta",
                "Tip objekta": "crta",
                "Navodilo": "",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CRTA_COLUMN_NOT_EMPTY" in error_codes
        assert any(e.column == "Zavihek" for e in errors)

    @pytest.mark.parametrize("zavihek", ["monolit1", "monolit2", "Monolit3"])
    def test_crta_row_with_zavihek_monolit_passes(
        self, rule: CrtaEmptyColumnsRule, zavihek: str
    ) -> None:
        """Zavihek sme biti zapolnjen s kodo monolita (monolit1, monolit2, ...)."""
        rows = [
            {
                "Zavihek": zavihek,
                "št. Koraka": "5",
                "Tip podatka": "crta",
                "Tip objekta": "crta",
                "Navodilo": "",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "CRTA_COLUMN_NOT_EMPTY"] == []

    def test_crta_row_with_other_zavihek_fails(self, rule: CrtaEmptyColumnsRule) -> None:
        """Zavihek z vrednostjo, ki ni koda monolita, ni dovoljen."""
        rows = [
            {
                "Zavihek": "Tab1",
                "št. Koraka": "5",
                "Tip podatka": "crta",
                "Tip objekta": "crta",
                "Navodilo": "",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CRTA_COLUMN_NOT_EMPTY" in error_codes
        assert any(e.column == "Zavihek" for e in errors)

    def test_crta_triggered_by_tip_objekta_not_tip_podatka(self, rule: CrtaEmptyColumnsRule) -> None:
        """Pravilo se sproži po Tip objekta, tudi če Tip podatka ni crta."""
        rows = [
            {
                "št. Koraka": "5",
                "Tip podatka": "edit",
                "Tip objekta": "crta",
                "Navodilo": "Ne sme biti",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CRTA_COLUMN_NOT_EMPTY" in error_codes
        assert any(e.column == "Navodilo" for e in errors)

    def test_crta_row_with_navodilo_fails(self, rule: CrtaEmptyColumnsRule) -> None:
        """Navodilo pri tipu objekta crta mora biti prazno."""
        rows = [
            {
                "št. Koraka": "5",
                "Tip podatka": "crta",
                "Tip objekta": "crta",
                "Navodilo": "Ločnik",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CRTA_COLUMN_NOT_EMPTY" in error_codes
        assert any(e.column == "Navodilo" for e in errors)

    def test_crta_row_with_control_fails(self, rule: CrtaEmptyColumnsRule) -> None:
        """Kontrole pri tipu objekta crta morajo biti prazne."""
        rows = [
            {
                "št. Koraka": "5",
                "Tip podatka": "crta",
                "Tip objekta": "crta",
                "Kontrola-1": "kontrolapraznopolje",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "CRTA_COLUMN_NOT_EMPTY" in error_codes

    def test_non_crta_row_not_checked(self, rule: CrtaEmptyColumnsRule) -> None:
        """Pri drugih tipih podatka pravilo ne preverja praznosti stolpcev."""
        rows = [
            {
                "št. Koraka": "1",
                "Tip podatka": "masa",
                "Tip objekta": "edit",
                "Navodilo": "Masa raztopine",
                "Ključ preverjanja": "key1",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert len(errors) == 0


class TestNaslovEmptyColumnsRule:
    """Tests for NaslovEmptyColumnsRule."""

    @pytest.fixture
    def rule(self) -> NaslovEmptyColumnsRule:
        return NaslovEmptyColumnsRule()

    def test_naslov_with_step_and_title_passes(self, rule: NaslovEmptyColumnsRule) -> None:
        rows = [
            {
                "št. Koraka": "1",
                "Navodilo": "Priprava monolita",
                "Tip objekta": "naslov",
                "Tip podatka": "",
                "Ključ preverjanja": "",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "NASLOV_COLUMN_NOT_EMPTY"] == []

    def test_naslov_with_abbreviated_step_column_passes(
        self, rule: NaslovEmptyColumnsRule
    ) -> None:
        """Okrajšava št. Kor. je številka koraka in sme (mora) biti zapolnjena."""
        rows = [
            {
                "št. Kor.": "1",
                "Navodilo": "Priprava monolita",
                "Tip objekta": "naslov",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "NASLOV_COLUMN_NOT_EMPTY"] == []
        assert [e for e in errors if e.code == "NASLOV_STEP_EMPTY"] == []

    def test_naslov_without_step_fails(self, rule: NaslovEmptyColumnsRule) -> None:
        """Pri naslovu mora biti št. Koraka zapolnjen."""
        rows = [
            {
                "št. Koraka": "",
                "Navodilo": "Priprava monolita",
                "Tip objekta": "naslov",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "NASLOV_STEP_EMPTY" for e in errors)

    def test_naslov_without_navodilo_fails(self, rule: NaslovEmptyColumnsRule) -> None:
        """Pri naslovu mora biti Navodilo zapolnjen."""
        rows = [
            {
                "št. Koraka": "1",
                "Navodilo": "",
                "Tip objekta": "naslov",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "NASLOV_NAVODILO_EMPTY" for e in errors)

    def test_naslov_with_extra_column_fails(self, rule: NaslovEmptyColumnsRule) -> None:
        rows = [
            {
                "št. Koraka": "1",
                "Navodilo": "Naslov",
                "Tip objekta": "naslov",
                "Ključ preverjanja": "key1",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "NASLOV_COLUMN_NOT_EMPTY" for e in errors)

    def test_naslov_by_tip_podatka(self, rule: NaslovEmptyColumnsRule) -> None:
        rows = [
            {
                "št. Koraka": "1",
                "Navodilo": "Sekcija",
                "Tip podatka": "naslov",
                "Kontrola 1": "kontrolapraznopolje",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "NASLOV_COLUMN_NOT_EMPTY" for e in errors)

    @pytest.mark.parametrize("zavihek", ["monolit1", "monolit2", "Monolit3"])
    def test_naslov_with_zavihek_monolit_passes(
        self, rule: NaslovEmptyColumnsRule, zavihek: str
    ) -> None:
        """Zavihek sme biti zapolnjen s kodo monolita (monolit1, monolit2, ...)."""
        rows = [
            {
                "Zavihek": zavihek,
                "št. Koraka": "1",
                "Navodilo": "Zavihek za palico",
                "Tip objekta": "naslov",
                "Tip podatka": "",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "NASLOV_COLUMN_NOT_EMPTY"] == []

    def test_naslov_with_other_zavihek_fails(self, rule: NaslovEmptyColumnsRule) -> None:
        """Zavihek z vrednostjo, ki ni koda monolita, ni dovoljen."""
        rows = [
            {
                "Zavihek": "Tab1",
                "št. Koraka": "1",
                "Navodilo": "Naslov",
                "Tip objekta": "naslov",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "NASLOV_COLUMN_NOT_EMPTY" in error_codes
        assert any(e.column == "Zavihek" for e in errors)


class TestSpustniseznamVrednostRule:
    """Tests for SpustniseznamVrednostRule."""

    @pytest.fixture
    def rule(self) -> SpustniseznamVrednostRule:
        """Create a SpustniseznamVrednostRule instance."""
        return SpustniseznamVrednostRule()

    def test_spustniseznam_with_value_passes(self, rule: SpustniseznamVrednostRule) -> None:
        """Spustniseznam z vrednostjo ne sme sprožiti napake."""
        rows = [
            {
                "Tip objekta": "spustniseznam",
                "Vrednost": "HPLC",
                "št. Koraka": "1",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert len(errors) == 0

    def test_spustniseznam_empty_value_fails(self, rule: SpustniseznamVrednostRule) -> None:
        """Spustniseznam brez vrednosti mora sprožiti napako."""
        rows = [
            {
                "Tip objekta": "spustniseznam",
                "Vrednost": "",
                "št. Koraka": "1",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "SPUSTNISEZNAM_VREDNOST_EMPTY" in error_codes

    def test_spustniseznam_whitespace_value_fails(self, rule: SpustniseznamVrednostRule) -> None:
        """Spustniseznam s presledki namesto vrednosti mora sprožiti napako."""
        rows = [
            {
                "Tip objekta": "spustniseznam",
                "Vrednost": "   ",
                "št. Koraka": "1",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "SPUSTNISEZNAM_VREDNOST_EMPTY" in error_codes

    def test_edit_empty_value_allowed(self, rule: SpustniseznamVrednostRule) -> None:
        """Pri tipu edit prazna vrednost ne sproži tega pravila."""
        rows = [
            {
                "Tip objekta": "edit",
                "Vrednost": "",
                "št. Koraka": "1",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert len(errors) == 0

    def test_equipment_spustniseznam_empty_value_fails(
        self, rule: SpustniseznamVrednostRule
    ) -> None:
        """Pri opremi s tipom objekta spustniseznam mora biti stolpec Vrednost zapolnjen."""
        rows = [
            {
                "Tip podatka": "HPLC",
                "Tip objekta": "spustniseznam",
                "Ključ preverjanja": "",
                "Vrednost": "",
                "št. Koraka": "1",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert "SPUSTNISEZNAM_VREDNOST_EMPTY" in [e.code for e in errors]

    def test_equipment_edit_empty_value_allowed(self, rule: SpustniseznamVrednostRule) -> None:
        """Pri opremi s tipom objekta edit prazna Vrednost ni napaka tega pravila."""
        rows = [
            {
                "Tip podatka": "tehtnica",
                "Tip objekta": "edit",
                "Ključ preverjanja": "",
                "Vrednost": "",
                "št. Koraka": "1",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert len(errors) == 0


class TestDataObjectCompatibilityRule:
    """Tests for DataObjectCompatibilityRule."""

    @pytest.fixture
    def rule(self) -> DataObjectCompatibilityRule:
        """Create a DataObjectCompatibilityRule instance."""
        return DataObjectCompatibilityRule()

    def test_valid_combination(self, rule: DataObjectCompatibilityRule) -> None:
        """Test that valid object/data type combinations pass."""
        rows = [
            {"Tip objekta": "edit", "Tip podatka": "kemijski"},
            {"Tip objekta": "edit", "Tip podatka": "raztopine"},
            {"Tip objekta": "checkbox", "Tip podatka": ""},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        obj_mismatch_errors = [e for e in errors if e.code == "OBJECT_TYPE_MISMATCH"]
        assert len(obj_mismatch_errors) == 0

    def test_invalid_combination(self, rule: DataObjectCompatibilityRule) -> None:
        """Test that invalid combinations raise errors."""
        rows = [
            {"Tip objekta": "checkbox", "Tip podatka": "kemikalija"},  # kemikalija requires "edit"
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "OBJECT_TYPE_MISMATCH" in error_codes

    @pytest.mark.parametrize("tip_objekta", ["formula", "formula0", "formula1"])
    def test_masa_disallows_formula_object_types(
        self,
        rule: DataObjectCompatibilityRule,
        tip_objekta: str,
    ) -> None:
        """Tip podatka 'masa' ne sme imeti formulskih tipov objekta."""
        rows = [
            {"Tip objekta": tip_objekta, "Tip podatka": "masa"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        mismatch_errors = [e for e in errors if e.code == "OBJECT_TYPE_MISMATCH"]
        assert len(mismatch_errors) == 1
        assert "ne sme biti 'formula', 'formula0' ali 'formula1'" in mismatch_errors[0].message


class TestLabelRequirementsRule:
    """Tests for LabelRequirementsRule."""

    @pytest.fixture
    def rule(self) -> LabelRequirementsRule:
        """Create a LabelRequirementsRule instance."""
        return LabelRequirementsRule()

    def test_valid_labela_koda(self, rule: LabelRequirementsRule) -> None:
        """Test that kemikalija with Labela='koda' passes."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "kemikalija",  # Requires Labela='koda'
                "Labela": "koda",
                "Navodilo": "Test instruction",
            },
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        labela_errors = [e for e in errors if e.code == "LABEL_MUST_BE_KODA"]
        assert len(labela_errors) == 0

    def test_labela_koda_missing(self, rule: LabelRequirementsRule) -> None:
        """Test that kemikalija without Labela='koda' raises an error."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "kemikalija",  # Requires Labela='koda'
                "Labela": "",  # Missing 'koda'
                "Navodilo": "Test",
            },
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "LABEL_MUST_BE_KODA" in error_codes

    def test_raztopina_requires_koda(self, rule: LabelRequirementsRule) -> None:
        """Raztopina mora imeti Labela='koda'."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "raztopina",
                "Labela": "koda",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_MUST_BE_KODA"] == []

        rows_bad = [{**rows[0], "Labela": "napaka"}]
        errors_bad = rule.run(rows_bad, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "LABEL_MUST_BE_KODA" for e in errors_bad)

    def test_embalaza_requires_koda(self, rule: LabelRequirementsRule) -> None:
        """Embalaža mora imeti Labela='koda'."""
        rows = [
            {"Tip objekta": "edit", "Tip podatka": "embalaza", "Labela": "koda"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_MUST_BE_KODA"] == []

    def test_equipment_requires_naziv_opreme(self, rule: LabelRequirementsRule) -> None:
        """Spustni seznam mora imeti Labela='naziv opreme'."""
        rows = [
            {
                "Tip objekta": "spustniseznam",
                "Tip podatka": "tehtnica",
                "Labela": "naziv opreme",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_MUST_BE_NAZIV_OPREME"] == []

        rows_bad = [{**rows[0], "Labela": "koda"}]
        errors_bad = rule.run(rows_bad, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "LABEL_MUST_BE_NAZIV_OPREME" for e in errors_bad)

    def test_equipment_edit_does_not_require_naziv_opreme(self, rule: LabelRequirementsRule) -> None:
        """Tip opreme z edit ne zahteva Labela='naziv opreme'."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "črpalka",
                "Labela": "mL/min",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_MUST_BE_NAZIV_OPREME"] == []

    def test_hplc_spustniseznam_requires_naziv_opreme(self, rule: LabelRequirementsRule) -> None:
        """Spustni seznam (HPLC) mora imeti Labela='naziv opreme'."""
        rows = [
            {
                "Tip objekta": "spustniseznam",
                "Tip podatka": "HPLC",
                "Labela": "naziv opreme",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_MUST_BE_NAZIV_OPREME"] == []

    def test_datetime_requires_datum_cas(self, rule: LabelRequirementsRule) -> None:
        """izberidatumcas / gumbdatumcas morata imeti Labela='datum/čas'."""
        for tip_obj in ("izberidatumcas", "gumbdatumcas"):
            rows = [
                {
                    "Tip objekta": tip_obj,
                    "Tip podatka": "datumcaskonec",
                    "Labela": "datum/čas",
                },
            ]
            errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
            assert [e for e in errors if e.code == "LABEL_MUST_BE_DATUM_CAS"] == []

        rows_bad = [
            {
                "Tip objekta": "izberidatumcas",
                "Tip podatka": "datumcaskonec",
                "Labela": "datum/cas",
            },
        ]
        errors_bad = rule.run(rows_bad, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "LABEL_MUST_BE_DATUM_CAS" for e in errors_bad)

    def test_datumcas_edit_does_not_require_datum_cas_label(self, rule: LabelRequirementsRule) -> None:
        """Tip podatka datumcas z edit ne zahteva Labela='datum/čas'."""
        rows = [
            {
                "Tip objekta": "edit",
                "Tip podatka": "datumcas",
                "Labela": "koda",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_MUST_BE_DATUM_CAS"] == []

    def test_masa_requires_unit(self, rule: LabelRequirementsRule) -> None:
        """Masa mora imeti enoto v Labeli."""
        rows = [
            {"Tip objekta": "edit", "Tip podatka": "masa", "Labela": "g", "Navodilo": "Masa"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_MUST_BE_UNIT"] == []

        rows_bad = [{**rows[0], "Labela": "koda"}]
        errors_bad = rule.run(rows_bad, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "LABEL_MUST_BE_UNIT" for e in errors_bad)

        rows_empty = [{**rows[0], "Labela": ""}]
        errors_empty = rule.run(rows_empty, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "LABEL_MUST_BE_UNIT" for e in errors_empty)


class TestCheckboxLabelaRule:
    """Tests for CheckboxLabelaRule."""

    @pytest.fixture
    def rule(self) -> CheckboxLabelaRule:
        """Create a CheckboxLabelaRule instance."""
        return CheckboxLabelaRule()

    def test_checkbox_valid_labela_da_kljukica(self, rule: CheckboxLabelaRule) -> None:
        """Checkbox z Labela 'DA (kljukica)' ne sme javiti napake."""
        rows = [
            {"Tip objekta": "checkbox", "Labela": "DA (kljukica)", "št. Koraka": "1"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_CHECKBOX_FORMAT"] == []

    def test_checkbox_valid_labela_da_ne(self, rule: CheckboxLabelaRule) -> None:
        """Checkbox z Labela 'DA (kljukica)/NE (prazno)' ne sme javiti napake."""
        rows = [
            {"Tip objekta": "checkbox", "Labela": "DA (kljukica)/NE (prazno)", "št. Koraka": "1"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_CHECKBOX_FORMAT"] == []

    def test_checkbox_invalid_labela_raises(self, rule: CheckboxLabelaRule) -> None:
        """Checkbox z napačno Labela mora javiti LABELA_CHECKBOX."""
        rows = [
            {"Tip objekta": "checkbox", "Labela": "Nepravilna labela", "št. Koraka": "1"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "LABEL_CHECKBOX_FORMAT" for e in errors)

    def test_checkbox_empty_labela_raises(self, rule: CheckboxLabelaRule) -> None:
        """Checkbox s prazno Labela mora javiti LABELA_CHECKBOX."""
        rows = [
            {"Tip objekta": "checkbox", "Labela": "", "št. Koraka": "1"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "LABEL_CHECKBOX_FORMAT" for e in errors)

    def test_non_checkbox_ignored(self, rule: CheckboxLabelaRule) -> None:
        """Vrstice brez tipa objekta checkbox se ne preverjajo za Labela."""
        rows = [
            {"Tip objekta": "edit", "Labela": "poljubno", "št. Koraka": "1"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "LABEL_CHECKBOX_FORMAT"] == []


class TestKeyValidationRule:
    """Tests for KeyValidationRule."""

    @pytest.fixture
    def rule(self) -> KeyValidationRule:
        """Create a KeyValidationRule instance."""
        return KeyValidationRule()

    def test_valid_key_format(self, rule: KeyValidationRule) -> None:
        """Test that valid key formats pass validation."""
        rows = [
            {"Ključ preverjanja": "VALID_KEY_1", "Tip podatka": "kemijski"},
            {"Ključ preverjanja": "TEST_KEY_123", "Tip podatka": "raztopine"},
            {"Ključ preverjanja": "ABC_DEF_GHI", "Tip podatka": "masa"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        key_format_errors = [e for e in errors if e.code == "KEY_INVALID_FORMAT"]
        assert len(key_format_errors) == 0

    def test_invalid_key_format(self, rule: KeyValidationRule) -> None:
        """Test that invalid key formats raise errors."""
        rows = [
            {"Ključ preverjanja": "invalid#key", "Tip podatka": "kemijski"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KEY_INVALID_FORMAT" in error_codes

    def test_key_edge_space_reports_error(self, rule: KeyValidationRule) -> None:
        """Presledek na začetku ali koncu ključa sproži KEY_INVALID_FORMAT."""
        rows = [
            {"Ključ preverjanja": " KEY_1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "KEY_2 ", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": " KEY_3 ", "Tip podatka": "kemikalija"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        key_errors = [e for e in errors if e.code == "KEY_INVALID_FORMAT"]

        assert len(key_errors) == 3
        assert all("začetku ali koncu" in e.message for e in key_errors)

    def test_key_interior_space_not_key_rule(self, rule: KeyValidationRule) -> None:
        """Presledek v sredini ključa ne sproži KEY_INVALID_FORMAT."""
        rows = [{"Ključ preverjanja": "invalid key", "Tip podatka": "kemikalija"}]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert [e for e in errors if e.code == "KEY_INVALID_FORMAT"] == []

    def test_key_required_for_main_types(self, rule: KeyValidationRule) -> None:
        """Test that keys are required for main data types."""
        rows = [
            {"Ključ preverjanja": "", "Tip podatka": "kemikalija"},  # Missing key for kemikalija
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KEY_REQUIRED" in error_codes

    def test_key_not_required_for_equipment(self, rule: KeyValidationRule) -> None:
        """Oprema ne zahteva ključa preverjanja (pri spustniseznam je obvezna Vrednost)."""
        rows = [
            {"Ključ preverjanja": "teht_1", "Tip podatka": "termometer"},
            {"Ključ preverjanja": "", "Tip podatka": "termometer"},
            {"Ključ preverjanja": "", "Tip podatka": "HPLC", "Tip objekta": "spustniseznam"},
            {"Ključ preverjanja": "", "Tip podatka": "tehtnica", "Tip objekta": "edit"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "KEY_REQUIRED"] == []

    def test_key_required_for_time_pair(self, rule: KeyValidationRule) -> None:
        """Časovni par mora imeti ključ preverjanja."""
        for tip in ("datumcaszacetek", "datumcaskonec"):
            rows = [{"Ključ preverjanja": "", "Tip podatka": tip}]
            errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
            assert any(e.code == "KEY_REQUIRED" for e in errors)

        rows_ok = [{"Ključ preverjanja": "cas_1", "Tip podatka": "datumcaszacetek"}]
        errors_ok = rule.run(rows_ok, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors_ok if e.code == "KEY_REQUIRED"] == []

    def test_key_not_required_for_datumcas(self, rule: KeyValidationRule) -> None:
        """Splošni datumcas brez para ključa ne zahteva ključa."""
        rows = [{"Ključ preverjanja": "", "Tip podatka": "datumcas"}]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "KEY_REQUIRED"] == []

    def test_key_not_required_for_checkbox_with_condition(self, rule: KeyValidationRule) -> None:
        """Checkbox s kontrolo pogoja ne zahteva ključa preverjanja."""
        for kontrola in ("aliobstajapogoj", "aliobstajapogoj_ali", "zaklenipolja"):
            rows = [
                {
                    "Tip podatka": "checkbox",
                    "Tip objekta": "checkbox",
                    "Ključ preverjanja": "",
                    "Kontrola 1": kontrola,
                },
            ]
            errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
            assert [e for e in errors if e.code == "KEY_REQUIRED"] == []

    def test_key_not_required_for_plain_checkbox(self, rule: KeyValidationRule) -> None:
        """Checkbox brez pogoja ne zahteva ključa."""
        rows = [
            {
                "Tip podatka": "checkbox",
                "Tip objekta": "checkbox",
                "Ključ preverjanja": "",
                "Kontrola 1": "aliobkljukan",
            },
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "KEY_REQUIRED"] == []


class TestFormulaSyntaxRule:
    """Tests for FormulaSyntaxRule."""

    @pytest.fixture
    def rule(self) -> FormulaSyntaxRule:
        """Create a FormulaSyntaxRule instance."""
        return FormulaSyntaxRule()

    def test_valid_formula(self, rule: FormulaSyntaxRule) -> None:
        """Test that valid formulas pass validation."""
        rows = [
            {"Tip objekta": "formula", "Vrednost": "=$12+$13"},  # Valid formula with step references
            {"Tip objekta": "formula0", "Vrednost": "=$1*$2"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        formula_errors = [e for e in errors if "FORMULA" in e.code]
        assert len(formula_errors) == 0

    def test_formula_syntax_error(self, rule: FormulaSyntaxRule) -> None:
        """Test that invalid formula syntax raises errors."""
        rows = [
            {"Tip objekta": "formula", "Vrednost": "invalid formula"},  # No = sign
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "FORMULA_SYNTAX" in error_codes

    def test_formula_no_reference(self, rule: FormulaSyntaxRule) -> None:
        """Test that formulas without step references raise errors."""
        rows = [
            {"Tip objekta": "formula", "Vrednost": "=123+456"},  # No $step references
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "FORMULA_NO_REFERENCE" in error_codes

    def test_formula_ampersand_dollar_is_error(self, rule: FormulaSyntaxRule) -> None:
        """Zapis &$ v formuli je napaka (napačen sklic namesto \"$\"&celica)."""
        rows = [
            {"Tip objekta": "formula", "Vrednost": "=$1&$2"},
            {"Tip objekta": "formula0", "Vrednost": '="tekst"&$C12'},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        ampersand_errors = [e for e in errors if e.code == "FORMULA_AMPERSAND_DOLLAR"]
        assert len(ampersand_errors) == 2
        assert all(e.column == "Vrednost" for e in ampersand_errors)

    def test_formula_dollar_then_ampersand_is_allowed(self, rule: FormulaSyntaxRule) -> None:
        """Pravilen sklic \"$\"&C… ne vsebuje '&$' in ni napaka."""
        rows = [
            {"Tip objekta": "formula", "Vrednost": '="=($"&C113&"-"&"$"&C108&")"'},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert [e for e in errors if e.code == "FORMULA_AMPERSAND_DOLLAR"] == []


class TestCommaNumberRule:
    """Tests for CommaNumberRule."""

    @pytest.fixture
    def rule(self) -> CommaNumberRule:
        """Create a CommaNumberRule instance."""
        return CommaNumberRule()

    def test_valid_number_format(self, rule: CommaNumberRule) -> None:
        """Test that valid number formats pass validation."""
        rows = [
            {"Vrednost": "123.45", "Tip podatka": "kemijski"},
            {"Vrednost": "100", "Tip podatka": "kemijski"},
            {"Vrednost": "0.5", "Tip podatka": "kemijski"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        comma_errors = [e for e in errors if e.code == "COMMA_NOT_ALLOWED"]
        assert len(comma_errors) == 0

    def test_comma_in_number(self, rule: CommaNumberRule) -> None:
        """Test that comma decimal separators raise errors."""
        rows = [
            {"Vrednost": "123,45", "Tip podatka": "kemijski"},  # Comma instead of dot
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "COMMA_NOT_ALLOWED" in error_codes


class TestNavodiloRangeDashSpacingRule:
    """Tests for NavodiloRangeDashSpacingRule."""

    @pytest.fixture
    def rule(self) -> NavodiloRangeDashSpacingRule:
        return NavodiloRangeDashSpacingRule()

    @staticmethod
    def _codes(rule: NavodiloRangeDashSpacingRule, navodilo: object) -> list[str]:
        rows = [{"Navodilo": navodilo, "Tip objekta": "edit", "št. Koraka": "1"}]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        return [e.code for e in errors]

    @pytest.mark.parametrize(
        "navodilo",
        [
            "Pretok 4000 – 4400 mL/min",
            "Pretok 4000 - 4400 mL/min",
            "Temperatura 20 – 25 °C (pH 6.5 – 7.0)",
            "Mešaj 4000 – 4400",
            "Brez razpona",
            "CAS 7647-14-5",
            "Datum 2026-01-01",
            "Oznaka SOP-123",
            "Korak A–B",
            "Priprava – glej navodilo",
            "",
            None,
        ],
    )
    def test_valid(self, rule: NavodiloRangeDashSpacingRule, navodilo: object) -> None:
        assert self._codes(rule, navodilo) == []

    @pytest.mark.parametrize(
        "navodilo",
        [
            "Pretok 4000–4400 mL/min",
            "Pretok 4000 –4400 mL/min",
            "Pretok 4000– 4400 mL/min",
            "Pretok 4000  –  4400 mL/min",
            "Pretok 4000—4400",
            "Pretok 4000-4400 mL/min",
            "Pretok 4000 -4400 mL/min",
            "Pretok 4000- 4400 mL/min",
            "pH 6.5–7.0",
            "Masa 4000g–4400g",
            "Temperatura 20-25 °C",
        ],
    )
    def test_invalid(self, rule: NavodiloRangeDashSpacingRule, navodilo: object) -> None:
        assert self._codes(rule, navodilo) == ["NAVODILO_RANGE_DASH_SPACING"]

    def test_single_error_per_cell_names_all_ranges(
        self, rule: NavodiloRangeDashSpacingRule
    ) -> None:
        rows = [{"Navodilo": "1–2 in 30-40", "Tip objekta": "edit"}]
        errors = list(rule.run(rows, sheet_name="Sheet1", row_offset=2))
        assert len(errors) == 1
        assert "1–2" in errors[0].message and "30-40" in errors[0].message
        assert errors[0].column == "Navodilo"


class TestNoSpacesRule:
    """Tests for NoSpacesRule."""

    @pytest.fixture
    def rule(self) -> NoSpacesRule:
        """Create a NoSpacesRule instance."""
        return NoSpacesRule()

    def test_no_spaces_valid(self, rule: NoSpacesRule) -> None:
        """Vrednosti brez presledkov ne sprožijo napake."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Opis koraka", "Vrednost": "123", "Labela": "g"},
            {"št. Koraka": "2", "Navodilo": "Drugi korak", "Vrednost": "abc", "Labela": "koda"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        assert len(space_errors) == 0

    def test_space_in_column_reports_error(self, rule: NoSpacesRule) -> None:
        """Presledek v vmesnosti (razen izjemnih stolpcev) sproži napako."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Korak", "Tip objekta": "edit x", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "SPACE_NOT_ALLOWED" in error_codes
        err = next(e for e in errors if e.code == "SPACE_NOT_ALLOWED")
        assert err.column == "Tip objekta"

    def test_space_in_zavihek_points_to_zavihek(self, rule: NoSpacesRule) -> None:
        """Presledek v Zavihek javi napako v tem stolpcu, ne pri zaklenipolja."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Korak", "Zavihek": "Tab 1", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        assert len(space_errors) == 1
        assert space_errors[0].column == "Zavihek"
        assert "Zavihek" in space_errors[0].message
        assert "ne odpira novega zavihka" in space_errors[0].message

    def test_vrednost_with_spaces_no_error(self, rule: NoSpacesRule) -> None:
        """Stolpec Vrednost se ne preverja za presledke."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Korak", "Vrednost": "vrednost s presledkom", "Labela": "g"},
            {"št. Koraka": "2", "Navodilo": "Korak", "Vrednost": " 10 g ", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        assert len(space_errors) == 0

    def test_navodilo_with_spaces_no_error(self, rule: NoSpacesRule) -> None:
        """Stolpec Navodilo sme vsebovati presledke."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Navodilo z več presledki in besedami", "Vrednost": "1", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        assert len(space_errors) == 0

    def test_leading_trailing_space_no_error(self, rule: NoSpacesRule) -> None:
        """Robni presledki v vrednosti ne sprožijo SPACE_NOT_ALLOWED (preveri se vmesnost)."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Korak", "Vrednost": " 123", "Labela": "g"},
            {"št. Koraka": "2", "Navodilo": "Korak", "Vrednost": "456 ", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        assert len(space_errors) == 0

    def test_empty_cells_no_error(self, rule: NoSpacesRule) -> None:
        """Prazne celice ne sprožijo napake."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Korak", "Vrednost": "", "Labela": ""},
            {"št. Koraka": "2", "Navodilo": "", "Vrednost": "x", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        assert len(space_errors) == 0

    def test_multiple_columns_with_spaces(self, rule: NoSpacesRule) -> None:
        """Presledek v vmesnosti v več stolpcih vrne napako za vsak tak stolpec."""
        rows = [
            {"št. Koraka": "1 2", "Navodilo": "Korak", "Vrednost": "a b", "Tip objekta": "x y", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        columns_with_errors = {e.column for e in space_errors}
        assert "št. Koraka" in columns_with_errors
        assert "Tip objekta" in columns_with_errors
        assert "Vrednost" not in columns_with_errors
        assert "Navodilo" not in columns_with_errors

    def test_kljuc_presledek_only_key_validation(self, rule: NoSpacesRule) -> None:
        """Ključ preverjanja: presledek (robni ali v vmesnosti) ne sproži SPACE_NOT_ALLOWED."""
        rows = [
            {"Ključ preverjanja": " KEY_1", "Vrednost": "1", "Tip podatka": "kemikalija"},
            {"Ključ preverjanja": "pretok mf1", "Vrednost": "1", "Tip podatka": "kemikalija"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert [e for e in errors if e.code == "SPACE_NOT_ALLOWED"] == []

    def test_labela_with_spaces_no_error(self, rule: NoSpacesRule) -> None:
        """Stolpec Labela se ne preverja za presledke (poljubna vrednost s presledki je dovoljena)."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Korak", "Labela": "DA (kljukica)"},
            {"št. Koraka": "2", "Navodilo": "Korak", "Labela": "DA (kljukica)/NE (prazno)"},
            {"št. Koraka": "3", "Navodilo": "Korak", "Labela": "naziv opreme"},
            {"št. Koraka": "4", "Navodilo": "Korak", "Labela": "nekaj z presledkom"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        assert len(space_errors) == 0


class TestFormulaReferenceRule:
    """Tests for FormulaReferenceRule."""

    @pytest.fixture
    def rule(self) -> FormulaReferenceRule:
        """Create a FormulaReferenceRule instance."""
        return FormulaReferenceRule()

    def test_valid_formula_references(self, rule: FormulaReferenceRule) -> None:
        """Test that formulas with valid step references pass."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit"},
            {"št. Koraka": "2", "Tip objekta": "edit"},
            {"št. Koraka": "3", "Tip objekta": "formula", "Vrednost": "=$1+$2"},  # References existing steps
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        bad_ref_errors = [e for e in errors if e.code == "FORMULA_INVALID_REFERENCE"]
        assert len(bad_ref_errors) == 0

    def test_formula_bad_reference(self, rule: FormulaReferenceRule) -> None:
        """Test that formulas with invalid step references raise errors."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit"},
            {"št. Koraka": "2", "Tip objekta": "formula", "Vrednost": "=$1+$99"},  # $99 doesn't exist
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "FORMULA_INVALID_REFERENCE" in error_codes


class TestFormulaStepEditLabelaRule:
    """Tests for FormulaStepEditLabelaRule."""

    @pytest.fixture
    def rule(self) -> FormulaStepEditLabelaRule:
        """Create a FormulaStepEditLabelaRule instance."""
        return FormulaStepEditLabelaRule()

    def test_formula_references_steps_with_edit(self, rule: FormulaStepEditLabelaRule) -> None:
        """When referenced steps have Tip objekta 'edit', no error."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit"},
            {"št. Koraka": "2", "Tip objekta": "edit"},
            {"št. Koraka": "3", "Tip objekta": "formula", "Vrednost": "=$1+$2"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        step_errors = [e for e in errors if e.code == "FORMULA_STEP_INVALID_TYPE"]
        assert len(step_errors) == 0

    def test_formula_references_allowed_formula_types(self, rule: FormulaStepEditLabelaRule) -> None:
        """When referenced steps are formula types, no error is reported."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "formula"},
            {"št. Koraka": "2", "Tip objekta": "formula0"},
            {"št. Koraka": "3", "Tip objekta": "formula1"},
            {"št. Koraka": "4", "Tip objekta": "formula", "Vrednost": "=$1+$2+$3"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        step_errors = [e for e in errors if e.code == "FORMULA_STEP_INVALID_TYPE"]
        assert len(step_errors) == 0

    def test_formula_references_klictehtnice1(self, rule: FormulaStepEditLabelaRule) -> None:
        """When a referenced step has Tip objekta klictehtnice1, no error is reported."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "klictehtnice1", "Tip podatka": "masa"},
            {"št. Koraka": "2", "Tip objekta": "formula", "Vrednost": "=$1"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Tip podatka", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        step_errors = [e for e in errors if e.code == "FORMULA_STEP_INVALID_TYPE"]
        assert len(step_errors) == 0

    def test_formula_references_step_without_allowed_type(self, rule: FormulaStepEditLabelaRule) -> None:
        """When a referenced step has no allowed object type, error is reported."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit"},
            {"št. Koraka": "2", "Tip objekta": "checkbox"},  # no edit at step 2
            {"št. Koraka": "3", "Tip objekta": "formula", "Vrednost": "=$1+$2"},
        ]
        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Vrednost"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        step_errors = [e for e in errors if e.code == "FORMULA_STEP_INVALID_TYPE"]
        assert len(step_errors) >= 1
        assert any("$2" in e.message for e in step_errors)

