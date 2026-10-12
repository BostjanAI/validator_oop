"""Tests for GUI input file filtering helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from validator_oop.ui.input_files import (
    WorkbookFilterResult,
    filter_workbooks_with_required_columns,
    format_no_valid_workbooks_message,
    is_under_staro_folder,
    iter_excel_candidates_in_folders,
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


class TestIterExcelCandidatesSkipsStaro:
    def test_does_not_yield_files_inside_staro(self, tmp_path: Path) -> None:
        active = tmp_path / "aktivno"
        active.mkdir()
        (active / "receptura.xlsm").write_bytes(b"")
        (active / "receptura_staro.xlsx").write_bytes(b"")
        (active / "staro").mkdir()
        (active / "staro" / "arhiv.xlsm").write_bytes(b"")
        nested = active / "podmapa" / "STARO"
        nested.mkdir(parents=True)
        (nested / "arhiv2.xls").write_bytes(b"")
        (active / "podmapa" / "veljavna.xlsx").write_bytes(b"")

        found = list(iter_excel_candidates_in_folders([active]))

        assert sorted(p.name for p in found) == [
            "receptura.xlsm",
            "receptura_staro.xlsx",
            "veljavna.xlsx",
        ]

    def test_selected_staro_folder_yields_nothing(self, tmp_path: Path) -> None:
        staro = tmp_path / "Staro"
        staro.mkdir()
        (staro / "arhiv.xlsm").write_bytes(b"")
        logs: list[str] = []

        found = list(iter_excel_candidates_in_folders([staro], log=logs.append))

        assert found == []
        assert len(logs) == 1
        assert "Preskočena mapa 'staro'" in logs[0]


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
        assert dialog == "Nobena izbrana datoteka nima stolpcev recepture."
        assert "stolpcev recepture" in log_line

    def test_mixed_skip_reasons(self) -> None:
        result = WorkbookFilterResult(
            skipped_staro=[Path(r"P:\x\staro\a.xlsm")],
            skipped_no_columns=[Path(r"P:\x\b.xlsm")],
        )
        dialog, log_line = format_no_valid_workbooks_message(result)
        assert "mapi 'staro'" in dialog
        assert "brez stolpcev recepture" in dialog
        assert "1 v mapi 'staro'" in log_line


class TestFilterWorkbooksWithRequiredColumns:
    def test_manually_selected_staro_file_is_validated(self) -> None:
        loader = MagicMock()
        loader.has_required_columns.return_value = True
        path = Path(r"P:\projekt\staro\receptura.xlsm")

        result = filter_workbooks_with_required_columns([path], loader)

        assert result.valid == [path]
        assert result.skipped_staro == []
        loader.has_required_columns.assert_called_once_with(path)
