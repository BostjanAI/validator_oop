"""Tests for RuleEngine and ValidatorEngine.

This module tests the core validation orchestration engines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from validator_oop.core.config import ValidatorConfig
from validator_oop.core.error import Severity, ValidationError
from validator_oop.core.report import ValidationReport
from validator_oop.core.rule_engine import RuleEngine
from validator_oop.core.validator_engine import ValidatorEngine
from validator_oop.excel.excel_loader import ExcelLoader, LoadedWorkbook
from validator_oop.rules.base_rule import RowRule, RuleContext, SheetRule, WorkbookRule
from validator_oop.rules.rule_registry import RuleRegistry


class TestRuleEngine:
    """Tests for RuleEngine."""

    @pytest.fixture
    def empty_registry(self) -> RuleRegistry:
        """Create an empty rule registry."""
        return RuleRegistry()

    @pytest.fixture
    def sample_workbook_data(self) -> dict[str, list[dict[str, Any]]]:
        """Create sample workbook data."""
        return {
            "Sheet1": [
                {"št. Koraka": "1", "Tip objekta": "edit", "Ključ preverjanja": "KEY_1"},
                {"št. Koraka": "2", "Tip objekta": "edit", "Ključ preverjanja": "KEY_2"},
            ],
            "Sheet2": [
                {"št. Koraka": "1", "Tip objekta": "edit", "Ključ preverjanja": "KEY_3"},
            ],
        }

    def test_run_with_no_rules(
        self,
        empty_registry: RuleRegistry,
        sample_workbook_data: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Test running with no registered rules."""
        engine = RuleEngine(empty_registry)
        errors = engine.run(sample_workbook_data)

        assert errors == []

    def test_run_row_rule(self, sample_workbook_data: dict[str, list[dict[str, Any]]]) -> None:
        """Test running a RowRule."""

        class TestRowRule(RowRule):
            name = "test_row_rule"
            code = "TEST_ROW"

            def evaluate(self, row, context):
                if not row.get("Ključ preverjanja"):
                    yield self.build_error("Missing key", context=context)

        registry = RuleRegistry()
        registry.register(TestRowRule)

        engine = RuleEngine(registry)
        errors = engine.run(sample_workbook_data)

        # All rows have keys, so no errors
        assert len(errors) == 0

    def test_run_row_rule_with_errors(self) -> None:
        """Test running a RowRule that produces errors."""

        class AlwaysErrorRule(RowRule):
            name = "always_error"
            code = "ALWAYS_ERROR"

            def evaluate(self, row, context):
                yield self.build_error("Always fails", context=context)

        registry = RuleRegistry()
        registry.register(AlwaysErrorRule)

        engine = RuleEngine(registry)
        workbook_data = {"Sheet1": [{"col": "val1"}, {"col": "val2"}]}
        errors = engine.run(workbook_data)

        assert len(errors) == 2
        assert all(e.code == "ALWAYS_ERROR" for e in errors)

    def test_run_sheet_rule(self) -> None:
        """Test running a SheetRule."""

        class CountRowsRule(SheetRule):
            name = "count_rows"
            code = "TOO_FEW_ROWS"

            def evaluate_sheet(self, rows, context, *, row_offset=2):
                if len(rows) < 3:
                    yield self.build_error(
                        f"Sheet has only {len(rows)} rows",
                        context=context,
                    )

        registry = RuleRegistry()
        registry.register(CountRowsRule)

        engine = RuleEngine(registry)
        workbook_data = {"Sheet1": [{"col": "val1"}, {"col": "val2"}]}  # Only 2 rows
        errors = engine.run(workbook_data)

        assert len(errors) == 1
        assert errors[0].code == "TOO_FEW_ROWS"

    def test_run_workbook_rule(self) -> None:
        """Test running a WorkbookRule."""

        class SheetCountRule(WorkbookRule):
            name = "sheet_count"
            code = "TOO_FEW_SHEETS"

            def evaluate_workbook(self, workbook_data, context, *, row_offset=2):
                if len(workbook_data) < 2:
                    yield self.build_error(
                        f"Workbook has only {len(workbook_data)} sheets",
                        context=context,
                    )

        registry = RuleRegistry()
        registry.register(SheetCountRule)

        engine = RuleEngine(registry)
        workbook_data = {"Sheet1": [{"col": "val"}]}  # Only 1 sheet
        errors = engine.run(workbook_data)

        assert len(errors) == 1
        assert errors[0].code == "TOO_FEW_SHEETS"

    def test_bypass_rules(self) -> None:
        """Test that bypassed rules are skipped."""

        class Rule1(RowRule):
            name = "rule1"
            code = "RULE1_CODE"

            def evaluate(self, row, context):
                yield self.build_error("Rule 1", context=context)

        class Rule2(RowRule):
            name = "rule2"
            code = "RULE2_CODE"

            def evaluate(self, row, context):
                yield self.build_error("Rule 2", context=context)

        registry = RuleRegistry()
        registry.register(Rule1)
        registry.register(Rule2)

        config = ValidatorConfig(bypass_rules=frozenset(["rule1"]))
        engine = RuleEngine(registry, config=config)

        workbook_data = {"Sheet1": [{"col": "val"}]}
        errors = engine.run(workbook_data)

        # Only rule2 should run
        assert len(errors) == 1
        assert errors[0].code == "RULE2_CODE"

    def test_bypass_codes(self) -> None:
        """Test that errors with bypassed codes are suppressed."""

        class MultiCodeRule(RowRule):
            name = "multi_code"

            def evaluate(self, row, context):
                yield self.build_error("Error A", context=context, code="CODE_A")
                yield self.build_error("Error B", context=context, code="CODE_B")

        registry = RuleRegistry()
        registry.register(MultiCodeRule)

        config = ValidatorConfig(bypass_codes=frozenset(["CODE_A"]))
        engine = RuleEngine(registry, config=config)

        workbook_data = {"Sheet1": [{"col": "val"}]}
        errors = engine.run(workbook_data)

        # Only CODE_B should remain
        assert len(errors) == 1
        assert errors[0].code == "CODE_B"

    def test_strict_mode(self) -> None:
        """Test that strict mode converts warnings to errors."""

        class WarningRule(RowRule):
            name = "warning_rule"
            code = "WARNING_CODE"
            severity = Severity.WARNING

            def evaluate(self, row, context):
                yield self.build_error("Warning message", context=context)

        registry = RuleRegistry()
        registry.register(WarningRule)

        config = ValidatorConfig(strict_mode=True)
        engine = RuleEngine(registry, config=config)

        workbook_data = {"Sheet1": [{"col": "val"}]}
        errors = engine.run(workbook_data)

        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_stop_on_first_error(self) -> None:
        """Test that stop_on_first_error stops after first rule produces errors."""

        class AlwaysErrorRule(RowRule):
            name = "always_error"
            code = "ALWAYS_ERROR"

            def evaluate(self, row, context):
                yield self.build_error("Error", context=context)

        class SecondRule(RowRule):
            name = "second_rule"
            code = "SECOND_ERROR"
            priority = 200  # Lower priority, runs after AlwaysErrorRule

            def evaluate(self, row, context):
                yield self.build_error("Second Error", context=context)

        registry = RuleRegistry()
        registry.register(AlwaysErrorRule)
        registry.register(SecondRule)

        config = ValidatorConfig(stop_on_first_error=True)
        engine = RuleEngine(registry, config=config)

        workbook_data = {"Sheet1": [{"col": "val1"}, {"col": "val2"}, {"col": "val3"}]}
        errors = engine.run(workbook_data)

        # Should have errors from first rule only (3 rows), second rule should not run
        error_codes = [e.code for e in errors]
        assert "ALWAYS_ERROR" in error_codes
        assert "SECOND_ERROR" not in error_codes

    def test_rule_priority(self) -> None:
        """Test that rules are executed in priority order."""
        execution_order: list[str] = []

        class LowPriorityRule(RowRule):
            name = "low_priority"
            priority = 200

            def evaluate(self, row, context):
                execution_order.append("low")
                return []

        class HighPriorityRule(RowRule):
            name = "high_priority"
            priority = 10

            def evaluate(self, row, context):
                execution_order.append("high")
                return []

        class MediumPriorityRule(RowRule):
            name = "medium_priority"
            priority = 100

            def evaluate(self, row, context):
                execution_order.append("medium")
                return []

        registry = RuleRegistry()
        registry.register(LowPriorityRule)
        registry.register(HighPriorityRule)
        registry.register(MediumPriorityRule)

        engine = RuleEngine(registry)
        workbook_data = {"Sheet1": [{"col": "val"}]}
        engine.run(workbook_data)

        # High priority should run first
        assert execution_order[0] == "high"

    def test_shared_context_injection(self) -> None:
        """Test that shared context is injected into rules."""
        received_context = []

        class ContextCheckRule(RowRule):
            name = "context_check"

            def evaluate(self, row, context):
                received_context.append(self.shared)
                return []

        registry = RuleRegistry()
        registry.register(ContextCheckRule)

        engine = RuleEngine(registry)
        workbook_data = {
            "Sheet1": [
                {"št. Koraka": "1", "Tip objekta": "edit"},
            ]
        }
        engine.run(workbook_data, sheet_headers={"Sheet1": ["št. Koraka", "Tip objekta"]})

        assert len(received_context) == 1
        assert received_context[0] is not None
        assert received_context[0].existing_steps == {1}

    def test_target_sheets_filtering(self) -> None:
        """Test that rules only run on target sheets."""
        sheets_processed: list[str] = []

        class TargetedRule(RowRule):
            name = "targeted"
            target_sheets = ("Sheet1",)

            def evaluate(self, row, context):
                sheets_processed.append(context.sheet)
                return []

        registry = RuleRegistry()
        registry.register(TargetedRule)

        engine = RuleEngine(registry)
        workbook_data = {
            "Sheet1": [{"col": "val"}],
            "Sheet2": [{"col": "val"}],
        }
        engine.run(workbook_data)

        assert "Sheet1" in sheets_processed
        assert "Sheet2" not in sheets_processed

    def test_reuses_first_sheet_shared_context_for_workbook_rules(self) -> None:
        """Workbook rules should reuse already-built shared context for the first sheet."""

        class NoOpRowRule(RowRule):
            name = "noop_row"

            def evaluate(self, row, context):
                return []

        class NoOpWorkbookRule(WorkbookRule):
            name = "noop_workbook"

            def evaluate_workbook(self, workbook_data, context, *, row_offset=2):
                return []

        registry = RuleRegistry()
        registry.register(NoOpRowRule)
        registry.register(NoOpWorkbookRule)

        engine = RuleEngine(registry)
        workbook_data = {"Sheet1": [{"št. Koraka": "1", "Tip objekta": "edit"}]}

        with patch.object(engine, "_build_shared_context", wraps=engine._build_shared_context) as build_ctx:
            engine.run(workbook_data, sheet_headers={"Sheet1": ["št. Koraka", "Tip objekta"]})

        assert build_ctx.call_count == 1


