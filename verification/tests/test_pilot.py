import ast
import subprocess
from decimal import Decimal

import pytest
import z3
from hypothesis import given, settings, strategies as st

from verification.__main__ import compare, run
from verification.cases import BASELINE, BOOK, SHEET, TARGETS, Case, domain
from verification.contracts import check_spec
from verification.interval_guard import check_guard, symbolic
from verification.revisions import ROOT, measure
from verification.worker import execute, observe
from validator_oop.rules.builtin.control import KontrolaIntervalParamRule


def observation(target, *values):
    return execute({"function": TARGETS[target].function, "sheet": SHEET, "book": BOOK,
                    "rows": Case(target, values).rows()})


def codes(obs):
    assert obs["exception"] is None and not obs["effects"]
    return [f["code"] for f in obs["findings"]]


@pytest.mark.parametrize(("target", "values", "expected"), [
    ("interval", ("0", "0"), ["CTRL_INTERVAL_RANGE"]),
    ("interval", ("", "1"), ["CTRL_INTERVAL_PARAMS"]),
    ("interval", ("0", "#REF!"), ["CTRL_INTERVAL_NOT_NUMBER"]),
    ("owner", ("kemikalija", "dH2O", "same", "absent"), ["PAIR_WATER_WITHOUT_VOLUME"]),
    ("owner", ("raztopina", "K", "other", "same"), ["PAIR_VOLUME_NOT_ALLOWED", "PAIR_SOL_WITHOUT_MASS"]),
    ("lock", ("3,5",), ["LOCK_P1_STEP_MISSING"]),
    ("lock", ("2,4",), ["LOCK_P1_WITHOUT_CONDITION"]),
])
def test_documented_examples(target, values, expected):
    assert sorted(codes(observation(target, *values))) == sorted(expected)


@settings(derandomize=True, max_examples=100, deadline=None, database=None)
@given(st.integers(-100_000, 100_000), st.integers(-100_000, 100_000))
def test_order_of_decimal_hundredths(lower, upper):
    args = [str(Decimal(v).scaleb(-2)) for v in (lower, upper)]
    assert codes(observation("interval", *args)) == ([] if upper > lower else ["CTRL_INTERVAL_RANGE"])


@settings(derandomize=True, max_examples=64, deadline=None, database=None)
@given(st.text(alphabet="ABCDEFGJ", min_size=1, max_size=8), st.booleans(), st.booleans())
def test_ordinary_key_requires_same_mass_and_forbids_same_volume(key, mass, volume):
    obs = observation("owner", "kemikalija", key, "same" if mass else "other", "same" if volume else "other")
    expected = ([] if mass else ["PAIR_CHEM_WITHOUT_MASS"]) + (["PAIR_VOLUME_NOT_ALLOWED"] if volume else [])
    assert sorted(codes(obs)) == sorted(expected)


@settings(derandomize=True, max_examples=64, deadline=None, database=None)
@given(st.integers(5, 10_000), st.sampled_from(["2", "3"]))
def test_missing_reference_at_end_of_valid_list(step, first):
    assert codes(observation("lock", f"{first},{step}")) == ["LOCK_P1_STEP_MISSING"]


