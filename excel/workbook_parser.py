"""Workbook parsing utilities.

This module converts openpyxl worksheets into normalized row dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from validator_oop.core.constants import EXCEL_ERROR_TOKENS


@dataclass(slots=True)
class WorkbookParser:
    """Convert openpyxl worksheets into normalized row dictionaries.

    Attributes:
        header_row_index: 1-based row index of the header row (default 1).
        stop_at_blank_row: If True, stop parsing at first fully blank row.
    """

    header_row_index: int = 1
    stop_at_blank_row: bool = True

    def parse(self, workbook: Any, parse_formulas: bool = False) -> dict[str, list[dict[str, Any]]]:
        """Parse an openpyxl workbook instance.

        Args:
            workbook: An openpyxl Workbook object.
            parse_formulas: If True, extract formulas instead of values.

        Returns:
            Dictionary mapping sheet names to lists of row dictionaries.
        """
        data: dict[str, list[dict[str, Any]]] = {}
        for sheet in workbook.worksheets:
            data[sheet.title] = self._parse_sheet(sheet, parse_formulas=parse_formulas)
        return data

    def parse_sheet(self, sheet: Any) -> list[dict[str, Any]]:
        """Parse a single worksheet.

        Args:
            sheet: An openpyxl Worksheet object.

        Returns:
            List of row dictionaries.
        """
        return self._parse_sheet(sheet)

    def _parse_sheet(self, sheet: Any, parse_formulas: bool = False) -> list[dict[str, Any]]:
        """Internal sheet parsing implementation.
        
        Args:
            sheet: An openpyxl Worksheet object.
            parse_formulas: If True, extract formulas instead of values.
        """
        if parse_formulas:
            # For formulas, we need to iterate cells and get .value which contains the formula
            # when data_only=False
            rows = []
            for row in sheet.iter_rows():
                row_values = []
                for cell in row:
                    # Get formula if present, otherwise get value
                    if cell.data_type == 'f':  # 'f' means formula
                        row_values.append(cell.value)  # This will be the formula string
                    else:
                        row_values.append(cell.value)
                rows.append(tuple(row_values))
        else:
            rows = list(sheet.iter_rows(values_only=True))
        
        if not rows:
            return []

        header_index = max(self.header_row_index - 1, 0)
        if header_index >= len(rows):
            return []

        headers = self._normalize_headers(rows[header_index])
        payload_rows = rows[header_index + 1:]

        parsed_rows: list[dict[str, Any]] = []
        for raw in payload_rows:
            # Check for blank row if stop_at_blank_row is enabled
            if self.stop_at_blank_row and self._is_blank_row(raw):
                break

            row_dict = {
                headers[idx]: raw[idx] if idx < len(raw) else None
                for idx in range(len(headers))
            }
            parsed_rows.append(row_dict)
        return parsed_rows

    def get_headers(self, sheet: Any) -> list[str]:
        """Extract and normalize headers from a sheet.

        Args:
            sheet: An openpyxl Worksheet object.

        Returns:
            List of normalized header strings.
        """
        rows = list(sheet.iter_rows(values_only=True, max_row=self.header_row_index))
        if not rows:
            return []
        header_index = max(self.header_row_index - 1, 0)
        if header_index >= len(rows):
            return []
        return self._normalize_headers(rows[header_index])

    @staticmethod
    def _normalize_headers(header_row: Sequence[Any]) -> list[str]:
        """Normalize header values to strings.

        Args:
            header_row: Sequence of header cell values.

        Returns:
            List of normalized header strings.
        """
        return [
            str(value).strip() if value is not None else f"column_{idx}"
            for idx, value in enumerate(header_row)
        ]

    @staticmethod
    def _is_blank_row(row: Sequence[Any]) -> bool:
        """Check if a row is completely blank.

        Args:
            row: Sequence of cell values.

        Returns:
            True if all cells are None or empty strings.
        """
        for cell in row:
            if cell is not None:
                if isinstance(cell, str) and cell.strip():
                    return False
                elif not isinstance(cell, str):
                    return False
        return True

    @staticmethod
    def is_excel_error(value: Any) -> bool:
        """Check if a cell value is an Excel error.

        Args:
            value: Cell value.

        Returns:
            True if value is an Excel error token.
        """
        if not isinstance(value, str):
            return False
        return value.strip().upper() in EXCEL_ERROR_TOKENS

    def find_column_index(self, sheet: Any, header_name: str) -> int | None:
        """Find the 1-based column index for a given header name.

        Args:
            sheet: An openpyxl Worksheet object.
            header_name: Name of the header to find.

        Returns:
            1-based column index, or None if not found.
        """
        headers = self.get_headers(sheet)
        for idx, header in enumerate(headers):
            if header == header_name:
                return idx + 1
        return None

    def get_cell_value(
        self,
        sheet: Any,
        row: int,
        column: int | str,
    ) -> Any:
        """Get a cell value from a worksheet.

        Args:
            sheet: An openpyxl Worksheet object.
            row: 1-based row index.
            column: 1-based column index or column letter.

        Returns:
            Cell value.
        """
        try:
            return sheet.cell(row=row, column=column).value
        except Exception:
            return None

    def get_cell_by_header(
        self,
        sheet: Any,
        row: int,
        header_name: str,
    ) -> Any:
        """Get a cell value by header name.

        Args:
            sheet: An openpyxl Worksheet object.
            row: 1-based row index (Excel row number).
            header_name: Name of the column header.

        Returns:
            Cell value, or None if not found.
        """
        col_idx = self.find_column_index(sheet, header_name)
        if col_idx is None:
            return None
        return self.get_cell_value(sheet, row, col_idx)
