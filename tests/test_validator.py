"""Tests for the validator engine.

Run with: python -m pytest validator_oop/tests/test_validator.py
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from validator_oop.core import (
    RuleEngine,
    Severity,
    ValidationError,
    ValidationReport,
    ValidatorConfig,
)
from validator_oop.rules import RowRule, RuleRegistry


class TestValidatorConfig:
    """Tests for ValidatorConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ValidatorConfig()

        assert config.bypass_rules == frozenset()
        assert config.strict_mode is False
        assert config.locale == "sl"
        assert config.row_offset == 2

    def test_should_skip_rule(self) -> None:
        """Test rule bypass logic."""
        config = ValidatorConfig(bypass_rules=frozenset(["skip_me", "SKIP_CODE"]))

        assert config.should_skip_rule("skip_me") is True
        assert config.should_skip_rule("other", "SKIP_CODE") is True
        assert config.should_skip_rule("other", "OTHER_CODE") is False

    def test_from_dict(self) -> None:
        """Test config creation from dictionary."""
        config = ValidatorConfig.from_dict({
            "bypass_rules": ["rule1", "rule2"],
            "strict_mode": True,
            "locale": "en",
        })

        assert "rule1" in config.bypass_rules
        assert "rule2" in config.bypass_rules
        assert config.strict_mode is True
        assert config.locale == "en"


class TestRuleEngine:
    """Tests for RuleEngine."""

    def test_run_with_bypass(self) -> None:
        """Test that bypassed rules are skipped."""

        class Rule1(RowRule):
            name = "rule1"

            def evaluate(self, row, context):
                yield self.build_error("Rule 1 error", context=context)

        class Rule2(RowRule):
            name = "rule2"

            def evaluate(self, row, context):
                yield self.build_error("Rule 2 error", context=context)

        registry = RuleRegistry()
        registry.register(Rule1)
        registry.register(Rule2)

        config = ValidatorConfig(bypass_rules=frozenset(["rule1"]))
        engine = RuleEngine(registry, config=config)

        errors = engine.run({"Sheet1": [{"col": "val"}]})

        assert len(errors) == 1
        assert errors[0].rule_name == "rule2"

    def test_strict_mode(self) -> None:
        """Test that strict mode converts warnings to errors."""

        class WarningRule(RowRule):
            name = "warning_rule"
            severity = Severity.WARNING

            def evaluate(self, row, context):
                yield self.build_error("Warning message", context=context)

        registry = RuleRegistry()
        registry.register(WarningRule)

        config = ValidatorConfig(strict_mode=True)
        engine = RuleEngine(registry, config=config)

        errors = engine.run({"Sheet1": [{"col": "val"}]})

        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR


class TestValidationReport:
    """Tests for ValidationReport."""

    def test_is_valid(self) -> None:
        """Test is_valid() returns True when no errors."""
        report = ValidationReport(source_path=Path("test.xlsx"))

        assert report.is_valid() is True

        report.add_error(ValidationError(
            rule_name="test",
            message="test",
            severity=Severity.WARNING,
        ))

        assert report.is_valid() is True  # warnings don't make invalid

        report.add_error(ValidationError(
            rule_name="test",
            message="test",
            severity=Severity.ERROR,
        ))

        assert report.is_valid() is False

    def test_counts_by_severity(self) -> None:
        """Test error counting by severity."""
        report = ValidationReport(source_path=Path("test.xlsx"))

        report.add_error(ValidationError(
            rule_name="test", message="1", severity=Severity.ERROR
        ))
        report.add_error(ValidationError(
            rule_name="test", message="2", severity=Severity.ERROR
        ))
        report.add_error(ValidationError(
            rule_name="test", message="3", severity=Severity.WARNING
        ))

        counts = report.counts_by_severity()

        assert counts[Severity.ERROR] == 2
        assert counts[Severity.WARNING] == 1
        assert counts[Severity.INFO] == 0

    def test_errors_by_sheet(self) -> None:
        """Test error grouping by sheet."""
        report = ValidationReport(source_path=Path("test.xlsx"))

        report.add_error(ValidationError(
            rule_name="test", message="1", sheet="Sheet1"
        ))
        report.add_error(ValidationError(
            rule_name="test", message="2", sheet="Sheet1"
        ))
        report.add_error(ValidationError(
            rule_name="test", message="3", sheet="Sheet2"
        ))

        by_sheet = report.errors_by_sheet()

        assert len(by_sheet["Sheet1"]) == 2
        assert len(by_sheet["Sheet2"]) == 1

    def test_to_dict(self) -> None:
        """Test report serialization."""
        report = ValidationReport(source_path=Path("test.xlsx"))
        report.add_error(ValidationError(
            rule_name="test",
            message="Test error",
            code="TEST_CODE",
            severity=Severity.ERROR,
            sheet="Sheet1",
            row_index=5,
        ))

        d = report.to_dict()

        assert d["source_path"] == "test.xlsx"
        assert d["is_valid"] is False
        assert len(d["errors"]) == 1
        assert d["counts"]["error"] == 1

