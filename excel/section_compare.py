"""Primerjava razdelkov med listi iste recepture (izoliran modul).

Razdelek se začne z vrstico tipa ``naslov`` (``Tip objekta`` ali
``Tip podatka``) — enaka logika kot v ``core/shared_context.py``, vendar
ta modul deluje samostojno in NE posega v validacijski engine.

Primerjava (prvi recepturni list je referenčni):
- število razdelkov med listi (``SECTION_COUNT_MISMATCH``),
- naslov razdelka (``SECTION_TITLE_MISMATCH``),
- število korakov v razdelku (``SECTION_STEP_COUNT_MISMATCH``),
- besedilo navodil v razdelku (``SECTION_INSTRUCTION_MISMATCH``).

Uporaba (GUI, CLI, web):
    result = compare_sections("receptura.xlsx")
    result.issues          # seznam napak (združljiv z ReportWriter)
    result.to_dict()       # JSON prikaz za spletni vmesnik
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from validator_oop.excel.excel_loader import ExcelLoader, LoadedWorkbook
from validator_oop.excel.recipe_workbook import sheet_has_required_columns
from validator_oop.utils.helpers import coerce_str, norm_text

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Section:
    """En razdelek na listu (od vrstice 'naslov' do naslednjega naslova)."""

    index: int                # zaporedna številka razdelka (1-based; 0 = pred prvim naslovom)
    title: str                # besedilo naslova (stolpec Navodilo vrstice 'naslov')
    start_row: int            # Excel vrstica naslova (oz. prve vrstice pri razdelku 0)
    end_row: int              # Excel vrstica zadnje vrstice razdelka
    row_count: int = 0        # število podatkovnih vrstic (brez naslova)
    steps: list[str] = field(default_factory=list)        # različni št. Koraka (po vrstnem redu)
    instructions: list[str] = field(default_factory=list)  # neprazna Navodila (brez naslova)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "title": self.title,
            "start_row": self.start_row,
            "end_row": self.end_row,
            "row_count": self.row_count,
            "step_count": self.step_count,
            "steps": list(self.steps),
        }


@dataclass(slots=True)
class SectionComparisonResult:
    """Rezultat primerjave razdelkov med listi ene datoteke."""

    filename: str
    base_sheet: str
    sheets: list[str]                                   # vsi primerjani recepturni listi
    sections_by_sheet: dict[str, list[Section]]
    issues: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_match(self) -> bool:
        return not any(i.get("severity") == "error" for i in self.issues)

    @property
    def counts(self) -> dict[str, int]:
        out = {"error": 0, "warning": 0, "info": 0}
        for issue in self.issues:
            sev = str(issue.get("severity", "error"))
            out[sev] = out.get(sev, 0) + 1
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "base_sheet": self.base_sheet,
            "sheets": list(self.sheets),
            "is_match": self.is_match,
            "counts": self.counts,
            "sections": {
                sheet: [s.to_dict() for s in sections]
                for sheet, sections in self.sections_by_sheet.items()
            },
            "issues": list(self.issues),
        }


def _is_naslov_row(row: dict[str, Any]) -> bool:
    tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
    tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
    return tip_obj == "naslov" or tip_data == "naslov"


def _row_is_empty(row: dict[str, Any]) -> bool:
    return not any(coerce_str(v) for v in row.values())


def parse_sections(rows: list[dict[str, Any]], row_offset: int = 2) -> list[Section]:
    """Razčleni vrstice lista v razdelke (po vrsticah 'naslov').

    Args:
        rows: Vrstice lista kot slovarji (izhod WorkbookParser).
        row_offset: Excel vrstica prve podatkovne vrstice (privzeto 2).

    Returns:
        Seznam razdelkov po vrstnem redu. Vrstice pred prvim naslovom se
        združijo v razdelek z indeksom 0 (samo če vsebujejo podatke).
    """
    sections: list[Section] = []
    current: Section | None = None

    for idx, row in enumerate(rows):
        excel_row = idx + row_offset

        if _is_naslov_row(row):
            title = coerce_str(row.get("Navodilo", "")) or coerce_str(row.get("Labela", ""))
            current = Section(
                index=len([s for s in sections if s.index > 0]) + 1,
                title=title,
                start_row=excel_row,
                end_row=excel_row,
            )
            sections.append(current)
            continue

        if _row_is_empty(row):
            continue

        if current is None:
            # Vrstice pred prvim naslovom → razdelek 0
            current = Section(index=0, title="(pred prvim naslovom)", start_row=excel_row, end_row=excel_row)
            sections.append(current)

        current.end_row = excel_row
        current.row_count += 1

        step = coerce_str(row.get("št. Koraka", ""))
        if step and step not in current.steps:
            current.steps.append(step)

        instruction = coerce_str(row.get("Navodilo", ""))
        if instruction:
            current.instructions.append(instruction)

    return sections


def _issue(
    sheet: str,
    row: int | str,
    code: str,
    message: str,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "sheet": sheet,
        "row": row,
        "col": "",
        "code": code,
        "message": message,
        "severity": severity,
    }


def _compare_sheet_pair(
    base_sheet: str,
    base_sections: list[Section],
    other_sheet: str,
    other_sections: list[Section],
) -> list[dict[str, Any]]:
    """Primerja razdelke referenčnega lista z razdelki drugega lista."""
    issues: list[dict[str, Any]] = []

    if len(base_sections) != len(other_sections):
        issues.append(
            _issue(
                other_sheet,
                other_sections[0].start_row if other_sections else "",
                "SECTION_COUNT_MISMATCH",
                (
                    f"List '{other_sheet}' ima {len(other_sections)} razdelkov, "
                    f"referenčni list '{base_sheet}' pa {len(base_sections)}."
                ),
            )
        )

    for base_sec, other_sec in zip(base_sections, other_sections):
        label = f"razdelek {base_sec.index}" + (f" ('{base_sec.title}')" if base_sec.title else "")

        if norm_text(base_sec.title) != norm_text(other_sec.title):
            issues.append(
                _issue(
                    other_sheet,
                    other_sec.start_row,
                    "SECTION_TITLE_MISMATCH",
                    (
                        f"Naslov razdelka {other_sec.index} se razlikuje: "
                        f"'{other_sec.title}' (list '{other_sheet}') proti "
                        f"'{base_sec.title}' (list '{base_sheet}')."
                    ),
                    severity="warning",
                )
            )

        if base_sec.step_count != other_sec.step_count:
            issues.append(
                _issue(
                    other_sheet,
                    other_sec.start_row,
                    "SECTION_STEP_COUNT_MISMATCH",
                    (
                        f"{label.capitalize()}: list '{other_sheet}' ima "
                        f"{other_sec.step_count} korakov, list '{base_sheet}' pa "
                        f"{base_sec.step_count}."
                    ),
                )
            )

        base_instr = [norm_text(t) for t in base_sec.instructions]
        other_instr = [norm_text(t) for t in other_sec.instructions]
        if base_instr != other_instr:
            detail = _first_instruction_difference(base_sec, other_sec)
            issues.append(
                _issue(
                    other_sheet,
                    other_sec.start_row,
                    "SECTION_INSTRUCTION_MISMATCH",
                    f"{label.capitalize()}: besedilo navodil se razlikuje med "
                    f"listoma '{base_sheet}' in '{other_sheet}'.{detail}",
                )
            )

    return issues


def _first_instruction_difference(base_sec: Section, other_sec: Section) -> str:
    """Vrne opis prve razlike v navodilih (za bolj uporabno sporočilo)."""
    for i, (a, b) in enumerate(zip(base_sec.instructions, other_sec.instructions)):
        if norm_text(a) != norm_text(b):
            return f" Prva razlika pri navodilu št. {i + 1}: '{_short(a)}' proti '{_short(b)}'."
    if len(base_sec.instructions) != len(other_sec.instructions):
        return (
            f" Različno število navodil: {len(base_sec.instructions)} proti "
            f"{len(other_sec.instructions)}."
        )
    return ""


def _short(text: str, limit: int = 60) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def find_recipe_sheets(workbook: LoadedWorkbook) -> list[str]:
    """Vrne liste, ki vsebujejo vse zahtevane IPO stolpce (recepturni listi)."""
    return [
        sheet
        for sheet in workbook.sheet_names
        if sheet_has_required_columns(workbook.get_headers(sheet))
    ]


def compare_sections(
    workbook_path: str | Path,
    *,
    loader: ExcelLoader | None = None,
) -> SectionComparisonResult:
    """Primerja razdelke med vsemi recepturnimi listi ene datoteke.

    Args:
        workbook_path: Pot do Excel datoteke (.xlsx/.xlsm).
        loader: Opcijski ExcelLoader (za teste / injekcijo).

    Returns:
        SectionComparisonResult z razdelki po listih in najdenimi razlikami.

    Raises:
        FileNotFoundError: Če datoteka ne obstaja.
        ValueError: Če datoteka nima vsaj dveh recepturnih listov.
    """
    path = Path(workbook_path)
    loader = loader or ExcelLoader()
    workbook = loader.load(path)

    recipe_sheets = find_recipe_sheets(workbook)
    if len(recipe_sheets) < 2:
        raise ValueError(
            "Za primerjavo razdelkov datoteka potrebuje vsaj dva lista z "
            f"recepturo (najdenih: {len(recipe_sheets)})."
        )

    sections_by_sheet: dict[str, list[Section]] = {
        sheet: parse_sections(workbook.get_sheet_data(sheet), workbook.row_offset)
        for sheet in recipe_sheets
    }

    base_sheet = recipe_sheets[0]
    issues: list[dict[str, Any]] = []
    for other_sheet in recipe_sheets[1:]:
        issues.extend(
            _compare_sheet_pair(
                base_sheet,
                sections_by_sheet[base_sheet],
                other_sheet,
                sections_by_sheet[other_sheet],
            )
        )

    logger.info(
        "Primerjava razdelkov (%s): %d listov, %d razlik.",
        path.name,
        len(recipe_sheets),
        len(issues),
    )

    return SectionComparisonResult(
        filename=path.name,
        base_sheet=base_sheet,
        sheets=recipe_sheets,
        sections_by_sheet=sections_by_sheet,
        issues=issues,
    )


def write_section_compare_report(
    result: SectionComparisonResult,
    out_path: str | Path,
    *,
    logger_: logging.Logger | None = None,
) -> Path:
    """Zapiše poročilo primerjave razdelkov (.xlsx ali .txt) prek ReportWriter.

    Args:
        result: Rezultat primerjave (``compare_sections``).
        out_path: Ciljna pot poročila (.xlsx ali .txt).

    Returns:
        Pot zapisanega poročila.

    Raises:
        ValueError: Če končnica ni .xlsx ali .txt.
    """
    from validator_oop.excel.report_writer import ReportWriter

    out_path = Path(out_path)
    writer = ReportWriter(logger=logger_ or logger)
    if out_path.suffix.lower() == ".xlsx":
        writer.write_excel_report(out_path, result.issues)
    elif out_path.suffix.lower() == ".txt":
        writer.write_text_report(out_path, result.issues)
    else:
        raise ValueError("Poročilo primerjave razdelkov mora biti .xlsx ali .txt")
    return out_path
