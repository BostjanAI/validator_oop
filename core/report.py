"""Validation report aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, MutableMapping

from .error import Severity, ValidationError


@dataclass(slots=True)
class ValidationReport:
    """Aggregates validation errors and exposes common summary helpers.

    Attributes:
        source_path: Path to the validated workbook file.
        errors: List of all validation errors found.
        metadata: Additional information about the validation run.
    """

    source_path: Path
    errors: list[ValidationError] = field(default_factory=list)
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def add_error(self, error: ValidationError) -> None:
        """Append a single error to the report."""
        self.errors.append(error)

    def extend(self, errors: Iterable[ValidationError]) -> None:
        """Append multiple errors in a single call."""
        self.errors.extend(errors)

    def is_valid(self) -> bool:
        """Return True when the workbook passed every validation rule."""
        return not any(e.severity == Severity.ERROR for e in self.errors)

    def has_errors(self) -> bool:
        """Return True if there are any ERROR-level issues."""
        return any(e.severity == Severity.ERROR for e in self.errors)

    def has_warnings(self) -> bool:
        """Return True if there are any WARNING-level issues."""
        return any(e.severity == Severity.WARNING for e in self.errors)

    def counts_by_severity(self) -> dict[Severity, int]:
        """Provide a quick summary grouped by severity."""
        summary: dict[Severity, int] = {level: 0 for level in Severity}
        for error in self.errors:
            summary[error.severity] += 1
        return summary

    def counts_by_code(self) -> dict[str, int]:
        """Provide a summary grouped by error code."""
        summary: dict[str, int] = {}
        for error in self.errors:
            code = error.code or error.rule_name
            summary[code] = summary.get(code, 0) + 1
        return summary

    def errors_by_sheet(self) -> dict[str, list[ValidationError]]:
        """Group errors by sheet name."""
        by_sheet: dict[str, list[ValidationError]] = {}
        for error in self.errors:
            sheet = error.sheet or "(unknown)"
            by_sheet.setdefault(sheet, []).append(error)
        return by_sheet

    def filter_by_severity(self, severity: Severity) -> list[ValidationError]:
        """Return only errors of the specified severity."""
        return [e for e in self.errors if e.severity == severity]

    def filter_by_code(self, code: str) -> list[ValidationError]:
        """Return only errors with the specified code."""
        return [e for e in self.errors if e.code == code]

    def to_dict(self) -> MutableMapping[str, Any]:
        """Serialize the report for persistence or the UI layer."""
        return {
            "source_path": str(self.source_path),
            "metadata": dict(self.metadata),
            "is_valid": self.is_valid(),
            "errors": [error.to_dict() for error in self.errors],
            "counts": {level.value: count for level, count in self.counts_by_severity().items()},
            "counts_by_code": self.counts_by_code(),
        }
