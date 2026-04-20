"""Helper functions for MES validation.

This module contains utility functions for:
- String normalization and coercion
- Checkbox state parsing
- Key manipulation (base extraction, suffix numbering)
- Equipment detection
- Time parsing (seconds, ranges, lower bounds)
- Unit extraction and normalization
- Numeric parsing and decimal handling
- Navodilo interval/inequality parsing
"""

from __future__ import annotations

import math
import re
from typing import Match, Sequence

from validator_oop.core.constants import (
    EQUIPMENT_REGEX,
    EQUIPMENT_TIP_PODATKA,
    EXCEL_ERROR_TOKENS,
    INEQ_RE,
    INVISIBLE_WHITESPACE,
    NUMERIC_TOKEN_RE,
    PM_RE,
    RANGE_RE,
    SINGLE_RE,
    TIME_DAY_PATTERN,
    TIME_HOUR_PATTERN,
    TIME_INEQUALITY_RE,
    TIME_MINUTE_PATTERN,
    TIME_RANGE_SEPARATOR,
    UNIT_AFTER_NUMBER_RE,
    UNIT_TOKEN_RE,
)

# ==============================================================================
# STRING NORMALIZATION
# ==============================================================================


def coerce_str(value: object) -> str:
    """Convert any value to a stripped string.

    Args:
        value: Any value (None, str, int, float, etc.)

    Returns:
        Stripped string representation, empty string for None/NaN.
    """
    if value is None:
        return ""
    # Handle pandas NaN if pandas is available
    try:
        import pandas as pd
        if pd.isna(value):
            return ""
    except (ImportError, TypeError, ValueError):
        pass
    return str(value).strip()