class TestValidatorEngine:
    """Tests for ValidatorEngine."""

    @pytest.fixture
    def mock_loader(self) -> MagicMock:
        """Create a mock ExcelLoader."""
        loader = MagicMock(spec=ExcelLoader)
        loader.load.return_value = LoadedWorkbook(
            values={"Sheet1": [{"col": "val"}]},
            headers={"Sheet1": ["col"]},
            sheet_names=["Sheet1"],
            row_offset=2,
            source_path=Path("test.xlsx"),
        )
        return loader

    @pytest.fixture
    def mock_rule_engine(self) -> MagicMock:
        """Create a mock RuleEngine."""
        engine = MagicMock(spec=RuleEngine)
        engine.run.return_value = []
        return engine

    def test_validate_returns_report(
        self,
        mock_loader: MagicMock,
        mock_rule_engine: MagicMock,
    ) -> None:
        """Test that validate returns a ValidationReport."""
        validator = ValidatorEngine(mock_rule_engine, mock_loader)
        report = validator.validate("test.xlsx")

        assert isinstance(report, ValidationReport)
        mock_loader.load.assert_called_once()
        mock_rule_engine.run.assert_called_once()

    def test_validate_with_errors(
        self,
        mock_loader: MagicMock,
        mock_rule_engine: MagicMock,
    ) -> None:
        """Test that validation errors are included in report."""
        mock_rule_engine.run.return_value = [
            ValidationError(
                rule_name="test_rule",
                message="Test error",
                code="TEST_CODE",
                severity=Severity.ERROR,
                sheet="Sheet1",
                row_index=2,
            )
        ]

        validator = ValidatorEngine(mock_rule_engine, mock_loader)
        report = validator.validate("test.xlsx")

        assert len(report.errors) == 1
        assert report.errors[0].code == "TEST_CODE"
        assert report.is_valid() is False

    def test_validate_with_no_errors(
        self,
        mock_loader: MagicMock,
        mock_rule_engine: MagicMock,
    ) -> None:
        """Test that valid workbook returns is_valid=True."""
        mock_rule_engine.run.return_value = []

        validator = ValidatorEngine(mock_rule_engine, mock_loader)
        report = validator.validate("test.xlsx")

        assert len(report.errors) == 0
        assert report.is_valid() is True

    def test_validate_loaded(
        self,
        mock_rule_engine: MagicMock,
    ) -> None:
        """Test validate_loaded with pre-loaded workbook."""
        loaded = LoadedWorkbook(
            values={"Sheet1": [{"col": "val"}]},
            headers={"Sheet1": ["col"]},
            sheet_names=["Sheet1"],
            row_offset=2,
            source_path=Path("test.xlsx"),
        )

        loader = MagicMock(spec=ExcelLoader)
        validator = ValidatorEngine(mock_rule_engine, loader)
        report = validator.validate_loaded(loaded)

        assert isinstance(report, ValidationReport)
        # Loader should not be called
        loader.load.assert_not_called()
        mock_rule_engine.run.assert_called_once()

    def test_metadata_included(
        self,
        mock_loader: MagicMock,
        mock_rule_engine: MagicMock,
    ) -> None:
        """Test that metadata is included in report."""
        validator = ValidatorEngine(mock_rule_engine, mock_loader)
        report = validator.validate("test.xlsx")

        assert "sheets" in report.metadata
        assert "row_offset" in report.metadata
        assert "sheet_names" in report.metadata
        assert report.metadata["row_offset"] == 2
        assert report.metadata["sheet_names"] == ["Sheet1"]

    def test_include_formulas_passed_to_loader(
        self,
        mock_loader: MagicMock,
        mock_rule_engine: MagicMock,
    ) -> None:
        """Test that include_formulas is passed to loader."""
        validator = ValidatorEngine(
            mock_rule_engine,
            mock_loader,
            include_formulas=True,
        )
        validator.validate("test.xlsx")

        mock_loader.load.assert_called_once()
        call_kwargs = mock_loader.load.call_args[1]
        assert call_kwargs.get("include_formulas") is True

