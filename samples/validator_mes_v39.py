#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validator MES Receptur – v 10.7 – 2025-10-22

Dogovorjena pravila (ključne točke):
- EPS: vedno se določa iz NAVODILA (iz decimalk števil v navodilu), nikoli iz Param1/Param2.
- Razpon a–b: Param1 = a−eps (EXACT), Param2 = b+eps (EXACT).
- Zapis x±t: Param1 = x−(t+eps) (EXACT), Param2 = x+(t+eps) (EXACT).
- Ena ciljna vrednost X: Param1 = X−eps (EXACT), Param2 = X+eps (EXACT).
- Neenačbe:
    >X ali ≥X: Param1 = X−eps (EXACT), Param2 ≥ X+eps (lahko več).
    <X ali ≤X: Param1 ≤ X−eps (lahko manj), Param2 = X+eps (EXACT).
- Več števil v navodilu: pri neenačbah izberemo kandidat z enoto (če prisotna) oziroma "najbolj specifičen"
  (enota > brez enote; v dvomu zadnji v besedilu). To pokrije primere kot: "prečrpano >10 MVS (> 6.7 L)" → 6.7 L.
"""

import sys
import os
import re
import math
import datetime
import platform
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set, Optional
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import pandas as pd
    from openpyxl import load_workbook, Workbook
    from openpyxl.utils import get_column_letter
    from openpyxl.styles import Protection
    from openpyxl.worksheet.protection import SheetProtection
except Exception:
    try:
        tk.Tk().withdraw()
        messagebox.showerror(
            "Manjkajoče knjižnice",
            "Ta program potrebuje knjižnice 'pandas' in 'openpyxl'.\n\n"
            "Zaženi v ukazni vrstici:\n  python -m pip install pandas openpyxl"
        )
    except Exception:
        print("Manjkajoče knjižnice: namestite 'pandas' in 'openpyxl' (python -m pip install pandas openpyxl).", file=sys.stderr)
    sys.exit(1)

VERSION = "v 39 – 2025-10-22"

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    _TZ = ZoneInfo("Europe/Ljubljana")
except Exception:
    _TZ = None

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_PATH = SCRIPT_DIR / f"validator_v39_{datetime.date.today().isoformat()}.log"

def _get_user_identity() -> str:
    try:
        user = os.getlogin()
    except Exception:
        user = os.environ.get("USERNAME") or os.environ.get("USER") or "neznano"
    host = platform.node() or "neznan-računalnik"
    return f"{host} / {user}"

def init_log() -> None:
    now_dt = datetime.datetime.now(_TZ) if _TZ else datetime.datetime.now()
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    header = [
        f"Zagon: {now}",
        f"Verzija: {VERSION}",
        f"Uporabnik: {_get_user_identity()}",
        ""
    ]
    try:
        LOG_PATH.write_text("\n".join(header), encoding="utf-8")
    except Exception:
        pass

def append_log(line: str) -> None:
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")
    except Exception:
        pass

# -------------------- Konstante (IPO struktura) --------------------

REQUIRED_COLUMNS = [
    "št. Koraka",
    "Navodilo",
    "Tip podatka",
    "Ključ preverjanja",
    "Vrednost",
    "Labela",
    "Tip objekta",
]

ALLOWED_TIP_OBJEKTA: Set[str] = {
    "edit", "checkbox", "crta",
    "formula", "formula0", "formula1",
    "gumbdatumcas", "izberidatumcas",
    "spustniseznam", "memo",
    "klictehtnice1",
    "naslov",
}

STANDARD_TIP_PODATKA = {
    "kemikalija", "masa", "embalaza",
    "datumcas", "datumcaszacetek", "datumcaskonec",
    "tehtnica", "termometer", "kopel",
    "zaposleni",
    "summasa", "masakonec",
    "monomerna", "monolit", "raztopina",
    "checkbox", "naslov", "crta", "memo", "formula",
    "repro", "reproodpis",
}

DATA_OBJECT_MAPPING: Dict[str, Set[str]] = {
    "kemikalija": {"edit"},
    "raztopina": {"edit"},
    "zaposleni": {"edit"},
    "monolit": {"edit"},
    "repro": {"edit"},
    "reproodpis": {"edit"},
    "masa": {"edit", "klictehtnice1"},
    "embalaza": {"edit"},
    "monomerna": {"edit"},
    "tehtnica": {"edit", "spustniseznam"},
    "termometer": {"edit", "spustniseznam"},
    "kopel": {"edit", "spustniseznam"},
    "summasa": {"edit", "formula", "formula0", "formula1"},
    "masakonec": {"edit"},
    "datumcas": {"gumbdatumcas", "izberidatumcas"},
    "datumcaszacetek": {"gumbdatumcas", "izberidatumcas"},
    "datumcaskonec": {"gumbdatumcas", "izberidatumcas"},
    "checkbox": {"checkbox"},
    "naslov": {"naslov"},
    "crta": {"crta"},
    "memo": {"memo"},
    "formula": {"formula", "formula0", "formula1"},
}

LABELA_KODA_TYPES = {"kemikalija", "zaposleni", "monolit", "repro", "reproodpis"}

KEY_PATTERN = re.compile(r"^[A-Za-z0-9_\-.]*$")
FORMULA_REF = re.compile(r"\$([0-9]+)")

CTRL_PAR1_PATTERNS = [
    re.compile(r"^kontrola\s*(?P<n>\d+)\s*(?:[-–:])?\s*par(?:am)?\s*1\s*$", re.IGNORECASE),
    re.compile(r"^p(?:ar|aram|m)\s*1\s*[,._-]?\s*(?P<n>\d+)\s*$", re.IGNORECASE),
]
CTRL_PAR2_PATTERNS = [
    re.compile(r"^kontrola\s*(?P<n>\d+)\s*(?:[-–:])?\s*par(?:am)?\s*2\s*$", re.IGNORECASE),
    re.compile(r"^p(?:ar|aram|m)\s*2\s*[,._-]?\s*(?P<n>\d+)\s*$", re.IGNORECASE),
]

ALLOWED_CONTROLS: Set[str] = {
    "kontrolapraznopolje", "kontrolainterval", "kontrolacasa",
    "aliobstajapogoj", "aliobstajapogoj_ali", "aliobkljukan", "aliniobkljukan",
    "kdoizpolni", "alipravavloga", "alipravavlogakoda",
    "zaklenipolja",
    "kontrolaveljavnostikemikalije", "kontrolaustreznostikemikalije",
    "kontrolamase", "kontrolarazmerjakemikalij",
    "kontrolaembalaze", "kontrolaprazneembalaze",
    "kontrolaveljavnostiopreme", "kontrolaustreznostiopreme", "kontrolaustreznostiopremeizmase",
    "kontrolaveljavnostimonolita", "kontrolaustreznostimonolita",
    "kontrolaveljavnostiraztopine", "kontrolaustreznostiraztopine",
    "kontrolaveljavnostirepro", "kontrolaustreznostirepro", "kontrolaprimernostirepro", "prenosrepro",
    "kontrolarazlika", "aliisto", "kontrolaistizapis",
    "kontrolaustreznostimonomerne", "kontrolaveljavnostimonomerne", "odpispraznemm",
}

EXCEL_ERROR_TOKENS = {"#REF!", "#N/A", "#DIV/0!", "#NAME?", "#NULL!", "#NUM!", "#VALUE!"}

def _is_excel_error_token(val: str) -> bool:
    return isinstance(val, str) and val.strip().upper() in EXCEL_ERROR_TOKENS

# -------------------- Pomožne funkcije --------------------

_INVISIBLE_WS = ("\u00A0", "\u200B", "\u200C", "\u200D", "\u2060")

def _norm_text(s: str) -> str:
    if not isinstance(s, str):
        s = "" if s is None else str(s)
    for ch in _INVISIBLE_WS:
        s = s.replace(ch, " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

def _norm_ctrl_name(s: str) -> str:
    s = _norm_text(s)
    s = re.sub(r"\s+", "", s)
    return s

def _norm_colnames(cols):
    cols = list(cols) if cols is not None else []
    return [(c.strip() if isinstance(c, str) else ("" if c is None else str(c))) for c in cols]

def _coerce_str(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()

def _lower(s: str) -> str:
    return s.lower().strip()

def _has_only_comma_separated_ints(s: str) -> bool:
    return bool(re.fullmatch(r"\s*\d+\s*(\s*,\s*\d+\s*)*\s*", s))

def base_key_no_trailing_number(key: str) -> str:
    return re.sub(r"[_\-\.\s]*\d+$", "", key.strip())

def extract_suffix_number(key: str) -> Tuple[str, int]:
    m = re.match(r"^(.*?)(\d+)$", key.strip())
    if m:
        return m.group(1), int(m.group(2))
    return (key.strip(), 0)

_EQUIP_KEYWORDS = [
    r"črpalka", r"crpalka", r"tehtnica", r"termometer", r"\bHPLC\b", r"pH\s*meter", r"\bVK\b", r"kopel"
]
EQUIPMENT_REGEX = re.compile("|".join(_EQUIP_KEYWORDS), flags=re.IGNORECASE)

def is_equipment_tip(tip_podatka: str) -> bool:
    t = _coerce_str(tip_podatka)
    if not t:
        return False
    if _lower(t) in {"tehtnica", "termometer", "kopel"}:
        return True
    return EQUIPMENT_REGEX.search(t) is not None

def has_equipment_with_key(df: pd.DataFrame, key: str) -> bool:
    if not key:
        return False
    for _, r in df.iterrows():
        if is_equipment_tip(_coerce_str(r.get("Tip podatka", ""))) and _coerce_str(r.get("Ključ preverjanja", "")) == key:
            return True
    return False

def is_equipment_row(tip_podatka_raw: str, present_names_ns: List[str]) -> bool:
    if is_equipment_tip(tip_podatka_raw):
        return True
    equipment_ctrls = {
        "kontrolaveljavnostiopreme",
        "kontrolaustreznostiopreme",
        "kontrolaustreznostiopremeizmase",
    }
    return any(c in present_names_ns for c in equipment_ctrls)

def _looks_like_number_with_commas(val: str) -> bool:
    if "," not in val:
        return False
    candidate = val.replace(",", "").strip()
    return bool(re.fullmatch(r"[+-]?\d+(\.\d+)?", candidate))

_NUMERIC_TOKEN_RE = re.compile(r"[+-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?")

def _parse_numeric_value(text: str) -> Optional[float]:
    s = _coerce_str(text)
    if not s:
        return None
    m = _NUMERIC_TOKEN_RE.search(s)
    if not m:
        return None
    token = m.group(0).replace(",", ".")
    try:
        return float(token)
    except Exception:
        return None

def _decimal_places_of_first_number(text: str) -> Optional[int]:
    s = _coerce_str(text)
    if not s:
        return None
    m = _NUMERIC_TOKEN_RE.search(s)
    if not m:
        return None
    token = m.group(0)
    if "," in token:
        frac = token.split(",", 1)[1]
    elif "." in token:
        frac = token.split(".", 1)[1]
    else:
        frac = ""
    if "e" in frac.lower():
        frac = frac.split("e", 1)[0]
    return len(frac) if frac else 0

_UNIT_TOKEN_RE = re.compile(
    r"\b(ml/min|l/min|ml|l|kg|g|°c|oc|c|mmol|mol|mm|cm|m|pa|bar)\b",
    flags=re.IGNORECASE
)

def _extract_unit_token(text: str) -> Optional[str]:
    s = _coerce_str(text)
    if not s:
        return None
    m = _UNIT_TOKEN_RE.search(s)
    if not m:
        return None
    token = m.group(1).replace("oc", "°c").lower()
    return token

def _derive_decimal_step_from_text(text: str) -> float:
    nums = [m.group(0) for m in _NUMERIC_TOKEN_RE.finditer(_coerce_str(text))]
    if not nums:
        return 1.0
    min_step = 1.0
    for tok in nums:
        if "," in tok:
            frac = tok.split(",", 1)[1]
        elif "." in tok:
            frac = tok.split(".", 1)[1]
        else:
            frac = ""
        if "e" in frac.lower():
            frac = frac.split("e", 1)[0]
        d = len(frac) if frac else 0
        step = 10 ** (-d) if d > 0 else 1.0
        if step < min_step:
            min_step = step
    return min_step

def _decimals_from_eps(eps: float) -> int:
    if eps <= 0:
        return 0
    for d in range(0, 12):
        if abs(eps - (10 ** (-d))) < 1e-12:
            return d
    try:
        d = int(round(-math.log10(eps)))
        return max(0, min(12, d))
    except Exception:
        return 0

def _eq_with_decimals(value: float, target: float, decimals: int) -> bool:
    return round(value, decimals) == round(target, decimals)

ALLOWED_CONTROLS_NS = {_norm_ctrl_name(x) for x in ALLOWED_CONTROLS}

def _find_column_index_ws(ws, header_name: str) -> Optional[int]:
    if ws is None:
        return None
    for j, cell in enumerate(ws[1], start=1):
        if (cell.value or "") == header_name:
            return j
    return None

def _excel_error_in_param1(ws_formula, ws_values, header_name: str, human_row: int) -> str:
    if ws_values is not None:
        ci = _find_column_index_ws(ws_values, header_name)
        if ci:
            cv = ws_values.cell(row=human_row, column=ci).value
            if isinstance(cv, str) and cv.strip().upper() in EXCEL_ERROR_TOKENS:
                return cv.strip().upper()
    if ws_formula is not None:
        ci = _find_column_index_ws(ws_formula, header_name)
        if ci:
            c = ws_formula.cell(row=human_row, column=ci)
            try:
                raw = "" if c.value is None else str(c.value)
                if "#REF!" in raw.upper():
                    return "#REF!"
            except Exception:
                pass
    return ""

# -------------------- Regexi za navodilo + INEQ --------------------

_RANGE_RE = re.compile(
    r"(?P<a>[+-]?\d+(?:[.,]\d+)?)\s*[-–—]\s*(?P<b>[+-]?\d+(?:[.,]\d+)?)(?:\s*(?P<unit>ml/min|l/min|ml|l|kg|g|°c|oc|c|mmol|mol|mm|cm|m|pa|bar))?",
    flags=re.IGNORECASE
)
_PM_RE = re.compile(
    r"(?P<x>[+-]?\d+(?:[.,]\d+)?)\s*(?:±|\+/-|\+\s*/\s*-)\s*(?P<t>\d+(?:[.,]\d+)?)(?:\s*(?P<unit>ml/min|l/min|ml|l|kg|g|°c|oc|c|mmol|mol|mm|cm|m|pa|bar))?",
    flags=re.IGNORECASE
)
_SINGLE_RE = re.compile(
    r"\b(?P<x>[+-]?\d+(?:[.,]\d+)?)(?:\s*(?P<unit>ml/min|l/min|ml|l|kg|g|°c|oc|c|mmol|mol|mm|cm|m|pa|bar))?\b",
    flags=re.IGNORECASE
)
_INEQ_RE = re.compile(
    r"(?P<op>>=|≥|>|<=|≤|<)\s*(?P<x>[+-]?\d+(?:[.,]\d+)?)(?:\s*(?P<unit>ml/min|l/min|ml|l|kg|g|°c|oc|c|mmol|mol|mm|cm|m|pa|bar))?",
    flags=re.IGNORECASE
)

def _choose_best_ineq_match(text: str):
    """Izberi najbolj 'specifično' neenačbo: prednost imajo ujemanja z enoto; pri izenačenju zadnje v besedilu."""
    cands = []
    for m in _INEQ_RE.finditer(text):
        score = 2 if m.group("unit") else 0
        cands.append((score, m.start(), m))
    if not cands:
        return None
    cands.sort(key=lambda t: (t[0], t[1]))
    return cands[-1][2]

def _choose_best_single_match(text: str):
    """Za eno številko brez simbola: prednost z enoto; pri izenačenju zadnja v besedilu."""
    cands = []
    for m in _SINGLE_RE.finditer(text):
        score = 2 if m.group("unit") else 0
        cands.append((score, m.start(), m))
    if not cands:
        return None
    cands.sort(key=lambda t: (t[0], t[1]))
    return cands[-1][2]

def _choose_best_range_match(text: str):
    """Če je več razponov, izberi tistega z enoto; pri izenačenju zadnji v besedilu."""
    cands = []
    for m in _RANGE_RE.finditer(text):
        score = 2 if m.group("unit") else 0
        cands.append((score, m.start(), m))
    if not cands:
        return None
    cands.sort(key=lambda t: (t[0], t[1]))
    return cands[-1][2]

def _parse_navodilo_interval(navodilo: str) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[float]]:
    text = _coerce_str(navodilo)
    m = _choose_best_range_match(text)
    if not m:
        return (None, None, None, None)
    a = float(m.group("a").replace(",", "."))
    b = float(m.group("b").replace(",", "."))
    unit = m.group("unit")
    if unit:
        unit = unit.replace("oc", "°c").lower()
    d1 = _decimal_places_of_first_number(m.group("a")) or 0
    d2 = _decimal_places_of_first_number(m.group("b")) or 0
    d = max(d1, d2)
    step = 10 ** (-d) if d > 0 else 1.0
    return (a, b, unit, step)

def _parse_navodilo_pm(navodilo: str) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[float]]:
    text = _coerce_str(navodilo)
    m = _PM_RE.search(text)
    if not m:
        return (None, None, None, None)
    x = float(m.group("x").replace(",", "."))
    t = float(m.group("t").replace(",", "."))
    unit = m.group("unit")
    if unit:
        unit = unit.replace("oc", "°c").lower()
    d1 = _decimal_places_of_first_number(m.group("x")) or 0
    d2 = _decimal_places_of_first_number(m.group("t")) or 0
    d = max(d1, d2)
    step = 10 ** (-d) if d > 0 else 1.0
    return (x, t, unit, step)

def _parse_navodilo_inequality(navodilo: str) -> Tuple[Optional[str], Optional[float], Optional[str], Optional[float]]:
    text = _coerce_str(navodilo)
    m = _choose_best_ineq_match(text)
    if not m:
        return (None, None, None, None)
    op_raw = m.group("op")
    if op_raw in (">=", "≥"): op = ">="
    elif op_raw in ("<=", "≤"): op = "<="
    elif op_raw == ">": op = ">"
    elif op_raw == "<": op = "<"
    else: op = None
    x = float(m.group("x").replace(",", "."))
    unit = m.group("unit")
    if unit:
        unit = unit.replace("oc", "°c").lower()
    d = _decimal_places_of_first_number(m.group("x")) or 0
    step = 10 ** (-d) if d > 0 else 1.0
    return (op, x, unit, step)

def _parse_navodilo_single(navodilo: str) -> Tuple[Optional[float], Optional[str], Optional[float]]:
    text = _coerce_str(navodilo)
    # Če je zaznan razpon/±/neenačba, ne obravnavamo 'single'
    if _RANGE_RE.search(text) or _PM_RE.search(text) or _INEQ_RE.search(text):
        return (None, None, None)
    m = _choose_best_single_match(text)
    if not m:
        return (None, None, None)
    x = float(m.group("x").replace(",", "."))
    unit = m.group("unit")
    if unit:
        unit = unit.replace("oc", "°c").lower()
    d = _decimal_places_of_first_number(m.group("x")) or 0
    step = 10 ** (-d) if d > 0 else 1.0
    return (x, unit, step)

# -------------------- Jedro validacije --------------------

def validate_dataframe(df: pd.DataFrame, origin: str,
                       ws_formula=None, ws_values=None) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    df = df.copy()
    df.columns = _norm_colnames(df.columns.tolist())

    # Par1/Par2 stolpci
    par1_cols, par2_cols = {}, {}
    for c in df.columns:
        if not isinstance(c, str): continue
        head = _norm_text(c)
        for pat in CTRL_PAR1_PATTERNS:
            m1 = pat.match(head)
            if m1:
                try:
                    par1_cols[int(m1.group('n'))] = c
                    break
                except Exception:
                    pass
        for pat in CTRL_PAR2_PATTERNS:
            m2 = pat.match(head)
            if m2:
                try:
                    par2_cols[int(m2.group('n'))] = c
                    break
                except Exception:
                    pass

    # 1) Obvezni stolpci
    for m in (c for c in REQUIRED_COLUMNS if c not in df.columns):
        issues.append(dict(sheet=origin, row="", col=m, severity="ERROR", code="MISSING_COLUMN",
                           message=f"Manjka obvezen stolpec: '{m}'"))

    # 1b) Številčenje korakov
    if "št. Koraka" in df.columns:
        step_vals = []
        for i, v in enumerate(df["št. Koraka"], start=2):
            s = _coerce_str(v)
            if not s: continue
            try:
                iv = int(s); step_vals.append((i, iv))
            except ValueError:
                issues.append(dict(sheet=origin, row=i, col="št. Koraka", severity="ERROR", code="STEP_NOT_INT",
                                   message=f"št. Koraka mora biti celo število, najdeno: {v!r}"))
        if step_vals:
            only = [iv for _, iv in step_vals]
            # Podvojeni koraki – preveri po skupinah 'Zavihek' (ali globalno, če stolpec ne obstaja)
            if "Zavihek" in df.columns:
                row_to_group = {i: _coerce_str(val) for i, val in enumerate(df["Zavihek"], start=2)}
            else:
                row_to_group = {i: "" for i, _ in step_vals}

            groups: Dict[str, List[Tuple[int, int]]] = {}
            for i, iv in step_vals:
                g = row_to_group.get(i, "")
                groups.setdefault(g, []).append((i, iv))

            for g, items in groups.items():
                ints = [iv for _, iv in items]
                dup_numbers = {x for x in set(ints) if ints.count(x) > 1}
                for d in sorted(dup_numbers):
                    rows = [r for (r, val) in items if val == d]
                    issues.append(dict(sheet=origin, row=",".join(map(str, rows)), col="št. Koraka",
                                       severity="ERROR", code="STEP_DUPLICATE",
                                       message=f"Podvojena številka koraka: {d}"))
            if min(only) == 1:
                expected = set(range(1, max(only) + 1))
                missing_steps = sorted(list(expected.difference(set(only))))
                if missing_steps:
                    issues.append(dict(sheet=origin, row="", col="št. Koraka", severity="ERROR", code="STEP_GAPS",
                                       message=f"Manjkajo koraki: {missing_steps}"))

    # 2) Vrstična preverjanja
    for idx, row in df.iterrows():
        human_row = idx + 2
        tip_podatka = _lower(_coerce_str(row.get("Tip podatka", "")))
        tip_podatka_raw = _coerce_str(row.get("Tip podatka", ""))
        tip_objekta = _lower(_coerce_str(row.get("Tip objekta", "")))
        kljuc = _coerce_str(row.get("Ključ preverjanja", ""))
        navodilo = _coerce_str(row.get("Navodilo", ""))
        vrednost = _coerce_str(row.get("Vrednost", ""))
        labela_val = _coerce_str(row.get("Labela", ""))
        labela = _lower(labela_val)

        if all(_coerce_str(row.get(c, "")) == "" for c in REQUIRED_COLUMNS):
            continue

        # 2.0 Tip objekta
        if not tip_objekta:
            issues.append(dict(sheet=origin, row=human_row, col="Tip objekta", severity="ERROR",
                               code="TIP_OBJEKTA_EMPTY",
                               message="Tip objekta ne sme biti prazen."))
        elif tip_objekta not in ALLOWED_TIP_OBJEKTA:
            issues.append(dict(sheet=origin, row=human_row, col="Tip objekta", severity="ERROR",
                               code="TIP_OBJEKTA_UNKNOWN",
                               message=f"Neznan Tip objekta: '{tip_objekta}'"))

        # 2.1 Tip podatka ↔ Tip objekta
        if tip_podatka in STANDARD_TIP_PODATKA:
            allowed = DATA_OBJECT_MAPPING.get(tip_podatka)
            if allowed and tip_objekta and tip_objekta not in allowed:
                issues.append(dict(sheet=origin, row=human_row, col="Tip objekta", severity="ERROR",
                                   code="OBJ_MISMATCH",
                                   message=f"'{tip_podatka}' zahteva Tip objekta {sorted(list(allowed))}, najdeno: '{tip_objekta}'"))

        # 2.2 Labela = 'koda' in enote Labela vs Navodilo
        if tip_podatka in LABELA_KODA_TYPES and labela != "koda":
            issues.append(dict(sheet=origin, row=human_row, col="Labela", severity="ERROR",
                               code="LABELA_KODA",
                               message=f"Za tip podatka '{tip_podatka}' mora biti Labela = 'koda'."))
        try:
            label_unit = _extract_unit_token(labela_val)
            nav_unit = _extract_unit_token(navodilo)
            if label_unit and nav_unit and label_unit != nav_unit:
                issues.append(dict(
                    sheet=origin,
                    row=human_row,
                    col="Labela",
                    severity="ERROR",
                    code="UNIT_MISMATCH",
                    message=f"Enota v 'Labela' ({label_unit}) se ne ujema z enoto v 'Navodilo' ({nav_unit})."
                ))
        except Exception:
            pass

        # 2.3 Ključ – allowed chars
        if kljuc and not KEY_PATTERN.match(kljuc):
            issues.append(dict(sheet=origin, row=human_row, col="Ključ preverjanja", severity="ERROR",
                               code="KEY_FORMAT",
                               message=f"Ključ preverjanja '{kljuc}' vsebuje nedovoljene znake (dovoljeni: črke, številke, _, - in .)."))

        # 2.4 Formule
        if tip_objekta in {"formula", "formula0", "formula1"}:
            if not vrednost.startswith("="):
                issues.append(dict(sheet=origin, row=human_row, col="Vrednost", severity="ERROR",
                                   code="FORMULA_SYNTAX",
                                   message="Pri formulskih objektih mora 'Vrednost' začeti z '=' in uporabljati $korake (npr. =$12+$13)."))
            if "$" not in vrednost:
                issues.append(dict(sheet=origin, row=human_row, col="Vrednost", severity="WARNING",
                                   code="FORMULA_NOREF",
                                   message="Formula ne vsebuje sklica na korake (npr. $12). Preveri sklice."))

        # 2.5 Vejice – decimalna pika je pravilo, razen v dovoljenih
        allowed_comma_cols = {"Navodilo"}

        # Kontrole v vrstici + dodatna pravila
        control_name_by_n: Dict[int, str] = {}
        for c in df.columns:
            if not isinstance(c, str): continue
            head = _norm_text(c)
            m2 = re.fullmatch(r"kontrola\s*[-–:]?\s*(\d+)\s*", head, flags=re.I)
            if not m2: continue
            n = int(m2.group(1))
            cname_raw = _coerce_str(row.get(c, ""))
            cname_ns = _norm_ctrl_name(cname_raw)
            control_name_by_n[n] = cname_ns

        for n, cname_ns in control_name_by_n.items():
            if cname_ns in {"zaklenipolja", "aliobstajapogoj"}:
                par1_col = par1_cols.get(n)
                if not par1_col:
                    for c in df.columns:
                        head2 = _norm_text(c)
                        for pat in CTRL_PAR1_PATTERNS:
                            m = pat.match(head2)
                            if m and _coerce_str(m.group('n')) == _coerce_str(n):
                                par1_col = c
                                break
                        if par1_col:
                            break
                if par1_col:
                    allowed_comma_cols.add(par1_col)

                    if cname_ns == "zaklenipolja":
                        par1_val = _coerce_str(row.get(par1_col, ""))
                        err_tok = _excel_error_in_param1(ws_formula, ws_values, par1_col, human_row)
                        if err_tok:
                            issues.append(dict(
                                sheet=origin, row=human_row, col=par1_col, severity="ERROR",
                                code="ZAKLENI_PAR1_EXCEL_ERR",
                                message=f"Kontrola 'zaklenipolja': Param1 vsebuje Excel napako ({err_tok})."
                            ))
                        elif par1_val and not _has_only_comma_separated_ints(par1_val):
                            issues.append(dict(sheet=origin, row=human_row, col=par1_col, severity="ERROR",
                                               code="ZAKLENI_PAR1_FORMAT",
                                               message="Kontrola 'zaklenipolja': 'par-1' mora biti seznam CELIH ŠTEVIL, ločenih z vejicami (npr. 12, 13, 14)."))

                if cname_ns == "aliobstajapogoj" and par1_col:
                    par1_val = _coerce_str(row.get(par1_col, ""))
                    if par1_val:
                        tokens = [t.strip() for t in par1_val.split(",")]
                        bad = [t for t in tokens if not t or not KEY_PATTERN.fullmatch(t)]
                        if bad:
                            issues.append(dict(
                                sheet=origin, row=human_row, col=par1_col, severity="ERROR",
                                code="P1_KEYS_FORMAT",
                                message=f"aliObstajaPogoj Param1 mora biti seznam ključev, ločenih z vejico. Neveljavno: {bad}"
                            ))

        # Vejice – napaka pri številih (razen dovoljenih)
        for j, c in enumerate(df.columns):
            if c in allowed_comma_cols: continue
            if j == 0: continue
            val = _coerce_str(row.get(c, ""))
            if not val or "," not in val: continue
            if _looks_like_number_with_commas(val):
                issues.append(dict(sheet=origin, row=human_row, col=c, severity="ERROR",
                                   code="COMMA_NOT_ALLOWED",
                                   message=f"Vrednost v '{c}' vsebuje vejico v številu (ni dovoljeno). Uporabi decimalno piko."))

    # --------- Relacije/pari po ključu ---------

    def collect_by_key(tname: str) -> Dict[str, List[int]]:
        pos: Dict[str, List[int]] = {}
        for idx, row in df.iterrows():
            if _lower(_coerce_str(row.get("Tip podatka", ""))) != tname:
                continue
            key = _coerce_str(row.get("Ključ preverjanja", ""))
            if not key: continue
            pos.setdefault(key, []).append(idx + 2)
        return pos

    kemikalija_by_key = collect_by_key("kemikalija")
    raztopina_by_key = collect_by_key("raztopina")
    masa_by_key = collect_by_key("masa")
    zacetek_by_key = collect_by_key("datumcaszacetek")
    konec_by_key = collect_by_key("datumcaskonec")

    # ---- Podvojeni ključi ----
    for k, rows in kemikalija_by_key.items():
        if len(rows) > 1:
            issues.append(dict(sheet=origin, row=",".join(map(str, rows)), col="Ključ preverjanja",
                               severity="ERROR", code="KEY_DUP_KEM",
                               message=f"Podvojen ključ '{k}' za tip 'kemikalija'."))

    for k, rows in raztopina_by_key.items():
        if len(rows) > 1:
            issues.append(dict(sheet=origin, row=",".join(map(str, rows)), col="Ključ preverjanja",
                               severity="ERROR", code="KEY_DUP_RAZT",
                               message=f"Podvojen ključ '{k}' za tip 'raztopina'."))

    for k, rows in masa_by_key.items():
        if len(rows) > 1:
            issues.append(dict(sheet=origin, row=",".join(map(str, rows)), col="Ključ preverjanja",
                               severity="ERROR", code="KEY_DUP_MASA",
                               message=f"Podvojen ključ '{k}' za tip 'masa'."))

    kem_or_raz = set(kemikalija_by_key) | set(raztopina_by_key)

    def _is_water_key(k: str) -> bool:
        if not k: return False
        s = str(k).strip()
        base = re.sub(r"[_\-\.\s]*\d+$", "", s)
        return _lower(base) in {"dh2o", "h2o"}

    for k in sorted(set(masa_by_key) - kem_or_raz):
        if _is_water_key(k): continue
        rows = masa_by_key[k]
        issues.append(dict(sheet=origin, row=",".join(map(str, rows)), col="Ključ preverjanja",
                           severity="ERROR", code="PAIR_MASA_NO_OWNER",
                           message=f"Za maso s ključem '{k}' ne obstaja ustrezna 'kemikalija' ali 'raztopina'."))

    # časovni pari
    for k in sorted(set(zacetek_by_key) - set(konec_by_key)):
        rows = zacetek_by_key[k]
        issues.append(dict(sheet=origin, row=",".join(map(str, rows)), col="Ključ preverjanja",
                           severity="ERROR", code="PAIR_TIME_NO_END",
                           message=f"Za 'datumcaszacetek' ključ '{k}' manjka ustrezen 'datumcaskonec'."))
    for k in sorted(set(konec_by_key) - set(zacetek_by_key)):
        rows = konec_by_key[k]
        issues.append(dict(sheet=origin, row=",".join(map(str, rows)), col="Ključ preverjanja",
                           severity="ERROR", code="PAIR_TIME_NO_START",
                           message=f"Za 'datumcaskonec' ključ '{k}' manjka ustrezen 'datumcaszacetek'."))

    # 3) Formule → sklici na obstoječe korake + oštevilčenje ključev
    if {"Tip objekta", "Vrednost", "št. Koraka"}.issubset(df.columns):
        existing_steps = {int(_coerce_str(v)) for v in df["št. Koraka"] if _coerce_str(v).isdigit()}
        for idx, row in df.iterrows():
            r = idx + 2
            if _lower(_coerce_str(row.get("Tip objekta", ""))) in {"formula", "formula0", "formula1"}:
                val = _coerce_str(row.get("Vrednost", ""))
                for m in FORMULA_REF.finditer(val):
                    step = int(m.group(1))
                    if step not in existing_steps:
                        issues.append(dict(sheet=origin, row=r, col="Vrednost", severity="ERROR",
                                           code="FORMULA_BAD_REF",
                                           message=f"Formula se sklicuje na neobstoječi korak ${step}."))

        # Oštevilčenje ključev — kemikalija/raztopina/masa
        allowed_types_for_numbering = {"kemikalija", "raztopina", "masa"}
        keys_for_numbering: List[str] = []
        for _, r in df.iterrows():
            t = _lower(_coerce_str(r.get("Tip podatka", "")))
            if t in allowed_types_for_numbering:
                k = _coerce_str(r.get("Ključ preverjanja", ""))
                if k: keys_for_numbering.append(k)

        state: Dict[str, Dict[str, Any]] = {}  # base -> {"bare": bool, "nums": set()}
        for key in keys_for_numbering:
            base, num = extract_suffix_number(key)
            st = state.setdefault(base, {"bare": False, "nums": set()})
            if num > 0: st["nums"].add(num)
            else:
                st["bare"] = True
                st["nums"].add(1)

        for base, st in state.items():
            nums_sorted = sorted(st["nums"])
            if nums_sorted and nums_sorted[0] != 1:
                issues.append(dict(sheet=origin, row="", col="Ključ preverjanja", severity="ERROR",
                                   code="KEY_NUM_START",
                                   message=f"Ključ '{base}…' začetek oštevilčenja ni 1 (najdeno {nums_sorted[0]})."))
            for n in range(1, nums_sorted[-1] + 1):
                if n not in st["nums"]:
                    issues.append(dict(sheet=origin, row="", col="Ključ preverjanja", severity="ERROR",
                                       code="KEY_NUM_GAP",
                                       message=f"Ključ '{base}{n}' manjka v zaporedju (preskok)."))
            if st["bare"] and 1 in st["nums"] and len(st["nums"]) > 1:
                issues.append(dict(sheet=origin, row="", col="Ključ preverjanja", severity="WARNING",
                                   code="KEY_NUM_DUPLICATE_ONE",
                                   message=f"Za bazo '{base}' sta uporabljena tako goli ključ ('{base}') kot '{base}1'. Uporabi le en stil."))

    # 4) Kontrole – prisotnost, kontekst in parametri (vključno z novimi INEQ pravili)
    existing_keys = {k for k in df.get("Ključ preverjanja", []) if k}
    control_cols: List[str] = []
    for c in df.columns:
        if not isinstance(c, str): continue
        head = _norm_text(c)
        if re.fullmatch(r"kontrola\s*[-–:]?\s*\d+\s*", head, flags=re.I):
            control_cols.append(c)
    control_cols.sort(key=lambda x: int(re.findall(r"\d+", _norm_text(x))[0]))

    for idx, row in df.iterrows():
        human_row = idx + 2
        tip_data = _lower(_coerce_str(row.get("Tip podatka", "")))
        tip_data_raw = _coerce_str(row.get("Tip podatka", ""))
        tip_obj  = _lower(_coerce_str(row.get("Tip objekta", "")))
        key_here = _coerce_str(row.get("Ključ preverjanja", ""))
        navodilo = _coerce_str(row.get("Navodilo", ""))

        present_ctrls: List[Tuple[str, str, str, str, str]] = []
        present_names_ns: List[str] = []
        for c in control_cols:
            cname_raw = _coerce_str(row.get(c, ""))
            if not cname_raw: continue
            n = int(re.findall(r"\d+", _norm_text(c))[0])
            p1c = par1_cols.get(n); p2c = par2_cols.get(n)
            cname_ns = _norm_ctrl_name(cname_raw)
            present_ctrls.append((cname_ns, cname_raw, c, p1c, p2c))
            present_names_ns.append(cname_ns)

        nav_n = _norm_text(navodilo)
        is_hplc_pump = bool(re.search(r"hplc\s*[-–]?\s*(?:č|c)rpalka\b", nav_n))

        if "zaklenipolja" in present_names_ns and "aliobkljukan" in present_names_ns:
            ali_cols = [ccol for (cname_ns, _, ccol, _, _) in present_ctrls if cname_ns == "aliobkljukan"]
            col_ref = ali_cols[0] if ali_cols else "(Kontrole)"
            issues.append(dict(
                sheet=origin, row=human_row, col=col_ref, severity="ERROR",
                code="CTRL_LOCKED_NO_CHECK",
                message="Pri 'zaklenipolja' ni dovoljena kontrola 'aliObkljukan'. Odstrani 'aliObkljukan' ali ne uporabi 'zaklenipolja'."
            ))

        if tip_obj in {"edit", "spustniseznam", "izberidatumcas", "gumbdatumcas", "memo"}:
            if "kontrolapraznopolje" not in present_names_ns:
                issues.append(dict(sheet=origin, row=human_row, col="(Kontrole)", severity="ERROR",
                                   code="CTRL_REQUIRED_EMPTY",
                                   message="Manjka kontrola 'kontrolaPraznoPolje' pri vnosnem polju."))
        if tip_obj == "checkbox" and "kontrolapraznopolje" in present_names_ns:
            issues.append(dict(sheet=origin, row=human_row, col="(Kontrole)", severity="ERROR",
                               code="CTRL_CHECKBOX_EMPTY",
                               message="Checkbox ne sme imeti 'kontrolaPraznoPolje'."))

        def warn_if_missing_any(one_of: List[str], label: str):
            if not any(c in present_names_ns for c in one_of):
                issues.append(dict(
                    sheet=origin, row=human_row, col="(Kontrole)", severity="WARNING",
                    code="CTRL_EXPECTED_MISSING",
                    message=f"{label} manjka: pričakovana vsaj ena od {one_of}"
                ))

        tip_n = _norm_text(tip_data)

        if tip_n == "kemikalija":
            for needed in [["kontrolaveljavnostikemikalije"], ["kontrolaustreznostikemikalije"]]:
                warn_if_missing_any(needed, "Kemikalija – pričakovane kontrole")

        if tip_n == "masa":
            porabljan_word = bool(re.search(r"\bporabljen(?:o|a)?\b|\bporabljano\b|\bporabljena\b", nav_n, flags=re.IGNORECASE))
            volume_number_present = bool(re.search(r"\d+(?:[.,]\d+)?\s*(?:ml|l)\b", nav_n, flags=re.IGNORECASE))
            has_concentration = bool(re.search(r"\b(?:mg|g)\s*/\s*ml\b", nav_n, flags=re.IGNORECASE))
            label_unit_token = _extract_unit_token(row.get("Labela", ""))
            nav_unit_token = _extract_unit_token(navodilo)
            any_volume_unit = (label_unit_token in {"ml", "l"}) or (nav_unit_token in {"ml", "l"})
            concentration_implies_volume = has_concentration and any_volume_unit
            no_numeric_in_navodilo = not bool(_NUMERIC_TOKEN_RE.search(nav_n))
            vrednost_has_number = bool(_NUMERIC_TOKEN_RE.search(_coerce_str(row.get("Vrednost", ""))))
            masa_is_exception = (porabljan_word or volume_number_present or concentration_implies_volume or no_numeric_in_navodilo) and (not vrednost_has_number)
            if not masa_is_exception:
                warn_if_missing_any(["kontrolamase", "kontrolainterval", "kontrolarazlika"], "Masa – pričakovane kontrole")

        if tip_n == "embalaza":
            for needed in [["kontrolaembalaze"], ["kontrolaprazneembalaze"]]:
                warn_if_missing_any(needed, "Embalaža – pričakovana kontrola")

        if tip_n == "datumcaskonec":
            warn_if_missing_any(["kontrolacasa"], "DatumCasKonec – pričakovana kontrola trajanja")

        if is_equipment_row(tip_podatka_raw, present_names_ns):
            if not is_hplc_pump:
                warn_if_missing_any(["kontrolaveljavnostiopreme"], "Oprema – pričakovana kontrola veljavnosti")
                warn_if_missing_any(["kontrolaustreznostiopreme"], "Oprema – pričakovana kontrola ustreznosti")

        if tip_n.startswith("monolit"):
            warn_if_missing_any(["kontrolaveljavnostimonolita"], "Monolit – pričakovana kontrola veljavnosti")
            warn_if_missing_any(["kontrolaustreznostimonolita"], "Monolit – pričakovana kontrola ustreznosti")
        if tip_n.startswith("raztopina"):
            warn_if_missing_any(["kontrolaveljavnostiraztopine"], "Raztopina – pričakovana kontrola veljavnosti")
            warn_if_missing_any(["kontrolaustreznostiraztopine"], "Raztopina – pričakovana kontrola ustreznosti")

        equipment_ctrls_ns = {
            "kontrolaveljavnostiopreme",
            "kontrolaustreznostiopreme",
            "kontrolaustreznostiopremeizmase",
        }

        for (cname_ns, cname_raw, ccol, p1c, p2c) in present_ctrls:
            if cname_ns not in ALLOWED_CONTROLS_NS:
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_UNKNOWN",
                                   message=f"Neznano ime kontrole: '{cname_raw}'"))

            if is_hplc_pump and cname_ns in equipment_ctrls_ns:
                continue

            def equipment_context_ok() -> bool:
                return is_equipment_tip(tip_podatka_raw) or has_equipment_with_key(df, key_here)

            if cname_ns in {"kontrolaveljavnostikemikalije", "kontrolaustreznostikemikalije"} and tip_data != "kemikalija":
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_BAD_CONTEXT",
                                   message=f"Kontrola '{cname_raw}' je na polju, ki ni 'kemikalija'."))

            if cname_ns == "kontrolamase" and tip_data != "masa":
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_BAD_CONTEXT",
                                   message=f"Kontrola '{cname_raw}' je na polju, ki ni 'masa'."))

            if cname_ns in {"kontrolaembalaze", "kontrolaprazneembalaze"} and tip_data != "embalaza":
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_BAD_CONTEXT",
                                   message=f"Kontrola '{cname_raw}' je na polju, ki ni 'embalaza'."))

            if cname_ns in equipment_ctrls_ns and not equipment_context_ok():
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_BAD_CONTEXT",
                                   message=f"Kontrola '{cname_raw}' mora biti na opremi ali povezani vrstici (isti ključ kot oprema)."))

            if cname_ns in {"kontrolaveljavnostimonolita", "kontrolaustreznostimonolita"} and not tip_data.startswith("monolit"):
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_BAD_CONTEXT",
                                   message=f"Kontrola '{cname_raw}' je na polju, ki ni 'monolit'."))

            if cname_ns in {"kontrolaveljavnostiraztopine", "kontrolaustreznostiraztopine"} and not tip_data.startswith("raztopina"):
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_BAD_CONTEXT",
                                   message=f"Kontrola '{cname_raw}' je na polju, ki ni 'raztopina'."))

            if cname_ns == "kontrolacasa" and tip_data != "datumcaskonec":
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_BAD_CONTEXT",
                                   message="Kontrola 'kontrolaCasa' naj bo na zaključnem času (datumcaskonec)."))

            if cname_ns in {"aliobkljukan", "aliniobkljukan"} and tip_obj  != "checkbox":
                issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                   code="CTRL_BAD_CONTEXT",
                                   message=f"Kontrola '{cname_raw}' je smiselna le na checkbox poljih."))

            # Parametri
            p1 = _coerce_str(row.get(p1c, "")) if p1c else ""
            p2 = _coerce_str(row.get(p2c, "")) if p2c else ""

            def _f(s: str) -> Optional[float]:
                try: return float(s.replace(",", "."))
                except Exception: return None

            if cname_ns == "kontrolainterval":
                if not p1 and not p2:
                    issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                       code="CTRL_INTERVAL_PARAMS",
                                       message="kontrolaInterval brez Param1/Param2 (vsaj ena meja mora biti podana)."))
                p1_is_num = _f(p1) is not None if p1 else False
                p2_is_num = _f(p2) is not None if p2 else False
                if p1 and not p1_is_num:
                    issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                       code="CTRL_INTERVAL_NUM",
                                       message=f"kontrolaInterval Param1 '{p1}' ni številčna."))
                if p2 and not p2_is_num:
                    issues.append(dict(sheet=origin, row=human_row, col=p2c or ccol, severity="ERROR",
                                       code="CTRL_INTERVAL_NUM",
                                       message=f"kontrolaInterval Param2 '{p2}' ni številčna."))
                if p1_is_num and p2_is_num:
                    try:
                        if float(p2.replace(",", ".")) <= float(p1.replace(",", ".")):
                            issues.append(dict(sheet=origin, row=human_row, col=p2c or ccol, severity="ERROR",
                                               code="CTRL_INTERVAL_ORDER",
                                               message="kontrolaInterval: Param2 (max) ≤ Param1 (min)."))
                    except Exception:
                        pass

                # parsing navodila
                a, b, unit_ab, step_ab = _parse_navodilo_interval(navodilo)
                xpm, tpm, unit_pm, step_pm = _parse_navodilo_pm(navodilo)
                op, xi, unit_in, step_in = _parse_navodilo_inequality(navodilo)
                xs, unit_s, step_s = _parse_navodilo_single(navodilo)

                p1v = _f(p1) if p1_is_num else None
                p2v = _f(p2) if p2_is_num else None

                # ---------- STROGO PRAVILO ----------
                # a) Razpon a–b
                if a is not None and b is not None and p1v is not None and p2v is not None:
                    eps = step_ab if step_ab is not None else _derive_decimal_step_from_text(navodilo)
                    d_exact = _decimals_from_eps(eps)
                    if not _eq_with_decimals(p1v, a - eps, d_exact):
                        issues.append(dict(
                            sheet=origin,
                            row=human_row,
                            col=p1c or ccol,
                            severity="ERROR",
                            code="CTRL_INTERVAL_RANGE_P1_EXACT",
                            message=(
                                f"Param1 mora biti {a - eps:.{d_exact}f} – spodnja meja iz navodila {navodilo}. "
                                f"({a:.{d_exact}f} − korak = {a - eps:.{d_exact}f})"
                            )
                        ))
                    if not _eq_with_decimals(p2v, b + eps, d_exact):
                        issues.append(dict(
                            sheet=origin,
                            row=human_row,
                            col=p2c or ccol,
                            severity="ERROR",
                            code="CTRL_INTERVAL_RANGE_P2_EXACT",
                            message=(
                                f"Param2 mora biti {b + eps:.{d_exact}f} – zgornja meja iz navodila {navodilo}. "
                                f"({b:.{d_exact}f} + korak = {b + eps:.{d_exact}f})"
                            )
                        ))

                # b) x ± t
                elif xpm is not None and tpm is not None and p1v is not None and p2v is not None:
                    eps = step_pm if step_pm is not None else _derive_decimal_step_from_text(navodilo)
                    d_exact = _decimals_from_eps(eps)
                    left_req  = xpm - (tpm + eps)
                    right_req = xpm + (tpm + eps)
                    if not _eq_with_decimals(p1v, left_req, d_exact):
                        issues.append(dict(
                            sheet=origin,
                            row=human_row,
                            col=p1c or ccol,
                            severity="ERROR",
                            code="CTRL_INTERVAL_PM_P1_EXACT",
                            message=(
                                f"Param1 mora biti {left_req:.{d_exact}f} – iz {xpm:.{d_exact}f} ± {tpm:.{d_exact}f}."
                            )
                        ))
                    if not _eq_with_decimals(p2v, right_req, d_exact):
                        issues.append(dict(
                            sheet=origin,
                            row=human_row,
                            col=p2c or ccol,
                            severity="ERROR",
                            code="CTRL_INTERVAL_PM_P2_EXACT",
                            message=(
                                f"Param2 mora biti {right_req:.{d_exact}f} – iz {xpm:.{d_exact}f} ± {tpm:.{d_exact}f}."
                            )
                        ))

                # c) Neenačbe
                elif op is not None and xi is not None:
                    eps = step_in if step_in is not None else _derive_decimal_step_from_text(navodilo)
                    d_exact = _decimals_from_eps(eps)

                    if op in (">", ">="):
                        # Param1 = X−eps (EXACT), Param2 ≥ X+eps
                        if not (p1_is_num and _eq_with_decimals(p1v, xi - eps, d_exact)):
                            issues.append(dict(
                                sheet=origin,
                                row=human_row,
                                col=p1c or ccol,
                                severity="ERROR",
                                code="CTRL_INTERVAL_TARGET_P1_EXACT",
                                message=(
                                    f"Param1 mora biti {xi - eps:.{d_exact}f} – spodnja meja iz navodila {navodilo}. "
                                    f"({xi:.{d_exact}f} − korak = {xi - eps:.{d_exact}f})"
                                )
                            ))
                        if not (p2_is_num and (p2v is not None) and (round(p2v, d_exact) >= round(xi + eps, d_exact))):
                            issues.append(dict(
                                sheet=origin,
                                row=human_row,
                                col=p2c or ccol,
                                severity="ERROR",
                                code="CTRL_INTERVAL_TARGET_P2_MIN",
                                message=(
                                    f"Param2 mora biti ≥ {xi + eps:.{d_exact}f} – zgornja meja iz navodila {navodilo}. "
                                    f"({xi:.{d_exact}f} + korak = {xi + eps:.{d_exact}f})"
                                )
                            ))

                    elif op in ("<", "<="):
                        # Param1 ≤ X−eps, Param2 = X+eps (EXACT)
                        if not (p1_is_num and (p1v is not None) and (round(p1v, d_exact) <= round(xi - eps, d_exact))):
                            issues.append(dict(
                                sheet=origin,
                                row=human_row,
                                col=p1c or ccol,
                                severity="ERROR",
                                code="CTRL_INTERVAL_TARGET_P1_MAX",
                                message=(
                                    f"Param1 mora biti ≤ {xi - eps:.{d_exact}f} – iz navodila {navodilo}. "
                                    f"({xi:.{d_exact}f} − korak = {xi - eps:.{d_exact}f})"
                                )
                            ))
                        if not (p2_is_num and _eq_with_decimals(p2v, xi + eps, d_exact)):
                            issues.append(dict(
                                sheet=origin,
                                row=human_row,
                                col=p2c or ccol,
                                severity="ERROR",
                                code="CTRL_INTERVAL_TARGET_P2_EXACT",
                                message=(
                                    f"Param2 mora biti {xi + eps:.{d_exact}f} – zgornja meja iz navodila {navodilo}. "
                                    f"({xi:.{d_exact}f} + korak = {xi + eps:.{d_exact}f})"
                                )
                            ))

                # d) ENA ciljna vrednost X
                elif xs is not None:
                    if not (p1_is_num and p2_is_num):
                        issues.append(dict(sheet=origin, row=human_row, col=ccol, severity="ERROR",
                                           code="CTRL_INTERVAL_NAVODILO_RULE",
                                           message="kontrolaInterval vs. navodilo (X): pričakovani sta številčni Param1 in Param2."))
                    else:
                        eps = step_s if step_s is not None else _derive_decimal_step_from_text(navodilo)
                        d_exact = _decimals_from_eps(eps)
                        if not _eq_with_decimals(p1v, xs - eps, d_exact):
                            issues.append(dict(
                                sheet=origin,
                                row=human_row,
                                col=p1c or ccol,
                                severity="ERROR",
                                code="CTRL_INTERVAL_TARGET_P1_EXACT",
                                message=(
                                    f"Param1 mora biti {xs - eps:.{d_exact}f} – iz {xs:.{d_exact}f}."
                                )
                            ))
                        if not _eq_with_decimals(p2v, xs + eps, d_exact):
                            issues.append(dict(
                                sheet=origin,
                                row=human_row,
                                col=p2c or ccol,
                                severity="ERROR",
                                code="CTRL_INTERVAL_TARGET_P2_EXACT",
                                message=(
                                    f"Param2 mora biti {xs + eps:.{d_exact}f} – iz {xs:.{d_exact}f}."
                                )
                            ))

            # ostale kontrole
            if cname_ns == "kontrolacasa":
                if not p1:
                    issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                       code="CTRL_CASA_MIN",
                                       message="kontrolaCasa zahteva Param1 (min trajanje v sekundah)."))
                else:
                    try: float(p1)
                    except: issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                               code="CTRL_CASA_MIN_NUM",
                                               message=f"kontrolaCasa Param1 '{p1}' ni številčna."))
                if p2:
                    try:
                        if p1 and float(p2.replace(",", ".")) < float(p1.replace(",", ".")):
                            issues.append(dict(sheet=origin, row=human_row, col=p2c or ccol, severity="WARNING",
                                               code="CTRL_CASA_ORDER",
                                               message="kontrolaCasa Param2 (max) < Param1 (min)."))
                    except:
                        issues.append(dict(sheet=origin, row=human_row, col=p2c or ccol, severity="ERROR",
                                           code="CTRL_CASA_MAX_NUM",
                                           message=f"kontrolaCasa Param2 '{p2}' ni številčna."))

            if cname_ns in {"kdoizpolni", "alipravavloga", "alipravavlogakoda"}:
                if not p1:
                    issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                       code="CTRL_ROLE_PARAM",
                                       message=f"Kontrola '{cname_raw}' zahteva parameter vloge (Param1)."))

            if cname_ns == "aliobstajapogoj":
                if not p1:
                    issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                       code="CTRL_POGOJ_P1",
                                       message="aliObstajaPogoj zahteva Param1 (referenčni ključ ali seznam ključev, ločenih z vejico)."))
                else:
                    keys = [t.strip() for t in p1.split(",") if t.strip()]
                    bad = [k for k in keys if not KEY_PATTERN.fullmatch(k)]
                    if bad:
                        issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                           code="CTRL_POGOJ_P1_FORMAT",
                                           message=f"aliObstajaPogoj Param1 vsebuje neveljavne ključe: {bad}"))
                    missing = [k for k in keys if k not in existing_keys]
                    if missing:
                        issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                           code="CTRL_POGOJ_KEY",
                                           message=f"aliObstajaPogoj referencira neobstoječe ključe: {missing}"))
                if not p2:
                    issues.append(dict(sheet=origin, row=human_row, col=p2c or ccol, severity="ERROR",
                                       code="CTRL_POGOJ_P2",
                                       message="aliObstajaPogoj zahteva Param2 (0/1)."))
                else:
                    p2_clean = p2.strip().lower()
                    valid_bool = False
                    try:
                        num = float(p2_clean.replace(",", "."))
                        if num in (0.0, 1.0): valid_bool = True
                    except:
                        pass
                    if p2_clean in {"0", "1"}:
                        valid_bool = True
                    if not valid_bool:
                        issues.append(dict(sheet=origin, row=human_row, col=p2c or ccol, severity="ERROR",
                                           code="CTRL_POGOJ_VAL",
                                           message=f"aliObstajaPogoj Param2 '{p2}' mora biti 0 ali 1."))

            if cname_ns in {"kontrolaveljavnostiraztopine", "kontrolaustreznostiraztopine"}:
                base = base_key_no_trailing_number(key_here) if key_here else ""
                if not key_here:
                    issues.append(dict(sheet=origin, row=human_row, col="Ključ preverjanja", severity="ERROR",
                                       code="SOLUTION_KEY_MISSING",
                                       message="Kontrola raztopine zahteva nastavljen 'Ključ preverjanja' v vrstici."))
                elif not p1:
                    issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                       code="SOLUTION_P1_MISSING",
                                       message="Kontrola raztopine zahteva Param1 = baza ključa (npr. EtOH1 → EtOH)."))
                elif p1 != base:
                    issues.append(dict(sheet=origin, row=human_row, col=p1c or ccol, severity="ERROR",
                                       code="SOLUTION_P1_BASE",
                                       message=f"Param1='{p1}' ne ustreza bazi ključa '{base}'."))

    # 6) Oprema ↔ povezava prek ključa (HPLC BYPASS)
    for idx, row in df.iterrows():
        tip_data_raw = _coerce_str(row.get("Tip podatka", ""))
        key = _coerce_str(row.get("Ključ preverjanja", ""))
        navodilo = _coerce_str(row.get("Navodilo", ""))
        nav_n = _norm_text(navodilo)
        is_hplc_pump = bool(re.search(r"hplc\s*[-–]?\s*(?:č|c)rpalka\b", nav_n))
        if is_hplc_pump:
            continue
        if is_equipment_tip(tip_data_raw) and key:
            if _lower(key) == "monomerna":
                if not any(_lower(_coerce_str(t)) == "monomerna" for t in df.get("Tip podatka", [])):
                    issues.append(dict(sheet=origin, row=idx+2, col="Ključ preverjanja", severity="ERROR",
                                       code="EQ_MONOMERNA",
                                       message="Oprema 'monomerna' brez definicije monomerne mešanice."))
            else:
                linked = any(
                    _coerce_str(r.get("Ključ preverjanja", "")) == key and
                    not is_equipment_tip(_coerce_str(r.get("Tip podatka", "")))
                    for _, r in df.iterrows()
                )
                if not linked:
                    issues.append(dict(sheet=origin, row=idx+2, col="Ključ preverjanja", severity="ERROR",
                                       code="EQ_KEY_ORPHAN",
                                       message=f"Oprema s ključem '{key}' ni povezana z nobenim materialom/meritvijo."))

    return issues

# -------------------- PREVODI KOD (za prikaz v poročilu) --------------------

CODE_TRANSLATIONS = {
    "MISSING_COLUMN": "Manjka obvezen stolpec",
    "STEP_NOT_INT": "Številka koraka ni celo število",
    "STEP_DUPLICATE": "Podvojena številka koraka",
    "STEP_GAPS": "Manjkajo vmesni koraki",
    "TIP_OBJEKTA_EMPTY": "Tip objekta ni določen",
    "TIP_OBJEKTA_UNKNOWN": "Neznan tip objekta",
    "OBJ_MISMATCH": "Tip objekta ne ustreza tipu podatka",
    "LABELA_KODA": "Labela mora biti 'koda'",
    "KEY_FORMAT": "Nepravilen zapis ključa",
    "FORMULA_SYNTAX": "Nepravilen zapis formule",
    "FORMULA_NOREF": "Formula nima sklica na korake",
    "FORMULA_BAD_REF": "Formula se sklicuje na neobstoječi korak",
    "COMMA_NOT_ALLOWED": "Vrednost vsebuje nedovoljeno vejico v številu",
    "PAIR_KEM_NO_MASA": "Za kemikalijo manjka ustrezna masa",
    "PAIR_RAZT_NO_MASA": "Za raztopino manjka ustrezna masa",
    "PAIR_MASA_NO_OWNER": "Masa nima pripadajoče kemikalije ali raztopine",
    "PAIR_TIME_NO_END": "Manjka končni čas",
    "PAIR_TIME_NO_START": "Manjka začetni čas",
    "KEY_NUM_START": "Oštevilčenje ključev se ne začne z 1",
    "KEY_NUM_GAP": "Manjkajoči ključ v zaporedju",
    "KEY_NUM_DUPLICATE_ONE": "Podvojen stil ključa ('base' in 'base1')",
    "CTRL_REQUIRED_EMPTY": "Manjka kontrola za prazno polje",
    "CTRL_CHECKBOX_EMPTY": "Checkbox ne sme imeti kontrole prazno polje",
    "CTRL_EXPECTED_MISSING": "Manjka pričakovana kontrola",
    "CTRL_UNKNOWN": "Neznano ime kontrole",
    "CTRL_BAD_CONTEXT": "Kontrola je v napačnem kontekstu",
    "CTRL_INTERVAL_PARAMS": "Kontrola interval brez mej",
    "CTRL_INTERVAL_NUM": "Meja intervala ni številčna",
    "CTRL_INTERVAL_ORDER": "Maksimalna meja je manjša ali enaka minimalni",
    "CTRL_INTERVAL_NAVODILO_RULE": "Parametra intervala ne sledita mejam iz navodila",
    "UNIT_MISMATCH": "Enota v 'Labela' se ne ujema z 'Navodilo'",
    "CTRL_CASA_MIN": "Kontrola časa brez minimalne vrednosti",
    "CTRL_CASA_MIN_NUM": "Minimalna vrednost časa ni številčna",
    "CTRL_CASA_ORDER": "Maksimalni čas je manjši od minimalnega",
    "CTRL_CASA_MAX_NUM": "Maksimalna vrednost časa ni številčna",
    "CTRL_ROLE_PARAM": "Manjka parameter vloge",
    "CTRL_POGOJ_P1": "Pogoj brez referenčnega ključa (Param1)",
    "CTRL_POGOJ_P1_FORMAT": "Pogoj – neveljavni ključi v Param1",
    "CTRL_POGOJ_KEY": "Pogoj referencira neobstoječe ključe",
    "CTRL_POGOJ_P2": "Pogoj brez vrednosti 0/1 (Param2)",
    "CTRL_POGOJ_VAL": "Param2 pri pogoju mora biti 0 ali 1",
    "CTRL_LOCKED_NO_CHECK": "Pri 'zaklenipolja' ni dovoljena kontrola 'aliObkljukan'",
    "SOLUTION_KEY_MISSING": "Kontrola raztopine brez ključa v vrstici",
    "SOLUTION_P1_MISSING": "Kontrola raztopine brez baze ključa (Param1)",
    "SOLUTION_P1_BASE": "Param1 ne ustreza bazi ključa",
    "EQ_MONOMERNA": "Oprema 'monomerna' brez definicije mešanice",
    "EQ_KEY_ORPHAN": "Oprema ni povezana z nobenim materialom/meritvijo",

    # Stroga 'exact/min/max' pravila za kontrolaInterval
    "CTRL_INTERVAL_RANGE_P1_EXACT": "Param1 ne sledi spodnji meji iz navodila",
    "CTRL_INTERVAL_RANGE_P2_EXACT": "Param2 ne sledi zgornji meji iz navodila",
    "CTRL_INTERVAL_PM_P1_EXACT": "Param1 ne sledi spodnji meji iz ±",
    "CTRL_INTERVAL_PM_P2_EXACT": "Param2 ne sledi zgornji meji iz ±",
    "CTRL_INTERVAL_TARGET_P1_EXACT": "Param1 ne sledi spodnji meji iz navodila",
    "CTRL_INTERVAL_TARGET_P2_EXACT": "Param2 ne sledi zgornji meji iz navodila",
    "CTRL_INTERVAL_TARGET_P1_MAX": "Param1 je nad dovoljeno spodnjo mejo",
    "CTRL_INTERVAL_TARGET_P2_MIN": "Param2 je pod zahtevano zgornjo mejo",

    "SHEET_READ_ERR": "Napaka pri branju lista",
    "ZAKLENI_PAR1_EXCEL_ERR": "Param1 vsebuje Excel napako",
    "ZAKLENI_PAR1_FORMAT": "Param1 pri 'zaklenipolja' ni pravilen seznam števil",
    "P1_KEYS_FORMAT": "Param1 mora biti seznam ključev, ločenih z vejico",
    "KEY_DUP_KEM": "Podvojen ključ za kemikalijo",
    "KEY_DUP_RAZT": "Podvojen ključ za raztopino",
    "KEY_DUP_MASA": "Podvojen ključ za maso",
}

def translate_code(code: str) -> str:
    return CODE_TRANSLATIONS.get(code, code)

# -------------------- Excel poročilo (en list) --------------------

def _auto_fit_columns(ws):
    max_col = ws.max_column or 1
    for col_idx in range(1, max_col + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 0
        for cell in ws[col_letter]:
            val = "" if cell.value is None else str(cell.value)
            if len(val) > max_len:
                max_len = len(val)
        ws.column_dimensions[col_letter].width = min(60, max(12, max_len + 2))

def _protect_with_filters(ws, header_row=1):
    last_col = get_column_letter(ws.max_column or 1)
    last_row = ws.max_row or header_row
    ws.auto_filter.ref = f"A{header_row}:{last_col}{last_row}"
    for row in ws.iter_rows(min_row=1, max_row=last_row, min_col=1, max_col=ws.max_column):
        for cell in row:
            cell.protection = Protection(locked=False)
    prot = ws.protection
    if not isinstance(prot, SheetProtection):
        ws.protection = SheetProtection()
        prot = ws.protection
    prot.sheet = True
    try:
        prot.enable()
    except Exception:
        pass

def write_excel_report(report_path: Path, issues: List[Dict[str, Any]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Povzetek"
    headers = ["List", "Vrstica", "Stolpec", "Napaka", "Opis napake"]
    for j, h in enumerate(headers, start=1):
        ws.cell(row=1, column=j, value=h)

    if not issues:
        ws.cell(row=2, column=4, value="OK")
        ws.cell(row=2, column=5, value="Ni najdenih strukturnih napak.")
    else:
        r = 2
        for i in issues:
            ws.cell(row=r, column=1, value=i.get("sheet", ""))
            ws.cell(row=r, column=2, value=i.get("row", ""))
            ws.cell(row=r, column=3, value=i.get("col", ""))
            ws.cell(row=r, column=4, value=translate_code(i.get("code", "")))
            ws.cell(row=r, column=5, value=i.get("message", ""))
            r += 1

    _auto_fit_columns(ws)
    last_col = get_column_letter(ws.max_column or 1)
    last_row = ws.max_row or 1
    ws.auto_filter.ref = f"A1:{last_col}{last_row}"
    wb.save(report_path)
    try:
        wb.close()
    except Exception:
        pass

def write_text_report(report_path: Path, issues: List[Dict[str, Any]] ) -> None:
    lines = []
    if not issues:
        lines.append("OK | Ni najdenih strukturnih napak.")
    else:
        for i in issues:
            lines.append(f"{i.get('sheet','')} | vrstica {i.get('row','')} | stolpec {i.get('col','')} | {translate_code(i.get('code',''))} – {i.get('message','')}")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")

# -------------------- GUI --------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Validator MES Receptur {VERSION}")
        self.geometry("900x540")
        self.minsize(860, 500)

        self.input_var = tk.StringVar()
        self.report_var = tk.StringVar()
        self.sheet_var = tk.StringVar()

        self._build_ui()

        now_dt = datetime.datetime.now(_TZ) if _TZ else datetime.datetime.now()
        now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        header = (
            f"🧩 Validator MES Receptur ({VERSION})\n"
            f"Avtor procesa: B. Komac\n"
            f"Uporaba: interna QA/Production skupina.\n"
            f"Log: {LOG_PATH.name}\n"
            f"Zagon: {now}\n"
        )
        self.log(header)

    def _build_ui(self):
        pad = {'padx': 10, 'pady': 8}
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, **pad)

        ttk.Label(frm, text="Vhodna Excel datoteka (receptura):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.input_var).grid(row=1, column=0, columnspan=2, sticky="we")
        ttk.Button(frm, text="Izberi...", command=self.pick_input).grid(row=1, column=2, sticky="e")

        ttk.Label(frm, text="Izhodno poročilo (.xlsx ali .txt):").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.report_var).grid(row=3, column=0, columnspan=2, sticky="we")
        ttk.Button(frm, text="Shrani kot...", command=self.pick_report).grid(row=3, column=2, sticky="e")

        ttk.Label(frm, text="(Neobvezno) Ime lista za validacijo:").grid(row=4, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.sheet_var).grid(row=5, column=0, columnspan=2, sticky="we")
        ttk.Label(frm, text="(Pusti prazno za vse ustrezne liste.)").grid(row=5, column=2, sticky="w")

        ttk.Button(frm, text="Zaženi validacijo", command=self.run_validation).grid(row=6, column=0, sticky="w", pady=12)
        ttk.Button(frm, text="Odpri mapo poročila", command=self.open_report_folder).grid(row=6, column=2, sticky="e")

        ttk.Label(frm, text="Status:").grid(row=7, column=0, sticky="w")
        self.txt = tk.Text(frm, height=12, wrap="word")
        self.txt.grid(row=8, column=0, columnspan=3, sticky="nsew")
        scr = ttk.Scrollbar(frm, command=self.txt.yview)
        self.txt.configure(yscrollcommand=scr.set)
        scr.grid(row=8, column=3, sticky="ns")

        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(2, weight=0)
        frm.rowconfigure(8, weight=1)

    def log(self, msg: str):
        self.txt.insert(tk.END, msg + "\n")
        self.txt.see(tk.END)
        self.update_idletasks()
        for line in msg.splitlines():
            append_log(line)

    def pick_input(self):
        path = filedialog.askopenfilename(
            title="Izberi Excel (receptura)",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            self.input_var.set(path)
            self.log(f"Izbrana datoteka: {path}")

    def pick_report(self):
        path = filedialog.asksaveasfilename(
            title="Shrani poročilo kot",
            defaultextension=".xlsx",
            filetypes=[("Excel report (*.xlsx)", "*.xlsx"), ("Text report (*.txt)", "*.txt")]
        )
        if path:
            self.report_var.set(path)
            self.log(f"Izhodno poročilo bo: {path}")

    def open_report_folder(self):
        p = self.report_var.get().strip()
        if not p:
            messagebox.showinfo("Info", "Najprej generiraj poročilo.")
            return
        folder = str(Path(p).resolve().parent)
        try:
            if platform.system() == 'Windows':
                os.startfile(folder)  # type: ignore
            elif platform.system() == 'Darwin':
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
            self.log(f"Odprta mapa: {folder}")
        except Exception as e:
            messagebox.showerror("Napaka", f"Ne morem odpreti mape: {e}")
            self.log(f"NAPAKA odprtja mape: {e}")

    def run_validation(self):
        in_path = Path(self.input_var.get().strip())
        out_path = Path(self.report_var.get().strip())
        sheet_name = self.sheet_var.get().strip()

        if not in_path.exists():
            messagebox.showerror("Napaka", f"Datoteka ne obstaja:\n{in_path}")
            self.log(f"NAPAKA: Datoteka ne obstaja: {in_path}")
            return
        if out_path.suffix.lower() not in {".xlsx", ".txt"}:
            messagebox.showerror("Napaka", "Poročilo mora biti .xlsx ali .txt")
            self.log("NAPAKA: Poročilo mora biti .xlsx ali .txt")
            return

        self.txt.delete("1.0", tk.END)
        self.log(f"Berem: {in_path} ...")
        try:
            xls = pd.read_excel(
                in_path,
                sheet_name=None,
                engine="openpyxl",
                dtype=str,
                keep_default_na=False
            )
            wb_formula = load_workbook(in_path, data_only=False)
            wb_values  = load_workbook(in_path, data_only=True)
            self.log("Excel uspešno prebran.")
        except Exception as e:
            messagebox.showerror("Napaka branja", f"Ne morem prebrati Excel datoteke:\n{e}")
            self.log(f"NAPAKA branja: {e}")
            return

        issues_all: List[Dict[str, Any]] = []

        if sheet_name:
            if sheet_name not in xls:
                messagebox.showerror("Napaka", f"List '{sheet_name}' ne obstaja v delovnem zvezku.")
                self.log(f"NAPAKA: Manjka list '{sheet_name}'")
                return
            df = xls[sheet_name]
            ws_f = wb_formula[sheet_name] if sheet_name in wb_formula.sheetnames else None
            ws_v = wb_values[sheet_name]  if sheet_name  in wb_values.sheetnames  else None
            issues_all.extend(validate_dataframe(df, origin=sheet_name, ws_formula=ws_f, ws_values=ws_v))
        else:
            for sname, df in xls.items():
                try:
                    cols_norm = set([c.strip() for c in df.columns if isinstance(c, str)])
                except Exception:
                    continue
                if any(c in cols_norm for c in REQUIRED_COLUMNS):
                    try:
                        ws_f = wb_formula[sname] if sname in wb_formula.sheetnames else None
                        ws_v = wb_values[sname]  if sname  in wb_values.sheetnames  else None
                        issues_all.extend(validate_dataframe(df, origin=sname, ws_formula=ws_f, ws_values=ws_v))
                    except Exception as e:
                        issues_all.append(dict(
                            sheet=sname, row="", col="", severity="ERROR", code="SHEET_READ_ERR",
                            message=f"Napaka pri obdelavi lista: {e}"
                        ))
                        self.log(f"NAPAKA obdelave lista '{sname}': {e}")

        try:
            if out_path.suffix.lower() == ".xlsx":
                write_excel_report(out_path, issues_all)
            else:
                write_text_report(out_path, issues_all)
            self.log(f"Poročilo zapisano: {out_path}")
        except Exception as e:
            messagebox.showerror("Napaka pisanja", f"Ne morem zapisati poročila:\n{e}")
            self.log(f"NAPAKA pisanja poročila: {e}")
            return

        errors = sum(1 for i in issues_all if i.get("severity") == "ERROR")
        warns  = sum(1 for i in issues_all if i.get("severity") == "WARNING")

        if errors == 0:
            self.log(f"OK: brez napak (opozoril: {warns}).")
            messagebox.showinfo("Končano", f"Brez napak (opozoril: {warns}).\nPoročilo:\n{out_path}")
        else:
            self.log(f"Končano z napakami: {errors} (opozoril: {warns}).")
            messagebox.showwarning("Končano", f"Najdene napake: {errors}\nOpozorila: {warns}\nPoročilo:\n{out_path}")

# -------------------- Run --------------------

if __name__ == "__main__":
    init_log()
    # Če je podana pot kot argument, zaženi CLI validacijo; sicer GUI
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        # CLI način: generiraj poročilo v isti mapi
        in_path = Path(sys.argv[1]).expanduser().resolve()
        if not in_path.exists():
            print(f"Napaka: datoteka ne obstaja: {in_path}", file=sys.stderr)
            sys.exit(2)
        try:
            # Preberi in uporabi isti mehanizem kot v GUI
            xls = pd.read_excel(in_path, sheet_name=None, engine="openpyxl", dtype=str, keep_default_na=False)
            wb_formula = load_workbook(in_path, data_only=False)
            wb_values  = load_workbook(in_path, data_only=True)
            issues_all: List[Dict[str, Any]] = []
            for sname, df in xls.items():
                cols_norm = set([c.strip() for c in df.columns if isinstance(c, str)])
                if any(c in cols_norm for c in REQUIRED_COLUMNS):
                    ws_f = wb_formula[sname] if sname in wb_formula.sheetnames else None
                    ws_v = wb_values[sname]  if sname  in wb_values.sheetnames  else None
                    issues_all.extend(validate_dataframe(df, origin=sname, ws_formula=ws_f, ws_values=ws_v))
            # Zapiši poročilo
            out_xlsx = in_path.with_name(in_path.stem + "_VALIDATION_REPORT.xlsx")
            write_excel_report(out_xlsx, issues_all)
            print(f"Končano. Poročilo: {out_xlsx}")
            sys.exit(0)
        except Exception as e:
            print("Pri validaciji je prišlo do napake:", e, file=sys.stderr)
            sys.exit(3)
    else:
        # GUI
        app = App()
        app.mainloop()
