"""Tests for validation rules.

Run with: python -m pytest validator_oop/tests/test_rules.py
"""

from __future__ import annotations

import pytest

from validator_oop.core import Severity, ValidationError
from validator_oop.rules import RowRule, RuleContext, RuleRegistry, SheetRule


class TestRowRule:
    """Tests for RowRule base class."""

    def test_row_rule_evaluate(self) -> None:
        """Test that RowRule.evaluate is called for each row."""

        class TestRule(RowRule):
            name = "test_rule"
            code = "TEST_CODE"

            def evaluate(self, row, context):
                if not row.get("required"):
                    yield self.build_error("Missing required", context=context)

        rule = TestRule()
        rows = [
            {"required": "yes"},
            {"required": ""},
            {"required": "no"},
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert len(errors) == 1
        assert errors[0].code == "TEST_CODE"
        assert errors[0].row_index == 3  # row_offset + 1

    def test_row_rule_applies_to(self) -> None:
        """Test target_sheets filtering."""

        class TargetedRule(RowRule):
            name = "targeted"
            target_sheets = ("Sheet1", "Sheet2")

            def evaluate(self, row, context):
                return []

        rule = TargetedRule()

        assert rule.applies_to("Sheet1") is True
        assert rule.applies_to("Sheet2") is True
        assert rule.applies_to("Sheet3") is False

    def test_row_rule_priority(self) -> None:
        """Test rule priority ordering."""

        class LowPriorityRule(RowRule):
            name = "low"
            priority = 200

            def evaluate(self, row, context):
                return []

        class HighPriorityRule(RowRule):
            name = "high"
            priority = 10

            def evaluate(self, row, context):
                return []

        registry = RuleRegistry()
        registry.register(LowPriorityRule)
        registry.register(HighPriorityRule)

        instances = registry.instantiate()

        assert instances[0].name == "high"
        assert instances[1].name == "low"


class TestSheetRule:
    """Tests for SheetRule base class."""

    def test_sheet_rule_evaluate(self) -> None:
        """Test that SheetRule.evaluate_sheet receives all rows."""

        class DuplicateKeyRule(SheetRule):
            name = "duplicate_key"
            code = "DUP_KEY"

            def evaluate_sheet(self, rows, context, *, row_offset=2):
                keys = {}
                for idx, row in enumerate(rows):
                    key = row.get("key")
                    if key:
                        if key in keys:
                            yield self.build_error(
                                f"Duplicate key: {key}",
                                context=context.with_row(idx + row_offset),
                            )
                        keys[key] = idx + row_offset

        rule = DuplicateKeyRule()
        rows = [
            {"key": "a"},
            {"key": "b"},
            {"key": "a"},  # duplicate
        ]

        errors = rule.run(rows, sheet_name="Sheet1", row_offset=2)

        assert len(errors) == 1
        assert errors[0].code == "DUP_KEY"
        assert errors[0].row_index == 4


class TestRuleRegistry:
    """Tests for RuleRegistry."""

    def test_register_and_get(self) -> None:
        """Test rule registration and retrieval."""

        class MyRule(RowRule):
            name = "my_rule"

            def evaluate(self, row, context):
                return []

        registry = RuleRegistry()
        registry.register(MyRule)

        assert registry.get("my_rule") is MyRule
        assert registry.get("nonexistent") is None

    def test_duplicate_registration(self) -> None:
        """Test that duplicate registration raises an error."""

        class MyRule(RowRule):
            name = "my_rule"

            def evaluate(self, row, context):
                return []

        registry = RuleRegistry()
        registry.register(MyRule)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(MyRule)

    def test_instantiate_with_dependencies(self) -> None:
        """Test dependency injection during instantiation."""

        class RuleWithDep(RowRule):
            name = "with_dep"

            def __init__(self, *, custom_dep: str = "default", **kwargs):
                super().__init__(**kwargs)
                self.custom_dep = custom_dep

            def evaluate(self, row, context):
                return []

        registry = RuleRegistry()
        registry.register(RuleWithDep)

        instances = registry.instantiate(custom_dep="injected")

        assert instances[0].custom_dep == "injected"


class TestRuleContext:
    """Tests for RuleContext."""

    def test_with_row(self) -> None:
        """Test context.with_row() creates new context."""
        ctx = RuleContext(sheet="Sheet1", workbook="test.xlsx")
        row_ctx = ctx.with_row(5)

        assert row_ctx.sheet == "Sheet1"
        assert row_ctx.workbook == "test.xlsx"
        assert row_ctx.row_index == 5
        assert ctx.row_index is None  # original unchanged

    def test_with_sheet(self) -> None:
        """Test context.with_sheet() creates new context."""
        ctx = RuleContext(sheet="Sheet1", row_index=5)
        sheet_ctx = ctx.with_sheet("Sheet2")

        assert sheet_ctx.sheet == "Sheet2"
        assert sheet_ctx.row_index is None
        assert ctx.sheet == "Sheet1"  # original unchanged


class TestValidationError:
    """Tests for ValidationError."""

    def test_to_dict(self) -> None:
        """Test error serialization."""
        error = ValidationError(
            rule_name="test_rule",
            message="Test message",
            code="TEST_CODE",
            severity=Severity.ERROR,
            sheet="Sheet1",
            row_index=5,
            column="A",
        )

        d = error.to_dict()

        assert d["rule"] == "test_rule"
        assert d["code"] == "TEST_CODE"
        assert d["severity"] == "error"
        assert d["message"] == "Test message"
        assert d["sheet"] == "Sheet1"
        assert d["row"] == 5
        assert d["col"] == "A"

