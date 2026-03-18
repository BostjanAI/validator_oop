"""Validation rules module.

This module exports the base classes for creating validation rules:
- BaseRule: Abstract base class for all rules
- RowRule: Rule that evaluates each row individually
- SheetRule: Rule that evaluates an entire sheet
- WorkbookRule: Rule that evaluates the entire workbook
- RuleContext: Contextual information for rule execution
- RuleRegistry: Registry for rule classes

Usage:
    from validator_oop.rules import RowRule, RuleRegistry, register

    @register
    class MyRule(RowRule):
        name = "my_rule"
        code = "MY_RULE_CODE"
        priority = 50  # Lower = earlier

        def evaluate(self, row, context):
            if not row.get("required_field"):
                yield self.build_error("Missing required field", context=context)
"""

from validator_oop.rules.base_rule import (
    BaseRule,
    RowRule,
    RuleContext,
    SheetRule,
    WorkbookData,
    WorkbookRule,
)
from validator_oop.rules.rule_registry import RuleRegistry, default_registry, register

__all__ = [
    "BaseRule",
    "RowRule",
    "RuleContext",
    "RuleRegistry",
    "SheetRule",
    "WorkbookData",
    "WorkbookRule",
    "default_registry",
    "register",
]

