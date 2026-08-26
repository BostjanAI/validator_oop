"""Trajna zgodovina validacij (faza 2).

Ob zaključku joba se rezultati in datoteke trajno shranijo (neodvisno od
TTL čiščenja začasnih jobov):
- metapodatki + povzetek → SQLite (``validation_history``),
- celotni rezultati (issues, poročila) → ``history/{job_id}/results.json``,
- generirana poročila → ``history/{job_id}/reports/…``,
- vhodne datoteke → ``history/{job_id}/input/…`` (za kasnejši diff verzij).
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .db import Database

logger = logging.getLogger("mes_web.history")


class HistoryStore:
    """Shranjevanje in branje trajne zgodovine validacij."""

    def __init__(self, db: Database, history_dir: Path) -> None:
        self._db = db
        self._dir = history_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------- write

    def persist_job(
        self,
        *,
        job_id: str,
        username: str,
        created_at: float,
        finished_at: float | None,
        state: str,
        config: dict[str, Any],
        results: dict[str, Any],
        job_dir: Path,
    ) -> None:
        """Trajno shrani zaključen job (metapodatki + datoteke).

        Args:
            job_id: ID joba (postane tudi ID vnosa zgodovine).
            username: Lastnik validacije.
            created_at/finished_at: Unix časa začetka/konca.
            state: Končno stanje ("done"/"error").
            config: Uporabljena konfiguracija (JSON-serializabilna).
            results: Rezultati v obliki ``JobResults`` (dict).
            job_dir: Delovna mapa joba (input/ + reports/).
        """
        target = self._dir / job_id
        try:
            target.mkdir(parents=True, exist_ok=True)

            for sub in ("input", "reports"):
                src = job_dir / sub
                if src.is_dir():
                    shutil.copytree(src, target / sub, dirs_exist_ok=True)

            (target / "results.json").write_text(
                json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Shranjevanje zgodovine za job %s ni uspelo: %s", job_id, exc)

        totals = results.get("totals", {})
        files_summary = [
            {
                "index": f.get("index"),
                "filename": f.get("filename"),
                "is_valid": f.get("is_valid"),
                "counts": f.get("counts", {}),
                "reports": f.get("reports", []),
                "error": f.get("error"),
            }
            for f in results.get("files", [])
        ]

        self._db.add_history(
            job_id=job_id,
            username=username,
            created_at=created_at,
            finished_at=finished_at,
            state=state,
            total_files=int(totals.get("files", 0)),
            invalid_files=int(totals.get("invalid_files", 0)),
            errors=int(totals.get("error", 0)),
            warnings=int(totals.get("warning", 0)),
            infos=int(totals.get("info", 0)),
            files=files_summary,
            combined_reports=results.get("combined_reports", []),
            config=config,
        )
        logger.info("Job %s shranjen v trajno zgodovino.", job_id)

    # ------------------------------------------------------------------ read

    def list(
        self, *, limit: int = 50, offset: int = 0, username: str | None = None
    ) -> tuple[list[dict[str, Any]], int]:
        return self._db.list_history(limit=limit, offset=offset, username=username)

    def get(self, job_id: str) -> dict[str, Any] | None:
        return self._db.get_history(job_id)

    def get_results(self, job_id: str) -> dict[str, Any] | None:
        """Vrne celotne rezultate (results.json) vnosa zgodovine."""
        path = self._dir / job_id / "results.json"
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Branje rezultatov zgodovine %s ni uspelo: %s", job_id, exc)
            return None

    def report_path(self, job_id: str, subdir: str, filename: str) -> Path | None:
        """Varno razreši pot do poročila v zgodovini (brez path traversal)."""
        base = (self._dir / job_id / "reports" / subdir).resolve()
        candidate = (base / filename).resolve()
        if not str(candidate).startswith(str(base)):
            return None
        return candidate if candidate.is_file() else None

    def input_path(self, job_id: str, filename: str) -> Path | None:
        """Varno razreši pot do vhodne datoteke v zgodovini (za diff)."""
        base = (self._dir / job_id / "input").resolve()
        candidate = (base / filename).resolve()
        if not str(candidate).startswith(str(base)):
            return None
        return candidate if candidate.is_file() else None

    # --------------------------------------------------------------- cleanup

    def cleanup_older_than(self, days: int) -> int:
        """Izbriše vnose zgodovine, starejše od N dni (0 = brez brisanja)."""
        if days <= 0:
            return 0
        cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
        removed_ids = self._db.delete_history_older_than(cutoff)
        for job_id in removed_ids:
            shutil.rmtree(self._dir / job_id, ignore_errors=True)
        if removed_ids:
            logger.info("Počiščenih %d starih vnosov zgodovine.", len(removed_ids))
        return len(removed_ids)
