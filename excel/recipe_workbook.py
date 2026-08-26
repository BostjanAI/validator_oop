"""Helpers for detecting IPO recipe workbooks by column structure."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from validator_oop.core.constants import REQUIRED_COLUMNS

try:  # pragma: no cover - optional dependency during scaffolding
    from openpyxl import load_workbook as _load_workbook
except ImportError:  # pragma: no cover
    _load_workbook = None

from validator_oop.excel.workbook_parser import WorkbookParser


def normalize_column_names(columns: Iterable[str]) -> set[str]:
    """Normalize header names for comparison (strip whitespace)."""
    return {col.strip() if isinstance(col, str) else str(col) for col in columns}


def sheet_has_required_columns(columns: Iterable[str]) -> bool:
    """Return True if a sheet contains all required IPO recipe columns."""
    columns_norm = normalize_column_names(columns)
    return all(col in columns_norm for col in REQUIRED_COLUMNS)


def workbook_has_required_columns(
    workbook_path: str | Path,
    *,
    parser: WorkbookParser | None = None,
) -> bool:
    """Return True if workbook has at least one sheet with recipe columns."""
    resolved_path = Path(workbook_path).expanduser().resolve()
    if not resolved_path.exists() or not resolved_path.is_file():
        return False
    if _load_workbook is None:
        return False

    workbook_parser = parser or WorkbookParser()
    try:
        workbook = _load_workbook(resolved_path, data_only=True, read_only=True)
    except Exception:
        return False

    try:
        for sheet in workbook.worksheets:
            if sheet_has_required_columns(workbook_parser.get_headers(sheet)):
                return True
        return False
    finally:
        workbook.close()
