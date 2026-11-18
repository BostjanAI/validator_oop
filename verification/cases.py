"""Fixed, synthetic verification domains. No imports from the application."""

from dataclasses import dataclass
from itertools import product


BASELINE = "f5fefb8733087923b9c141db10cbfbcf9bb3a743"
SHEET = "Pilot"
BOOK = "synthetic.xlsx"
P1 = "Kontrola 2 - par 1"
P2 = "Kontrola 2 - par 2"
LOCK_P1 = "Kontrola 1 - par 1"
TIP = "Tip podatka"
KEY = "Ključ preverjanja"
STEP = "št. Koraka"


@dataclass(frozen=True)
class Target:
    function: str
    requirements: tuple[str, ...]
    domain: str


TARGETS = {
    "interval": Target(
        "rules.builtin.control.KontrolaIntervalParamRule.evaluate",
        ("CTRL_INTERVAL_PARAMS", "CTRL_INTERVAL_NOT_NUMBER", "CTRL_INTERVAL_RANGE"),
        "One interval control, every ordered pair of literal strings in BOUNDS, "
        "except mixed missing/malformed pairs (diagnostic precedence unspecified).",
    ),
    "owner": Target(
        "rules.builtin.relational.OwnerMassPairRule.evaluate_sheet",
        ("PAIR_CHEM_WITHOUT_MASS", "PAIR_SOL_WITHOUT_MASS", "PAIR_WATER_WITHOUT_VOLUME",
         "PAIR_VOLUME_NOT_ALLOWED"),
        "One tab, one owner (kemikalija/raztopina, K/dH2O), one mass slot and one "
        "volume slot, independently absent/same/other. Water with both matches excluded.",
    ),
    "lock": Target(
        "rules.builtin.control.ZakleniParamRule.evaluate",
        ("LOCK_P1_FORMAT", "LOCK_P1_STEP_MISSING", "LOCK_P1_WITHOUT_CONDITION"),
        "One locking checkbox. Steps 2 and 3 conditional, 4 unconditional, 5 missing. "
        "Exactly the nonempty literal strings in LOCK_LISTS.",
    ),
}

BOUNDS = ("-1", "-0.5", "0", "0.5", "1", "", "#REF!")
LOCK_LISTS = ("2", "3", "4", "5", "2,3", "3,2", "2,4", "3,5", "2, 3", "2,", "2.5", "x")


@dataclass(frozen=True)
class Case:
    target: str
    values: tuple[str, ...]

    def rows(self) -> list[dict]:
        if self.target == "interval":
            lower, upper = self.values
            return [{"Kontrola 2": "kontrolainterval", P1: lower, P2: upper}]
        if self.target == "owner":
            kind, key, mass, volume = self.values
            rows = [{TIP: kind, KEY: key}]
            for tip, slot in (("masa", mass), ("volumen", volume)):
                rows.append({TIP: "", KEY: ""} if slot == "absent" else
                            {TIP: tip, KEY: key if slot == "same" else "ALT"})
            return rows
        if self.target == "lock":
            return [
                {STEP: "1", "Tip objekta": "checkbox", KEY: "K",
                 "Kontrola 1": "zaklenipolja", LOCK_P1: self.values[0]},
                *[{STEP: step, "Kontrola 1": "aliObstajaPogoj", LOCK_P1: "K",
                   "Kontrola 1 - par 2": "1"} for step in ("2", "3")],
                {STEP: "4"},
            ]
        raise ValueError(self.target)


def domain(target: str) -> list[Case]:
    if target == "interval":
        values = [pair for pair in product(BOUNDS, repeat=2) if set(pair) != {"", "#REF!"}]
    elif target == "owner":
        slots = ("absent", "same", "other")
        values = [entry for entry in product(("kemikalija", "raztopina"), ("K", "dH2O"), slots, slots)
                  if entry[1:] != ("dH2O", "same", "same")]
    elif target == "lock":
        values = [(s,) for s in LOCK_LISTS]
    else:
        raise ValueError(target)
    return [Case(target, v) for v in values]
