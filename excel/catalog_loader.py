"""Catalog loader for solution/chemical code validation.

Loads external Excel catalogs (Izvoz_sifre_razt.xlsx, Izvoz_kem.xlsx)
and builds normalized lookup dictionaries for matching recipe keys against
registered catalog codes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from openpyxl import load_workbook

from validator_oop.utils.helpers import strip_instance_suffix

COL_SIFRA = "kataloskestevilke_sifra"

CATALOG_LOOKUP_COLUMNS = {
    "raztopina": (COL_SIFRA, "material_kataloske"),
    "kemikalija": (
        COL_SIFRA,
        "material_sifra",
        "material_naziv_kratki",
        "material_naziv_dolgi",
        "material_kataloske",
    ),
}

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


@dataclass(slots=True)
class CatalogData:
    """Loaded catalog data for one type (raztopina or kemikalija).

    Attributes:
        lookup: Normalized key -> original catalog code mapping.
        all_codes: Sorted list of all unique catalog codes.
    """

    lookup: dict[str, str] = field(default_factory=dict)
    all_codes: list[str] = field(default_factory=list)


def load_catalog(
    path: Path,
    lookup_columns: Sequence[str] = (COL_SIFRA,),
) -> CatalogData:
    """Load a single catalog Excel file and build the lookup dictionary.

    Args:
        path: Path to the catalog Excel file.
        lookup_columns: Column names to use for building the lookup.

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
            if v:
                cols[v] = cell.column
        max_row = ws.max_row or 0

        if COL_SIFRA not in cols:
            raise ValueError(
                f"V {path.name} manjka stolpec \u201e{COL_SIFRA}\u201c. "
                f"Najdeni: {', '.join(cols)}"
            )
        c_sifra = cols[COL_SIFRA]
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
) -> dict[str, CatalogData] | None:
    """Load both catalogs if paths are provided.

    Args:
        raztopine_path: Path to Izvoz_sifre_razt.xlsx (or equivalent).
        kemikalije_path: Path to Izvoz_kem.xlsx (or equivalent).

    Returns:
        Dictionary mapping tip ("raztopina", "kemikalija") to CatalogData,
        or None if neither path is provided.
    """
    if not raztopine_path and not kemikalije_path:
        return None

    catalogs: dict[str, CatalogData] = {}

    if raztopine_path:
        catalogs["raztopina"] = load_catalog(
            raztopine_path,
            CATALOG_LOOKUP_COLUMNS["raztopina"],
        )

    if kemikalije_path:
        catalogs["kemikalija"] = load_catalog(
            kemikalije_path,
            CATALOG_LOOKUP_COLUMNS["kemikalija"],
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


VALIDATED_TIP_TYPES = frozenset({"raztopina", "kemikalija"})


def build_catalog_validation_summary(
    workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
    catalog_data: dict[str, CatalogData],
    errors: Sequence[Any],
    *,
    raztopine_path: str | None = None,
    kemikalije_path: str | None = None,
) -> dict[str, Any]:
    """Build summary metadata for catalog validation (report / status log).

    Args:
        workbook_data: Filtered sheet rows used during validation.
        catalog_data: Loaded catalogs by tip (raztopina, kemikalija).
        errors: Validation errors from the run.
        raztopine_path: Path to raztopine catalog file (optional).
        kemikalije_path: Path to kemikalije catalog file (optional).

    Returns:
        Dictionary suitable for report.metadata[\"catalog_validation\"].
    """
    from validator_oop.utils import coerce_str, norm_text

    rows_raztopina = 0
    rows_kemikalija = 0
    for rows in workbook_data.values():
        for row in rows:
            tip = norm_text(coerce_str(row.get("Tip podatka", "")))
            kljuc = coerce_str(row.get("Ključ preverjanja", "")).strip()
            if not kljuc or tip not in VALIDATED_TIP_TYPES:
                continue
            if tip == "raztopina":
                rows_raztopina += 1
            elif tip == "kemikalija":
                rows_kemikalija += 1

    mismatches = sum(
        1 for e in errors
        if getattr(e, "code", None) == "CATALOG_CODE_MISMATCH"
    )

    return {
        "enabled": True,
        "raztopine_path": raztopine_path or "",
        "kemikalije_path": kemikalije_path or "",
        "catalog_codes_raztopina": len(catalog_data.get("raztopina", CatalogData()).all_codes),
        "catalog_codes_kemikalija": len(catalog_data.get("kemikalija", CatalogData()).all_codes),
        "rows_checked_raztopina": rows_raztopina,
        "rows_checked_kemikalija": rows_kemikalija,
        "rows_checked_total": rows_raztopina + rows_kemikalija,
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
        f"(raztopina/kemikalija): {total}, napak šifer: {mismatches}."
    )
