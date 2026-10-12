"""Upravljanje validacijskih jobov v ozadju.

Validacija lahko traja nekaj sekund na datoteko, zato se izvaja v ločeni
niti (ThreadPoolExecutor), brskalnik pa polla napredek. Stanje jobov je
v pomnilniku (za en proces). Za večprocesni deployment bi to zamenjal
deljen store (npr. Redis) – za interno orodje zadošča.
"""

from __future__ import annotations

import logging
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .schemas import (
    FileResult,
    FileStatus,
    JobResults,
    JobStatus,
    ReportRef,
    ValidationConfigIn,
)
from .service import ValidationService, load_catalog_data, load_sop

logger = logging.getLogger("mes_web.jobs")


@dataclass
class JobFile:
    index: int
    filename: str
    path: Path
    state: str = "queued"
    error: str | None = None
    result: FileResult | None = None
    # MES/MySQL vir: id recepture v bazi (path je takrat samo placeholder)
    recipe_id: int | None = None


@dataclass
class Job:
    job_id: str
    output_dir: Path
    config: ValidationConfigIn
    files: list[JobFile]
    sop_path: Path | None = None
    catalog_raztopine_path: Path | None = None
    catalog_kemikalije_path: Path | None = None
    catalog_repro_path: Path | None = None
    state: str = "queued"
    message: str = ""
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    combined_reports: list[ReportRef] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    # Faza 2: lastnik joba (prijavljen uporabnik) za zgodovino in dostop
    owner: str = ""
    # MES/MySQL vir: shrani rezultate v validation_runs/validation_findings
    save_results: bool = False

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def processed_files(self) -> int:
        return sum(1 for f in self.files if f.state in {"done", "error"})


