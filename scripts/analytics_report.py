"""Avtomatsko analitično poročilo (trendi, časovne serije) iz validacij.

Ta skripta združi:
- `validation_progress.json` (čas validacije + total napak/opozoril)
- Excel poročila (ReportWriter) z listom "Število napak" (Koda/Število)

Rezultat so CSV datoteke za nadaljnjo analitiko (Excel/PowerBI/Python) in
opcijsko osnovni grafi (PNG), če je nameščen matplotlib.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from openpyxl import load_workbook

try:
    # Normal case: package installed / executed as `python -m validator_oop...`
    from validator_oop.utils.validation_progress import get_progress_path, load_progress
except ModuleNotFoundError:
    # Dev convenience: allow running from repo root as `python -m scripts.analytics_report`
    _pkg_dir = Path(__file__).resolve().parent.parent  # .../validator_oop
    _parent = _pkg_dir.parent
    if str(_parent) not in sys.path:
        sys.path.insert(0, str(_parent))
    from validator_oop.utils.validation_progress import get_progress_path, load_progress  # type: ignore


SHEET_COUNTS = "Število napak"
SHEET_SUMMARY = "Povzetek"


@dataclass(frozen=True, slots=True)
class RunRecord:
    run_no: int
    when: datetime
    workbook_path: Path
    errors: int
    warnings: int
    valid: bool


def _parse_iso_dt(value: str) -> datetime:
    # datetime.fromisoformat supports "+00:00" but not "Z" in older versions
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iter_report_files(reports_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in reports_dir.rglob("*.xlsx"):
        # Skip Excel lock/temp files
        if p.name.startswith("~$"):
            continue
        files.append(p)
    return files


def _score_candidate(
    *,
    candidate: Path,
    workbook_stem: str,
    run_time: datetime,
) -> float:
    """Lower score is better."""
    stem = candidate.stem
    if stem == workbook_stem:
        base = 0.0
    elif stem.startswith(workbook_stem):
        base = 1.0
    elif workbook_stem in stem:
        base = 2.0
    else:
        base = 10.0

    try:
        mtime = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc)
        dt_sec = abs((mtime - run_time).total_seconds())
    except OSError:
        dt_sec = 365.0 * 24 * 3600

    # Prefer time proximity, but keep name match primary
    return base * 1_000_000.0 + dt_sec


def _pick_report_for_run(
    run: RunRecord,
    *,
    reports_index: list[Path],
) -> Path | None:
    workbook_stem = run.workbook_path.stem

    candidates = [
        p
        for p in reports_index
        if (p.stem == workbook_stem or p.stem.startswith(workbook_stem) or workbook_stem in p.stem)
    ]
    if not candidates:
        return None

    return min(
        candidates,
        key=lambda p: _score_candidate(candidate=p, workbook_stem=workbook_stem, run_time=run.when),
    )


def _read_counts_by_code(report_xlsx: Path) -> dict[str, int]:
    wb = load_workbook(report_xlsx, read_only=True, data_only=True)
    try:
        if SHEET_COUNTS not in wb.sheetnames:
            raise KeyError(
                f"V poročilu manjka list '{SHEET_COUNTS}'. Najdeno: {', '.join(wb.sheetnames)}"
            )
        ws = wb[SHEET_COUNTS]

        # Expect headers in first row: Koda | Opis | Število
        counts: dict[str, int] = {}
        first = True
        for row in ws.iter_rows(values_only=True):
            if first:
                first = False
                continue
            if not row:
                continue
            code = (row[0] or "").strip() if isinstance(row[0], str) else (row[0] or "")
            if not code:
                continue
            raw_n = row[2] if len(row) >= 3 else None
            try:
                n = int(raw_n) if raw_n is not None and raw_n != "" else 0
            except (TypeError, ValueError):
                n = 0
            counts[str(code)] = counts.get(str(code), 0) + n
        return counts
    finally:
        try:
            wb.close()
        except Exception:
            pass


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, headers: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _ascii_safe(text: object) -> str:
    """Return ASCII-safe text for Windows consoles."""
    s = str(text)
    return s.encode("ascii", "backslashreplace").decode("ascii")


def _maybe_plot(out_dir: Path, daily_rows: list[dict[str, Any]], top_codes: list[str]) -> list[Path]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return []

    # Prepare series
    days = [r["day"] for r in daily_rows]
    errors = [r["errors_sum"] for r in daily_rows]
    warnings = [r["warnings_sum"] for r in daily_rows]

    plots: list[Path] = []

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(days, errors, label="Napake (sum)", linewidth=2)
    ax.plot(days, warnings, label="Opozorila (sum)", linewidth=2)
    ax.set_title("Napake in opozorila skozi čas (dnevno)")
    ax.set_xlabel("Dan")
    ax.set_ylabel("Število")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.autofmt_xdate(rotation=30, ha="right")
    p1 = out_dir / "trend_errors_warnings.png"
    fig.tight_layout()
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    plots.append(p1)

    if top_codes:
        fig, ax = plt.subplots(figsize=(10, 4))
        for code in top_codes:
            series = [r.get(f"code__{code}", 0) for r in daily_rows]
            ax.plot(days, series, label=code, linewidth=2)
        ax.set_title("Top kode napak skozi čas (dnevno)")
        ax.set_xlabel("Dan")
        ax.set_ylabel("Število")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.autofmt_xdate(rotation=30, ha="right")
        p2 = out_dir / "trend_top_codes.png"
        fig.tight_layout()
        fig.savefig(p2, dpi=150)
        plt.close(fig)
        plots.append(p2)

    return plots


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Ustvari avtomatsko analiticno porocilo iz validation_progress.json + Excel reportov."
    )
    ap.add_argument(
        "--progress",
        type=Path,
        default=None,
        help="Pot do validation_progress.json (privzeto: projektna mapa).",
    )
    ap.add_argument(
        "--reports-dir",
        type=Path,
        required=True,
        help="Mapa, kjer so shranjena Excel porocila (rekurzivno).",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Izhodna mapa za CSV/porocilo (privzeto: ./analytics_out).",
    )
    ap.add_argument(
        "--top-n",
        type=int,
        default=8,
        help="Koliko top kod prikazati v dnevnih trendih (privzeto: 8).",
    )
    args = ap.parse_args(argv)

    progress_path = args.progress or get_progress_path()
    reports_dir = args.reports_dir.expanduser().resolve()
    out_dir = (args.out_dir or (Path(__file__).resolve().parent.parent / "analytics_out")).resolve()
    _ensure_dir(out_dir)

    data = load_progress(progress_path)
    runs_raw = data.get("runs", [])
    runs: list[RunRecord] = []
    for r in runs_raw:
        try:
            run_no = int(r.get("zaporedna_stevilka") or 0)
            when = _parse_iso_dt(str(r.get("date") or ""))
            workbook_path = Path(str(r.get("path") or "")).expanduser()
            errors = int(r.get("errors") or 0)
            warnings = int(r.get("warnings") or 0)
            valid = bool(r.get("valid")) if "valid" in r else (errors == 0)
            if run_no <= 0 or not str(workbook_path):
                continue
            runs.append(
                RunRecord(
                    run_no=run_no,
                    when=when,
                    workbook_path=workbook_path,
                    errors=errors,
                    warnings=warnings,
                    valid=valid,
                )
            )
        except Exception:
            continue

    reports_index = _iter_report_files(reports_dir)

    # Build per-run rows + long format codes
    run_rows: list[dict[str, Any]] = []
    code_rows: list[dict[str, Any]] = []
    missing_reports: list[RunRecord] = []
    all_code_counts = Counter()

    for run in runs:
        report_path = _pick_report_for_run(run, reports_index=reports_index)
        if report_path is None:
            missing_reports.append(run)
            run_rows.append(
                {
                    "run_no": run.run_no,
                    "date_utc": run.when.isoformat(),
                    "workbook_path": str(run.workbook_path),
                    "report_path": "",
                    "errors": run.errors,
                    "warnings": run.warnings,
                    "valid": run.valid,
                    "codes_total": 0,
                }
            )
            continue

        try:
            counts_by_code = _read_counts_by_code(report_path)
        except Exception:
            counts_by_code = {}

        codes_total = sum(counts_by_code.values())
        run_rows.append(
            {
                "run_no": run.run_no,
                "date_utc": run.when.isoformat(),
                "workbook_path": str(run.workbook_path),
                "report_path": str(report_path),
                "errors": run.errors,
                "warnings": run.warnings,
                "valid": run.valid,
                "codes_total": codes_total,
            }
        )

        for code, n in counts_by_code.items():
            all_code_counts[code] += n
            code_rows.append(
                {
                    "run_no": run.run_no,
                    "date_utc": run.when.isoformat(),
                    "day": run.when.date().isoformat(),
                    "workbook_path": str(run.workbook_path),
                    "report_path": str(report_path),
                    "code": code,
                    "count": n,
                }
            )

    # Daily aggregation
    daily = defaultdict(lambda: {"runs_count": 0, "errors_sum": 0, "warnings_sum": 0, "invalid_count": 0})
    daily_codes = defaultdict(lambda: Counter())
    for rr in run_rows:
        day = _parse_iso_dt(rr["date_utc"]).date().isoformat()
        d = daily[day]
        d["runs_count"] += 1
        d["errors_sum"] += int(rr["errors"] or 0)
        d["warnings_sum"] += int(rr["warnings"] or 0)
        d["invalid_count"] += 0 if rr["valid"] else 1
    for cr in code_rows:
        daily_codes[cr["day"]][cr["code"]] += int(cr["count"] or 0)

    # Pick top codes by total count (global)
    top_codes = [c for c, _ in all_code_counts.most_common(max(0, int(args.top_n)))]

    daily_rows: list[dict[str, Any]] = []
    for day in sorted(daily.keys()):
        base = dict(daily[day])
        base["day"] = day
        runs_count = base["runs_count"]
        base["invalid_rate"] = round((base["invalid_count"] / runs_count), 4) if runs_count else 0.0
        for code in top_codes:
            base[f"code__{code}"] = daily_codes[day].get(code, 0)
            base[f"rate__{code}"] = (
                round(base[f"code__{code}"] / runs_count, 4) if runs_count else 0.0
            )
        daily_rows.append(base)

    # Write outputs
    _write_csv(
        out_dir / "runs.csv",
        ["run_no", "date_utc", "workbook_path", "report_path", "errors", "warnings", "valid", "codes_total"],
        run_rows,
    )
    _write_csv(
        out_dir / "codes_long.csv",
        ["run_no", "date_utc", "day", "workbook_path", "report_path", "code", "count"],
        code_rows,
    )
    daily_headers = ["day", "runs_count", "errors_sum", "warnings_sum", "invalid_count", "invalid_rate"] + [
        h for code in top_codes for h in (f"code__{code}", f"rate__{code}")
    ]
    _write_csv(out_dir / "daily_timeseries.csv", daily_headers, daily_rows)

    plots = _maybe_plot(out_dir, daily_rows, top_codes)

    # Minimal human-readable summary
    summary = {
        "progress_path": str(progress_path),
        "reports_dir": str(reports_dir),
        "out_dir": str(out_dir),
        "total_runs": len(runs),
        "runs_with_report": sum(1 for r in run_rows if r.get("report_path")),
        "runs_missing_report": len(missing_reports),
        "top_codes": top_codes,
        "generated_files": [
            str(out_dir / "runs.csv"),
            str(out_dir / "codes_long.csv"),
            str(out_dir / "daily_timeseries.csv"),
        ]
        + [str(p) for p in plots],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # ASCII-safe output for Windows consoles (avoid UnicodeEncodeError)
    print("Koncano.")
    print(f"- progress: {_ascii_safe(progress_path)}")
    print(f"- reporti:  {_ascii_safe(reports_dir)}")
    print(f"- izhod:    {_ascii_safe(out_dir)}")
    print(f"- runs:     {summary['total_runs']} (ujemanje reportov: {summary['runs_with_report']}, manjkajo: {summary['runs_missing_report']})")
    if top_codes:
        print(f"- top kode: {', '.join(top_codes)}")
    print("- datoteke:")
    for p in summary["generated_files"]:
        print(f"  - {_ascii_safe(p)}")

    # Exit code: 0 if at least one report matched, else 1
    return 0 if summary["runs_with_report"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

