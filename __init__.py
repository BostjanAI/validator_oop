"""Validator OOP package."""

"""MES Excel Validator - Object-Oriented Python Implementation.

This package provides a modular, extensible framework for validating
MES (Manufacturing Execution System) Excel workbooks.

Quick Start:
    from validator_oop import ValidatorEngine, RuleEngine, ExcelLoader
    from validator_oop.rules import RuleRegistry, RowRule

    # Create registry and register rules
    registry = RuleRegistry()

    @registry.decorator
    class MyRule(RowRule):
        name = "my_rule"
        code = "MY_RULE_CODE"

        def evaluate(self, row, context):
            if not row.get("required_field"):
                yield self.build_error("Missing required field", context=context)

    # Create engines
    loader = ExcelLoader()
    rule_engine = RuleEngine(registry)
    validator = ValidatorEngine(rule_engine, loader)

    # Validate
    report = validator.validate("path/to/workbook.xlsx")
    print(report.to_dict())
"""

from validator_oop.core import (
    RuleEngine,
    Severity,
    SharedContext,
    ValidationError,
    ValidationReport,
    ValidatorConfig,
    ValidatorEngine,
)
from validator_oop.excel import (
    ExcelLoader,
    LoadedWorkbook,
    ReportWriter,
    WorkbookFixer,
    WorkbookParser,
)
from validator_oop.rules import (
    BaseRule,
    RowRule,
    RuleContext,
    RuleRegistry,
    SheetRule,
    WorkbookRule,
    default_registry,
    register,
)

__version__ = "0.1.0"
__author__ = "MES Validator Team"

__all__ = [
    # Core
    "RuleEngine",
    "Severity",
    "SharedContext",
    "ValidationError",
    "ValidationReport",
    "ValidatorConfig",
    "ValidatorEngine",
    # Excel
    "ExcelLoader",
    "LoadedWorkbook",
    "ReportWriter",
    "WorkbookFixer",
    "WorkbookParser",
    # Rules
    "BaseRule",
    "RowRule",
    "RuleContext",
    "RuleRegistry",
    "SheetRule",
    "WorkbookRule",
    "default_registry",
    "register",
]