class JobManager:
    """Sprejema jobe, jih izvaja v ozadju in hrani rezultate."""

    def __init__(
        self,
        *,
        max_workers: int = 2,
        jobs_dir: Path,
        on_complete: Callable[[Job], None] | None = None,
    ) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="mes-val")
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._jobs_dir = jobs_dir
        self._service = ValidationService()
        # Faza 2: hook ob zaključku joba (npr. trajna zgodovina + audit)
        self._on_complete = on_complete

    def create_job(
        self,
        *,
        config: ValidationConfigIn,
        recipe_files: list[tuple[str, bytes]],
        sop_file: tuple[str, bytes] | None = None,
        catalog_raztopine: tuple[str, bytes] | None = None,
        catalog_kemikalije: tuple[str, bytes] | None = None,
        catalog_repro: tuple[str, bytes] | None = None,
        owner: str = "",
    ) -> str:
        """Ustvari job, shrani naložene datoteke in ga uvrsti v izvajanje."""
        job_id = uuid.uuid4().hex
        output_dir = self._jobs_dir / job_id
        input_dir = output_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        job_files: list[JobFile] = []
        for i, (name, data) in enumerate(recipe_files):
            safe_name = _safe_filename(name) or f"datoteka_{i}.xlsx"
            dest = input_dir / safe_name
            dest = _dedupe_path(dest)
            dest.write_bytes(data)
            job_files.append(JobFile(index=i, filename=dest.name, path=dest))

        sop_path = self._save_optional(input_dir, sop_file)
        razt_path = self._save_optional(input_dir, catalog_raztopine)
        kem_path = self._save_optional(input_dir, catalog_kemikalije)
        repro_path = self._save_optional(input_dir, catalog_repro)

        job = Job(
            job_id=job_id,
            output_dir=output_dir,
            config=config,
            files=job_files,
            sop_path=sop_path,
            catalog_raztopine_path=razt_path,
            catalog_kemikalije_path=kem_path,
            catalog_repro_path=repro_path,
            owner=owner,
        )
        with self._lock:
            self._jobs[job_id] = job

        self._executor.submit(self._run_job, job_id)
        return job_id

    def create_db_job(
        self,
        *,
        config: ValidationConfigIn,
        recipe_id: int,
        save_results: bool = False,
        owner: str = "",
    ) -> str:
        """Ustvari job z virom iz MES MySQL baze (namesto naloženih datotek).

        Validacija in poročila tečejo skozi isto job infrastrukturo kot pri
        uploadu – zamenjan je samo korak nalaganja (MySQLLoader).
        """
        job_id = uuid.uuid4().hex
        output_dir = self._jobs_dir / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        job_files = [
            JobFile(
                index=0,
                filename=f"MES_receptura_{recipe_id}",
                path=output_dir / "input" / "db",  # placeholder, datoteke ni
                recipe_id=int(recipe_id),
            )
        ]
        job = Job(
            job_id=job_id,
            output_dir=output_dir,
            config=config,
            files=job_files,
            owner=owner,
            save_results=save_results,
        )
        with self._lock:
            self._jobs[job_id] = job

        self._executor.submit(self._run_job, job_id)
        return job_id

    @staticmethod
    def _save_optional(input_dir: Path, item: tuple[str, bytes] | None) -> Path | None:
        if not item:
            return None
        name, data = item
        dest = _dedupe_path(input_dir / (_safe_filename(name) or "datoteka"))
        dest.write_bytes(data)
        return dest

    def _run_job(self, job_id: str) -> None:
        job = self.get_job(job_id)
        if job is None:
            return
        with job.lock:
            job.state = "running"
            job.message = "Nalaganje SOP in šifrantov…"

        try:
            sop_data = load_sop(job.sop_path) if job.config.enable_sop_validation else None
            catalog_data, catalog_paths = (None, {})
            if job.config.enable_catalog_validation:
                catalog_data, catalog_paths = load_catalog_data(
                    job.catalog_raztopine_path,
                    job.catalog_kemikalije_path,
                    job.catalog_repro_path,
                )
        except Exception as exc:  # pragma: no cover - defenzivno
            logger.exception("Priprava virov ni uspela: %s", exc)
            sop_data, catalog_data, catalog_paths = None, None, {}

        reports_dir = job.output_dir / "reports"
        for job_file in job.files:
            with job.lock:
                job_file.state = "running"
                job.message = f"Validacija: {job_file.filename}"
            try:
                if job_file.recipe_id is not None:
                    result = self._service.validate_db_recipe(
                        index=job_file.index,
                        recipe_id=job_file.recipe_id,
                        config=job.config,
                        output_dir=reports_dir / f"{job_file.index}",
                        save_results=job.save_results,
                    )
                else:
                    result = self._service.validate_file(
                        index=job_file.index,
                        recipe_path=job_file.path,
                        config=job.config,
                        output_dir=reports_dir / f"{job_file.index}",
                        sop_data=sop_data,
                        catalog_data=catalog_data,
                        catalog_paths=catalog_paths,
                    )
                with job.lock:
                    job_file.result = result
                    job_file.state = "done"
            except Exception as exc:
                logger.exception("Validacija ni uspela za %s: %s", job_file.filename, exc)
                with job.lock:
                    job_file.state = "error"
                    job_file.error = str(exc)

        # Skupno poročilo za batch (samo pri več uspešno validiranih datotekah)
        ok_results = [f.result for f in job.files if f.result is not None]
        if len(ok_results) > 1:
            with job.lock:
                job.message = "Generiranje skupnega poročila…"
            try:
                combined = self._service.write_combined_reports(
                    reports_dir / "combined", ok_results
                )
            except Exception as exc:
                logger.warning("Skupno poročilo ni uspelo: %s", exc)
                combined = []
            with job.lock:
                job.combined_reports = combined

        with job.lock:
            job.state = "done"
            job.message = "Zaključeno."
            job.finished_at = time.time()

        # Faza 2: hook za trajno zgodovino / audit (izven job locka)
        if self._on_complete is not None:
            try:
                self._on_complete(job)
            except Exception:  # pragma: no cover - defenzivno
                logger.exception("on_complete hook za job %s ni uspel.", job_id)

    def get_job(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def status(self, job_id: str) -> JobStatus | None:
        job = self.get_job(job_id)
        if job is None:
            return None
        with job.lock:
            total = job.total_files
            processed = job.processed_files
            progress = (processed / total) if total else 0.0
            return JobStatus(
                job_id=job.job_id,
                state=job.state,  # type: ignore[arg-type]
                progress=round(progress, 4),
                message=job.message,
                created_at=job.created_at,
                total_files=total,
                processed_files=processed,
                files=[
                    FileStatus(
                        index=f.index, filename=f.filename, state=f.state, error=f.error  # type: ignore[arg-type]
                    )
                    for f in job.files
                ],
                error=job.error,
            )

    def results(self, job_id: str) -> JobResults | None:
        job = self.get_job(job_id)
        if job is None:
            return None
        with job.lock:
            file_results: list[FileResult] = []
            totals = {"error": 0, "warning": 0, "info": 0, "files": job.total_files, "invalid_files": 0}
            for f in job.files:
                if f.result is not None:
                    file_results.append(f.result)
                    for sev in ("error", "warning", "info"):
                        totals[sev] += f.result.counts.get(sev, 0)
                    if not f.result.is_valid:
                        totals["invalid_files"] += 1
                else:
                    file_results.append(
                        FileResult(
                            index=f.index,
                            filename=f.filename,
                            is_valid=False,
                            counts={},
                            counts_by_code={},
                            counts_by_sheet={},
                            issues=[],
                            reports=[],
                            error=f.error or ("V obdelavi…" if f.state != "error" else "Napaka"),
                        )
                    )
            return JobResults(
                job_id=job.job_id,
                state=job.state,
                totals=totals,
                files=file_results,
                combined_reports=list(job.combined_reports),
            )

    def report_path(self, job_id: str, file_index: int, filename: str) -> Path | None:
        """Varno razreši pot do generiranega poročila znotraj job mape."""
        return self._resolve_report(job_id, str(file_index), filename)

    def combined_report_path(self, job_id: str, filename: str) -> Path | None:
        """Varno razreši pot do skupnega poročila (batch) znotraj job mape."""
        return self._resolve_report(job_id, "combined", filename)

    def _resolve_report(self, job_id: str, subdir: str, filename: str) -> Path | None:
        job = self.get_job(job_id)
        if job is None:
            return None
        base = (job.output_dir / "reports" / subdir).resolve()
        candidate = (base / filename).resolve()
        if not str(candidate).startswith(str(base)):
            return None
        if not candidate.is_file():
            return None
        return candidate

    def cleanup_expired(self, ttl_seconds: int) -> int:
        """Odstrani jobe starejše od TTL (in njihove datoteke)."""
        now = time.time()
        removed = 0
        with self._lock:
            expired = [
                jid
                for jid, job in self._jobs.items()
                if job.state in {"done", "error"}
                and (now - (job.finished_at or job.created_at)) > ttl_seconds
            ]
            for jid in expired:
                job = self._jobs.pop(jid, None)
                if job is not None:
                    shutil.rmtree(job.output_dir, ignore_errors=True)
                    removed += 1
        return removed

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


def _safe_filename(name: str) -> str:
    """Vrne varno ime datoteke (brez poti / nevarnih znakov)."""
    base = Path(name).name
    cleaned = "".join(c for c in base if c.isalnum() or c in " .,-_()[]+#&čšžČŠŽ").strip()
    return cleaned


def _dedupe_path(path: Path) -> Path:
    """Če pot obstaja, doda številčni sufiks."""
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1
