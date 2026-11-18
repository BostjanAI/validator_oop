"""Synthetic contract tests; one actual .xlsx smoke test of the existing copy fixer."""

import hashlib
from dataclasses import replace
from datetime import datetime, timezone

from openpyxl import Workbook, load_workbook
from openpyxl.workbook.defined_name import DefinedName
import pytest

from verification.sync_contract import (
    PROTECTED, Cell, Change, Image, Permit, Plan, Receipt, publication_issues,
)
from validator_oop.excel.report_writer import WorkbookFixer


def scenario():
    target = ("Pilot", "A1")
    formula = ("Pilot", "B1")
    change = Change(Cell("number", "1"), Cell("number", "2"))
    source = Image("source", {target: change.old, formula: Cell("formula", "=A1+1")},
                   dict.fromkeys(PROTECTED, "fixture fingerprint"))
    after = Image("published", {**source.cells, target: change.new}, dict(source.structure))
    plan = Plan("op-1", "tester", "QA-test", source.digest, {target: Permit(change)})
    receipt = Receipt(plan.operation_id, plan.actor, plan.approval_id, datetime.now(timezone.utc),
                      True, source.digest, after.digest, {target: change})
    return dict(source=source, source_digest_after=source.digest, previous_output_digest=None,
                published=after, plan=plan, committed=True, receipt=receipt)


def test_authorized_edit_exactly_matches_published_diff_and_receipt():
    case = scenario()
    assert publication_issues(**case) == []
    case["receipt"] = replace(case["receipt"], approval_id="different approval", changes={})
    assert set(publication_issues(**case)) == {"invalid receipt", "audit changes differ from published cells"}


def test_stale_plan_and_unknown_coverage_block_approval():
    case = scenario()
    case["plan"] = replace(case["plan"], source_digest="another workbook")
    case["source"] = replace(case["source"], structure={})
    case["published"] = replace(case["published"], structure={})
    assert set(publication_issues(**case)) == {
        "plan is for a different source revision", "incomplete or changed workbook structure",
    }


def test_replaced_formula_needs_explicit_authorization():
    case = scenario()
    addr = ("Pilot", "B1")
    change = Change(case["source"].cells[addr], Cell("number", "7"))
    case["published"] = replace(case["published"], cells={**case["published"].cells, addr: change.new})
    issues = publication_issues(**case)
    assert "changed cells differ from authorized plan" in issues
    assert "formula changed without formula authorization" in issues
    case["plan"] = replace(case["plan"], permits={**case["plan"].permits, addr: Permit(change)})
    case["receipt"] = replace(case["receipt"], changes={**case["receipt"].changes, addr: change})
    assert publication_issues(**case) == ["formula changed without formula authorization"]
    case["plan"] = replace(case["plan"], permits={**case["plan"].permits, addr: Permit(change, True)})
    assert publication_issues(**case) == []


@pytest.mark.parametrize("component", sorted(PROTECTED))
def test_changed_protected_fingerprint(component):
    case = scenario()
    after = case["published"]
    case["published"] = replace(after, structure={**after.structure, component: "changed"})
    assert "incomplete or changed workbook structure" in publication_issues(**case)


@pytest.mark.parametrize("existing_output", [None, "previous"])
def test_failed_attempt_preserves_preexisting_output_or_absence(existing_output):
    case = scenario()
    visible = replace(case["source"], digest=existing_output) if existing_output else None
    case.update(previous_output_digest=existing_output, published=visible, committed=False,
                receipt=replace(case["receipt"], published_digest=existing_output, committed=False, changes={}))
    assert publication_issues(**case) == []
    case.update(published=case["source"], source_digest_after="changed")
    assert {"partial publication", "source modified"} <= set(publication_issues(**case))


def test_existing_fixer_synthetic_xlsx_copy(tmp_path):
    src, dst = tmp_path / "source.xlsx", tmp_path / "copy.xlsx"
    book = Workbook()
    sheet = book.active
    sheet.title = "Pilot"
    sheet["A1"], sheet["B1"], sheet["A2"] = 1, "=A1+1", "synthetic"
    sheet.merge_cells("C1:D1")
    book.create_sheet("Other")
    book.defined_names.add(DefinedName("PilotValue", attr_text="'Pilot'!$A$1"))
    book.properties.title = "Synthetic pilot"
    book.save(src)
    book.close()
    original = hashlib.sha256(src.read_bytes()).digest()
    edits = [{"sheet": "Pilot", "target_cell": "A1", "proposed_value": 2, "fix_kind": "set_value"}]
    assert WorkbookFixer().apply_fixes(src, dst, edits) == 1
    assert hashlib.sha256(src.read_bytes()).digest() == original
    result = load_workbook(dst, data_only=False)
    try:
        assert result.sheetnames == ["Pilot", "Other"]
        assert result["Pilot"]["A1"].value == 2
        assert (result["Pilot"]["B1"].data_type, result["Pilot"]["B1"].value) == ("f", "=A1+1")
        assert result["Pilot"]["A2"].value == "synthetic"
        assert str(result["Pilot"].merged_cells) == "C1:D1"
        assert result.defined_names["PilotValue"].attr_text == "'Pilot'!$A$1"
        assert result.properties.title == "Synthetic pilot"
    finally:
        result.close()
