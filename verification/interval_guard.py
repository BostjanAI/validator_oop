"""Symbolically check the production CTRL_INTERVAL_RANGE comparison after numeric parsing."""

import argparse
import ast
import hashlib
import json
import subprocess

import z3

from .cases import TARGETS
from .revisions import ROOT, git


def extract_guard(source):
    cls = next(n for n in ast.parse(source).body
               if isinstance(n, ast.ClassDef) and n.name == "KontrolaIntervalParamRule")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate")
    emissions = [k for k in ast.walk(method) if isinstance(k, ast.keyword) and k.arg == "code"
                 and isinstance(k.value, ast.Constant) and k.value.value == "CTRL_INTERVAL_RANGE"]
    if len(emissions) != 1:
        raise ValueError("Unsupported number of explicit CTRL_INTERVAL_RANGE emissions")
    guards = []
    for node in ast.walk(method):
        if not isinstance(node, ast.If) or len(node.body) != 1:
            continue
        stmt = node.body[0]
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            continue
        call = stmt.value
        if ast.unparse(call.func) != "errors.append" or len(call.args) != 1:
            continue
        error = call.args[0]
        if isinstance(error, ast.Call) and ast.unparse(error.func) == "self.build_error":
            if any(k.arg == "code" and isinstance(k.value, ast.Constant)
                   and k.value.value == "CTRL_INTERVAL_RANGE" for k in error.keywords):
                guards.append(node.test)
    if len(guards) != 1:
        raise ValueError("Cannot identify one immediate CTRL_INTERVAL_RANGE emission guard")
    return guards[0]


def symbolic(node, values):
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, ast.BoolOp):
        op = {ast.And: z3.And, ast.Or: z3.Or}[type(node.op)]
        return op(*(symbolic(part, values) for part in node.values))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return z3.Not(symbolic(node.operand, values))
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left = symbolic(node.left, values)
        right = node.comparators[0]
        if isinstance(right, ast.Constant) and right.value is None and z3.is_fp(left):
            if isinstance(node.ops[0], (ast.Is, ast.IsNot)):
                return z3.BoolVal(isinstance(node.ops[0], ast.IsNot))  # both operands are numeric
        op = {ast.Lt: z3.fpLT, ast.LtE: z3.fpLEQ, ast.Gt: z3.fpGT,
              ast.GtE: z3.fpGEQ, ast.Eq: z3.fpEQ}[type(node.ops[0])]
        return op(left, symbolic(right, values))
    raise ValueError(f"Unsupported guard syntax: {ast.dump(node)}")


def check_guard(sha, bits=None, *, repository=ROOT):
    result = {
        "function": TARGETS["interval"].function, "requirement_id": "CTRL_INTERVAL_RANGE",
        "method": "SMT check of extracted Python predicate (IEEE 754 binary64)",
        "tool": "z3-solver", "domain": "All pairs of finite binary64 numbers, including signed zeros.",
        "assumptions": "Execution reaches this guard. p1_val and p2_val are the parsed minimum and maximum.",
        "limitations": "Parser, paths reaching the guard, diagnostic construction and Excel I/O are outside this proof.",
        "counterexamples": [],
    }
    try:
        source = git("show", f"{sha}:rules/builtin/control.py", cwd=repository).stdout
        guard = extract_guard(source)
        result.update(predicate=ast.unparse(guard), source_sha256=hashlib.sha256(source).hexdigest())
        lo, hi = z3.FPs("minimum maximum", z3.Float64())
        actual = symbolic(guard, {"p1_val": lo, "p2_val": hi})
        expected = z3.Not(z3.fpGT(hi, lo))  # NAV-158: the maximum must exceed the minimum
        solver = z3.Solver()
        solver.set(timeout=10000)
        for operand in (lo, hi):
            solver.add(z3.Not(z3.fpIsNaN(operand)), z3.Not(z3.fpIsInf(operand)))
        if bits:
            for operand, value in zip((lo, hi), bits, strict=True):
                if not 0 <= value < 2**64 or ((value >> 52) & 0x7ff) == 0x7ff:
                    raise ValueError("Replay requires finite binary64 bit patterns")
                solver.add(z3.fpToIEEEBV(operand) == value)
            result["domain"] = [f"0x{v:016x}" for v in bits]
        solver.add(actual != expected)
        outcome = solver.check()
        if outcome == z3.unsat:
            result["result"] = "PASS"
        elif outcome == z3.unknown:
            result.update(result="INCONCLUSIVE", reason=solver.reason_unknown())
        else:
            model = solver.model()
            args = [f"0x{model.eval(z3.fpToIEEEBV(v)).as_long():016x}" for v in (lo, hi)]
            result["result"] = "FAIL"
            result["counterexamples"] = [{
                "function": result["function"], "violated_requirement": "CTRL_INTERVAL_RANGE",
                "inputs": {"minimum_bits": args[0], "maximum_bits": args[1]},
                "expected": str(model.eval(expected)), "actual": str(model.eval(actual)),
                "classification": "Counterexample to extracted predicate; confirm reachability in Python.",
                "reproduce": f"python -m verification.interval_guard --candidate {sha} --bits {' '.join(args)}",
            }]
    except (ValueError, KeyError, StopIteration, SyntaxError, subprocess.CalledProcessError,
            z3.Z3Exception) as exc:
        result.update(result="INCONCLUSIVE", reason=f"Could not verify extracted predicate: {exc}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="HEAD")
    parser.add_argument("--bits", nargs=2, type=lambda s: int(s, 0))
    args = parser.parse_args()
    sha = git("rev-parse", "--verify", "--end-of-options", f"{args.candidate}^{{commit}}").stdout.decode().strip()
    report = check_guard(sha, args.bits)
    print(json.dumps(report, indent=2))
    raise SystemExit({"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}[report["result"]])
