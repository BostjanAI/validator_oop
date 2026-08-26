"""Tests for GUI input file filtering helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from validator_oop.ui.input_files import (
    WorkbookFilterResult,
    filter_workbooks_with_required_columns,
    format_no_valid_workbooks_message,
    is_under_staro_folder,
)


class TestStaroFolderDetection:
    def test_detects_staro_in_path(self) -> None:
        path = Path(r"P:\projekt\7 RAZT_SET\staro\receptura.xlsm")
        assert is_under_staro_folder(path) is True

    def test_detects_staro_case_insensitive(self) -> None:
        path = Path(r"P:\projekt\Staro\receptura.xlsm")
        assert is_under_staro_folder(path) is True

    def test_ignores_staro_in_filename(self) -> None:
        path = Path(r"P:\projekt\receptura_staro.xlsm")
        assert is_under_staro_folder(path) is False


class TestFormatNoValidWorkbooksMessage:
    def test_staro_only_single_file(self) -> None:
        result = WorkbookFilterResult(
            skipped_staro=[Path(r"P:\x\staro\receptura.xlsm")],
        )
        dialog, log_line = format_no_valid_workbooks_message(result)
        assert "mapi 'staro'" in dialog
        assert "Validacija arhivskih datotek ni dovoljena" in dialog
        assert "validacija ni bila izvedena" in log_line

    def test_missing_columns_only(self) -> None:
        result = WorkbookFilterResult(
            skipped_no_columns=[Path(r"P:\x\receptura.xlsm")],
        )
        dialog, log_line = format_no_valid_workbooks_message(result)
        assert dialog == "Nobena izbrana datoteka nima zahtevanih stolpcev recepture."
        assert "zahtevanih stolpcev" in log_line

    def test_mixed_skip_reasons(self) -> None:
        result = WorkbookFilterResult(
            skipped_staro=[Path(r"P:\x\staro\a.xlsm")],
            skipped_no_columns=[Path(r"P:\x\b.xlsm")],
        )
        dialog, log_line = format_no_valid_workbooks_message(result)
        assert "mapi 'staro'" in dialog
        assert "brez zahtevanih stolpcev" in dialog
        assert "1 v mapi 'staro'" in log_line


class TestFilterWorkbooksWithRequiredColumns:
    def test_staro_file_is_skipped_without_column_check(self) -> None:
        loader = MagicMock()
        loader.has_required_columns.return_value = True

        result = filter_workbooks_with_required_columns(
            [Path(r"P:\projekt\staro\receptura.xlsm")],
            loader,
        )

        assert result.valid == []
        assert len(result.skipped_staro) == 1
        loader.has_required_columns.assert_not_called()
