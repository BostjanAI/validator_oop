"""Management report writer for IPO Validator.

Generates a Markdown management report from validation issues,
grouping errors by sheet and by error type with counts and details.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from validator_oop.core.constants import translate_code


def write_management_report(
    report_path: str | Path,
    issues: Sequence[Mapping[str, Any]],
    source_filename: str = "",
) -> None:
    """Write a Markdown management report from validation issues.

    Args:
        report_path: Path to the output .md file.
        issues: List of issue dictionaries (same format as ReportWriter).
        source_filename: Name of the validated file (for the header).
    """
    path = Path(report_path)
    now = datetime.now()
    date_str = now.strftime("%d. %m. %Y")
    time_str = now.strftime("%H:%M")

    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────────────────
    fname = source_filename or path.stem
    lines += [
        f"# Poročilo o validaciji recepture",
        f"**Datoteka:** `{fname}`  ",
        f"**Datum validacije:** {date_str}, {time_str}  ",
        f"**Orodje:** IPO Validator",
        "",
        "---",
        "",
    ]

    if not issues:
        lines += [
            "## Rezultat",
            "",
            "Receptura je prestala validacijo brez napak.",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    total = len(issues)

    # ── Group by sheet ─────────────────────────────────────────────────────────
    sheet_counts: dict[str, int] = defaultdict(int)
    for issue in issues:
        sheet = _strip_filename(issue.get("sheet") or "(neznano)", source_filename)
        sheet_counts[sheet] += 1

    # ── Group by error code ────────────────────────────────────────────────────
    code_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for issue in issues:
        code = issue.get("code") or "(neznano)"
        code_groups[code].append(issue)

    # ── Summary ────────────────────────────────────────────────────────────────
    lines += [
        "## 1. Povzetek",
        "",
        f"Validacija je odkrila skupno **{total} napak** v **{len(sheet_counts)} listih** recepture.",
        "",
    ]

    # ── Errors by sheet ────────────────────────────────────────────────────────
    lines += [
        "## 2. Napake po listih",
        "",
        "| List | Število napak |",
        "|---|---|",
    ]
    for sheet, count in sorted(sheet_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {sheet} | {count} |")
    lines += [
        f"| **SKUPAJ** | **{total}** |",
        "",
    ]

    # ── Errors by type ─────────────────────────────────────────────────────────
    lines += [
        "## 3. Napake po vrsti",
        "",
        "| Koda | Opis | Število |",
        "|---|---|---|",
    ]
    for code, group in sorted(code_groups.items(), key=lambda x: -len(x[1])):
        desc = translate_code(code)
        lines.append(f"| `{code}` | {desc} | {len(group)} |")
    lines.append("")

    # ── Details per code ───────────────────────────────────────────────────────
    lines += [
        "## 4. Podrobnosti",
        "",
    ]
    for code, group in sorted(code_groups.items(), key=lambda x: -len(x[1])):
        desc = translate_code(code)
        lines += [
            f"### {desc} (`{code}`)",
            "",
            f"Število pojavitev: **{len(group)}**",
            "",
        ]

        # Sheets affected
        sheets_affected = sorted({
            _strip_filename(i.get("sheet") or "(neznano)", source_filename)
            for i in group
        })
        if sheets_affected:
            lines.append(f"Prizadeti listi: {', '.join(f'`{s}`' for s in sheets_affected)}")
            lines.append("")

        # Show up to 5 representative messages (only unique ones)
        seen_msgs: set[str] = set()
        shown = 0
        for issue in group:
            msg = issue.get("message") or ""
            row = issue.get("row") or ""
            col = issue.get("col") or ""
            sheet = _strip_filename(issue.get("sheet") or "", source_filename)
            # Build a compact unique key
            key = f"{sheet}|{col}|{msg}"
            if key in seen_msgs:
                continue
            seen_msgs.add(key)
            location = _format_location(sheet, row, col)
            lines.append(f"- {location}{msg}")
            shown += 1
            if shown >= 5:
                remaining = len(group) - shown
                if remaining > 0:
                    lines.append(f"- *… in še {remaining} podobnih napak*")
                break
        lines.append("")

    # ── Footer ─────────────────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        f"*Poročilo pripravljeno z aplikacijo IPO Validator, {date_str}*",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def _strip_filename(sheet: str, filename: str) -> str:
    """Remove the filename prefix from sheet label (e.g. 'file.xlsm:Sheet1' → 'Sheet1')."""
    if filename and sheet.startswith(filename + ":"):
        return sheet[len(filename) + 1:]
    # Also try just the base name without extension
    stem = Path(filename).name if filename else ""
    if stem and sheet.startswith(stem + ":"):
        return sheet[len(stem) + 1:]
    return sheet


def _format_location(sheet: str, row: Any, col: Any) -> str:
    """Format location string for a report line."""
    parts = []
    if sheet:
        parts.append(f"`{sheet}`")
    if row:
        parts.append(f"vr. {row}")
    if col:
        parts.append(f"stl. {col}")
    if parts:
        return "(" + ", ".join(parts) + ") "
    return ""
