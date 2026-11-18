"""Run with python -m verification from the repository root."""

import argparse
import hashlib
import json
import platform
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import z3

from .cases import BASELINE, TARGETS, domain
from .contracts import check_spec
from .interval_guard import check_guard
from .revisions import git, measure
from .sync_contract import frame_result


def witness(case_id, case, sha, expected, actual, violated, classification):
    return {
        "function": TARGETS[case.target].function, "case": case_id,
        "inputs": {"parameters": case.values, "rows": case.rows()},
        "violated_requirement": violated, "expected": expected, "actual": actual,
        "classification": classification,
        "reproduce": f"python -m verification --candidate {sha} --case {case_id}",
    }


def compare(target, indexed, reference, candidate, baseline_info, candidate_info):
    spec = TARGETS[target]
    common = {**asdict(spec), "cases_requested": len(indexed), "requirements_source": f"NAV-158 v5 @ {BASELINE}"}
    eq = {**common, "method": "Exhaustive differential execution", "tool": "CPython",
          "requirement_id": f"EQ-{target}", "cases_checked": 0, "counterexamples": [],
          "limitations": "Finite fixtures; ordered findings, exceptions, state mutations and captured logs/streams."}
    sc = {**common, "method": "Bounded SMT specification check on observed Python relation",
          "tool": "z3-solver", "requirement_id": f"SPEC-{target}", "cases_checked": 0,
          "counterexamples": [], "limitations": "Only enumerated inputs and specified diagnostic projection."}
    if reference is None or candidate is None:
        missing = [s for s in (baseline_info, candidate_info) if "reason" in s]
        eq.update(result="INCONCLUSIVE" if any(s["status"] == "INCONCLUSIVE" for s in missing)
                  else "NOT VERIFIED", reason=[s["reason"] for s in missing])
    else:
        for (case_id, case), old, new in zip(indexed, reference, candidate, strict=True):
            if json.dumps(old, sort_keys=True) != json.dumps(new, sort_keys=True):
                eq["counterexamples"].append(witness(
                    case_id, case, candidate_info["commit"], old, new, eq["requirement_id"],
                    "Observable behavior changed; requires impact review."))
        eq.update(result="FAIL" if eq["counterexamples"] else "PASS", cases_checked=len(indexed))
    if candidate is None:
        sc.update(result=candidate_info["status"], reason=candidate_info["reason"])
    else:
        try:
            failures, unknown = check_spec(target, [c for _, c in indexed], candidate)
        except (ValueError, KeyError, z3.Z3Exception) as exc:
            sc.update(result="INCONCLUSIVE", reason=f"Cannot check the observation table: {exc}")
            return [eq, sc]
        for index, expected in failures:
            case_id, case = indexed[index]
            obs = candidate[index]
            actual_locations = [(f["code"], f["row_index"], f["column"]) for f in obs["findings"]]
            changed = set(expected).symmetric_difference(actual_locations)
            violated = sorted({code for code, _, _ in changed if code in spec.requirements})
            counterexample = witness(
                case_id, case, candidate_info["commit"],
                {"required_findings": expected, "severity": "error", "exception": None,
                 "input_mutations": False}, obs, violated or [sc["requirement_id"]],
                "Documented requirement discrepancy; review requirement, fixture and implementation.")
            # Review this seed before adding it to the executable regression corpus.
            counterexample["regression_case"] = {
                "target": target, "values": case.values, "required_findings": expected,
            }
            sc["counterexamples"].append(counterexample)
        sc["cases_checked"] = len(indexed)
        if unknown:
            sc["reason"] = "Solver could not complete search: " + unknown
        sc["result"] = "FAIL" if failures else "INCONCLUSIVE" if unknown else "PASS"
    return [eq, sc]


def run(candidate_ref, selector=None):
    groups = {}
    for target in TARGETS:
        cases = [(f"{target}/{i:02}", c) for i, c in enumerate(domain(target))]
        selected = [(name, case) for name, case in cases if selector is None or name == selector]
        if selected:
            groups[target] = selected
    if not groups:
        raise ValueError(f"Unknown pilot case {selector!r}")

    inputs = [case for entries in groups.values() for _, case in entries]
    baseline, old = measure(BASELINE, inputs)
    candidate, new = measure(candidate_ref, inputs)
    checks = []
    start = 0
    for target, indexed in groups.items():
        end = start + len(indexed)
        checks.extend(compare(target, indexed, None if old is None else old[start:end],
                              None if new is None else new[start:end], baseline, candidate))
        start = end
    if selector is None:
        if candidate["commit"]:
            checks.append(check_guard(candidate["commit"]))
        else:
            checks.append({"function": TARGETS["interval"].function, "requirement_id": "CTRL_INTERVAL_RANGE",
                           "result": "NOT VERIFIED", "method": "extracted numeric predicate",
                           "tool": "z3-solver", "domain": "finite binary64", "counterexamples": [],
                           "limitations": candidate["reason"]})
        checks.extend(frame_result())
    statuses = {r["result"] for r in checks}
    # The separate future-adapter entry is informative, outside the pilot gate.
    gate = {r["result"] for r in checks if r["requirement_id"] != "SYNC-XLSX"}
    harness = Path(__file__).resolve().parent
    report = {
        "schema": 1, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": candidate, "reference": baseline,
        "harness_commit": git("rev-parse", "HEAD").stdout.decode().strip(),
        "harness_files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(harness.glob("*.py"))},
        "platform": platform.platform(),
        "tools": {"CPython": platform.python_version(), "z3-solver": version("z3-solver"),
                  "z3_runtime": z3.get_version_string(),
                  "openpyxl": version("openpyxl"), "git": git("--version").stdout.decode().strip()},
        "scope": selector or "full pilot", "status_values_present": sorted(statuses),
        "requirement_documents": {
            "revision": BASELINE,
            "paths": ["docs/Navodila_Validator/NAV-158_Navodila_Validator.md",
                      "docs/NAVODILA_PRIPRAVA_RECEPTURE.md"],
            "approval": "Controlled-copy confirmation pending",
        },
        "selected_case_parameters": {name: case.values for group in groups.values() for name, case in group},
        "assumptions": ["Committed trees only. Trusted deterministic rule code, one fresh rule and context per case.",
                        "Row offset 2, workbook synthetic.xlsx, sheet Pilot; reference data are synthetic.",
                        "Requirements transcribed from repository documents; controlled-copy approval pending."],
        "result": next(status for status in ("FAIL", "INCONCLUSIVE", "NOT VERIFIED", "PASS") if status in gate),
        "checks": checks,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="HEAD", help="committed Git revision to check")
    parser.add_argument("--case", help="replay one case from a report, e.g. lock/08")
    parser.add_argument("--output", type=Path, help="new JSON file (default: stdout)")
    args = parser.parse_args()
    try:
        report = run(args.candidate, args.case)
        body = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(body)
            print(f"{report['result']}  {args.output}")
        else:
            print(body, end="")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Verification could not complete: {exc}\n")
    return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2, "NOT VERIFIED": 2}[report["result"]]


if __name__ == "__main__":
    raise SystemExit(main())
