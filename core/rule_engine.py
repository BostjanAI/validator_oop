"""Rule execution engine.

This module coordinates rule instantiation and execution, handling
RowRule, SheetRule, and WorkbookRule types appropriately.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Sequence

from validator_oop.core.config import DEFAULT_CONFIG, ValidatorConfig
from validator_oop.core.error import Severity, ValidationError
from validator_oop.core.shared_context import SharedContext, SharedContextBuilder
from validator_oop.rules.base_rule import BaseRule, RowRule, SheetRule, WorkbookRule
from validator_oop.rules.rule_registry import RuleRegistry

# Type alias for workbook data structure
WorkbookData = Mapping[str, Sequence[Mapping[str, Any]]]


class RuleEngine:
    """Coordinates rule instantiation and execution.

    The RuleEngine handles three types of rules:
    - RowRule: Executed per-row within each sheet
    - SheetRule: Executed once per sheet with all rows
    - WorkbookRule: Executed once with the entire workbook

    It also manages the SharedContext, building it before rule execution
    and injecting it into each rule.
    """

    def __init__(
        self,
        registry: RuleRegistry,
        *,
        config: ValidatorConfig | None = None,
        logger: logging.Logger | None = None,
        rule_dependencies: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the rule engine.

        Args:
            registry: Registry containing rule classes to instantiate.
            config: Validator configuration (uses defaults if not provided).
            logger: Logger instance for debugging.
            rule_dependencies: Dependencies to inject into rule constructors.
        """
        self._registry = registry
        self._config = config or DEFAULT_CONFIG
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._rule_dependencies = rule_dependencies or {}

    @property
    def config(self) -> ValidatorConfig:
        """Get the current configuration."""
        return self._config

    def run(
        self,
        workbook_data: WorkbookData,
        *,
        workbook_name: str | None = None,
        sheet_headers: Mapping[str, Sequence[str]] | None = None,
        workbook_values: Any = None,
        workbook_formulas: Any = None,
        parsed_formulas: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
        all_workbook_data: WorkbookData | None = None,
        all_workbook_headers: Mapping[str, Sequence[str]] | None = None,
    ) -> list[ValidationError]:
        """Execute all registered rules against the provided workbook data.

        Args:
            workbook_data: Mapping of sheet names to row sequences (filtered).
            workbook_name: Name of the workbook file.
            sheet_headers: Optional mapping of sheet names to header sequences.
            all_workbook_data: Original unfiltered workbook data (for SOP validation).
            all_workbook_headers: Original unfiltered headers (for SOP validation).

        Returns:
            List of all validation errors found.
        """
        errors: list[ValidationError] = []

        # Instantiate all rules (sorted by priority)
        all_rules = self._registry.instantiate(
            logger_factory=self._build_child_logger,
            **self._rule_dependencies,
        )

        # Filter out bypassed rules
        rules = [
            rule for rule in all_rules
            if not self._config.should_skip_rule(rule.display_name, rule.error_code)
        ]

        if len(rules) < len(all_rules):
            skipped = len(all_rules) - len(rules)
            self._logger.info("Skipped %d bypassed rules", skipped)

        # Separate rules by type
        row_rules: list[RowRule] = []
        sheet_rules: list[SheetRule] = []
        workbook_rules: list[WorkbookRule] = []

        for rule in rules:
            if isinstance(rule, WorkbookRule):
                workbook_rules.append(rule)
            elif isinstance(rule, SheetRule):
                sheet_rules.append(rule)
            elif isinstance(rule, RowRule):
                row_rules.append(rule)
            else:
                # Legacy BaseRule - log warning
                self._logger.warning(
                    "Rule %s inherits from BaseRule directly; consider using RowRule/SheetRule/WorkbookRule",
                    rule.display_name,
                )

        # Process each sheet
        for sheet_name, rows in workbook_data.items():
            if self._config.stop_on_first_error and errors:
                break

            # Build shared context for this sheet
            if sheet_headers and sheet_name in sheet_headers:
                columns = list(sheet_headers[sheet_name])
            else:
                columns = list(rows[0].keys()) if rows else []
            shared_context = self._build_shared_context(rows, columns)
            
            # Add workbook objects to extra for rules that need them
            if workbook_values is not None:
                shared_context.extra["workbook_values"] = workbook_values
            if workbook_formulas is not None:
                shared_context.extra["workbook_formulas"] = workbook_formulas
            if parsed_formulas is not None:
                shared_context.extra["parsed_formulas"] = parsed_formulas
            if all_workbook_data is not None:
                shared_context.extra["all_workbook_data"] = all_workbook_data
            if all_workbook_headers is not None:
                shared_context.extra["all_workbook_headers"] = all_workbook_headers

            # Inject shared context into all rules
            for rule in rules:
                rule.set_shared_context(shared_context)

            # Run row rules
            for rule in row_rules:
                if self._config.stop_on_first_error and errors:
                    break
                if not rule.applies_to(sheet_name):
                    continue

                self._logger.debug("Running RowRule %s on sheet %s", rule.display_name, sheet_name)
                sheet_errors = rule.run(
                    rows,
                    sheet_name=sheet_name,
                    workbook_name=workbook_name,
                    row_offset=self._config.row_offset,
                )
                errors.extend(self._filter_errors(sheet_errors))

            # Run sheet rules
            for rule in sheet_rules:
                if self._config.stop_on_first_error and errors:
                    break
                if not rule.applies_to(sheet_name):
                    continue

                self._logger.debug("Running SheetRule %s on sheet %s", rule.display_name, sheet_name)
                sheet_errors = rule.run(
                    rows,
                    sheet_name=sheet_name,
                    workbook_name=workbook_name,
                    row_offset=self._config.row_offset,
                )
                errors.extend(self._filter_errors(sheet_errors))

        # Run workbook rules (once for entire workbook)
        for rule in workbook_rules:
            if self._config.stop_on_first_error and errors:
                break

            # Build a shared context for workbook rules
            # Use first sheet's context as base, but with all workbook data
            if workbook_data:
                first_sheet = next(iter(workbook_data.keys()))
                first_rows = workbook_data[first_sheet]
                first_columns = (
                    list(sheet_headers[first_sheet]) if sheet_headers and first_sheet in sheet_headers
                    else list(first_rows[0].keys()) if first_rows else []
                )
                workbook_shared_context = self._build_shared_context(first_rows, first_columns)
                
                # Add all workbook data to extra
                if all_workbook_data is not None:
                    workbook_shared_context.extra["all_workbook_data"] = all_workbook_data
                if all_workbook_headers is not None:
                    workbook_shared_context.extra["all_workbook_headers"] = all_workbook_headers
                if workbook_values is not None:
                    workbook_shared_context.extra["workbook_values"] = workbook_values
                if workbook_formulas is not None:
                    workbook_shared_context.extra["workbook_formulas"] = workbook_formulas
                if parsed_formulas is not None:
                    workbook_shared_context.extra["parsed_formulas"] = parsed_formulas
                
                # Inject shared context
                rule.set_shared_context(workbook_shared_context)
            else:
                # No data, create empty context
                workbook_shared_context = self._build_shared_context([], [])
                if all_workbook_data is not None:
                    workbook_shared_context.extra["all_workbook_data"] = all_workbook_data
                if all_workbook_headers is not None:
                    workbook_shared_context.extra["all_workbook_headers"] = all_workbook_headers
                rule.set_shared_context(workbook_shared_context)

            self._logger.debug("Running WorkbookRule %s", rule.display_name)
            wb_errors = rule.run_workbook(
                workbook_data,
                workbook_name=workbook_name,
                row_offset=self._config.row_offset,
            )
            errors.extend(self._filter_errors(wb_errors))

        # Apply strict mode if enabled
        if self._config.strict_mode:
            for error in errors:
                if error.severity == Severity.WARNING:
                    # Create a new error with ERROR severity
                    errors[errors.index(error)] = ValidationError(
                        rule_name=error.rule_name,
                        message=error.message,
                        code=error.code,
                        severity=Severity.ERROR,
                        sheet=error.sheet,
                        workbook=error.workbook,
                        row_index=error.row_index,
                        column=error.column,
                        payload=error.payload,
                    )

        return errors

    def _filter_errors(self, errors: list[ValidationError]) -> list[ValidationError]:
        """Filter errors based on configuration.

        Args:
            errors: List of errors to filter.

        Returns:
            Filtered list of errors.
        """
        return [
            error for error in errors
            if not self._config.should_suppress_error(error.code)
        ]

    def _build_shared_context(
        self,
        rows: Sequence[Mapping[str, Any]],
        columns: Sequence[str],
    ) -> SharedContext:
        """Build shared context for a sheet.

        Args:
            rows: Sequence of row dictionaries.
            columns: List of column names.

        Returns:
            Populated SharedContext instance.
        """
        builder = SharedContextBuilder(row_offset=self._config.row_offset)
        ctx = builder.build(rows, columns)

        # Expose selected configuration flags to rules via SharedContext.extra.
        # This mirrors the BYPASS_* flags used in the original MES_validator.py.
        ctx.extra.setdefault(
            "bypass_zakleni_require_empty_for_checkbox",
            self._config.bypass_zakleni_require_empty_for_checkbox,
        )
        ctx.extra.setdefault(
            "bypass_zakleni_require_pogoj_for_param1_steps",
            self._config.bypass_zakleni_require_pogoj_for_param1_steps,
        )
        ctx.extra.setdefault(
            "bypass_zakleni_inverse_pogoj_requirement",
            self._config.bypass_zakleni_inverse_pogoj_requirement,
        )
        # Also expose the full config for advanced rules if needed.
        ctx.extra.setdefault("config", self._config)
        return ctx

    def _build_child_logger(self, rule_name: str) -> logging.Logger:
        """Create a child logger for a specific rule."""
        return self._logger.getChild(rule_name)
