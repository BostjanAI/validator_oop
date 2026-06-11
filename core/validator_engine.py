"""High-level validation orchestrator.

This module provides the main entry point for validating Excel workbooks.
"""

from __future__ import annotations

import logging
from pathlib import Path

from validator_oop.core.constants import REQUIRED_COLUMNS
from validator_oop.core.report import ValidationReport
from validator_oop.excel.excel_loader import ExcelLoader, LoadedWorkbook

try:
    from validator_oop.excel.sop_loader import SOPData
except ImportError:
    SOPData = None  # type: ignore

from validator_oop.excel.catalog_loader import (
    CatalogData,
    build_catalog_validation_summary,
    load_catalogs,
)

from .rule_engine import RuleEngine


class ValidatorEngine:
    """High-level orchestrator that wires the Excel loader to the rule engine.

    This class provides the main entry point for validating Excel workbooks.
    It coordinates loading the workbook, executing rules, and generating reports.
    """

    def __init__(
        self,
        rule_engine: RuleEngine,
        excel_loader: ExcelLoader,
        *,
        logger: logging.Logger | None = None,
        include_formulas: bool = False,
        sop_data: SOPData | None = None,
        catalog_data: dict[str, CatalogData] | None = None,
        catalog_paths: dict[str, str] | None = None,
    ) -> None:
        """Initialize the validator engine.

        Args:
            rule_engine: Engine for executing validation rules.
            excel_loader: Loader for reading Excel files.
            logger: Logger instance for debugging.
            include_formulas: If True, load cell formulas for formula validation.
            sop_data: Optional SOP data for compliance validation.
            catalog_data: Optional catalog data for code validation.
            catalog_paths: Optional paths to catalog files (raztopina, kemikalija keys).
        """
        self._rule_engine = rule_engine
        self._excel_loader = excel_loader
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._include_formulas = include_formulas
        self._sop_data = sop_data
        self._catalog_data = catalog_data
        self._catalog_paths = catalog_paths or {}
        
        # Pass sop_data to rule_engine via rule_dependencies
        if sop_data is not None:
            self._rule_engine._rule_dependencies["sop_data"] = sop_data

        # Pass catalog_data to rule_engine via rule_dependencies
        if catalog_data is not None:
            self._rule_engine._rule_dependencies["catalog_data"] = catalog_data

    def validate(self, workbook_path: str | Path) -> ValidationReport:
        """Load the workbook, execute rules, and return a detailed report.

        Args:
            workbook_path: Path to the Excel file to validate.

        Returns:
            ValidationReport containing all validation errors and metadata.
        """
        resolved_path = Path(workbook_path).expanduser().resolve()
        self._logger.info("Validating workbook %s", resolved_path)

        # Load workbook
        loaded = self._excel_loader.load(
            resolved_path,
            include_formulas=self._include_formulas,
        )

        # Filter sheets: only validate sheets that have at least one REQUIRED_COLUMN
        # This matches the behavior of MES_validator.py
        filtered_values, filtered_headers = self._filter_sheets_by_required_columns(
            loaded.values, loaded.headers
        )

        # Run validation on filtered sheets only
        # Pass original data in extra for SOP compliance rule
        errors = self._rule_engine.run(
            filtered_values,
            workbook_name=resolved_path.name,
            sheet_headers=filtered_headers,
            workbook_values=loaded.raw_workbook_values if self._include_formulas else None,
            workbook_formulas=loaded.raw_workbook_formulas if self._include_formulas else None,
            parsed_formulas=loaded.formulas if self._include_formulas else None,
            all_workbook_data=loaded.values,  # Add original unfiltered data
            all_workbook_headers=loaded.headers,  # Add original unfiltered headers
        )

        # Metadata reflects validated sheets when available; otherwise fallback to original
        meta_sheets = filtered_values if filtered_values else loaded.values
        meta_sheet_names = (
            [sheet for sheet in loaded.sheet_names if sheet in filtered_values]
            if filtered_values
            else loaded.sheet_names
        )

        # Build report
        report = ValidationReport(source_path=resolved_path)
        report.extend(errors)
        report.metadata["sheets"] = {
            sheet: len(rows) for sheet, rows in meta_sheets.items()
        }
        report.metadata["row_offset"] = loaded.row_offset
        report.metadata["sheet_names"] = list(meta_sheet_names)
        self._attach_catalog_metadata(report, filtered_values, errors)

        return report

    def _attach_catalog_metadata(
        self,
        report: ValidationReport,
        filtered_values: dict[str, list[dict[str, object]]],
        errors: list,
    ) -> None:
        """Add catalog validation summary to report metadata when catalogs are loaded."""
        if not self._catalog_data:
            report.metadata["catalog_validation"] = {"enabled": False}
            return
        report.metadata["catalog_validation"] = build_catalog_validation_summary(
            filtered_values,
            self._catalog_data,
            errors,
            raztopine_path=self._catalog_paths.get("raztopina"),
            kemikalije_path=self._catalog_paths.get("kemikalija"),
        )

    def _filter_sheets_by_required_columns(
        self,
        values: dict[str, list[dict[str, object]]],
        headers: dict[str, list[str]],
    ) -> tuple[dict[str, list[dict[str, object]]], dict[str, list[str]]]:
        """Filter sheets to only include those with at least one REQUIRED_COLUMN.

        This matches the behavior of MES_validator.py, which only validates
        sheets that contain recipe data (have required columns like "št. Koraka",
        "Navodilo", etc.). Sheets like "Spremembe" or "Podatki" are skipped.

        Args:
            values: Dictionary mapping sheet names to row data.
            headers: Dictionary mapping sheet names to column headers.

        Returns:
            Tuple of (filtered_values, filtered_headers) containing only sheets
            with at least one REQUIRED_COLUMN.
        """
        filtered_values: dict[str, list[dict[str, object]]] = {}
        filtered_headers: dict[str, list[str]] = {}

        for sheet_name, rows in values.items():
            # Get columns for this sheet
            if sheet_name in headers:
                columns = set(headers[sheet_name])
            elif rows:
                # Fallback: get columns from first row
                columns = set(rows[0].keys()) if rows else set()
            else:
                columns = set()

            # Normalize column names (strip whitespace, like in MES_validator.py)
            columns_norm = {col.strip() if isinstance(col, str) else str(col) for col in columns}

            # Check if sheet has at least one REQUIRED_COLUMN
            # This matches: if any(c in cols_norm for c in REQUIRED_COLUMNS):
            has_required = any(col in columns_norm for col in REQUIRED_COLUMNS)

            if has_required:
                filtered_values[sheet_name] = rows
                if sheet_name in headers:
                    filtered_headers[sheet_name] = headers[sheet_name]
                self._logger.debug("Including sheet '%s' for validation", sheet_name)
            else:
                self._logger.debug(
                    "Skipping sheet '%s' - no required columns found (columns: %s)",
                    sheet_name,
                    sorted(columns_norm),
                )

        return filtered_values, filtered_headers

    def validate_loaded(self, loaded: LoadedWorkbook) -> ValidationReport:
        """Validate an already-loaded workbook.

        This is useful when you want to load the workbook once and validate
        multiple times, or when you need access to the raw workbook data.

        Args:
            loaded: LoadedWorkbook instance from ExcelLoader.

        Returns:
            ValidationReport containing all validation errors and metadata.
        """
        source_path = loaded.source_path or Path("unknown")
        self._logger.info("Validating loaded workbook %s", source_path)

        # Filter sheets: only validate sheets that have at least one REQUIRED_COLUMN
        # This matches the behavior of MES_validator.py
        filtered_values, filtered_headers = self._filter_sheets_by_required_columns(
            loaded.values, loaded.headers
        )

        # Run validation on filtered sheets only
        errors = self._rule_engine.run(
            filtered_values,
            workbook_name=source_path.name if loaded.source_path else None,
            sheet_headers=filtered_headers,
            workbook_values=loaded.raw_workbook_values if self._include_formulas else None,
            workbook_formulas=loaded.raw_workbook_formulas if self._include_formulas else None,
            parsed_formulas=loaded.formulas if self._include_formulas else None,
        )

        meta_sheets = filtered_values if filtered_values else loaded.values
        meta_sheet_names = (
            [sheet for sheet in loaded.sheet_names if sheet in filtered_values]
            if filtered_values
            else loaded.sheet_names
        )

        # Build report
        report = ValidationReport(source_path=source_path)
        report.extend(errors)
        report.metadata["sheets"] = {
            sheet: len(rows) for sheet, rows in meta_sheets.items()
        }
        report.metadata["row_offset"] = loaded.row_offset
        report.metadata["sheet_names"] = list(meta_sheet_names)
        self._attach_catalog_metadata(report, filtered_values, errors)

        return report
