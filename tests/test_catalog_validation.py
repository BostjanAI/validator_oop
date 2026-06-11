"""Tests for catalog code validation and report metadata."""

from __future__ import annotations

from validator_oop.core.constants import translate_code
from validator_oop.core.error import Severity, ValidationError
from validator_oop.excel.catalog_loader import (
    CatalogData,
    build_catalog_validation_summary,
    format_catalog_summary_log_line,
    match_key,
)
from validator_oop.excel.report_writer import ReportWriter
from validator_oop.rules.builtin.catalog_code_rule import CatalogCodeRule
from validator_oop.utils.helpers import base_key_no_trailing_number, strip_instance_suffix


def test_match_key_instance_suffix():
    catalog = CatalogData(lookup={"gk": "GK-001"}, all_codes=["GK-001"])
    ok, code, method = match_key("GK1", catalog)
    assert ok
    assert code == "GK-001"
    assert method == "brez številk na koncu"


def test_strip_instance_suffix_gk_not_ph_or_h2so4():
    assert strip_instance_suffix("20mM-AP_50mM-NaCl-pH5.0-GK1") == "20mM-AP_50mM-NaCl-pH5.0-GK"
    assert strip_instance_suffix("20mM-AP_50mM-NaCl-pH5.0-GK10") == "20mM-AP_50mM-NaCl-pH5.0-GK"
    assert strip_instance_suffix("20mM-AP_50mM-NaCl-pH5.0") == "20mM-AP_50mM-NaCl-pH5.0"
    assert strip_instance_suffix("H2SO4") == "H2SO4"
    assert base_key_no_trailing_number("GK1") == "GK"


def test_catalog_code_rule_one_error_per_base():
    catalog_data = {
        "raztopina": CatalogData(lookup={"known": "SIF-1"}, all_codes=["SIF-1"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [
        {
            "Tip podatka": "raztopina",
            "Ključ preverjanja": "20mM-AP_50mM-NaCl-pH5.0-GK1",
            "št. Koraka": "1",
        },
        {
            "Tip podatka": "raztopina",
            "Ključ preverjanja": "20mM-AP_50mM-NaCl-pH5.0-GK2",
            "št. Koraka": "2",
        },
    ]
    errors = rule.run(rows, sheet_name="List1", workbook_name="test.xlsx")
    assert len(errors) == 1
    assert "pH5.0-GK" in errors[0].message


def test_catalog_code_rule_reports_mismatch():
    catalog_data = {
        "raztopina": CatalogData(lookup={"known": "SIF-1"}, all_codes=["SIF-1"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [
        {
            "Tip podatka": "raztopina",
            "Ključ preverjanja": "UNKNOWN_X",
            "št. Koraka": "1",
        },
    ]
    errors = rule.run(rows, sheet_name="List1", workbook_name="test.xlsx")
    assert len(errors) == 1
    assert errors[0].code == "CATALOG_CODE_MISMATCH"
    assert "UNKNOWN_X" in errors[0].message


def test_build_catalog_validation_summary():
    catalog_data = {"raztopina": CatalogData(lookup={"a": "A"}, all_codes=["A"])}
    workbook = {
        "S1": [
            {"Tip podatka": "raztopina", "Ključ preverjanja": "a"},
            {"Tip podatka": "raztopina", "Ključ preverjanja": "missing"},
        ],
    }
    errors = [
        ValidationError(
            rule_name="catalog_code_rule",
            message="Šifra 'missing' (tip: raztopina) ni najdena v šifrantu.",
            code="CATALOG_CODE_MISMATCH",
            severity=Severity.ERROR,
            sheet="S1",
            row_index=3,
            column="Ključ preverjanja",
        ),
    ]
    summary = build_catalog_validation_summary(
        workbook,
        catalog_data,
        errors,
        raztopine_path="/tmp/razt.xlsx",
    )
    assert summary["enabled"] is True
    assert summary["rows_checked_raztopina"] == 2
    assert summary["mismatches"] == 1
    assert summary["status"] == "napake"
    assert "razt.xlsx" in summary["raztopine_path"]


def test_translate_catalog_code():
    assert "šifrant" in translate_code("CATALOG_CODE_MISMATCH").lower()


def test_report_writer_catalog_sheet(tmp_path):
    issues = [
        {
            "sheet": "f:S1",
            "row": 5,
            "col": "Ključ preverjanja",
            "code": "CATALOG_CODE_MISMATCH",
            "message": "Šifra 'X' ni najdena.",
            "severity": "ERROR",
        },
    ]
    summary = {
        "enabled": True,
        "raztopine_path": "razt.xlsx",
        "kemikalije_path": "",
        "catalog_codes_raztopina": 10,
        "catalog_codes_kemikalija": 0,
        "rows_checked_raztopina": 3,
        "rows_checked_kemikalija": 0,
        "rows_checked_total": 3,
        "mismatches": 1,
        "status": "napake",
    }
    out = tmp_path / "report.xlsx"
    ReportWriter().write_excel_report(out, issues, catalog_summary=summary)
    from openpyxl import load_workbook

    wb = load_workbook(out, read_only=True)
    assert "Šifranti" in wb.sheetnames
    pov = wb["Povzetek"]
    assert pov["A1"].value == "Validator IPO Receptur"
    assert pov["A2"].value == "Preverjanje šifrantov"
    assert pov["B2"].value == "Da"
    wb.close()
    line = format_catalog_summary_log_line(summary)
    assert "napak šifer: 1" in line
