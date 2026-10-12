"""Catalog loader for solution/chemical/repro code validation.

Loads external Excel catalogs (Izvoz_sifre_razt.xlsx, Izvoz_kem.xlsx,
šifrant repro materiala) and builds normalized lookup dictionaries for
matching recipe keys against registered catalog codes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from openpyxl import load_workbook

from validator_oop.utils.helpers import coerce_str, norm_control_name, strip_instance_suffix

COL_SIFRA = "kataloskestevilke_sifra"
COL_MATERIAL_SIFRA = "material_sifra"

CATALOG_PRIMARY_COLUMN = {
    "raztopina": COL_SIFRA,
    "kemikalija": COL_SIFRA,
    "repro": COL_MATERIAL_SIFRA,
}

CATALOG_LOOKUP_COLUMNS = {
    "raztopina": (COL_SIFRA, "material_kataloske"),
    "kemikalija": (
        COL_SIFRA,
        COL_MATERIAL_SIFRA,
        "material_naziv_kratki",
        "material_naziv_dolgi",
        "material_kataloske",
    ),
    "repro": (COL_MATERIAL_SIFRA,),
}

# Recipe "Tip podatka" → catalog key in load_catalogs() result.
RECIPE_TIP_TO_CATALOG = {
    "raztopina": "raztopina",
    "kemikalija": "kemikalija",
    "repro": "repro",
    "reproodpis": "repro",
}

REPRO_TIPS = frozenset({"repro", "reproodpis"})
REPRO_USTREZNOST_CONTROL = "kontrolaustreznostirepro"
RAZTOPINA_USTREZNOST_CONTROL = "kontrolaustreznostiraztopine"

_CTRL_COL_RE = re.compile(r"^kontrola\s*[-–:]?\s*(\d+)\s*$", re.I)
_PAR1_COL_RES = (
    re.compile(r"^kontrola[-\s]*(?P<n>\d+)\s*[:]\s*par(?:am)?\s*1\s*$", re.I),
    re.compile(r"^kontrola\s*(?P<n>\d+)\s*(?:[-–:])?\s*par(?:am)?\s*1\s*$", re.I),
    re.compile(r"^p(?:ar|aram|m)\s*1\s*[,._-]?\s*(?P<n>\d+)\s*$", re.I),
)

_NUMERIC = re.compile(r"\d+\.\d+|\d+")


def _norm(s: object) -> str:
    if s is None:
        return ""
    return str(s).strip()


def _norm_key(s: object) -> str:
    return _norm(s).casefold()


def _norm_num(m: re.Match[str]) -> str:
    v = float(m.group(0))
    if v == int(v):
        return str(int(v))
    return f"{v:g}"


def normalize_concentrations(s: str) -> str:
    """Normalize numbers in string (e.g. 0.9 -> 0, 1.0 -> 1)."""
    return _NUMERIC.sub(_norm_num, s.casefold())


def catalog_lookup_keys(raw_sifra: str) -> list[str]:
    """All key variants for catalog lookup."""
    keys: list[str] = []
    for variant in (raw_sifra, strip_instance_suffix(raw_sifra)):
        if not variant:
            continue
        keys.append(_norm_key(variant))
        keys.append(normalize_concentrations(variant))
    out: list[str] = []
    seen: set[str] = set()
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def recipe_lookup_keys(raw_kljuc: str) -> list[str]:
    """All key variants for recipe key lookup."""
    keys: list[str] = []
    for variant in (raw_kljuc, strip_instance_suffix(raw_kljuc)):
        if not variant:
            continue
        keys.append(_norm_key(variant))
        keys.append(normalize_concentrations(variant))
    out: list[str] = []
    seen: set[str] = set()
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _split_catalog_values(value: object) -> list[str]:
    """Split comma-separated catalog values and extract base parts."""
    values: list[str] = []
    for part in _norm(value).split(","):
        cleaned = _norm(part)
        if not cleaned:
            continue
        values.append(cleaned)
        if " - " in cleaned:
            values.append(_norm(cleaned.split(" - ", 1)[0]))

    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _control_layout(
    row: Mapping[str, object],
    shared: Any | None = None,
) -> tuple[list[str], dict[str, int | None], dict[int, str]]:
    """Control / Param1 columns from SharedContext or from row keys."""
    if shared is not None and getattr(shared, "control_columns", None):
        return (
            list(shared.control_columns),
            dict(shared.control_numbers),
            dict(shared.param1_columns),
        )

    control_columns: list[str] = []
    control_numbers: dict[str, int | None] = {}
    param1_columns: dict[int, str] = {}
    for key in row:
        if not isinstance(key, str):
            continue
        head = key.strip()
        m_ctrl = _CTRL_COL_RE.fullmatch(head)
        if m_ctrl:
            control_columns.append(key)
            control_numbers[key] = int(m_ctrl.group(1))
            continue
        for pat in _PAR1_COL_RES:
            m_p1 = pat.match(head)
            if m_p1:
                param1_columns[int(m_p1.group("n"))] = key
                break
    return control_columns, control_numbers, param1_columns


def extract_control_param1_code(
    row: Mapping[str, object],
    control_ns: str,
    shared: Any | None = None,
) -> tuple[str, str]:
    """Vrednost Param1 pri navedeni kontroli (normalizirano ime).

    Returns:
        Tuple of (code, param1_column_name). Empty strings if not found.
    """
    target = norm_control_name(control_ns)
    control_columns, control_numbers, param1_columns = _control_layout(row, shared)
    for column in control_columns:
        raw = coerce_str(row.get(column, ""))
        if not raw:
            continue
        if norm_control_name(raw) != target:
            continue
        ctrl_number = control_numbers.get(column)
        param1_col = param1_columns.get(ctrl_number) if ctrl_number is not None else None
        if not param1_col:
            continue
        code = coerce_str(row.get(param1_col, "")).strip()
        if code:
            return code, param1_col
    return "", ""


def extract_repro_catalog_code(
    row: Mapping[str, object],
    shared: Any | None = None,
) -> tuple[str, str]:
    """Šifra repro materiala iz Param1 pri kontroli kontrolaustreznostirepro."""
    return extract_control_param1_code(row, REPRO_USTREZNOST_CONTROL, shared)


def extract_raztopina_catalog_code(
    row: Mapping[str, object],
    shared: Any | None = None,
) -> tuple[str, str]:
    """Šifra raztopine iz Param1 pri kontroli kontrolaustreznostiraztopine."""
    return extract_control_param1_code(row, RAZTOPINA_USTREZNOST_CONTROL, shared)


@dataclass(slots=True)
class CatalogData:
    """Loaded catalog data for one type (raztopina, kemikalija or repro).

    Attributes:
        lookup: Normalized key -> original catalog code mapping.
        all_codes: Sorted list of all unique catalog codes.
    """

    lookup: dict[str, str] = field(default_factory=dict)
    all_codes: list[str] = field(default_factory=list)


def load_catalog(
    path: Path,
    lookup_columns: Sequence[str] = (COL_SIFRA,),
    *,
    primary_column: str = COL_SIFRA,
) -> CatalogData:
    """Load a single catalog Excel file and build the lookup dictionary.

    Args:
        path: Path to the catalog Excel file.
        lookup_columns: Column names to use for building the lookup.
        primary_column: Column whose values are stored as display codes.

    Returns:
        CatalogData with populated lookup and all_codes.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the required column is missing.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Kataložna datoteka ne obstaja: {path}")

    wb = load_workbook(path, data_only=True)
    lookup: dict[str, str] = {}
    all_codes: list[str] = []
    seen_display: set[str] = set()
    try:
        ws = wb.active
        assert ws is not None
        cols: dict[str, int] = {}
        for cell in ws[1]:
            v = _norm(cell.value)
            col = cell.column
            if v and col is not None:
                cols[v] = col
        max_row = ws.max_row or 0

        if primary_column not in cols:
            raise ValueError(
                f"V {path.name} manjka stolpec \u201e{primary_column}\u201c. "
                f"Najdeni: {', '.join(cols)}"
            )
        c_sifra = cols[primary_column]
        lookup_col_indexes = [cols[col] for col in lookup_columns if col in cols]

        for r in range(2, max_row + 1):
            sifra = _norm(ws.cell(row=r, column=c_sifra).value)
            if not sifra:
                continue
            if sifra not in seen_display:
                seen_display.add(sifra)
                all_codes.append(sifra)
            for c_lookup in lookup_col_indexes:
                for value in _split_catalog_values(ws.cell(row=r, column=c_lookup).value):
                    for k in catalog_lookup_keys(value):
                        lookup.setdefault(k, sifra)
    finally:
        wb.close()

    all_codes.sort(key=str.casefold)
    return CatalogData(lookup=lookup, all_codes=all_codes)


