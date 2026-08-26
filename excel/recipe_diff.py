"""Diff dveh verzij recepture (izoliran modul, brez validacijske logike).

Primerja dve Excel datoteki (verzijo A in verzijo B) po listih in vrsticah:
- dodani / odstranjeni listi,
- dodani / odstranjeni stolpci na skupnih listih,
- dodane / odstranjene / spremenjene vrstice (poravnava z difflib.SequenceMatcher),
- pri spremenjenih vrsticah seznam spremenjenih stolpcev (stara → nova vrednost).

Modul uporablja obstoječi ``ExcelLoader`` in NE posega v engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from validator_oop.excel.excel_loader import ExcelLoader
from validator_oop.utils.helpers import coerce_str

logger = logging.getLogger(__name__)

# Stolpci za kratek opis vrstice v poročilu (prikaz dodanih/odstranjenih vrstic)
_PREVIEW_COLUMNS = ("št. Koraka", "Ključ preverjanja", "Tip podatka", "Navodilo")
_PREVIEW_LIMIT = 60


@dataclass(slots=True)
class CellChange:
    """Sprememba ene celice v paru vrstic."""

    column: str
    old: str
    new: str

    def to_dict(self) -> dict[str, str]:
        return {"column": self.column, "old": self.old, "new": self.new}


@dataclass(slots=True)
class RowChange:
    """Spremenjena vrstica (obstaja v obeh verzijah, a z drugačno vsebino)."""

    row_a: int
    row_b: int
    preview: str
    changes: list[CellChange] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_a": self.row_a,
            "row_b": self.row_b,
            "preview": self.preview,
            "changes": [c.to_dict() for c in self.changes],
        }


@dataclass(slots=True)
class SheetDiff:
    """Razlike enega lista med verzijama."""

    sheet: str
    status: str  # "common" | "added" | "removed"
    columns_added: list[str] = field(default_factory=list)
    columns_removed: list[str] = field(default_factory=list)
    rows_added: list[dict[str, Any]] = field(default_factory=list)    # {row, preview}
    rows_removed: list[dict[str, Any]] = field(default_factory=list)  # {row, preview}
    rows_changed: list[RowChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(
            self.status != "common"
            or self.columns_added
            or self.columns_removed
            or self.rows_added
            or self.rows_removed
            or self.rows_changed
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sheet": self.sheet,
            "status": self.status,
            "has_changes": self.has_changes,
            "columns_added": list(self.columns_added),
            "columns_removed": list(self.columns_removed),
            "rows_added": list(self.rows_added),
            "rows_removed": list(self.rows_removed),
            "rows_changed": [r.to_dict() for r in self.rows_changed],
        }


@dataclass(slots=True)
class RecipeDiff:
    """Skupni rezultat primerjave dveh verzij recepture."""

    file_a: str
    file_b: str
    sheets: list[SheetDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(s.has_changes for s in self.sheets)

    @property
    def summary(self) -> dict[str, int]:
        out = {
            "sheets_added": 0,
            "sheets_removed": 0,
            "sheets_changed": 0,
            "rows_added": 0,
            "rows_removed": 0,
            "rows_changed": 0,
        }
        for sd in self.sheets:
            if sd.status == "added":
                out["sheets_added"] += 1
            elif sd.status == "removed":
                out["sheets_removed"] += 1
            elif sd.has_changes:
                out["sheets_changed"] += 1
            out["rows_added"] += len(sd.rows_added)
            out["rows_removed"] += len(sd.rows_removed)
            out["rows_changed"] += len(sd.rows_changed)
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_a": self.file_a,
            "file_b": self.file_b,
            "has_changes": self.has_changes,
            "summary": self.summary,
            "sheets": [s.to_dict() for s in self.sheets],
        }


def _row_preview(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for col in _PREVIEW_COLUMNS:
        value = coerce_str(row.get(col, ""))
        if value:
            if len(value) > _PREVIEW_LIMIT:
                value = value[: _PREVIEW_LIMIT - 1] + "…"
            parts.append(f"{col}={value}")
    return " | ".join(parts) or "(prazna vrstica)"


def _row_signature(row: dict[str, Any], columns: list[str]) -> tuple[str, ...]:
    return tuple(coerce_str(row.get(col, "")) for col in columns)


def _diff_rows(
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
    columns: list[str],
    row_offset_a: int,
    row_offset_b: int,
    sheet_diff: SheetDiff,
) -> None:
    """Poravna vrstice obeh verzij in zabeleži dodane/odstranjene/spremenjene."""
    sigs_a = [_row_signature(r, columns) for r in rows_a]
    sigs_b = [_row_signature(r, columns) for r in rows_b]

    matcher = SequenceMatcher(a=sigs_a, b=sigs_b, autojunk=False)
    for tag, a0, a1, b0, b1 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag in ("delete", "replace"):
            removed = range(a0, a1)
        else:
            removed = range(0)
        if tag in ("insert", "replace"):
            added = range(b0, b1)
        else:
            added = range(0)

        if tag == "replace":
            # Vrstice v bloku 'replace' parimo po vrstnem redu → spremenjene vrstice
            pairs = min(a1 - a0, b1 - b0)
            for k in range(pairs):
                ia, ib = a0 + k, b0 + k
                changes = [
                    CellChange(column=col, old=coerce_str(rows_a[ia].get(col, "")), new=coerce_str(rows_b[ib].get(col, "")))
                    for col in columns
                    if coerce_str(rows_a[ia].get(col, "")) != coerce_str(rows_b[ib].get(col, ""))
                ]
                if changes:
                    sheet_diff.rows_changed.append(
                        RowChange(
                            row_a=ia + row_offset_a,
                            row_b=ib + row_offset_b,
                            preview=_row_preview(rows_b[ib]),
                            changes=changes,
                        )
                    )
            removed = range(a0 + pairs, a1)
            added = range(b0 + pairs, b1)

        for ia in removed:
            sheet_diff.rows_removed.append(
                {"row": ia + row_offset_a, "preview": _row_preview(rows_a[ia])}
            )
        for ib in added:
            sheet_diff.rows_added.append(
                {"row": ib + row_offset_b, "preview": _row_preview(rows_b[ib])}
            )


def diff_recipes(
    path_a: str | Path,
    path_b: str | Path,
    *,
    loader: ExcelLoader | None = None,
) -> RecipeDiff:
    """Primerja dve verziji recepture (datoteka A = stara, B = nova).

    Args:
        path_a: Pot do prve (stare) verzije.
        path_b: Pot do druge (nove) verzije.
        loader: Opcijski ExcelLoader.

    Returns:
        RecipeDiff z razlikami po listih.

    Raises:
        FileNotFoundError: Če katera od datotek ne obstaja.
    """
    path_a, path_b = Path(path_a), Path(path_b)
    loader = loader or ExcelLoader()

    wb_a = loader.load(path_a)
    wb_b = loader.load(path_b)

    result = RecipeDiff(file_a=path_a.name, file_b=path_b.name)

    sheets_a = list(wb_a.sheet_names)
    sheets_b = list(wb_b.sheet_names)
    set_a, set_b = set(sheets_a), set(sheets_b)

    for sheet in sheets_a:
        if sheet not in set_b:
            result.sheets.append(SheetDiff(sheet=sheet, status="removed"))
    for sheet in sheets_b:
        if sheet not in set_a:
            result.sheets.append(SheetDiff(sheet=sheet, status="added"))

    for sheet in sheets_a:
        if sheet not in set_b:
            continue
        headers_a = wb_a.get_headers(sheet)
        headers_b = wb_b.get_headers(sheet)
        common_columns = [c for c in headers_a if c in set(headers_b)]

        sheet_diff = SheetDiff(
            sheet=sheet,
            status="common",
            columns_added=[c for c in headers_b if c not in set(headers_a)],
            columns_removed=[c for c in headers_a if c not in set(headers_b)],
        )
        _diff_rows(
            wb_a.get_sheet_data(sheet),
            wb_b.get_sheet_data(sheet),
            common_columns,
            wb_a.row_offset,
            wb_b.row_offset,
            sheet_diff,
        )
        result.sheets.append(sheet_diff)

    logger.info(
        "Diff receptur %s ⟷ %s: %s",
        path_a.name,
        path_b.name,
        result.summary,
    )
    return result
