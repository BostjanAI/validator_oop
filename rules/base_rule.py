"""Base classes for validation rules.

This module provides three rule types:
- RowRule: Evaluates each row individually (most common)
- SheetRule: Evaluates an entire sheet at once (for cross-row validation)
- WorkbookRule: Evaluates the entire workbook (for cross-sheet validation)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Mapping, MutableMapping, Sequence

from validator_oop.core.error import Severity, ValidationError

if TYPE_CHECKING:
    from validator_oop.core.shared_context import SharedContext

# Type alias for workbook data structure
WorkbookData = Mapping[str, Sequence[Mapping[str, Any]]]


@dataclass(slots=True, frozen=True)
class RuleContext:
    """Carries contextual metadata for rule execution.

    Attributes:
        sheet: Name of the current sheet being validated.
        row_index: 1-based Excel row index (None for sheet/workbook-level context).
        workbook: Name of the workbook file.
        shared: Reference to pre-computed shared context across rules.
        extra: Additional arbitrary metadata.
    """

    sheet: str
    row_index: int | None = None
    workbook: str | None = None
    shared: SharedContext | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def with_row(self, row_index: int) -> RuleContext:
        """Return a new context bound to a specific row index."""
        return RuleContext(
            sheet=self.sheet,
            row_index=row_index,
            workbook=self.workbook,
            shared=self.shared,
            extra=self.extra,
        )

    def with_sheet(self, sheet: str) -> RuleContext:
        """Return a new context bound to a different sheet."""
        return RuleContext(
            sheet=sheet,
            row_index=None,
            workbook=self.workbook,
            shared=self.shared,
            extra=self.extra,
        )


class BaseRule(ABC):
    """Abstract base class for all validation rules.

    Class Attributes:
        name: Human-readable rule name (defaults to class name).
        description: Documentation string for the rule.
        code: Unique error code prefix (e.g., 'KEY_FORMAT').
        tags: Categorization tags for filtering.
        severity: Default severity for errors from this rule.
        priority: Execution order (lower = earlier, default 100).
        target_sheets: Tuple of sheet names to run against (None = all sheets).
    """

    name: str = ""
    description: str = ""
    code: str = ""
    tags: tuple[str, ...] = ()
    severity: Severity = Severity.ERROR
    priority: int = 100
    target_sheets: tuple[str, ...] | None = None

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._shared_context: SharedContext | None = None

    def set_shared_context(self, shared: SharedContext) -> None:
        """Inject the shared context before rule execution."""
        self._shared_context = shared

    @property
    def shared(self) -> SharedContext | None:
        """Access the shared context."""
        return self._shared_context

    def applies_to(self, sheet_name: str) -> bool:
        """Return True when the rule should run against the provided sheet."""
        if not self.target_sheets:
            return True
        return sheet_name in self.target_sheets

    @property
    def display_name(self) -> str:
        """Human-friendly name fallback."""
        return self.name or self.__class__.__name__

    @property
    def error_code(self) -> str:
        """Error code fallback."""
        return self.code or self.__class__.__name__.upper()

    def build_error(
        self,
        message: str,
        *,
        context: RuleContext,
        code: str | None = None,
        column: str | None = None,
        severity: Severity | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ValidationError:
        """Utility helper to create a standardized ValidationError."""
        return ValidationError(
            rule_name=self.display_name,
            message=message,
            code=code or self.error_code,
            severity=severity or self.severity,
            sheet=context.sheet,
            workbook=context.workbook,
            row_index=context.row_index,
            column=column,
            payload=payload,
        )

    def _enrich_error(self, error: ValidationError, context: RuleContext) -> ValidationError:
        """Ensure every emitted error contains the required metadata."""
        # If error already has all required fields, return as-is
        if error.rule_name and error.code:
            return error

        payload: MutableMapping[str, Any] | None = None
        if error.payload:
            payload = dict(error.payload)

        return ValidationError(
            rule_name=error.rule_name or self.display_name,
            message=error.message,
            code=error.code or self.error_code,
            severity=error.severity or self.severity,
            sheet=error.sheet or context.sheet,
            workbook=error.workbook or context.workbook,
            row_index=error.row_index if error.row_index is not None else context.row_index,
            column=error.column,
            payload=payload,
        )


class RowRule(BaseRule):
    """Rule that evaluates each row individually.

    This is the most common rule type. Override `evaluate()` to implement
    the validation logic for a single row.
    """

    def run(
        self,
        rows: Sequence[Mapping[str, Any]],
        *,
        sheet_name: str,
        workbook_name: str | None = None,
        row_offset: int = 2,
    ) -> list[ValidationError]:
        """Execute the rule against a list of row dictionaries.

        Args:
            rows: Sequence of row dictionaries (header -> value).
            sheet_name: Name of the sheet being validated.
            workbook_name: Name of the workbook file.
            row_offset: Excel row number of the first data row (default 2).

        Returns:
            List of validation errors found.
        """
        if not rows:
            return []

        base_context = RuleContext(
            sheet=sheet_name,
            workbook=workbook_name,
            shared=self._shared_context,
        )
        errors: list[ValidationError] = []

        for index, row in enumerate(rows):
            excel_row = index + row_offset
            row_context = base_context.with_row(excel_row)
            for error in self.evaluate(row, row_context) or ():
                errors.append(self._enrich_error(error, row_context))

        return errors

    @abstractmethod
    def evaluate(self, row: Mapping[str, Any], context: RuleContext) -> Iterable[ValidationError] | None:
        """Implement rule-specific validation logic for a single row.

        Args:
            row: Dictionary mapping column headers to cell values.
            context: Contextual information including sheet, row index, etc.

        Returns:
            Iterable of ValidationError objects, or None if no errors.
        """


class SheetRule(BaseRule):
    """Rule that evaluates an entire sheet at once.

    Use this for cross-row validation such as:
    - Duplicate key detection
    - Pair matching (kemikalija-masa)
    - Sequential step validation
    """

    def run(
        self,
        rows: Sequence[Mapping[str, Any]],
        *,
        sheet_name: str,
        workbook_name: str | None = None,
        row_offset: int = 2,
    ) -> list[ValidationError]:
        """Execute the rule against all rows in a sheet.

        Args:
            rows: All rows in the sheet.
            sheet_name: Name of the sheet being validated.
            workbook_name: Name of the workbook file.
            row_offset: Excel row number of the first data row (default 2).

        Returns:
            List of validation errors found.
        """
        context = RuleContext(
            sheet=sheet_name,
            workbook=workbook_name,
            shared=self._shared_context,
        )
        errors: list[ValidationError] = []

        for error in self.evaluate_sheet(rows, context, row_offset=row_offset) or ():
            errors.append(self._enrich_error(error, context))

        return errors

    @abstractmethod
    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, Any]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable[ValidationError] | None:
        """Implement rule-specific validation logic for the entire sheet.

        Args:
            rows: All rows in the sheet.
            context: Contextual information (row_index will be None).
            row_offset: Excel row number of the first data row.

        Returns:
            Iterable of ValidationError objects, or None if no errors.
        """


class WorkbookRule(BaseRule):
    """Rule that evaluates the entire workbook across all sheets.

    Use this for cross-sheet validation such as:
    - Global key uniqueness
    - Cross-sheet references
    """

    def run_workbook(
        self,
        workbook_data: WorkbookData,
        *,
        workbook_name: str | None = None,
        row_offset: int = 2,
    ) -> list[ValidationError]:
        """Execute the rule against the entire workbook.

        Args:
            workbook_data: Mapping of sheet names to row sequences.
            workbook_name: Name of the workbook file.
            row_offset: Excel row number of the first data row (default 2).

        Returns:
            List of validation errors found.
        """
        context = RuleContext(
            sheet="",  # Will be set per-sheet in evaluate_workbook
            workbook=workbook_name,
            shared=self._shared_context,
        )
        errors: list[ValidationError] = []

        for error in self.evaluate_workbook(workbook_data, context, row_offset=row_offset) or ():
            errors.append(self._enrich_error(error, context))

        return errors

    # Provide a default run() that does nothing (workbook rules use run_workbook)
    def run(
        self,
        rows: Sequence[Mapping[str, Any]],
        *,
        sheet_name: str,
        workbook_name: str | None = None,
        row_offset: int = 2,
    ) -> list[ValidationError]:
        """WorkbookRule does not process individual sheets via run().

        Override run_workbook() instead.
        """
        return []

    @abstractmethod
    def evaluate_workbook(
        self,
        workbook_data: WorkbookData,
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable[ValidationError] | None:
        """Implement rule-specific validation logic for the entire workbook.

        Args:
            workbook_data: Mapping of sheet names to row sequences.
            context: Contextual information (sheet will be empty string).
            row_offset: Excel row number of the first data row.

        Returns:
            Iterable of ValidationError objects, or None if no errors.
        """
