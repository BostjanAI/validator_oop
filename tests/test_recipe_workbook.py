"""Tests for recipe workbook detection."""

from __future__ import annotations

from validator_oop.excel.recipe_workbook import (
    sheet_has_any_required_column,
    sheet_has_required_columns,
)
from validator_oop.core.constants import REQUIRED_COLUMNS


class TestSheetHasRequiredColumns:
    def test_empty_headers(self) -> None:
        assert sheet_has_required_columns([]) is False

    def test_partial_recipe_headers(self) -> None:
        assert sheet_has_required_columns(["št. Koraka", "Navodilo"]) is False

    def test_unrelated_headers(self) -> None:
        assert sheet_has_required_columns(["Datum", "Število napak", "Koda"]) is False

    def test_all_required_columns(self) -> None:
        assert sheet_has_required_columns(REQUIRED_COLUMNS) is True

    def test_whitespace_in_headers_is_ignored(self) -> None:
        assert sheet_has_required_columns([f" {col} " for col in REQUIRED_COLUMNS]) is True


class TestSheetHasAnyRequiredColumn:
    def test_empty_headers(self) -> None:
        assert sheet_has_any_required_column([]) is False

    def test_unrelated_headers(self) -> None:
        assert sheet_has_any_required_column(["Datum", "Število napak", "Koda"]) is False

    def test_partial_recipe_headers(self) -> None:
        assert sheet_has_any_required_column(["št. Koraka", "Navodilo"]) is True

    def test_single_recipe_header(self) -> None:
        assert sheet_has_any_required_column(["Kontrola 4"]) is True
