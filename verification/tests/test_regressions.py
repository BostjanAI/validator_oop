"""Promoted, reproduced requirement discrepancies. A failing implementation stays red."""

import json
from pathlib import Path

import pytest

from verification.cases import BOOK, SHEET, TARGETS, Case
from verification.worker import execute


CASES = json.loads((Path(__file__).resolve().parents[1] / "regressions.json").read_text())


@pytest.mark.parametrize("record", CASES, ids=[f"{c['target']}-{c['values']}" for c in CASES])
def test_documented_requirement(record):
    case = Case(record["target"], tuple(record["values"]))
    observed = execute({"function": TARGETS[case.target].function, "rows": case.rows(),
                        "book": BOOK, "sheet": SHEET})
    assert observed["exception"] is None
    assert not ({"rows", "context", "rule"} & observed["effects"].keys())
    required = sorted((code, row, col, "error", BOOK, SHEET) for code, row, col in record["required_findings"])
    actual = sorted((f["code"], f["row_index"], f["column"], f["severity"], f["workbook"], f["sheet"])
                    for f in observed["findings"])
    assert actual == required
