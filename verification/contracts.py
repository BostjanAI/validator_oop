"""Independent finite specifications derived from NAV-158 v5, §§4.3–4.4.

Z3 searches for a violating input in a complete table of real Python observations.
It does not translate or symbolically execute the Python interpreter.
"""

from dataclasses import dataclass
from fractions import Fraction

import z3

from .cases import BOOK, LOCK_P1, P1, P2, SHEET, TIP, Case


@dataclass
class Finding:
    code: str
    row: int
    column: str
    required: z3.BoolRef

    @property
    def location(self):
        return self.code, self.row, self.column


@dataclass
class Contract:
    variables: tuple
    findings: tuple[Finding, ...]

    def projection(self, observation):
        """One bit per documented diagnostic; -1 for an invalid observation."""
        if observation["exception"] or {"rows", "context", "rule"} & observation["effects"].keys():
            return -1
        bits = {f.location: 1 << i for i, f in enumerate(self.findings)}
        mask = 0
        for f in observation["findings"]:
            bit = bits.get((f["code"], f["row_index"], f["column"]))
            if (bit is None or mask & bit or f["sheet"] != SHEET
                    or f["workbook"] != BOOK or f["severity"] != "error"):
                return -1
            mask |= bit
        return mask

    def expected_mask(self):
        return z3.Sum([z3.If(f.required, 1 << i, 0) for i, f in enumerate(self.findings)])


def contract(target):
    if target == "interval":
        # Numeric encodings are exact half-unit ticks; -4 and -3 are disjoint tags.
        lo, hi = z3.Ints("lower upper")
        return Contract((lo, hi), (
            Finding("CTRL_INTERVAL_PARAMS", 2, P1, lo == -4),
            Finding("CTRL_INTERVAL_PARAMS", 2, P2, hi == -4),
            Finding("CTRL_INTERVAL_NOT_NUMBER", 2, P1, lo == -3),
            Finding("CTRL_INTERVAL_NOT_NUMBER", 2, P2, hi == -3),
            Finding("CTRL_INTERVAL_RANGE", 2, P2, z3.And(lo >= -2, hi >= -2, hi <= lo)),
        ))
    if target == "owner":
        owner, key, mass, volume = (z3.String(s) for s in ("owner", "key", "mass", "volume"))
        water = key == "dH2O"
        missing_mass = z3.And(z3.Not(water), mass != "same")
        return Contract((owner, key, mass, volume), (
            Finding("PAIR_CHEM_WITHOUT_MASS", 2, TIP, z3.And(owner == "kemikalija", missing_mass)),
            Finding("PAIR_SOL_WITHOUT_MASS", 2, TIP, z3.And(owner == "raztopina", missing_mass)),
            Finding("PAIR_WATER_WITHOUT_VOLUME", 2, TIP, z3.And(water, volume != "same")),
            Finding("PAIR_VOLUME_NOT_ALLOWED", 4, TIP, z3.And(z3.Not(water), volume == "same")),
        ))
    if target == "lock":
        param = z3.String("lock_list")
        number = z3.Plus(z3.Range("0", "9"))
        grammar = z3.Concat(number, z3.Star(z3.Concat(z3.Re(","), number)))
        valid = z3.InRe(param, grammar)
        delimited = z3.Concat(",", param, ",")
        return Contract((param,), (
            Finding("LOCK_P1_FORMAT", 2, LOCK_P1, z3.Not(valid)),
            Finding("LOCK_P1_STEP_MISSING", 2, LOCK_P1, z3.And(valid, z3.Contains(delimited, ",5,"))),
            Finding("LOCK_P1_WITHOUT_CONDITION", 2, LOCK_P1, z3.And(valid, z3.Contains(delimited, ",4,"))),
        ))
    raise ValueError(target)


def encoding(case: Case):
    if case.target == "interval":
        tags = {"": -4, "#REF!": -3}
        ticks = []
        for token in case.values:
            if token in tags:
                ticks.append(tags[token])
                continue
            tick = 2 * Fraction(token)
            if tick.denominator != 1 or not -2 <= tick <= 2:
                raise ValueError("Numeric token outside the declared half-unit domain")
            ticks.append(int(tick))
        return tuple(ticks)
    return case.values


def check_spec(target, cases, observations, *, timeout_ms=10000):
    """Return every SAT witness, or a reason if the solver did not finish."""
    if not cases or len(cases) != len(observations):
        raise ValueError("Incomplete observation table")
    model = contract(target)
    index, actual = z3.Ints("case_index observed_mask")
    rows = []
    seen = set()
    for i, (case, obs) in enumerate(zip(cases, observations, strict=True)):
        values = encoding(case)
        if case.target != target or values in seen:
            raise ValueError("Observation table has a wrong target or duplicate input encoding")
        seen.add(values)
        binding = [var == val for var, val in zip(model.variables, values, strict=True)]
        rows.append(z3.And(index == i, actual == model.projection(obs), *binding))
    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    solver.add(z3.Or(rows), actual != model.expected_mask())
    witnesses = []
    while True:
        decision = solver.check()
        if decision == z3.unsat:
            return sorted(witnesses), None
        if decision == z3.unknown:
            return sorted(witnesses), solver.reason_unknown()
        witness = solver.model()
        i = witness.eval(index).as_long()
        expected = [f.location for f in model.findings if z3.is_true(witness.eval(f.required))]
        witnesses.append((i, expected))
        solver.add(index != i)