def test_equivalence_compares_dependencies_in_distinct_commits(tmp_path):
    checkout = tmp_path / "candidate"
    subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", str(ROOT), str(checkout)], check=True)

    def git(*args):
        return subprocess.run(["git", "-c", "user.name=Pilot", "-c", "user.email=pilot@example.invalid",
                               *args], cwd=checkout, check=True, capture_output=True)

    git("checkout", "--quiet", "--detach", BASELINE)
    cases = domain("interval")
    indexed = [(f"interval/{i:02}", c) for i, c in enumerate(cases)]
    base, old = measure(BASELINE, cases, repository=checkout)
    assert old is not None, base
    src = checkout / "rules/builtin/control.py"
    original = src.read_text()
    comparison = "p2_val is not None and p2_val <= p1_val:"
    assert original.count(comparison) == 1
    src.write_text(original.replace(comparison, "p2_val is not None and not (p1_val < p2_val):"))
    git("commit", "-qam", "Equivalent finite-input refactor in temporary test clone")
    changed, new = measure("HEAD", cases, repository=checkout)
    eq, spec = compare("interval", indexed, old, new, base, changed)
    assert (eq["result"], spec["result"]) == ("PASS", "PASS")
    assert check_guard(changed["commit"], repository=checkout)["result"] == "PASS"

    # Change a transitive dependency only. A checker sharing live helpers would miss this.
    helper = checkout / "utils/helpers.py"
    helper.write_text(helper.read_text().replace("    if value is None:", '    if value == "0.5":\n'
                                                 '        return "0"\n    if value is None:', 1))
    git("commit", "-qam", "Negative control: misread a decimal in a dependency")
    mutated, new = measure("HEAD", cases, repository=checkout)
    eq, spec = compare("interval", indexed, old, new, base, mutated)
    assert (eq["result"], spec["result"]) == ("FAIL", "FAIL")
    assert any(w["inputs"]["parameters"] == ("0", "0.5") for w in eq["counterexamples"])

    src.write_text(original.replace(comparison, "p2_val is not None and p2_val < p1_val:"))
    git("commit", "-qam", "Negative control: accept equal limits")
    guard = check_guard("HEAD", repository=checkout)
    assert guard["result"] == "FAIL"
    inputs = guard["counterexamples"][0]["inputs"]
    bits = [int(inputs[k], 0) for k in ("minimum_bits", "maximum_bits")]
    assert check_guard("HEAD", bits, repository=checkout)["result"] == "FAIL"


def test_space_counterexample_has_a_separate_engine_diagnostic():
    from validator_oop.core.rule_engine import RuleEngine
    from validator_oop.rules import default_registry
    from validator_oop.rules.builtin import register_all

    register_all()
    rows = Case("lock", ("2, 3",)).rows()
    errors = RuleEngine(default_registry).run({SHEET: rows}, workbook_name=BOOK)
    assert any(e.code == "SPACE_NOT_ALLOWED" and e.row_index == 2 and e.column == "Kontrola 1 - par 1"
               for e in errors)


def test_exception_and_side_effects_are_observable():
    class MutatedRule(KontrolaIntervalParamRule):
        def evaluate(self, row, context):
            row["changed"] = True
            context.shared.extra["changed"] = True
            self.counter = 1
            self._logger.warning("synthetic event")
            raise ValueError("synthetic exception")

    case = Case("interval", ("0", "1"))
    baseline = observation("interval", *case.values)
    mutated = observe(MutatedRule(), "evaluate", case.rows(), SHEET, BOOK)
    assert {"rows", "context", "rule", "log"} <= mutated["effects"].keys()
    assert mutated["exception"] == {"type": "builtins.ValueError", "args": {"tuple": ["synthetic exception"]}}
    eq, spec = compare("interval", [("interval/example", case)], [baseline], [mutated],
                       {"commit": BASELINE}, {"commit": BASELINE})
    assert (eq["result"], spec["result"]) == ("FAIL", "FAIL")


def test_guard_mutant_detected_for_signed_zero():
    lo, hi = z3.FPs("test_lo test_hi", z3.Float64())
    # A mutant that omits equality fails even for the two representations of zero.
    strict = symbolic(ast.parse("p2_val < p1_val", mode="eval").body, {"p1_val": lo, "p2_val": hi})
    solver = z3.Solver()
    solver.add(lo == z3.fpMinusZero(z3.Float64()), hi == z3.fpPlusZero(z3.Float64()),
               strict != z3.Not(z3.fpGT(hi, lo)))
    assert solver.check() == z3.sat


def test_solver_unknown_and_missing_tree_do_not_pass(monkeypatch):
    class Unknown(z3.Solver):
        def check(self, *args):
            return z3.unknown

        def reason_unknown(self):
            return "synthetic timeout"

    case = Case("interval", ("0", "1"))
    obs = observation("interval", *case.values)
    with pytest.raises(ValueError, match="Incomplete"):
        check_spec("interval", [case], [])
    monkeypatch.setattr(z3, "Solver", Unknown)
    _, spec = compare("interval", [("interval/example", case)], [obs], [obs],
                      {"commit": BASELINE}, {"commit": BASELINE})
    assert spec["result"] == "INCONCLUSIVE"
    missing = run("missing-verification-test-revision", "lock/08")
    assert missing["result"] == "NOT VERIFIED"
    assert all(check["cases_checked"] == 0 for check in missing["checks"])
