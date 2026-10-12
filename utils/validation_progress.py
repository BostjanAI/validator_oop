"""Spremljanje napredka validacije (delež pregledanih receptur, število napak).

Shranjevanje v eni JSON datoteki (validation_progress.json) v mapi projekta:
- total_recipes: skupno število receptur (nastavi uporabnik)
- runs: seznam zapisov validacij (zaporedna_stevilka, path, datum, errors, warnings, valid).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Privzeta pot: mapa projekta (mapa, v kateri je paket validator_oop)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PROGRESS_FILE = _PROJECT_ROOT / "validation_progress.json"


def _default_data() -> dict[str, Any]:
    return {
        "total_recipes": 0,
        "runs": [],
    }


def get_progress_path() -> Path:
    """Vrne pot do datoteke napredka (privzeto validation_progress.json v mapi projekta)."""
    return _DEFAULT_PROGRESS_FILE


def load_progress(progress_path: Path | None = None) -> dict[str, Any]:
    """Naloži podatke napredka iz JSON. Če datoteka ne obstaja, vrne privzeto strukturo."""
    path = progress_path or get_progress_path()
    if not path.exists():
        return _default_data()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default_data()
    if "runs" not in data:
        data["runs"] = []
    if "total_recipes" not in data:
        data["total_recipes"] = 0
    return data


def save_progress(data: dict[str, Any], progress_path: Path | None = None) -> None:
    """Shrani podatke napredka v JSON."""
    path = progress_path or get_progress_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_run(
    file_path: str | Path,
    errors: int,
    warnings: int,
    *,
    valid: bool | None = None,
    progress_path: Path | None = None,
) -> None:
    """Zapiše eno validacijo v napredek (doda v runs) z zaporedno številko validacije."""
    path_resolved = Path(file_path).resolve()
    if valid is None:
        valid = errors == 0
    data = load_progress(progress_path)
    zaporedna_stevilka = len(data["runs"]) + 1
    entry = {
        "zaporedna_stevilka": zaporedna_stevilka,
        "path": str(path_resolved),
        "date": datetime.now().astimezone().isoformat(),
        "errors": errors,
        "warnings": warnings,
        "valid": valid,
    }
    data["runs"].append(entry)
    save_progress(data, progress_path)


def set_total_recipes(total: int, progress_path: Path | None = None) -> None:
    """Nastavi skupno število receptur za izračun deleža pregledanih."""
    data = load_progress(progress_path)
    data["total_recipes"] = max(0, total)
    save_progress(data, progress_path)


def get_metrics(progress_path: Path | None = None) -> dict[str, Any]:
    """Izračuna kazalnike iz shranjenih runs.

    Vrne:
    - total_runs: število vseh zapisov validacij
    - unique_files: število unikatnih datotek (pregledanih receptur)
    - total_errors: skupaj zaznanih napak
    - total_warnings: skupaj opozoril
    - total_recipes: skupno število receptur (za delež)
    - coverage_ratio: delež pregledanih (unique_files / total_recipes), 0.0 če total_recipes == 0
    """
    data = load_progress(progress_path)
    runs = data.get("runs", [])
    total_recipes = max(0, data.get("total_recipes", 0))

    unique_paths = {r.get("path", "") for r in runs if r.get("path")}
    unique_files = len(unique_paths)

    total_errors = sum(r.get("errors", 0) for r in runs)
    total_warnings = sum(r.get("warnings", 0) for r in runs)

    coverage_ratio = (unique_files / total_recipes) if total_recipes else 0.0

    return {
        "total_runs": len(runs),
        "unique_files": unique_files,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "total_recipes": total_recipes,
        "coverage_ratio": round(coverage_ratio, 4),
    }
