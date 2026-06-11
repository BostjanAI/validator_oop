"""Shared GUI helpers for catalog (šifrant) file loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from validator_oop.excel.catalog_loader import (
    CatalogData,
    format_catalog_summary_log_line,
    load_catalogs,
)

LogFn = Callable[[str], None]


def load_catalog_for_validation(
    razt_path_str: str,
    kem_path_str: str,
    *,
    log: LogFn | None = None,
) -> tuple[dict[str, CatalogData] | None, dict[str, str]]:
    """Load catalog Excel files from path strings.

    Returns:
        (catalog_data, catalog_paths) for ValidatorEngine.
        catalog_data is None if no valid paths or load failed.
    """
    razt_path = Path(razt_path_str.strip()) if razt_path_str.strip() else None
    kem_path = Path(kem_path_str.strip()) if kem_path_str.strip() else None

    if razt_path and not razt_path.is_file():
        if log:
            log(f"Opozorilo: Šifrant raztopin ne obstaja: {razt_path}")
        razt_path = None
    if kem_path and not kem_path.is_file():
        if log:
            log(f"Opozorilo: Šifrant kemikalij ne obstaja: {kem_path}")
        kem_path = None

    if not razt_path and not kem_path:
        return None, {}

    try:
        catalog_data = load_catalogs(
            raztopine_path=razt_path,
            kemikalije_path=kem_path,
        )
        if not catalog_data:
            return None, {}

        paths: dict[str, str] = {}
        if razt_path:
            paths["raztopina"] = str(razt_path)
        if kem_path:
            paths["kemikalija"] = str(kem_path)

        if log:
            loaded = ", ".join(catalog_data.keys())
            log(f"Šifranti naloženi: {loaded}")
            if razt_path:
                log(f"  Raztopine: {razt_path.name}")
            if kem_path:
                log(f"  Kemikalije: {kem_path.name}")

        return catalog_data, paths
    except Exception as e:
        if log:
            log(f"Opozorilo: Napaka pri nalaganju šifranta: {e}")
        return None, {}


def merge_catalog_summaries(summaries: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Merge catalog_validation metadata from multiple workbook runs."""
    enabled_items = [s for s in summaries if s.get("enabled")]
    if not enabled_items:
        return {"enabled": False}

    raz_path = next((s.get("raztopine_path") for s in enabled_items if s.get("raztopine_path")), "")
    kem_path = next((s.get("kemikalije_path") for s in enabled_items if s.get("kemikalije_path")), "")

    mismatches = sum(int(s.get("mismatches", 0)) for s in enabled_items)
    rows_r = sum(int(s.get("rows_checked_raztopina", 0)) for s in enabled_items)
    rows_k = sum(int(s.get("rows_checked_kemikalija", 0)) for s in enabled_items)
    codes_r = max(int(s.get("catalog_codes_raztopina", 0)) for s in enabled_items)
    codes_k = max(int(s.get("catalog_codes_kemikalija", 0)) for s in enabled_items)

    return {
        "enabled": True,
        "raztopine_path": raz_path,
        "kemikalije_path": kem_path,
        "catalog_codes_raztopina": codes_r,
        "catalog_codes_kemikalija": codes_k,
        "rows_checked_raztopina": rows_r,
        "rows_checked_kemikalija": rows_k,
        "rows_checked_total": rows_r + rows_k,
        "mismatches": mismatches,
        "status": "napake" if mismatches else "v redu",
    }


def log_catalog_summary_from_report(
    catalog_summary: Mapping[str, Any] | None,
    log: LogFn,
) -> None:
    """Log catalog validation result to GUI status."""
    if catalog_summary is None:
        log("Preverjanje šifrantov: ni izvedeno.")
        return
    log(format_catalog_summary_log_line(catalog_summary))
