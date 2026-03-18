"""Validation error types and severity levels."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, MutableMapping


class Severity(str, Enum):
    """Severity levels supported by the validation framework."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True)
class ValidationError:
    """Represents a single validation failure raised by a rule.

    Attributes:
        rule_name: Human-readable name of the rule that generated this error.
        message: Descriptive error message (often in Slovenian for MES).
        code: Unique error code for programmatic identification (e.g., 'KEY_FORMAT').
        severity: Error severity level.
        sheet: Name of the sheet where the error occurred.
        workbook: Name of the workbook file.
        row_index: 1-based Excel row index (None for sheet/workbook-level errors).
        column: Column header name where the error occurred.
        payload: Additional structured data for debugging or reporting.
    """

    rule_name: str
    message: str
    code: str = ""
    severity: Severity = Severity.ERROR
    sheet: str | None = None
    workbook: str | None = None
    row_index: int | None = None
    column: str | None = None
    payload: Mapping[str, Any] | None = None

    def to_dict(self) -> MutableMapping[str, Any]:
        """Serialize the error into a dictionary for reporting/export."""
        data: MutableMapping[str, Any] = {
            "rule": self.rule_name,
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
        }
        if self.sheet is not None:
            data["sheet"] = self.sheet
        if self.workbook is not None:
            data["workbook"] = self.workbook
        if self.row_index is not None:
            data["row"] = self.row_index
        if self.column is not None:
            data["col"] = self.column
        if self.payload:
            data["payload"] = dict(self.payload)
        return data