def load_catalogs(
    raztopine_path: Path | None = None,
    kemikalije_path: Path | None = None,
    repro_path: Path | None = None,
) -> dict[str, CatalogData] | None:
    """Load catalogs if paths are provided.

    Args:
        raztopine_path: Path to Izvoz_sifre_razt.xlsx (or equivalent).
        kemikalije_path: Path to Izvoz_kem.xlsx (or equivalent).
        repro_path: Path to repro material catalog Excel (material_sifra).

    Returns:
        Dictionary mapping tip ("raztopina", "kemikalija", "repro") to CatalogData,
        or None if no path is provided.
    """
    if not raztopine_path and not kemikalije_path and not repro_path:
        return None

    catalogs: dict[str, CatalogData] = {}

    if raztopine_path:
        catalogs["raztopina"] = load_catalog(
            raztopine_path,
            CATALOG_LOOKUP_COLUMNS["raztopina"],
            primary_column=CATALOG_PRIMARY_COLUMN["raztopina"],
        )

    if kemikalije_path:
        catalogs["kemikalija"] = load_catalog(
            kemikalije_path,
            CATALOG_LOOKUP_COLUMNS["kemikalija"],
            primary_column=CATALOG_PRIMARY_COLUMN["kemikalija"],
        )

    if repro_path:
        catalogs["repro"] = load_catalog(
            repro_path,
            CATALOG_LOOKUP_COLUMNS["repro"],
            primary_column=CATALOG_PRIMARY_COLUMN["repro"],
        )

    return catalogs if catalogs else None


