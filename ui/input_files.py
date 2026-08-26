"""Shared helpers for discovering and filtering GUI input workbooks."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from validator_oop.excel.excel_loader import ExcelLoader

EXCEL_SUFFIXES = frozenset({".xlsx", ".xlsm", ".xls"})
STARO_FOLDER_NAME = "staro"


def is_excel_input_file(path: Path) -> bool:
    return path.suffix.lower() in EXCEL_SUFFIXES


def is_under_staro_folder(path: Path) -> bool:
    return any(part.casefold() == STARO_FOLDER_NAME for part in path.parts)


def iter_excel_candidates_in_folders(folders: list[Path]) -> Iterator[Path]:
    """Yield Excel files from folders, skipping anything under `staro`."""
    for folder in folders:
        if not folder.exists() or not folder.is_dir():
            continue
        for candidate in folder.rglob("*"):
            if not candidate.is_file():
                continue
            if not is_excel_input_file(candidate):
                continue
            if is_under_staro_folder(candidate):
                continue
            yield candidate


def merge_unique_paths(existing: list[str], new_paths: list[Path | str]) -> list[str]:
    all_paths = existing + [str(p) for p in new_paths]
    seen: set[str] = set()
    deduped: list[str] = []
    for path in all_paths:
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def discover_recipe_workbooks(
    folders: list[Path],
    loader: ExcelLoader,
    *,
    log: Callable[[str], None] | None = None,
) -> list[Path]:
    """Find recipe workbooks in folders; skip Excel files without required columns."""
    discovered: list[Path] = []
    skipped = 0
    for candidate in iter_excel_candidates_in_folders(folders):
        if loader.has_required_columns(candidate):
            discovered.append(candidate)
        else:
            skipped += 1
            if log:
                log(f"Preskočeno (brez zahtevanih stolpcev): {candidate.name}")

    if log:
        if discovered:
            log(f"Najdenih receptur: {len(discovered)}")
        if skipped:
            log(f"Preskočenih Excel datotek brez zahtevanih stolpcev: {skipped}")
    return discovered


@dataclass(slots=True)
class WorkbookFilterResult:
    """Outcome of filtering selected workbooks before validation."""

    valid: list[Path] = field(default_factory=list)
    skipped_staro: list[Path] = field(default_factory=list)
    skipped_no_columns: list[Path] = field(default_factory=list)


def filter_workbooks_with_required_columns(
    paths: list[Path],
    loader: ExcelLoader,
    *,
    log: Callable[[str], None] | None = None,
) -> WorkbookFilterResult:
    """Keep only workbooks with all REQUIRED_COLUMNS on at least one sheet."""
    result = WorkbookFilterResult()
    for path in paths:
        if is_under_staro_folder(path):
            result.skipped_staro.append(path)
            if log:
                log(f"Preskočeno (mapa 'staro'): {path.name}")
            continue
        if loader.has_required_columns(path):
            result.valid.append(path)
        else:
            result.skipped_no_columns.append(path)
            if log:
                log(f"Preskočeno (brez zahtevanih stolpcev): {path.name}")
    return result


def format_no_valid_workbooks_message(result: WorkbookFilterResult) -> tuple[str, str]:
    """Return user-facing dialog text and matching log line."""
    if result.skipped_staro and not result.skipped_no_columns:
        if len(result.skipped_staro) == 1:
            dialog = (
                "Izbrana datoteka se nahaja v mapi 'staro'.\n\n"
                "Validacija arhivskih datotek ni dovoljena. "
                "Premakni datoteko iz mape 'staro' ali izberi datoteko iz aktivne mape."
            )
            log_line = (
                "NAPAKA: Izbrana datoteka se nahaja v mapi 'staro' – validacija ni bila izvedena."
            )
        else:
            dialog = (
                f"Vse izbrane datoteke ({len(result.skipped_staro)}) se nahajajo v mapi 'staro'.\n\n"
                "Validacija arhivskih datotek ni dovoljena. "
                "Premakni datoteke iz mape 'staro' ali izberi datoteke iz aktivne mape."
            )
            log_line = (
                f"NAPAKA: {len(result.skipped_staro)} datotek v mapi 'staro' – validacija ni bila izvedena."
            )
        return dialog, log_line

    if result.skipped_staro and result.skipped_no_columns:
        dialog = (
            "Nobena izbrana datoteka ni bila validirana:\n\n"
            f"- {len(result.skipped_staro)} datotek v mapi 'staro' (validacija ni dovoljena)\n"
            f"- {len(result.skipped_no_columns)} datotek brez zahtevanih stolpcev recepture"
        )
        log_line = (
            "NAPAKA: Nobena datoteka ni bila validirana "
            f"({len(result.skipped_staro)} v mapi 'staro', "
            f"{len(result.skipped_no_columns)} brez zahtevanih stolpcev)."
        )
        return dialog, log_line

    dialog = "Nobena izbrana datoteka nima zahtevanih stolpcev recepture."
    log_line = "NAPAKA: Nobena datoteka nima zahtevanih stolpcev recepture."
    return dialog, log_line
