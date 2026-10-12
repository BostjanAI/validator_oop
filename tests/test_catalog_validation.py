"""Tests for catalog code validation and report metadata."""

from __future__ import annotations

from validator_oop.core.constants import translate_code
from validator_oop.core.error import Severity, ValidationError
from validator_oop.core.shared_context import SharedContext
from validator_oop.excel.catalog_loader import (
    CatalogData,
    build_catalog_validation_summary,
    extract_raztopina_catalog_code,
    extract_repro_catalog_code,
    format_catalog_summary_log_line,
    match_key,
)
from validator_oop.excel.report_writer import ReportWriter
from validator_oop.rules.builtin.catalog_code_rule import CatalogCodeRule
from validator_oop.utils.helpers import (
    base_key_no_trailing_number,
    parse_index_match_formula,
    strip_instance_suffix,
)


def _run_catalog_rule(rule: CatalogCodeRule, rows, *, sheet="List1"):
    return rule.run_workbook({sheet: rows}, workbook_name="test.xlsx")


def test_match_key_instance_suffix():
    catalog = CatalogData(lookup={"gk": "GK-001"}, all_codes=["GK-001"])
    ok, code, method = match_key("GK1", catalog)
    assert ok
    assert code == "GK-001"
    assert method == "brez številk na koncu"


def test_match_key_kemikalija_etoh_instance_suffix():
    catalog = CatalogData(lookup={"etoh": "EtOH"}, all_codes=["EtOH"])
    ok, code, method = match_key("EtOH1", catalog)
    assert ok
    assert code == "EtOH"
    assert method == "brez številk na koncu"
    ok_base, code_base, method_base = match_key("EtOH", catalog)
    assert ok_base
    assert code_base == "EtOH"
    assert method_base == "natančno"


def test_strip_instance_suffix_gk_not_ph_or_h2so4():
    assert strip_instance_suffix("20mM-AP_50mM-NaCl-pH5.0-GK1") == "20mM-AP_50mM-NaCl-pH5.0-GK"
    assert strip_instance_suffix("20mM-AP_50mM-NaCl-pH5.0-GK10") == "20mM-AP_50mM-NaCl-pH5.0-GK"
    assert strip_instance_suffix("20mM-AP_50mM-NaCl-pH5.0") == "20mM-AP_50mM-NaCl-pH5.0"
    assert strip_instance_suffix("H2SO4") == "H2SO4"
    assert base_key_no_trailing_number("GK1") == "GK"
    assert strip_instance_suffix("EtOH1") == "EtOH"
    assert strip_instance_suffix("EtOH") == "EtOH"
    assert strip_instance_suffix("NaCl2") == "NaCl"
    assert strip_instance_suffix("MeOH10") == "MeOH"


def _raztopina_row(
    param1: str,
    *,
    kljuc: str = "IGNORIRAN_KLJUC",
    korak: str = "1",
) -> dict[str, str]:
    return {
        "Tip podatka": "raztopina",
        "Ključ preverjanja": kljuc,
        "št. Koraka": korak,
        "Kontrola-1": "kontrolaUstreznostiRaztopine",
        "Kontrola-1: Par 1": param1,
    }