def match_key(kljuc: str, catalog: CatalogData) -> tuple[bool, str, str]:
    """Check if a recipe key matches any entry in the catalog.

    Args:
        kljuc: The recipe key to check.
        catalog: CatalogData to search in.

    Returns:
        Tuple of (is_match, matched_code, match_method).
    """
    stripped_kljuc = strip_instance_suffix(kljuc)
    stripped_keys = {_norm_key(stripped_kljuc), normalize_concentrations(stripped_kljuc)}

    for k in recipe_lookup_keys(kljuc):
        if k in catalog.lookup:
            if _norm_key(kljuc) == k:
                return True, catalog.lookup[k], "natančno"
            if stripped_kljuc != kljuc and k in stripped_keys:
                return True, catalog.lookup[k], "brez številk na koncu"
            if normalize_concentrations(kljuc) == k:
                return True, catalog.lookup[k], "normalizacija števil"
            return True, catalog.lookup[k], "normalizirano"

    return False, "", ""


VALIDATED_TIP_TYPES = frozenset(RECIPE_TIP_TO_CATALOG)


def build_catalog_validation_summary(
    workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
    catalog_data: dict[str, CatalogData],
    errors: Sequence[Any],
    *,
    raztopine_path: str | None = None,
    kemikalije_path: str | None = None,
    repro_path: str | None = None,
) -> dict[str, Any]:
    """Build summary metadata for catalog validation (report / status log).

    Args:
        workbook_data: Filtered sheet rows used during validation.
        catalog_data: Loaded catalogs by tip (raztopina, kemikalija, repro).
        errors: Validation errors from the run.
        raztopine_path: Path to raztopine catalog file (optional).
        kemikalije_path: Path to kemikalije catalog file (optional).
        repro_path: Path to repro material catalog file (optional).

    Returns:
        Dictionary suitable for report.metadata[\"catalog_validation\"].
    """
    from validator_oop.utils import coerce_str, norm_text

    rows_raztopina = 0
    rows_kemikalija = 0
    rows_repro = 0
    for rows in workbook_data.values():
        for row in rows:
            tip = norm_text(coerce_str(row.get("Tip podatka", "")))
            if tip not in VALIDATED_TIP_TYPES:
                continue
            if tip == "raztopina":
                sifra, _col = extract_raztopina_catalog_code(row)
                if sifra:
                    rows_raztopina += 1
            elif tip == "kemikalija":
                if coerce_str(row.get("Ključ preverjanja", "")).strip():
                    rows_kemikalija += 1
            elif tip in REPRO_TIPS:
                sifra, _col = extract_repro_catalog_code(row)
                if sifra:
                    rows_repro += 1

    mismatches = sum(
        1 for e in errors
        if getattr(e, "code", None) == "CATALOG_CODE_MISMATCH"
    )

    return {
        "enabled": True,
        "raztopine_path": raztopine_path or "",
        "kemikalije_path": kemikalije_path or "",
        "repro_path": repro_path or "",
        "catalog_codes_raztopina": len(catalog_data.get("raztopina", CatalogData()).all_codes),
        "catalog_codes_kemikalija": len(catalog_data.get("kemikalija", CatalogData()).all_codes),
        "catalog_codes_repro": len(catalog_data.get("repro", CatalogData()).all_codes),
        "rows_checked_raztopina": rows_raztopina,
        "rows_checked_kemikalija": rows_kemikalija,
        "rows_checked_repro": rows_repro,
        "rows_checked_total": rows_raztopina + rows_kemikalija + rows_repro,
        "mismatches": mismatches,
        "status": "napake" if mismatches else "v redu",
    }


def format_catalog_summary_log_line(summary: Mapping[str, Any]) -> str:
    """One-line status message for GUI log."""
    if not summary.get("enabled"):
        return "Preverjanje šifrantov: ni izvedeno (šifranti niso naloženi)."
    mismatches = summary.get("mismatches", 0)
    total = summary.get("rows_checked_total", 0)
    status = summary.get("status", "")
    return (
        f"Preverjanje šifrantov: {status} — pregledanih vrstic "
        f"(raztopina/kemikalija/repro): {total}, napak šifer: {mismatches}."
    )
