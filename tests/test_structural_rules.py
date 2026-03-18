"""Tests for structural validation rules.

This module tests RequiredColumnsRule and StepNumberingRule.
"""

from __future__ import annotations

from typing import Any

import pytest

from validator_oop.core.config import ValidatorConfig
from validator_oop.core.shared_context import SharedContextBuilder
from validator_oop.rules.builtin.structural import RequiredColumnsRule, StepNumberingRule


class TestRequiredColumnsRule:
    """Tests for RequiredColumnsRule."""

    @pytest.fixture
    def rule(self) -> RequiredColumnsRule:
        """Create a RequiredColumnsRule instance."""
        return RequiredColumnsRule()

    def test_all_required_columns_present(self, rule: RequiredColumnsRule) -> None:
        """Test that no errors are raised when all required columns are present."""
        rows = [
            {
                "št. Koraka": "1",
                "Tip objekta": "edit",
                "Tip podatka": "kemijski",
                "Ključ preverjanja": "KEY_1",
                "Vrednost": "100",
                "Navodilo": "Test",
                "Labela": "Test Label",
            }
        ]

        # Build shared context with all required columns
        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Tip podatka", "Ključ preverjanja", "Vrednost", "Navodilo", "Labela"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert len(errors) == 0

    def test_missing_required_column(self, rule: RequiredColumnsRule) -> None:
        """Test that an error is raised when a required column is missing."""
        rows = [{"Tip objekta": "edit", "Tip podatka": "kemijski"}]

        # Build shared context without "št. Koraka"
        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta", "Tip podatka"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        # Should have errors for missing required columns
        assert len(errors) > 0
        error_codes = [e.code for e in errors]
        assert "MANJKA_STOLPEC" in error_codes

    def test_error_contains_column_name(self, rule: RequiredColumnsRule) -> None:
        """Test that the error message contains the missing column name."""
        rows = [{"Tip objekta": "edit"}]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["Tip objekta"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        # At least one error should mention a missing column
        assert any("št. Koraka" in e.message or "Tip podatka" in e.message for e in errors)


class TestStepNumberingRule:
    """Tests for StepNumberingRule."""

    @pytest.fixture
    def rule(self) -> StepNumberingRule:
        """Create a StepNumberingRule instance."""
        return StepNumberingRule()

    def test_valid_step_sequence(self, rule: StepNumberingRule) -> None:
        """Test that no errors are raised for valid step numbering."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "2", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "3", "Tip objekta": "edit", "Zavihek": "Tab1"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        # Filter only step-related errors
        step_errors = [e for e in errors if "STEP" in e.code]
        assert len(step_errors) == 0

    def test_non_integer_step(self, rule: StepNumberingRule) -> None:
        """Test that an error is raised for non-integer step values."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "abc", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "3", "Tip objekta": "edit", "Zavihek": "Tab1"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KORAK_NI_CELO" in error_codes

    def test_missing_step(self, rule: StepNumberingRule) -> None:
        """Test that an error is raised for rows with missing step numbers."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "3", "Tip objekta": "edit", "Zavihek": "Tab1"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KORAK_MANJKA" in error_codes

    def test_duplicate_step(self, rule: StepNumberingRule) -> None:
        """Test that an error is raised for duplicate step numbers."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "2", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "2", "Tip objekta": "edit", "Zavihek": "Tab1"},  # Duplicate
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KORAK_PODVOJEN" in error_codes

    def test_step_gaps(self, rule: StepNumberingRule) -> None:
        """Test that an error is raised for gaps in step numbering."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "2", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "5", "Tip objekta": "edit", "Zavihek": "Tab1"},  # Gap: 3, 4 missing
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KORAK_PRESLEDKI" in error_codes

    def test_tab_start_not_one(self, rule: StepNumberingRule) -> None:
        """Test that an error is raised when a new tab doesn't start at step 1."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "2", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "3", "Tip objekta": "edit", "Zavihek": "Tab2"},  # New tab, not starting at 1
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        error_codes = [e.code for e in errors]
        assert "KORAKI_ZAVIH_NE_1" in error_codes

    def test_row_index_in_error(self, rule: StepNumberingRule) -> None:
        """Test that errors contain the correct Excel row index."""
        rows = [
            {"št. Koraka": "1", "Tip objekta": "edit", "Zavihek": "Tab1"},
            {"št. Koraka": "abc", "Tip objekta": "edit", "Zavihek": "Tab1"},  # Row 3 in Excel
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Tip objekta", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        # The error for "abc" should be at Excel row 3 (offset 2 + index 1)
        step_not_int_errors = [e for e in errors if e.code == "KORAK_NI_CELO"]
        assert len(step_not_int_errors) == 1
        assert step_not_int_errors[0].row_index == 3

    def test_naslov_rows_skipped(self, rule: StepNumberingRule) -> None:
        """Test that rows without any REQUIRED_COLUMNS data are skipped for step validation."""
        # naslov rows typically have no Navodilo, Tip podatka, Ključ preverjanja, Vrednost
        rows = [
            {"št. Koraka": "1", "Navodilo": "Test", "Tip podatka": "kemijski", "Ključ preverjanja": "K1", "Vrednost": "1", "Zavihek": "Tab1"},
            {"št. Koraka": "", "Navodilo": "", "Tip podatka": "", "Ključ preverjanja": "", "Vrednost": "", "Zavihek": "Tab1"},  # empty row - should be skipped
            {"št. Koraka": "2", "Navodilo": "Test2", "Tip podatka": "kemijski", "Ključ preverjanja": "K2", "Vrednost": "2", "Zavihek": "Tab1"},
        ]

        builder = SharedContextBuilder(row_offset=2)
        columns = ["št. Koraka", "Navodilo", "Tip podatka", "Ključ preverjanja", "Vrednost", "Zavihek"]
        ctx = builder.build(rows, columns)
        rule.set_shared_context(ctx)

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        # No STEP_MISSING error for empty row
        step_missing_errors = [e for e in errors if e.code == "KORAK_MANJKA"]
        assert len(step_missing_errors) == 0

