"""Excel report writing utilities.

This module handles writing validation reports to Excel and text files.
"""

from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Mapping, Sequence

from validator_oop.core.constants import translate_code, VERSION_REPORT

try:  # pragma: no cover - optional dependency
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Protection
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.protection import SheetProtection

    _OPENPYXL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OPENPYXL_AVAILABLE = False


def _auto_fit_columns(ws: Any) -> None:
    """Auto-fit column widths based on content.

    Args:
        ws: openpyxl Worksheet object.
    """
    max_col = ws.max_column or 1
    for col_idx in range(1, max_col + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 0
        for cell in ws[col_letter]:
            val = "" if cell.value is None else str(cell.value)
            if len(val) > max_len:
                max_len = len(val)
        ws.column_dimensions[col_letter].width = min(60, max(12, max_len + 2))


def _protect_with_filters(ws: Any, header_row: int = 1) -> None:
    """Protect worksheet while allowing filter usage.

    Args:
        ws: openpyxl Worksheet object.
        header_row: Row number of the header row.
    """
    last_col = get_column_letter(ws.max_column or 1)
    last_row = ws.max_row or header_row
    ws.auto_filter.ref = f"A{header_row}:{last_col}{last_row}"

    for row in ws.iter_rows(min_row=1, max_row=last_row, min_col=1, max_col=ws.max_column):
        for cell in row:
            cell.protection = Protection(locked=False)

    prot = ws.protection
    if not isinstance(prot, SheetProtection):
        ws.protection = SheetProtection()
        prot = ws.protection
    prot.sheet = True
    try:
        prot.enable()
    except Exception:
        pass


class ReportWriter:
    """Writes validation reports to Excel and text files."""

    @staticmethod
    def _catalog_info_rows(catalog_summary: Mapping[str, Any]) -> list[tuple[str, str]]:
        """Rows for catalog block on Povzetek sheet."""
        if not catalog_summary.get("enabled"):
            return [
                ("Preverjanje šifrantov", "Ni izvedeno"),
            ]
        rows = [
            ("Preverjanje šifrantov", "Da"),
            ("Šifrant raztopin", catalog_summary.get("raztopine_path") or "—"),
            ("Šifrant kemikalij", catalog_summary.get("kemikalije_path") or "—"),
            ("Šifrant repro materiala", catalog_summary.get("repro_path") or "—"),
            (
                "Šifer v katalogu (raztopina / kemikalija / repro)",
                f"{catalog_summary.get('catalog_codes_raztopina', 0)} / "
                f"{catalog_summary.get('catalog_codes_kemikalija', 0)} / "
                f"{catalog_summary.get('catalog_codes_repro', 0)}",
            ),
            (
                "Pregledanih vrstic (raztopina / kemikalija / repro)",
                f"{catalog_summary.get('rows_checked_raztopina', 0)} / "
                f"{catalog_summary.get('rows_checked_kemikalija', 0)} / "
                f"{catalog_summary.get('rows_checked_repro', 0)}",
            ),
            ("Napak šifer (CATALOG_CODE_MISMATCH)", catalog_summary.get("mismatches", 0)),
            ("Status šifrantov", catalog_summary.get("status", "")),
        ]
        return rows

    @staticmethod
    def _write_catalog_sheet(
        wb: Any,
        catalog_summary: Mapping[str, Any],
        issues: Sequence[Mapping[str, Any]],
    ) -> None:
        """Dedicated sheet for catalog validation summary and šifra errors."""
        ws = wb.create_sheet(title="Šifranti")
        ws.append(["Parameter", "Vrednost"])
        for label, value in ReportWriter._catalog_info_rows(catalog_summary):
            ws.append([label, value])
        ws.append([])
        ws.append(["Napake šifrantov (samo CATALOG_CODE_MISMATCH)"])
        ws.append(["List", "Vrstica", "Stolpec", "Ključ / opis"])
        catalog_issues = [
            i for i in issues if (i.get("code") or "") == "CATALOG_CODE_MISMATCH"
        ]
        if not catalog_issues:
            ws.append(["—", "—", "—", "Ni napak šifrantov"])
        else:
            for issue in catalog_issues:
                ws.append([
                    issue.get("sheet", ""),
                    issue.get("row", ""),
                    issue.get("col", ""),
                    issue.get("message", ""),
                ])
        _auto_fit_columns(ws)

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        """Initialize the report writer.

        Args:
            logger: Logger instance for debugging.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def write_excel_report(
        self,
        report_path: str | Path,
        issues: Sequence[Mapping[str, Any]],
        *,
        catalog_summary: Mapping[str, Any] | None = None,
    ) -> None:
        """Write validation issues to an Excel report.

        Args:
            report_path: Path to the output Excel file.
            issues: List of issue dictionaries.
            catalog_summary: Optional metadata from catalog validation (Šifranti).

        Raises:
            RuntimeError: If openpyxl is not installed.
        """
        if not _OPENPYXL_AVAILABLE:
            raise RuntimeError(
                "openpyxl is required to write Excel reports. "
                "Install with: pip install openpyxl"
            )

        resolved_path = Path(report_path)
        self._logger.info("Writing Excel report to %s", resolved_path)
        now = datetime.now()
        report_date = now.strftime("%d. %m. %Y")
        report_datetime = now.strftime("%d. %m. %Y %H:%M")

        wb = Workbook()

        # 1) Main sheet with error list
        ws = wb.active
        ws.title = "Povzetek"
        # Verzija aplikacije na vrhu poročila
        ws.cell(row=1, column=1, value="Validator IPO Receptur")
        ws.cell(row=1, column=2, value=VERSION_REPORT)

        if catalog_summary is not None:
            info_rows = self._catalog_info_rows(catalog_summary)
            for i, (label, value) in enumerate(info_rows):
                r = 2 + i
                ws.cell(row=r, column=1, value=label)
                ws.cell(row=r, column=2, value=value)
            header_row = 2 + len(info_rows) + 1
        else:
            header_row = 2

        headers = ["Datum in ura", "List", "Vrstica", "Stolpec", "Napaka", "Opis napake"]
        for j, h in enumerate(headers, start=1):
            ws.cell(row=header_row, column=j, value=h)

        data_start = header_row + 1
        if not issues:
            ws.cell(row=data_start, column=1, value=report_datetime)
            ws.cell(row=data_start, column=5, value="OK")
            ws.cell(row=data_start, column=6, value="Ni najdenih strukturnih napak.")
        else:
            r = data_start
            for issue in issues:
                ws.cell(row=r, column=1, value=report_datetime)
                ws.cell(row=r, column=2, value=issue.get("sheet", ""))
                ws.cell(row=r, column=3, value=issue.get("row", ""))
                ws.cell(row=r, column=4, value=issue.get("col", ""))
                ws.cell(row=r, column=5, value=translate_code(issue.get("code", "")))
                ws.cell(row=r, column=6, value=issue.get("message", ""))
                r += 1

        _auto_fit_columns(ws)
        last_col = get_column_letter(ws.max_column or 1)
        last_row = ws.max_row or header_row
        ws.auto_filter.ref = f"A{header_row}:{last_col}{last_row}"

        # 2) Sheet with error counts by code
        ws2 = wb.create_sheet(title="Število napak")
        ws2_headers = ["Koda", "Opis", "Število"]
        for j, h in enumerate(ws2_headers, start=1):
            ws2.cell(row=1, column=j, value=h)

        if issues:
            # Count occurrences by code
            counts: dict[str, int] = {}
            for issue in issues:
                code = issue.get("code") or ""
                if not code:
                    continue
                counts[code] = counts.get(code, 0) + 1

            total = sum(counts.values())
            r2 = 2
            for code in sorted(counts.keys()):
                ws2.cell(row=r2, column=1, value=code)
                ws2.cell(row=r2, column=2, value=translate_code(code))
                ws2.cell(row=r2, column=3, value=counts[code])
                r2 += 1

            # SUM row
            ws2.cell(row=r2, column=2, value="SKUPAJ")
            ws2.cell(row=r2, column=3, value=total)

        _auto_fit_columns(ws2)
        last_col2 = get_column_letter(ws2.max_column or 1)
        # Auto-filter only over data rows (exclude SUM row)
        filter_last_row = (ws2.max_row - 1) if issues else (ws2.max_row or 1)
        ws2.auto_filter.ref = f"A1:{last_col2}{filter_last_row}"

        # 3) Sheet with error counts grouped by sheet name
        ws3 = wb.create_sheet(title="Po listih")
        ws3_headers = ["List", "Število napak"]
        for j, h in enumerate(ws3_headers, start=1):
            ws3.cell(row=1, column=j, value=h)

        if issues:
            sheet_counts: dict[str, int] = {}
            for issue in issues:
                sheet_name = issue.get("sheet") or "(neznano)"
                sheet_counts[sheet_name] = sheet_counts.get(sheet_name, 0) + 1

            r3 = 2
            for sheet_name in sorted(sheet_counts.keys()):
                ws3.cell(row=r3, column=1, value=sheet_name)
                ws3.cell(row=r3, column=2, value=sheet_counts[sheet_name])
                r3 += 1

            # SUM row
            ws3.cell(row=r3, column=1, value="SKUPAJ")
            ws3.cell(row=r3, column=2, value=sum(sheet_counts.values()))

        _auto_fit_columns(ws3)
        last_col3 = get_column_letter(ws3.max_column or 1)
        filter_last_row3 = (ws3.max_row - 1) if issues else (ws3.max_row or 1)
        ws3.auto_filter.ref = f"A1:{last_col3}{filter_last_row3}"

        if catalog_summary is not None:
            self._write_catalog_sheet(wb, catalog_summary, issues)

        wb.save(resolved_path)
        try:
            wb.close()
        except Exception:
            pass

    def write_text_report(
        self,
        report_path: str | Path,
        issues: Sequence[Mapping[str, Any]],
        *,
        catalog_summary: Mapping[str, Any] | None = None,
    ) -> None:
        """Write validation issues to a text report.

        Args:
            report_path: Path to the output text file.
            issues: List of issue dictionaries.
        """
        resolved_path = Path(report_path)
        self._logger.info("Writing text report to %s", resolved_path)

        lines: list[str] = []
        if catalog_summary is not None:
            lines.append("=== Preverjanje šifrantov ===")
            for label, value in self._catalog_info_rows(catalog_summary):
                lines.append(f"{label}: {value}")
            lines.append("")
        if not issues:
            lines.append("OK | Ni najdenih strukturnih napak.")
        else:
            for issue in issues:
                sheet = issue.get("sheet", "")
                row = issue.get("row", "")
                col = issue.get("col", "")
                code = translate_code(issue.get("code", ""))
                message = issue.get("message", "")
                lines.append(f"{sheet} | vrstica {row} | stolpec {col} | {code} – {message}")
        lines.append("")

        resolved_path.write_text("\n".join(lines), encoding="utf-8")

    def write_json_report(
        self,
        report_path: str | Path,
        report_dict: Mapping[str, Any],
    ) -> None:
        """Write validation report to a JSON file.

        Args:
            report_path: Path to the output JSON file.
            report_dict: Report dictionary from ValidationReport.to_dict().
        """
        import json

        resolved_path = Path(report_path)
        self._logger.info("Writing JSON report to %s", resolved_path)

        with open(resolved_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)


class WorkbookFixer:
    """Applies proposed fixes to Excel workbooks."""

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        """Initialize the workbook fixer.

        Args:
            logger: Logger instance for debugging.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def apply_fixes(
        self,
        input_path: str | Path,
        output_path: str | Path,
        issues: Sequence[Mapping[str, Any]],
    ) -> int:
        """Apply proposed fixes to a copy of the Excel workbook.

        Args:
            input_path: Path to the input Excel file.
            output_path: Path to the output Excel file.
            issues: List of issue dictionaries with fix information.

        Returns:
            Number of fixes applied.

        Raises:
            RuntimeError: If openpyxl is not installed.
        """
        if not _OPENPYXL_AVAILABLE:
            raise RuntimeError(
                "openpyxl is required to apply fixes. "
                "Install with: pip install openpyxl"
            )

        input_resolved = Path(input_path)
        output_resolved = Path(output_path)

        self._logger.info("Applying fixes from %s to %s", input_resolved, output_resolved)

        wb = load_workbook(input_resolved, data_only=False)
        applied = 0

        for issue in issues:
            sheet = issue.get("sheet")
            cell = issue.get("target_cell")
            value = issue.get("proposed_value")
            kind = issue.get("fix_kind")

            if not (sheet and cell and kind == "set_value" and value is not None):
                continue

            try:
                if sheet in wb.sheetnames:
                    ws = wb[sheet]
                    ws[cell].value = float(value)
                    applied += 1
                    self._logger.debug("Applied fix: %s!%s = %s", sheet, cell, value)
            except Exception as e:
                self._logger.warning("Failed to apply fix to %s!%s: %s", sheet, cell, e)
                continue

        wb.save(output_resolved)
        try:
            wb.close()
        except Exception:
            pass

        self._logger.info("Applied %d fixes", applied)
        return applied