def norm_text(text: str) -> str:
    """Normalize text: replace invisible whitespace, collapse spaces, lowercase.

    Args:
        text: Input text.

    Returns:
        Normalized lowercase text.
    """
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    for char in INVISIBLE_WHITESPACE:
        text = text.replace(char, " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def norm_control_name(name: str) -> str:
    """Normalize control name: lowercase, remove all whitespace/underscores/dashes.

    Args:
        name: Control name (e.g., 'kontrola Interval', 'Kontrola_Interval').

    Returns:
        Normalized name (e.g., 'kontrolainterval').
    """
    name = norm_text(name)
    return re.sub(r"\s+", "", name)


def normalize_column_names(columns: Sequence[str] | None) -> list[str]:
    """Normalize a list of column names.

    Args:
        columns: List of column names.

    Returns:
        List of stripped column names.
    """
    if columns is None:
        return []
    return [
        (c.strip() if isinstance(c, str) else ("" if c is None else str(c)))
        for c in columns
    ]


# ==============================================================================
# CHECKBOX STATE PARSING
# ==============================================================================


def parse_checkbox_state(value: str) -> int | None:
    """Parse checkbox state from textual value.

    Args:
        value: Checkbox value string.

    Returns:
        1 for checked, 0 for unchecked, None if unknown.
    """
    s = coerce_str(value).lower()
    if s in {"1", "da", "yes", "true", "obkljukan"}:
        return 1
    if s in {"0", "ne", "no", "false", "niobkljukan"}:
        return 0
    return None


def has_only_comma_separated_ints(text: str) -> bool:
    """Check if text contains only comma-separated integers.

    Args:
        text: Input text (e.g., "3,5,6" or "3,5,6,").

    Returns:
        True if valid comma-separated integers.
    """
    return bool(re.fullmatch(r"\s*\d+\s*(\s*,\s*\d+\s*)*\s*,?\s*", text))


# ==============================================================================
# KEY MANIPULATION
# ==============================================================================


def base_key_no_trailing_number(key: str) -> str:
    """Remove trailing number and separator from key.

    Args:
        key: Key string (e.g., 'kemikalija_1', 'masa2', 'GK10').

    Returns:
        Base key without trailing number (e.g., 'kemikalija', 'masa', 'GK').
    """
    key = key.strip()
    # Vedno odstranimo vse številke na koncu, ne samo zadnjo
    return re.sub(r"[_\-\.\s]*\d+$", "", key)


def extract_suffix_number(key: str) -> tuple[str, int]:
    """Extract base and numeric suffix from key.

    Args:
        key: Key string (e.g., 'kemikalija1', 'masa_2').

    Returns:
        Tuple of (base, number). Number is 0 if no suffix.
    """
    match = re.match(r"^(.*?)(\d+)?$", key.strip())
    if not match:
        return key.strip(), 0
    base = (match.group(1) or "").rstrip("_- .")
    num = int(match.group(2)) if match.group(2) else 0
    return base, num


def split_key_number(key: str) -> tuple[str, int]:
    """Alias for extract_suffix_number for compatibility."""
    return extract_suffix_number(key)


# ==============================================================================
# EQUIPMENT DETECTION
# ==============================================================================


def is_equipment_tip(tip_podatka: str) -> bool:
    """Check if tip_podatka represents equipment.

    Args:
        tip_podatka: Data type string.

    Returns:
        True if equipment type.
    """
    t = coerce_str(tip_podatka)
    if not t:
        return False
    t_lower = t.lower().strip()
    if t_lower in EQUIPMENT_TIP_PODATKA:
        return True
    return EQUIPMENT_REGEX.search(t) is not None


def is_equipment_row(tip_podatka: str, control_names_normalized: Sequence[str]) -> bool:
    """Check if row represents equipment based on tip_podatka or controls.

    Args:
        tip_podatka: Data type string.
        control_names_normalized: List of normalized control names in row.

    Returns:
        True if equipment row.
    """
    if is_equipment_tip(tip_podatka):
        return True
    equipment_controls = {
        "kontrolaveljavnostiopreme",
        "kontrolaustreznostiopreme",
        "kontrolaustreznostiopremeizmase",
    }
    return any(c in control_names_normalized for c in equipment_controls)


# ==============================================================================
# EXCEL ERROR DETECTION
# ==============================================================================


def is_excel_error_token(value: str) -> bool:
    """Check if value is an Excel error token.

    Args:
        value: Cell value string.

    Returns:
        True if Excel error (#REF!, #N/A, etc.).
    """
    return isinstance(value, str) and value.strip().upper() in EXCEL_ERROR_TOKENS


def looks_like_number_with_commas(value: str) -> bool:
    """Check if value looks like a number with comma separators.

    Args:
        value: Value string.

    Returns:
        True if appears to be comma-separated number.
    """
    if "," not in value:
        return False
    candidate = value.replace(",", "").strip()
    return bool(re.fullmatch(r"[+-]?\d+(\.\d+)?", candidate))


# ==============================================================================
# TIME PARSING
# ==============================================================================


def parse_time_phrase_to_seconds(text: str) -> float | None:
    """Parse time phrase to seconds.

    Supports formats like:
    - "2 h", "15 min", "3 dni"
    - "2 h 15 min" (combined)

    Args:
        text: Time phrase.

    Returns:
        Total seconds, or None if not parseable.
    """
    s = coerce_str(text)
    if not s:
        return None

    days: float = 0.0
    hours: float = 0.0
    minutes: float = 0.0

    match_d = TIME_DAY_PATTERN.search(s)
    if match_d:
        try:
            days = float(match_d.group("num").replace(",", "."))
        except (ValueError, AttributeError):
            days = 0.0

    match_h = TIME_HOUR_PATTERN.search(s)
    if match_h:
        try:
            hours = float(match_h.group("num").replace(",", "."))
        except (ValueError, AttributeError):
            hours = 0.0

    match_m = TIME_MINUTE_PATTERN.search(s)
    if match_m:
        try:
            minutes = float(match_m.group("num").replace(",", "."))
        except (ValueError, AttributeError):
            minutes = 0.0

    if days == 0.0 and hours == 0.0 and minutes == 0.0:
        return None

    return days * 86400.0 + hours * 3600.0 + minutes * 60.0


def _detect_time_unit(segment: str) -> str | None:
    """Detect time unit in segment."""
    s = coerce_str(segment)
    if TIME_HOUR_PATTERN.search(s):
        return "h"
    if TIME_MINUTE_PATTERN.search(s):
        return "min"
    if TIME_DAY_PATTERN.search(s):
        return "d"
    return None


def _parse_time_with_default_unit(segment: str, default_unit: str | None) -> float | None:
    """Parse time segment, using default unit if none specified."""
    val = parse_time_phrase_to_seconds(segment)
    if val is not None:
        return val

    if not default_unit:
        return None

    match = NUMERIC_TOKEN_RE.search(coerce_str(segment))
    if not match:
        return None

    try:
        x = float(match.group(0).replace(",", "."))
    except ValueError:
        return None

    if default_unit == "h":
        return x * 3600.0
    if default_unit == "min":
        return x * 60.0
    if default_unit == "d":
        return x * 86400.0
    return None


def parse_time_range_from_navodilo(navodilo: str) -> tuple[float | None, float | None]:
    """Parse time range from navodilo text.

    Supports formats like:
    - "2 h - 2 h 15 min"
    - "10 min – 15 min"
    - "1 h ± 5 min"
    - "2 h 15 min" (single value = min=max)

    Args:
        navodilo: Instruction text.

    Returns:
        Tuple of (min_seconds, max_seconds), or (None, None) if not parseable.
    """
    full_text = coerce_str(navodilo)
    if not full_text:
        return (None, None)

    # Check for content in parentheses
    paren_match = re.search(r"\(([^)]*)\)", full_text)
    text = paren_match.group(1) if paren_match else full_text
    if not text:
        return (None, None)

    # Handle ± notation
    pm_match = re.search(r"(?P<center>.+?)(?:±|\+/-|\+\s*/\s*-)\s*(?P<tol>.+)", text)
    if pm_match:
        center_seg = pm_match.group("center")
        tol_seg = pm_match.group("tol")

        center_sec = parse_time_phrase_to_seconds(center_seg)
        tol_sec = parse_time_phrase_to_seconds(tol_seg)

        if center_sec is None:
            unit_tol = _detect_time_unit(tol_seg)
            center_sec = _parse_time_with_default_unit(center_seg, unit_tol)

        if tol_sec is None:
            unit_center = _detect_time_unit(center_seg)
            tol_sec = _parse_time_with_default_unit(tol_seg, unit_center)

        if center_sec is not None and tol_sec is not None:
            return (center_sec - tol_sec, center_sec + tol_sec)

    # Handle range notation
    parts = TIME_RANGE_SEPARATOR.split(text)
    if len(parts) >= 2:
        left_seg = parts[0]
        right_seg = parts[1]
        u_left = _detect_time_unit(left_seg)
        u_right = _detect_time_unit(right_seg)
        default_u = u_left or u_right

        left = _parse_time_with_default_unit(left_seg, default_u)
        right = _parse_time_with_default_unit(right_seg, default_u)

        if left is not None and right is not None:
            return (min(left, right), max(left, right))

    # Single value
    one = parse_time_phrase_to_seconds(text)
    if one is not None:
        return (one, one)

    return (None, None)


def parse_time_lower_bound_from_navodilo(navodilo: str) -> float | None:
    """Parse time lower bound from inequality in navodilo.

    Supports: '≥ 2 h', '> 10 min', '>=2 h 15 min'

    Args:
        navodilo: Instruction text.

    Returns:
        Lower bound in seconds, or None if not found.
    """
    text = coerce_str(navodilo)
    if not text:
        return None

    match = TIME_INEQUALITY_RE.search(text)
    if not match:
        return None

    after = text[match.end():]
    return parse_time_phrase_to_seconds(after)


# ==============================================================================
# NUMERIC PARSING
# ==============================================================================


def parse_numeric_value(text: str) -> float | None:
    """Parse first numeric value from text.

    Args:
        text: Text containing a number.

    Returns:
        Parsed float, or None if not found.
    """
    s = _normalize_spaced_decimal_separator(coerce_str(text))
    if not s:
        return None

    match = NUMERIC_TOKEN_RE.search(s)
    if not match:
        return None

    token = match.group(0).replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return None


def _normalize_spaced_decimal_separator(text: str) -> str:
    """Normalize spaced decimal separators like ``2 .0`` to ``2.0``."""
    if not text:
        return text
    return re.sub(r"(?<=\d)\s*([.,])\s*(?=\d)", r"\1", text)


def decimal_places_of_first_number(text: str) -> int | None:
    """Get decimal places of first number in text.

    Args:
        text: Text containing a number.

    Returns:
        Number of decimal places, or None if no number found.
    """
    s = _normalize_spaced_decimal_separator(coerce_str(text))
    if not s:
        return None

    match = NUMERIC_TOKEN_RE.search(s)
    if not match:
        return None

    token = match.group(0)
    if "," in token:
        frac = token.split(",", 1)[1]
    elif "." in token:
        frac = token.split(".", 1)[1]
    else:
        frac = ""

    if "e" in frac.lower():
        frac = frac.split("e", 1)[0]

    return len(frac) if frac else 0


def derive_decimal_step_from_text(text: str) -> float:
    """Derive smallest decimal step from numbers in text.

    Args:
        text: Text containing numbers.

    Returns:
        Smallest step (e.g., 0.01 for 2 decimal places).
    """
    normalized = _normalize_spaced_decimal_separator(coerce_str(text))
    nums = [m.group(0) for m in NUMERIC_TOKEN_RE.finditer(normalized)]
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


def decimals_from_eps(eps: float) -> int:
    """Get number of decimal places from epsilon value.

    Args:
        eps: Epsilon value (e.g., 0.001).

    Returns:
        Number of decimal places (e.g., 3).
    """
    if eps <= 0:
        return 0

    for d in range(0, 12):
        if abs(eps - (10 ** (-d))) < 1e-12:
            return d

    try:
        d = int(round(-math.log10(eps)))
        return max(0, min(12, d))
    except (ValueError, OverflowError):
        return 0


def eq_with_decimals(value: float, target: float, decimals: int) -> bool:
    """Compare two floats with specified decimal precision.

    Args:
        value: First value.
        target: Second value.
        decimals: Number of decimal places for comparison.

    Returns:
        True if equal when rounded to specified decimals.
    """
    return round(value, decimals) == round(target, decimals)


def max_decimals(*args: float | str | None) -> int:
    """Return maximum number of decimals among arguments.

    Args:
        *args: Values to check.

    Returns:
        Maximum decimal places (at least 3 if any value has 3+).
    """
    def _decs(x: float | str | None) -> int:
        if x is None:
            return 0
        if isinstance(x, str):
            s = x.replace(",", ".").rstrip("0").rstrip(".")
            if "." in s:
                return len(s.split(".")[-1])
            return 0
        if isinstance(x, (int, float)):
            s = f"{x:.10f}".rstrip("0").rstrip(".")
            if "." in s:
                return len(s.split(".")[-1])
            return 0
        return 0

    max_d = 0
    for a in args:
        d = _decs(a)
        if d > max_d:
            max_d = d

    return max(max_d, 3 if max_d >= 3 else max_d)


# ==============================================================================
# UNIT EXTRACTION
# ==============================================================================


def extract_unit_token(text: str) -> str | None:
    """Extract unit token from text.

    Args:
        text: Text containing a unit.

    Returns:
        Normalized unit string (lowercase, 'µ' -> 'u'), or None.
    """
    s = coerce_str(text)
    if not s:
        return None

    match = UNIT_TOKEN_RE.search(s)
    if not match:
        return None

    token = match.group(0)
    # Normalize: ASCII 'oc' -> '°c', micro symbol -> 'u', lowercase
    token = token.replace("oc", "°c")
    token = token.replace("µ", "u").lower()
    return token


def extract_unit_token_near_number(text: str) -> str | None:
    """Extract unit token that follows a number.

    Handles cases with inequalities (≤, ≥, <, >) before the number.
    Prefers the last match to handle cases like "prečrpano >10 MVS (> 6.7 L)".

    Args:
        text: Text containing number+unit.

    Returns:
        Normalized unit string, or None.
    """
    s = coerce_str(text)
    if not s:
        return None

    # First try to find unit after number with inequality operators using INEQ_RE
    # This handles cases like "≤ 20 bar", ">= 10 °C", etc.
    match = _choose_best_match(s, INEQ_RE, "unit")
    
    if match and match.group("unit"):
        token = match.group("unit")
        token = token.replace("oc", "°c")
        token = token.replace("µ", "u").lower()
        return token

    # If no inequality match found, fall back to original pattern
    match = None
    for m in UNIT_AFTER_NUMBER_RE.finditer(s):
        match = m

    if not match:
        return None

    token = match.group("unit")
    token = token.replace("oc", "°c")
    token = token.replace("µ", "u").lower()
    return token


# ==============================================================================
# NAVODILO INTERVAL PARSING
# ==============================================================================


def _choose_best_match(
    text: str,
    pattern: re.Pattern,
    unit_group: str = "unit",
) -> Match | None:
    """Choose best regex match, preferring matches with units."""
    candidates: list[tuple[int, int, Match]] = []
    for m in pattern.finditer(text):
        score = 2 if m.group(unit_group) else 0
        candidates.append((score, m.start(), m))

    if not candidates:
        return None

    candidates.sort(key=lambda t: (t[0], t[1]))
    return candidates[-1][2]


def parse_navodilo_interval(
    navodilo: str,
) -> tuple[float | None, float | None, str | None, float | None]:
    """Parse numeric range from navodilo.

    Handles formats like: "10 - 15 °C", "5.5–6.0 g"

    Args:
        navodilo: Instruction text.

    Returns:
        Tuple of (a, b, unit, step) or (None, None, None, None).
    """
    text = _normalize_spaced_decimal_separator(coerce_str(navodilo))
    match = _choose_best_match(text, RANGE_RE)
    if not match:
        return (None, None, None, None)

    a = float(match.group("a").replace(",", "."))
    b = float(match.group("b").replace(",", "."))
    unit = match.group("unit")
    if unit:
        unit = unit.replace("oc", "°c").replace("µ", "u").lower()

    d1 = decimal_places_of_first_number(match.group("a")) or 0
    d2 = decimal_places_of_first_number(match.group("b")) or 0
    d = max(d1, d2)
    step = 10 ** (-d) if d > 0 else 1.0

    return (a, b, unit, step)


def parse_navodilo_pm(
    navodilo: str,
) -> tuple[float | None, float | None, str | None, float | None]:
    """Parse ± notation from navodilo.

    Handles formats like: "25 ± 2 °C", "10.5 +/- 0.5 g"

    Args:
        navodilo: Instruction text.

    Returns:
        Tuple of (center, tolerance, unit, step) or (None, None, None, None).
    """
    text = _normalize_spaced_decimal_separator(coerce_str(navodilo))
    match = PM_RE.search(text)
    if not match:
        return (None, None, None, None)

    x = float(match.group("x").replace(",", "."))
    t = float(match.group("t").replace(",", "."))
    unit = match.group("unit")
    if unit:
        unit = unit.replace("oc", "°c").replace("µ", "u").lower()

    d1 = decimal_places_of_first_number(match.group("x")) or 0
    d2 = decimal_places_of_first_number(match.group("t")) or 0
    d = max(d1, d2)
    step = 10 ** (-d) if d > 0 else 1.0

    return (x, t, unit, step)


def parse_navodilo_inequality(
    navodilo: str,
) -> tuple[str | None, float | None, str | None, float | None]:
    """Parse inequality from navodilo.

    Handles formats like: ">= 10 °C", "< 5 g", "≥ 2.5"

    Args:
        navodilo: Instruction text.

    Returns:
        Tuple of (operator, value, unit, step) or (None, None, None, None).
    """
    text = _normalize_spaced_decimal_separator(coerce_str(navodilo))
    match = _choose_best_match(text, INEQ_RE)
    if not match:
        return (None, None, None, None)

    op_raw = match.group("op")
    if op_raw in (">=", "≥"):
        op = ">="
    elif op_raw in ("<=", "≤"):
        op = "<="
    elif op_raw == ">":
        op = ">"
    elif op_raw == "<":
        op = "<"
    else:
        op = None

    x = float(match.group("x").replace(",", "."))
    unit = match.group("unit")
    if unit:
        unit = unit.replace("oc", "°c").replace("µ", "u").lower()

    d = decimal_places_of_first_number(match.group("x")) or 0
    step = 10 ** (-d) if d > 0 else 1.0

    return (op, x, unit, step)


def parse_navodilo_single(
    navodilo: str,
) -> tuple[float | None, str | None, float | None]:
    """Parse single numeric value from navodilo.

    Only matches if no range/±/inequality is present.

    Args:
        navodilo: Instruction text.

    Returns:
        Tuple of (value, unit, step) or (None, None, None).
    """
    text = _normalize_spaced_decimal_separator(coerce_str(navodilo))

    # Don't match if range/±/inequality is present
    if RANGE_RE.search(text) or PM_RE.search(text) or INEQ_RE.search(text):
        return (None, None, None)

    match = _choose_best_match(text, SINGLE_RE)
    if not match:
        return (None, None, None)

    x = float(match.group("x").replace(",", "."))
    unit = match.group("unit")
    if unit:
        unit = unit.replace("oc", "°c").replace("µ", "u").lower()

    d = decimal_places_of_first_number(match.group("x")) or 0
    step = 10 ** (-d) if d > 0 else 1.0

    return (x, unit, step)


# ==============================================================================
# EXCEL FORMULA PARSING
# ==============================================================================


def column_letter_to_number(letter: str) -> int:
    """Convert Excel column letter to number (A=1, B=2, ..., Z=26, AA=27, etc.).
    
    Args:
        letter: Excel column letter(s) (e.g., "A", "B", "AA", "X").
    
    Returns:
        Column number (1-based).
    
    Example:
        >>> column_letter_to_number("A")
        1
        >>> column_letter_to_number("X")
        24
        >>> column_letter_to_number("AA")
        27
    """
    result = 0
    for char in letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result


def parse_index_match_formula(formula: str) -> tuple[str, int, str] | None:
    """Parse INDEX MATCH formula to extract sheet, column, and lookup cell.
    
    Parses formulas like: =INDEX(Podatki!$A:$AP,MATCH($A$2,Podatki!$A:$A,0),24)
    
    Args:
        formula: Excel formula string.
    
    Returns:
        Tuple of (sheet_name, column_number, lookup_cell) or None if not parseable.
        Example: ("Podatki", 24, "$A$2")
    """
    if not formula or not formula.strip().startswith("="):
        return None
    
    # Pattern: INDEX(Sheet!Range, MATCH(lookup_cell, Sheet!Range, 0), column_num)
    # More flexible pattern to handle various formats
    pattern = r'INDEX\s*\(\s*([^!]+)![^,]+,\s*MATCH\s*\(\s*([^,]+),\s*[^!]+![^,]+,\s*0\s*\)\s*,\s*(\d+)\s*\)'
    match = re.search(pattern, formula, re.IGNORECASE)
    
    if not match:
        return None
    
    sheet_name = match.group(1).strip()
    lookup_cell = match.group(2).strip()
    column_num = int(match.group(3))
    
    return (sheet_name, column_num, lookup_cell)


def find_row_by_match(
    workbook_values: Any,
    sheet_name: str,
    lookup_cell: str,
    current_sheet_name: str,
    current_row_index: int,
) -> int | None:
    """Find row number using MATCH logic from INDEX MATCH formula.
    
    Args:
        workbook_values: openpyxl Workbook loaded with data_only=True.
        sheet_name: Sheet to search in (e.g., "Podatki").
        lookup_cell: Cell reference like "$A$2" (absolute) or "A2" (relative).
        current_sheet_name: Current sheet name where formula is located.
        current_row_index: Current row index (1-based) where formula is located.
    
    Returns:
        Row number (1-based) or None if not found.
    """
    if workbook_values is None:
        return None
    
    try:
        # Parse lookup cell (e.g., "$A$2" -> column A, row 2)
        match = re.match(r'\$?([A-Z]+)\$?(\d+)', lookup_cell.upper())
        if not match:
            return None
        
        col_letter = match.group(1)
        row_ref_str = match.group(2)
        
        # Determine if row is absolute or relative
        # Check if row part has $ before the number (e.g., $A$2)
        # Split by $ and check if row number follows a $
        parts = lookup_cell.split('$')
        is_absolute_row = False
        for i, part in enumerate(parts):
            if part == row_ref_str and i > 0:
                is_absolute_row = True
                break
        
        if is_absolute_row or lookup_cell.count('$') >= 2:
            # Absolute reference (e.g., $A$2)
            lookup_row = int(row_ref_str)
        else:
            # Relative reference - calculate from current row
            lookup_row = current_row_index
        
        # Get lookup value from current sheet
        if current_sheet_name not in workbook_values.sheetnames:
            return None
        
        current_sheet = workbook_values[current_sheet_name]
        col_num = column_letter_to_number(col_letter)
        lookup_value = current_sheet.cell(row=lookup_row, column=col_num).value
        
        # Search in target sheet column A (column 1)
        if sheet_name not in workbook_values.sheetnames:
            return None
        
        target_sheet = workbook_values[sheet_name]
        for row_idx in range(1, target_sheet.max_row + 1):
            cell_value = target_sheet.cell(row=row_idx, column=1).value
            if cell_value == lookup_value:
                return row_idx
        
        return None
    except Exception:
        return None


def get_cell_value_from_workbook(
    workbook_values: Any,
    sheet_name: str,
    row_index: int,
    column_number: int,
) -> Any:
    """Get cell value from workbook by sheet, row, and column number.
    
    Args:
        workbook_values: openpyxl Workbook loaded with data_only=True.
        sheet_name: Name of the sheet.
        row_index: Excel row number (1-based).
        column_number: Column number (1-based, A=1, B=2, etc.).
    
    Returns:
        Cell value or None if not found.
    """
    if workbook_values is None:
        return None
    
    try:
        if sheet_name not in workbook_values.sheetnames:
            return None
        
        sheet = workbook_values[sheet_name]
        cell = sheet.cell(row=row_index, column=column_number)
        return cell.value
    except Exception:
        return None


# ==============================================================================
# WATER KEY DETECTION
# ==============================================================================


def is_water_key(key: str) -> bool:
    """Check if key represents water (dH2O, H2O).

    Args:
        key: Key string.

    Returns:
        True if water key.
    """
    if not key:
        return False
    base = re.sub(r"[_\-\.\s]*\d+$", "", key.strip(), flags=re.IGNORECASE)
    return base.lower() in {"dh2o", "h2o"}

