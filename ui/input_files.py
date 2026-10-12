"""Shared helpers for discovering and filtering GUI input workbooks."""

from __future__ import annotations

import os
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


def iter_excel_candidates_in_folders(
    folders: list[Path],
    *,
    log: Callable[[str], None] | None = None,
) -> Iterator[Path]:
    """Yield Excel files from folders, never entering a directory named `staro`."""
    for folder in folders:
        if not folder.exists() or not folder.is_dir():
            continue
        if is_under_staro_folder(folder):
            if log:
                log(f"Preskočena mapa 'staro': {folder}")
            continue
        for dirpath, dirnames, filenames in os.walk(folder):
            kept_dirs: list[str] = []
            for name in dirnames:
                if name.casefold() == STARO_FOLDER_NAME:
                    if log:
                        log(f"Preskočena mapa 'staro': {Path(dirpath) / name}")
                    continue
                kept_dirs.append(name)
            dirnames[:] = kept_dirs
            base = Path(dirpath)
            for filename in filenames:
                candidate = base / filename
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
    """Find recipe workbooks in folders; skip Excel files with no recipe columns."""
    discovered: list[Path] = []
    skipped = 0
    for candidate in iter_excel_candidates_in_folders(folders, log=log):
        if loader.has_required_columns(candidate):
            discovered.append(candidate)
        else:
            skipped += 1
            if log:
                log(f"Preskočeno (ni stolpcev recepture): {candidate.name}")

    if log:
        if discovered:
            log(f"Najdenih receptur: {len(discovered)}")
        if skipped:
            log(f"Preskočenih Excel datotek brez stolpcev recepture: {skipped}")
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
    """Keep explicitly selected workbooks that have a recipe column.

    Files inside a `staro` folder are allowed here. Folder discovery
    (`iter_excel_candidates_in_folders`) still skips that folder.
    """
    result = WorkbookFilterResult()
    for path in paths:
        if loader.has_required_columns(path):
            result.valid.append(path)
        else:
            result.skipped_no_columns.append(path)
            if log:
                log(f"Preskočeno (ni stolpcev recepture): {path.name}")
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
            f"- {len(result.skipped_no_columns)} datotek brez stolpcev recepture"
        )
        log_line = (
            "NAPAKA: Nobena datoteka ni bila validirana "
            f"({len(result.skipped_staro)} v mapi 'staro', "
            f"{len(result.skipped_no_columns)} brez stolpcev recepture)."
        )
        return dialog, log_line

    dialog = "Nobena izbrana datoteka nima stolpcev recepture."
    log_line = "NAPAKA: Nobena datoteka nima stolpcev recepture."
    return dialog, log_line
