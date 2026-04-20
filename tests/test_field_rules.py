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
    DataObjectCompatibilityRule,
    FormulaReferenceRule,
    FormulaStepEditLabelaRule,
    FormulaSyntaxRule,
    KeyValidationRule,
    LabelRequirementsRule,
    NoSpacesRule,
    ObjectTypeRule,
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
            {"Ključ preverjanja": "invalid key", "Tip podatka": "kemijski"},  # spaces
            {"Ključ preverjanja": "123_STARTS_WITH_NUMBER", "Tip podatka": "kemijski"},  # starts with number
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KEY_INVALID_FORMAT" in error_codes

    def test_key_required_for_main_types(self, rule: KeyValidationRule) -> None:
        """Test that keys are required for main data types."""
        rows = [
            {"Ključ preverjanja": "", "Tip podatka": "kemikalija"},  # Missing key for kemikalija
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KEY_REQUIRED" in error_codes


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
        """Presledek v stolpcu (razen Navodilo) sproži napako."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Korak", "Vrednost": "vrednost s presledkom", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        error_codes = [e.code for e in errors]
        assert "SPACE_NOT_ALLOWED" in error_codes
        err = next(e for e in errors if e.code == "SPACE_NOT_ALLOWED")
        assert err.column == "Vrednost"

    def test_navodilo_with_spaces_no_error(self, rule: NoSpacesRule) -> None:
        """Stolpec Navodilo sme vsebovati presledke."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Navodilo z več presledki in besedami", "Vrednost": "1", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        assert len(space_errors) == 0

    def test_leading_trailing_space_reports_error(self, rule: NoSpacesRule) -> None:
        """Začetni ali končni presledek v vrednosti sproži napako."""
        rows = [
            {"št. Koraka": "1", "Navodilo": "Korak", "Vrednost": " 123", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "SPACE_NOT_ALLOWED" and e.column == "Vrednost" for e in errors)
        rows_trailing = [
            {"št. Koraka": "2", "Navodilo": "Korak", "Vrednost": "456 ", "Labela": "g"},
        ]
        errors_trailing = rule.run(rows_trailing, sheet_name="Sheet1", row_offset=2)
        assert any(e.code == "SPACE_NOT_ALLOWED" and e.column == "Vrednost" for e in errors_trailing)

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
        """Več stolpcev s presledki vrne napako za vsak tak stolpec."""
        rows = [
            {"št. Koraka": "1 ", "Navodilo": "Korak", "Vrednost": "a b", "Labela": "g"},
        ]
        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)
        space_errors = [e for e in errors if e.code == "SPACE_NOT_ALLOWED"]
        columns_with_errors = {e.column for e in space_errors}
        assert "št. Koraka" in columns_with_errors
        assert "Vrednost" in columns_with_errors
        assert "Navodilo" not in columns_with_errors

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

