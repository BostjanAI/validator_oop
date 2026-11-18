"""Read-only postconditions for a future staged Recipe Sync publisher."""

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

import z3


Address = tuple[str, str]  # exact worksheet name and canonical A1 address
PROTECTED = {"sheet_layout", "merged_ranges", "defined_names", "styles", "metadata",
             "vba", "relationships_and_other_parts"}


@dataclass(frozen=True)
class Cell:
    kind: str  # e.g. "number", "text", "formula"; preserve the raw formula expression
    value: str


@dataclass(frozen=True)
class Image:
    digest: str  # SHA-256 of the visible file
    cells: Mapping[Address, Cell]
    structure: Mapping[str, str]  # fingerprints, including explicit absence of optional parts


@dataclass(frozen=True)
class Change:
    old: Cell | None
    new: Cell | None


@dataclass(frozen=True)
class Permit:
    change: Change
    allow_formula_edit: bool = False


@dataclass(frozen=True)
class Plan:
    operation_id: str
    actor: str
    approval_id: str
    source_digest: str
    permits: Mapping[Address, Permit]


@dataclass(frozen=True)
class Receipt:
    operation_id: str
    actor: str
    approval_id: str
    timestamp: datetime
    committed: bool
    source_digest: str
    published_digest: str | None
    changes: Mapping[Address, Change]


def publication_issues(*, source: Image, source_digest_after: str, previous_output_digest: str | None,
                       published: Image | None, plan: Plan,
                       committed: bool, receipt: Receipt) -> list[str]:
    """Check externally observed publication against an independently supplied authorized plan.

    The caller must obtain complete, canonical snapshots and a trusted receipt.
    No loader, authorization decision, audit store or file publication is implemented here.
    """
    issues = []
    visible = published.digest if published else None
    if plan.source_digest != source.digest:
        issues.append("plan is for a different source revision")
    if source_digest_after != source.digest:
        issues.append("source modified")
    identity = (receipt.actor, receipt.operation_id, receipt.approval_id)
    if (not all(identity) or identity != (plan.actor, plan.operation_id, plan.approval_id)
            or receipt.timestamp.utcoffset() is None or receipt.committed != committed
            or receipt.source_digest != source.digest or receipt.published_digest != visible):
        issues.append("invalid receipt")
    if not committed:
        if visible != previous_output_digest or receipt.changes:
            issues.append("partial publication")
        return issues
    if published is None:
        return issues + ["missing published output"]
    if (not all(source.structure.get(k) for k in PROTECTED)
            or published.structure != source.structure):
        issues.append("incomplete or changed workbook structure")
    changes = {}
    for addr in source.cells.keys() | published.cells.keys():
        old, new = source.cells.get(addr), published.cells.get(addr)
        if old != new:
            changes[addr] = Change(old, new)
    if changes != {addr: p.change for addr, p in plan.permits.items()}:
        issues.append("changed cells differ from authorized plan")
    for addr, edit in changes.items():
        permit = plan.permits.get(addr)
        if edit.old and edit.old.kind == "formula" and not (permit and permit.allow_formula_edit):
            issues.append("formula changed without formula authorization")
    if changes != receipt.changes:
        issues.append("audit changes differ from published cells")
    return issues


def frame_result():
    # Mathematical model of ONE cell update. No Python writer is under this theorem.
    cells = z3.Array("cells", z3.IntSort(), z3.IntSort())
    target, address, value = z3.Ints("target address value")
    approved, formula, formula_edit, committed = z3.Bools("approved formula formula_edit committed")
    allow = z3.And(approved, z3.Or(z3.Not(formula), formula_edit), committed)
    after = z3.If(allow, z3.Store(cells, target, value), cells)
    protected = z3.Or(address != target, z3.Not(approved), z3.Not(committed),
                      z3.And(formula, z3.Not(formula_edit)))
    solver = z3.Solver()
    solver.set(timeout=10000)
    solver.add(protected, after[address] != cells[address])
    answer = solver.check()
    check = {
        "function": "abstract guarded single-cell update", "requirement_id": "SYNC-FRAME",
        "domain": "All integer addresses and values, symbolic authorization/formula/commit flags.",
        "method": "SMT proof of a frame property in array theory", "tool": "z3-solver",
        "result": {str(z3.unsat): "PASS", str(z3.sat): "FAIL", str(z3.unknown): "INCONCLUSIVE"}[str(answer)],
        "assumptions": "The model performs exactly the specified guarded Store; flags are trusted inputs.",
        "limitations": "Only this mathematical transition. No file, receipt or storage system is modeled.",
        "counterexamples": [],
    }
    if answer == z3.sat:
        check["counterexamples"].append({"function": check["function"], "violated_requirement": "SYNC-FRAME",
                                        "inputs": str(solver.model()), "expected": "protected cell unchanged",
                                        "actual": "cell changed", "reproduce": "python -m verification"})
    elif answer == z3.unknown:
        check["reason"] = solver.reason_unknown()
    return [check, {
        "function": "future Recipe Sync adapter", "requirement_id": "SYNC-XLSX",
        "domain": "Real xlsx/xlsm files and publication failures", "method": "integration qualification",
        "tool": "none", "result": "NOT VERIFIED", "counterexamples": [],
        "limitations": "No Recipe Sync publisher or qualified Excel snapshot adapter in this revision.",
    }]
