"""Tests for PodatkiColumnUsageRule (stolpci zavihka Podatki brez INDEX/MATCH)."""

from __future__ import annotations

from validator_oop.core.error import Severity
from validator_oop.core.shared_context import SharedContext
from validator_oop.rules.builtin.podatki_usage_rule import (
    PodatkiColumnUsageRule,
    PodatkiUsage,
    collect_podatki_columns,
    number_to_letters,
)


def _f(col: int, rng: str = "$A:$BY") -> str:
    return f"=INDEX(Podatki!{rng},MATCH($D$2,Podatki!$A:$A,0),{col})"


def _usage(*formulas: str) -> PodatkiUsage:
    usage = PodatkiUsage()
    for formula in formulas:
        collect_podatki_columns(formula, usage)
    return usage


def test_number_to_letters():
    assert number_to_letters(1) == "A"
    assert number_to_letters(26) == "Z"
    assert number_to_letters(27) == "AA"
    assert number_to_letters(60) == "BH"


def test_index_match_marks_index_column_and_match_column_only():
    usage = _usage(_f(60))
    assert usage.columns == {1, 60}
    assert not usage.all_columns


def test_semicolon_and_quoted_sheet():
    usage = _usage("=INDEX('Podatki'!$A:$BZ;MATCH($A$2;Podatki!$A:$A;0);43)")
    assert usage.columns == {1, 43}


def test_index_range_starting_after_column_a_is_offset():
    usage = _usage("=INDEX(Podatki!$C:$F,MATCH($A$2,Podatki!$A:$A,0),2)")
    assert usage.columns == {1, 4}


def test_formula_with_multiple_index_calls():
    usage = _usage(f'=IF({_f(5)[1:]}="x",{_f(7)[1:]},"")')
    assert usage.columns == {1, 5, 7}


def test_vlookup_literal_column():
    usage = _usage("=VLOOKUP($A$2,Podatki!$A:$BY,9,0)")
    assert usage.columns == {9}


def test_direct_cell_reference():
    usage = _usage("=Podatki!E5")
    assert usage.columns == {5}


def test_dynamic_column_is_conservative():
    usage = _usage(
        '=INDEX(Podatki!$A:$BY,MATCH($A$2,Podatki!$A:$A,0),MATCH("Naziv",Podatki!$A$1:$BY$1,0))'
    )
    assert usage.columns >= {1, 2, 77}


def test_non_podatki_formula_ignored():
    usage = PodatkiUsage()
    assert not collect_podatki_columns("=INDEX(Drugo!$A:$B,MATCH(1,Drugo!$A:$A,0),2)", usage)
    assert not usage.found


def _headers(n: int = 6) -> list[str]:
    return [str(i) for i in range(1, n + 1)]


def _row(n: int = 6, **cells: str) -> dict[str, str]:
    row = {str(i): "" for i in range(1, n + 1)}
    row.update({k.lstrip("c"): v for k, v in cells.items()})
    return row


def _run(formulas, podatki_rows, headers=None):
    rule = PodatkiColumnUsageRule()
    shared = SharedContext()
    shared.extra["parsed_formulas"] = {"List1": [{"Vrednost": f} for f in formulas]}
    shared.extra["all_workbook_data"] = {"List1": [], "Podatki": podatki_rows}
    shared.extra["all_workbook_headers"] = {"Podatki": headers or _headers()}
    rule.set_shared_context(shared)
    return rule.run_workbook({"List1": []}, workbook_name="t.xlsx")


def test_reports_unused_columns_with_data():
    rows = [
        _row(c1="Receptura", c2="Ključ 1", c3="Ključ 2", c4="Ključ 3"),
        _row(c1="R-A-4", c2="a", c3="b", c4="c"),
    ]
    errors = _run([_f(2, "$A:$F"), _f(3, "$A:$F")], rows)
    assert [e.column for e in errors] == ["D"]
    assert errors[0].sheet == "Podatki"
    assert errors[0].severity == Severity.ERROR
    assert errors[0].code == "PODATKI_COLUMN_UNUSED"
    assert "Ključ 3" in errors[0].message


def test_unused_column_with_only_label_is_ok():
    rows = [
        _row(c1="Receptura", c2="Ključ 1", c3="Ključ 2"),
        _row(c1="R-A-4", c2="a"),
    ]
    assert _run([_f(2, "$A:$F")], rows) == []


def test_all_used_no_errors_and_empty_columns_ignored():
    rows = [_row(c1="Receptura", c2="Ključ 1"), _row(c1="R-A-4", c2="a")]
    assert _run([_f(2, "$A:$F")], rows) == []


def test_skipped_without_formulas_or_references():
    rows = [_row(c1="Receptura", c2="Ključ 1")]
    assert _run([], rows) == []
    assert _run(["=SUM(A1:A3)"], rows) == []


def test_skipped_without_podatki_sheet():
    rule = PodatkiColumnUsageRule()
    shared = SharedContext()
    shared.extra["parsed_formulas"] = {"List1": [{"Vrednost": _f(2)}]}
    shared.extra["all_workbook_data"] = {"List1": []}
    rule.set_shared_context(shared)
    assert rule.run_workbook({"List1": []}, workbook_name="t.xlsx") == []
