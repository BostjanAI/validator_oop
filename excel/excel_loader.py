"""Excel file loading utilities.

This module handles reading Excel files and returning normalized data
structures for validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .recipe_workbook import workbook_has_required_columns
from .workbook_parser import WorkbookParser

try:  # pragma: no cover - optional dependency during scaffolding
    from openpyxl import load_workbook as _load_workbook
except ImportError:  # pragma: no cover
    _load_workbook = None


@dataclass(slots=True)
class LoadedWorkbook:
    """Container for loaded workbook data.

    This dataclass holds both the parsed values and optionally the formulas,
    along with metadata about the workbook.

    Attributes:
        values: Mapping of sheet names to lists of row dictionaries (cell values).
        formulas: Mapping of sheet names to lists of row dictionaries (cell formulas).
        headers: Mapping of sheet names to lists of column headers.
        raw_workbook_values: The openpyxl Workbook loaded with data_only=True.
        raw_workbook_formulas: The openpyxl Workbook loaded with data_only=False.
        source_path: Path to the source Excel file.
        row_offset: Excel row number of the first data row (default 2).
        sheet_names: Ordered list of sheet names.
    """

    values: dict[str, list[dict[str, Any]]]
    formulas: dict[str, list[dict[str, Any]]] | None = None
    headers: dict[str, list[str]] = field(default_factory=dict)
    raw_workbook_values: Any = None
    raw_workbook_formulas: Any = None
    source_path: Path | None = None
    row_offset: int = 2
    sheet_names: list[str] = field(default_factory=list)

    def get_sheet_data(self, sheet_name: str) -> list[dict[str, Any]]:
        """Get parsed row data for a specific sheet.

        Args:
            sheet_name: Name of the sheet.

        Returns:
            List of row dictionaries, or empty list if sheet not found.
        """
        return self.values.get(sheet_name, [])

    def get_sheet_formulas(self, sheet_name: str) -> list[dict[str, Any]] | None:
        """Get formula data for a specific sheet.

        Args:
            sheet_name: Name of the sheet.

        Returns:
            List of row dictionaries with formulas, or None if not loaded.
        """
        if self.formulas is None:
            return None
        return self.formulas.get(sheet_name)

    def get_headers(self, sheet_name: str) -> list[str]:
        """Get column headers for a specific sheet.

        Args:
            sheet_name: Name of the sheet.

        Returns:
            List of header strings, or empty list if sheet not found.
        """
        return self.headers.get(sheet_name, [])

    def close(self) -> None:
        """Close any open workbook handles."""
        if self.raw_workbook_values is not None:
            try:
                self.raw_workbook_values.close()
            except Exception:
                pass
        if self.raw_workbook_formulas is not None:
            try:
                self.raw_workbook_formulas.close()
            except Exception:
                pass


class ExcelLoader:
    """Responsible for reading Excel files and returning normalized data.

    This class handles loading Excel workbooks and parsing them into
    dictionaries suitable for validation rules.
    """

    def __init__(
        self,
        parser: WorkbookParser | None = None,
        *,
        logger: logging.Logger | None = None,
        header_row_index: int = 1,
    ) -> None:
        """Initialize the Excel loader.

        Args:
            parser: WorkbookParser instance for converting sheets to dicts.
            logger: Logger instance for debugging.
            header_row_index: 1-based row index of the header row.
        """
        self._parser = parser or WorkbookParser(header_row_index=header_row_index)
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def load(
        self,
        workbook_path: str | Path,
        *,
        include_formulas: bool = False,
        keep_workbooks_open: bool = False,
    ) -> LoadedWorkbook:
        """Load an Excel workbook and return parsed data.

        Args:
            workbook_path: Path to the Excel file.
            include_formulas: If True, also load cell formulas.
            keep_workbooks_open: If True, keep raw workbooks open for later access.

        Returns:
            LoadedWorkbook containing parsed data and metadata.

        Raises:
            FileNotFoundError: If the workbook file doesn't exist.
            RuntimeError: If openpyxl is not installed.
        """
        resolved_path = Path(workbook_path).expanduser().resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(f"Workbook not found: {resolved_path}")

        if _load_workbook is None:
            raise RuntimeError("openpyxl is required to load Excel workbooks. Install with: pip install openpyxl")

        self._logger.debug("Opening workbook %s", resolved_path)

        # Load workbook with data_only=True (computed values)
        wb_values = _load_workbook(resolved_path, data_only=True, read_only=True)
        values = self._parser.parse(wb_values)
        sheet_names = [sheet.title for sheet in wb_values.worksheets]

        # Extract headers
        headers: dict[str, list[str]] = {}
        for sheet in wb_values.worksheets:
            headers[sheet.title] = self._parser.get_headers(sheet)

        # Load formulas if requested
        formulas: dict[str, list[dict[str, Any]]] | None = None
        wb_formulas = None
        if include_formulas:
            self._logger.debug("Loading formulas from %s", resolved_path)
            wb_formulas = _load_workbook(resolved_path, data_only=False, read_only=True)
            formulas = self._parser.parse(wb_formulas, parse_formulas=True)

        # Calculate row offset (header row + 1)
        row_offset = self._parser.header_row_index + 1

        result = LoadedWorkbook(
            values=values,
            formulas=formulas,
            headers=headers,
            raw_workbook_values=wb_values if keep_workbooks_open else None,
            raw_workbook_formulas=wb_formulas if keep_workbooks_open else None,
            source_path=resolved_path,
            row_offset=row_offset,
            sheet_names=sheet_names,
        )

        # Close workbooks if not keeping them open
        if not keep_workbooks_open:
            wb_values.close()
            if wb_formulas is not None:
                wb_formulas.close()

        return result

    def has_required_columns(self, workbook_path: str | Path) -> bool:
        """Return True if any sheet contains at least one IPO recipe column."""
        return workbook_has_required_columns(
            workbook_path,
            parser=self._parser,
        )

    def load_simple(self, workbook_path: str | Path) -> dict[str, list[dict[str, Any]]]:
        """Load workbook and return only the values dictionary.

        This is a convenience method for simple use cases that don't need
        formulas or metadata.

        Args:
            workbook_path: Path to the Excel file.

        Returns:
            Dictionary mapping sheet names to lists of row dictionaries.
        """
        loaded = self.load(workbook_path, include_formulas=False)
        return loaded.values