def test_catalog_code_rule_one_error_per_base():
    catalog_data = {
        "raztopina": CatalogData(lookup={"known": "SIF-1"}, all_codes=["SIF-1"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [
        _raztopina_row("20mM-AP_50mM-NaCl-pH5.0-GK1", korak="1"),
        _raztopina_row("20mM-AP_50mM-NaCl-pH5.0-GK2", korak="2"),
    ]
    errors = _run_catalog_rule(rule, rows)
    assert len(errors) == 1
    assert "pH5.0-GK" in errors[0].message
    assert errors[0].column == "Kontrola-1: Par 1"


def test_catalog_code_rule_kemikalija_etoh1_matches_etoh():
    catalog_data = {
        "kemikalija": CatalogData(lookup={"etoh": "EtOH"}, all_codes=["EtOH"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [
        {"Tip podatka": "kemikalija", "Ključ preverjanja": "EtOH1"},
        {"Tip podatka": "kemikalija", "Ključ preverjanja": "EtOH"},
    ]
    errors = _run_catalog_rule(rule, rows)
    assert errors == []


def test_catalog_code_rule_reports_mismatch():
    catalog_data = {
        "raztopina": CatalogData(lookup={"known": "SIF-1"}, all_codes=["SIF-1"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [_raztopina_row("UNKNOWN_X")]
    errors = _run_catalog_rule(rule, rows)
    assert len(errors) == 1
    assert errors[0].code == "CATALOG_CODE_MISMATCH"
    assert "UNKNOWN_X" in errors[0].message
    assert errors[0].column == "Kontrola-1: Par 1"


def test_extract_raztopina_catalog_code_from_param1():
    row = _raztopina_row("20mM-AP", kljuc="DRUGI_KLJUC")
    code, column = extract_raztopina_catalog_code(row)
    assert code == "20mM-AP"
    assert column == "Kontrola-1: Par 1"


def test_catalog_code_rule_raztopina_ignores_kljuc_preverjanja():
    catalog_data = {
        "raztopina": CatalogData(lookup={"known": "SIF-1"}, all_codes=["SIF-1"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [_raztopina_row("known", kljuc="UNKNOWN_KEY")]
    errors = _run_catalog_rule(rule, rows)
    assert errors == []


def test_catalog_code_rule_raztopina_skips_without_ustrezost_param1():
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
    errors = _run_catalog_rule(rule, rows)
    assert errors == []


def test_build_catalog_validation_summary():
    catalog_data = {"raztopina": CatalogData(lookup={"a": "A"}, all_codes=["A"])}
    workbook = {
        "S1": [
            _raztopina_row("a", korak="1"),
            _raztopina_row("missing", korak="2"),
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
            column="Kontrola-1: Par 1",
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
    assert summary["rows_checked_repro"] == 0
    assert summary["mismatches"] == 1
    assert summary["status"] == "napake"
    assert "razt.xlsx" in summary["raztopine_path"]


def _repro_row(
    tip: str,
    param1: str,
    *,
    kljuc: str = "IGNORIRAN_KLJUC",
    korak: str = "1",
) -> dict[str, str]:
    return {
        "Tip podatka": tip,
        "Ključ preverjanja": kljuc,
        "št. Koraka": korak,
        "Kontrola-1": "kontrolaUstreznostiRepro",
        "Kontrola-1: Par 1": param1,
    }


def test_extract_repro_catalog_code_from_param1():
    row = _repro_row("repro", "TELO_SAMEC", kljuc="DRUGI_KLJUC")
    code, column = extract_repro_catalog_code(row)
    assert code == "TELO_SAMEC"
    assert column == "Kontrola-1: Par 1"


def test_catalog_code_rule_repro_mismatch():
    catalog_data = {
        "repro": CatalogData(lookup={"rm-100": "RM-100"}, all_codes=["RM-100"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [_repro_row("repro", "UNKNOWN_REPRO")]
    errors = _run_catalog_rule(rule, rows)
    assert len(errors) == 1
    assert errors[0].code == "CATALOG_CODE_MISMATCH"
    assert "UNKNOWN_REPRO" in errors[0].message
    assert "repro" in errors[0].message
    assert errors[0].column == "Kontrola-1: Par 1"


def test_catalog_code_rule_repro_match():
    catalog_data = {
        "repro": CatalogData(lookup={"rm-100": "RM-100"}, all_codes=["RM-100"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [
        _repro_row("repro", "RM-100", korak="1"),
        _repro_row("reproodpis", "RM-100", korak="2"),
    ]
    errors = _run_catalog_rule(rule, rows)
    assert errors == []


def test_catalog_code_rule_repro_ignores_kljuc_preverjanja():
    catalog_data = {
        "repro": CatalogData(lookup={"rm-100": "RM-100"}, all_codes=["RM-100"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [_repro_row("repro", "RM-100", kljuc="UNKNOWN_KEY")]
    errors = _run_catalog_rule(rule, rows)
    assert errors == []


def test_catalog_code_rule_repro_skips_without_ustrezost_param1():
    catalog_data = {
        "repro": CatalogData(lookup={"rm-100": "RM-100"}, all_codes=["RM-100"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [
        {
            "Tip podatka": "repro",
            "Ključ preverjanja": "UNKNOWN_REPRO",
            "št. Koraka": "1",
        },
    ]
    errors = _run_catalog_rule(rule, rows)
    assert errors == []


def test_catalog_code_rule_reproodpis_mismatch():
    catalog_data = {
        "repro": CatalogData(lookup={"rm-100": "RM-100"}, all_codes=["RM-100"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    rows = [_repro_row("reproodpis", "UNKNOWN_ODPIS")]
    errors = _run_catalog_rule(rule, rows)
    assert len(errors) == 1
    assert "UNKNOWN_ODPIS" in errors[0].message
    assert errors[0].column == "Kontrola-1: Par 1"


def test_load_catalog_repro_uses_material_sifra(tmp_path):
    from openpyxl import Workbook

    from validator_oop.excel.catalog_loader import COL_MATERIAL_SIFRA, load_catalogs

    path = tmp_path / "sifrant_repro.xlsx"
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append([COL_MATERIAL_SIFRA, "material_naziv"])
    ws.append(["TELO_SAMEC", "Telo samec"])
    ws.append(["TELO_SAMICA", "Telo samica"])
    wb.save(path)
    wb.close()

    catalogs = load_catalogs(repro_path=path)
    assert catalogs is not None
    repro = catalogs["repro"]
    assert "TELO_SAMEC" in repro.all_codes
    assert "TELO_SAMICA" in repro.all_codes
    ok, code, _method = match_key("TELO_SAMEC", repro)
    assert ok
    assert code == "TELO_SAMEC"
    ok_missing, _, _ = match_key("UNKNOWN_REPRO", repro)
    assert not ok_missing


def test_build_catalog_validation_summary_repro():
    catalog_data = {"repro": CatalogData(lookup={"rm-100": "RM-100"}, all_codes=["RM-100"])}
    workbook = {
        "S1": [
            _repro_row("repro", "RM-100", korak="1"),
            _repro_row("reproodpis", "RM-200", korak="2"),
        ],
    }
    summary = build_catalog_validation_summary(
        workbook,
        catalog_data,
        [],
        repro_path="/tmp/repro.xlsx",
    )
    assert summary["rows_checked_repro"] == 2
    assert summary["catalog_codes_repro"] == 1
    assert "repro.xlsx" in summary["repro_path"]
    assert summary["rows_checked_total"] == 2


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
        "repro_path": "repro.xlsx",
        "catalog_codes_raztopina": 10,
        "catalog_codes_kemikalija": 0,
        "catalog_codes_repro": 4,
        "rows_checked_raztopina": 3,
        "rows_checked_kemikalija": 0,
        "rows_checked_repro": 2,
        "rows_checked_total": 5,
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


INDEX_P1 = "=INDEX(Podatki!$A:$BY,MATCH($D$2,Podatki!$A:$A,0),60)"
INDEX_P1_SI = "=INDEX(Podatki!$A:$BY;MATCH($D$2;Podatki!$A:$A;0);60)"


def test_parse_index_match_formula_comma_and_semicolon():
    parsed = parse_index_match_formula(INDEX_P1)
    assert parsed == ("Podatki", 60, "$D$2")
    parsed_si = parse_index_match_formula(INDEX_P1_SI)
    assert parsed_si == ("Podatki", 60, "$D$2")
    quoted = parse_index_match_formula(
        "=INDEX('Podatki'!$A:$BZ,MATCH($A$2,Podatki!$A:$A,0),43)"
    )
    assert quoted == ("Podatki", 43, "$A$2")
    assert parse_index_match_formula("known") is None


def _podatki_headers(n: int = 60) -> list[str]:
    return [str(i) for i in range(1, n + 1)]


def _podatki_row(recipe: str, col: int, value: str, n: int = 60) -> dict[str, str]:
    row = {str(i): "" for i in range(1, n + 1)}
    row["1"] = recipe
    row[str(col)] = value
    return row


def test_catalog_code_rule_index_match_checks_all_podatki_rows():
    catalog_data = {
        "raztopina": CatalogData(lookup={"known": "SIF-1"}, all_codes=["SIF-1"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    recipe_rows = [_raztopina_row("known")]
    formula_rows = [_raztopina_row(INDEX_P1)]
    headers = _podatki_headers()
    podatki_rows = [
        _podatki_row("Receptura", 60, "Ključ 1"),
        _podatki_row("R-A-4", 60, "MISSING_A"),
        _podatki_row("R-A-8", 60, "known"),
        _podatki_row("R-A-80", 60, "MISSING_B"),
    ]
    shared = SharedContext()
    shared.extra["parsed_formulas"] = {"List1": formula_rows}
    shared.extra["all_workbook_data"] = {"List1": recipe_rows, "Podatki": podatki_rows}
    shared.extra["all_workbook_headers"] = {"List1": [], "Podatki": headers}
    rule.set_shared_context(shared)

    errors = rule.run_workbook({"List1": recipe_rows}, workbook_name="test.xlsx")
    missing = {err.message for err in errors}
    assert len(errors) == 2
    assert all(err.sheet == "Podatki" for err in errors)
    assert all(err.column == "60" for err in errors)
    assert any("MISSING_A" in msg for msg in missing)
    assert any("MISSING_B" in msg for msg in missing)
    assert errors[0].row_index == 3
    assert errors[1].row_index == 5


def test_catalog_code_rule_index_match_semicolon_podatki_column():
    catalog_data = {
        "raztopina": CatalogData(lookup={"known": "SIF-1"}, all_codes=["SIF-1"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    recipe_rows = [_raztopina_row("known")]
    formula_rows = [_raztopina_row(INDEX_P1_SI)]
    headers = _podatki_headers()
    podatki_rows = [
        _podatki_row("Receptura", 60, "Ključ 1"),
        _podatki_row("R-A-4", 60, "UNKNOWN_SI"),
    ]
    shared = SharedContext()
    shared.extra["parsed_formulas"] = {"List1": formula_rows}
    shared.extra["all_workbook_data"] = {"Podatki": podatki_rows}
    shared.extra["all_workbook_headers"] = {"Podatki": headers}
    rule.set_shared_context(shared)

    errors = rule.run_workbook({"List1": recipe_rows}, workbook_name="test.xlsx")
    assert len(errors) == 1
    assert errors[0].sheet == "Podatki"
    assert "UNKNOWN_SI" in errors[0].message


def test_catalog_code_rule_repro_index_match_checks_all_podatki_rows():
    catalog_data = {
        "repro": CatalogData(lookup={"rm-100": "RM-100"}, all_codes=["RM-100"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    recipe_rows = [_repro_row("repro", "RM-100")]
    formula_rows = [_repro_row("repro", INDEX_P1)]
    headers = _podatki_headers()
    podatki_rows = [
        _podatki_row("Receptura", 60, "Ključ 1"),
        _podatki_row("R-A-4", 60, "MISSING_REPRO_A"),
        _podatki_row("R-A-8", 60, "RM-100"),
        _podatki_row("R-A-80", 60, "MISSING_REPRO_B"),
    ]
    shared = SharedContext()
    shared.extra["parsed_formulas"] = {"List1": formula_rows}
    shared.extra["all_workbook_data"] = {"List1": recipe_rows, "Podatki": podatki_rows}
    shared.extra["all_workbook_headers"] = {"List1": [], "Podatki": headers}
    rule.set_shared_context(shared)

    errors = rule.run_workbook({"List1": recipe_rows}, workbook_name="test.xlsx")
    missing = {err.message for err in errors}
    assert len(errors) == 2
    assert all(err.sheet == "Podatki" for err in errors)
    assert all(err.column == "60" for err in errors)
    assert all("repro" in err.message for err in errors)
    assert any("MISSING_REPRO_A" in msg for msg in missing)
    assert any("MISSING_REPRO_B" in msg for msg in missing)


def test_catalog_code_rule_index_match_keeps_raztopina_and_repro_catalogs_apart():
    catalog_data = {
        "raztopina": CatalogData(lookup={"sol-ok": "SOL-OK"}, all_codes=["SOL-OK"]),
        "repro": CatalogData(lookup={"rm-ok": "RM-OK"}, all_codes=["RM-OK"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    razt_formula = "=INDEX(Podatki!$A:$BY,MATCH($D$2,Podatki!$A:$A,0),60)"
    repro_formula = "=INDEX(Podatki!$A:$BY,MATCH($D$2,Podatki!$A:$A,0),45)"
    recipe_rows = [
        _raztopina_row("sol-ok", korak="1"),
        _repro_row("repro", "rm-ok", korak="2"),
    ]
    formula_rows = [
        _raztopina_row(razt_formula, korak="1"),
        _repro_row("repro", repro_formula, korak="2"),
    ]
    headers = _podatki_headers()
    podatki_rows = [
        _podatki_row("Receptura", 60, "Ključ 1"),
        {**_podatki_row("R-A-4", 60, "sol-ok"), "45": "BAD-REPRO"},
    ]
    # Ensure column 45 header-name row is skipped via Receptura in col 1.
    shared = SharedContext()
    shared.extra["parsed_formulas"] = {"List1": formula_rows}
    shared.extra["all_workbook_data"] = {"Podatki": podatki_rows}
    shared.extra["all_workbook_headers"] = {"Podatki": headers}
    rule.set_shared_context(shared)

    errors = rule.run_workbook({"List1": recipe_rows}, workbook_name="test.xlsx")
    assert len(errors) == 1
    assert errors[0].sheet == "Podatki"
    assert errors[0].column == "45"
    assert "BAD-REPRO" in errors[0].message
    assert "repro" in errors[0].message


def test_catalog_code_rule_workbook_dedupes_across_sheets():
    catalog_data = {
        "kemikalija": CatalogData(lookup={"etoh": "EtOH"}, all_codes=["EtOH"]),
    }
    rule = CatalogCodeRule(catalog_data=catalog_data)
    errors = rule.run_workbook(
        {
            "S1": [{"Tip podatka": "kemikalija", "Ključ preverjanja": "UnknownChem1"}],
            "S2": [{"Tip podatka": "kemikalija", "Ključ preverjanja": "UnknownChem2"}],
        },
        workbook_name="test.xlsx",
    )
    assert len(errors) == 1
    assert "UnknownChem" in errors[0].message
