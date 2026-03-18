"""Tests for ExcelLoader and WorkbookParser.

This module tests Excel file loading and parsing functionality.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from validator_oop.excel.excel_loader import ExcelLoader, LoadedWorkbook
from validator_oop.excel.workbook_parser import WorkbookParser


class TestLoadedWorkbook:
    """Tests for LoadedWorkbook dataclass."""

    def test_get_sheet_data(self) -> None:
        """Test get_sheet_data method."""
        loaded = LoadedWorkbook(
            values={
                "Sheet1": [{"col": "val1"}, {"col": "val2"}],
                "Sheet2": [{"col": "val3"}],
            },
            sheet_names=["Sheet1", "Sheet2"],
            row_offset=2,
        )

        assert loaded.get_sheet_data("Sheet1") == [{"col": "val1"}, {"col": "val2"}]
        assert loaded.get_sheet_data("Sheet2") == [{"col": "val3"}]
        assert loaded.get_sheet_data("NonExistent") == []

    def test_get_sheet_formulas(self) -> None:
        """Test get_sheet_formulas method."""
        loaded = LoadedWorkbook(
            values={"Sheet1": [{"col": "val"}]},
            formulas={"Sheet1": [{"col": "=A1+B1"}]},
            sheet_names=["Sheet1"],
            row_offset=2,
        )

        assert loaded.get_sheet_formulas("Sheet1") == [{"col": "=A1+B1"}]

    def test_get_sheet_formulas_none(self) -> None:
        """Test get_sheet_formulas when formulas not loaded."""
        loaded = LoadedWorkbook(
            values={"Sheet1": [{"col": "val"}]},
            formulas=None,
            sheet_names=["Sheet1"],
            row_offset=2,
        )

        assert loaded.get_sheet_formulas("Sheet1") is None

    def test_get_headers(self) -> None:
        """Test get_headers method."""
        loaded = LoadedWorkbook(
            values={"Sheet1": [{"col1": "val", "col2": "val"}]},
            headers={"Sheet1": ["col1", "col2"]},
            sheet_names=["Sheet1"],
            row_offset=2,
        )

        assert loaded.get_headers("Sheet1") == ["col1", "col2"]
        assert loaded.get_headers("NonExistent") == []

    def test_close(self) -> None:
        """Test close method."""
        mock_wb_values = MagicMock()
        mock_wb_formulas = MagicMock()

        loaded = LoadedWorkbook(
            values={"Sheet1": []},
            sheet_names=["Sheet1"],
            row_offset=2,
            raw_workbook_values=mock_wb_values,
            raw_workbook_formulas=mock_wb_formulas,
        )

        loaded.close()

        mock_wb_values.close.assert_called_once()
        mock_wb_formulas.close.assert_called_once()


class TestWorkbookParser:
    """Tests for WorkbookParser."""

    @pytest.fixture
    def parser(self) -> WorkbookParser:
        """Create a WorkbookParser with default settings."""
        return WorkbookParser(header_row_index=1)

    def test_normalize_headers(self, parser: WorkbookParser) -> None:
        """Test header normalization."""
        headers = parser._normalize_headers(["Col1", "  Col2  ", None, "Col4"])

        assert headers == ["Col1", "Col2", "column_2", "Col4"]

    def test_normalize_headers_empty(self, parser: WorkbookParser) -> None:
        """Test header normalization with empty input."""
        headers = parser._normalize_headers([])

        assert headers == []

    def test_is_blank_row(self, parser: WorkbookParser) -> None:
        """Test blank row detection."""
        assert parser._is_blank_row([None, None, None]) is True
        assert parser._is_blank_row(["", "", ""]) is True
        assert parser._is_blank_row(["", "  ", ""]) is True
        assert parser._is_blank_row([None, "value", None]) is False
        assert parser._is_blank_row([1, None, None]) is False

    def test_is_excel_error(self, parser: WorkbookParser) -> None:
        """Test Excel error detection."""
        assert parser.is_excel_error("#REF!") is True
        assert parser.is_excel_error("#N/A") is True
        assert parser.is_excel_error("#VALUE!") is True
        assert parser.is_excel_error("#DIV/0!") is True
        assert parser.is_excel_error("#NAME?") is True
        assert parser.is_excel_error("#NULL!") is True
        assert parser.is_excel_error("#NUM!") is True
        assert parser.is_excel_error("  #REF!  ") is True
        assert parser.is_excel_error("normal value") is False
        assert parser.is_excel_error(123) is False
        assert parser.is_excel_error(None) is False


class TestExcelLoader:
    """Tests for ExcelLoader."""

    @pytest.fixture
    def loader(self) -> ExcelLoader:
        """Create an ExcelLoader with default settings."""
        return ExcelLoader()

    def test_init_with_custom_parser(self) -> None:
        """Test initialization with custom parser."""
        custom_parser = WorkbookParser(header_row_index=3)
        loader = ExcelLoader(parser=custom_parser)

        assert loader._parser.header_row_index == 3

    def test_init_with_header_row_index(self) -> None:
        """Test initialization with header_row_index."""
        loader = ExcelLoader(header_row_index=5)

        assert loader._parser.header_row_index == 5

    def test_load_file_not_found(self, loader: ExcelLoader) -> None:
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent_file.xlsx")

    @patch("validator_oop.excel.excel_loader._load_workbook")
    def test_load_basic(self, mock_load_workbook: MagicMock, loader: ExcelLoader, tmp_path: Path) -> None:
        """Test basic workbook loading."""
        # Create a temporary file
        test_file = tmp_path / "test.xlsx"
        test_file.touch()

        # Mock the workbook
        mock_sheet = MagicMock()
        mock_sheet.title = "Sheet1"
        mock_sheet.iter_rows.return_value = [
            ("Col1", "Col2"),  # Header row
            ("val1", "val2"),  # Data row
        ]

        mock_wb = MagicMock()
        mock_wb.worksheets = [mock_sheet]
        mock_load_workbook.return_value = mock_wb

        result = loader.load(test_file)

        assert isinstance(result, LoadedWorkbook)
        assert "Sheet1" in result.values
        assert result.sheet_names == ["Sheet1"]
        assert result.row_offset == 2
        assert result.source_path == test_file.resolve()

    @patch("validator_oop.excel.excel_loader._load_workbook")
    def test_load_with_formulas(self, mock_load_workbook: MagicMock, loader: ExcelLoader, tmp_path: Path) -> None:
        """Test loading with formulas enabled."""
        test_file = tmp_path / "test.xlsx"
        test_file.touch()

        def make_cell(value: object, data_type: str) -> MagicMock:
            cell = MagicMock()
            cell.value = value
            cell.data_type = data_type
            return cell

        mock_sheet = MagicMock()
        mock_sheet.title = "Sheet1"
        header_cell = make_cell("Col1", "s")
        formula_cell = make_cell("=A1", "f")

        def iter_rows(*args, **kwargs):
            # When parsing values, WorkbookParser calls iter_rows(values_only=True)
            if kwargs.get("values_only"):
                return [
                    ("Col1",),
                    ("val1",),
                ]
            # When parsing formulas, WorkbookParser calls iter_rows() and inspects cell.data_type
            return [
                (header_cell,),
                (formula_cell,),
            ]

        mock_sheet.iter_rows.side_effect = iter_rows

        mock_wb = MagicMock()
        mock_wb.worksheets = [mock_sheet]
        mock_load_workbook.return_value = mock_wb

        result = loader.load(test_file, include_formulas=True)

        assert result.formulas is not None
        # Should have called load_workbook twice (values and formulas)
        assert mock_load_workbook.call_count == 2

    @patch("validator_oop.excel.excel_loader._load_workbook")
    def test_load_simple(self, mock_load_workbook: MagicMock, loader: ExcelLoader, tmp_path: Path) -> None:
        """Test load_simple convenience method."""
        test_file = tmp_path / "test.xlsx"
        test_file.touch()

        mock_sheet = MagicMock()
        mock_sheet.title = "Sheet1"
        mock_sheet.iter_rows.return_value = [
            ("Col1",),
            ("val1",),
        ]

        mock_wb = MagicMock()
        mock_wb.worksheets = [mock_sheet]
        mock_load_workbook.return_value = mock_wb

        result = loader.load_simple(test_file)

        assert isinstance(result, dict)
        assert "Sheet1" in result

    @patch("validator_oop.excel.excel_loader._load_workbook", None)
    def test_load_without_openpyxl(self, loader: ExcelLoader, tmp_path: Path) -> None:
        """Test that loading without openpyxl raises error."""
        test_file = tmp_path / "test.xlsx"
        test_file.touch()

        with pytest.raises(RuntimeError, match="openpyxl"):
            loader.load(test_file)


class TestReportWriter:
    """Tests for ReportWriter."""

    def test_write_text_report(self, tmp_path: Path) -> None:
        """Test writing text report."""
        from validator_oop.excel.report_writer import ReportWriter

        writer = ReportWriter()
        report_path = tmp_path / "report.txt"

        issues = [
            {"sheet": "Sheet1", "row": 2, "col": "A", "code": "TEST", "message": "Test error"},
        ]

        writer.write_text_report(report_path, issues)

        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "Sheet1" in content
        assert "Test error" in content

    def test_write_text_report_empty(self, tmp_path: Path) -> None:
        """Test writing text report with no issues."""
        from validator_oop.excel.report_writer import ReportWriter

        writer = ReportWriter()
        report_path = tmp_path / "report.txt"

        writer.write_text_report(report_path, [])

        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "OK" in content

    def test_write_json_report(self, tmp_path: Path) -> None:
        """Test writing JSON report."""
        import json

        from validator_oop.excel.report_writer import ReportWriter

        writer = ReportWriter()
        report_path = tmp_path / "report.json"

        report_dict = {
            "source_path": "test.xlsx",
            "is_valid": False,
            "errors": [{"code": "TEST", "message": "Test error"}],
        }

        writer.write_json_report(report_path, report_dict)

        assert report_path.exists()
        with open(report_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["source_path"] == "test.xlsx"
        assert loaded["is_valid"] is False

