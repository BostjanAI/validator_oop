"""FastAPI aplikacija za MES Excel Validator (spletna plast).

Endpointi:
- ``GET  /api/health``                              – zdravstveni pregled
- ``GET  /api/rules``                               – katalog pravil + kod
- ``POST /api/validate``                            – naloži recepture + konfiguracijo → job_id
- ``GET  /api/jobs/{id}``                           – stanje/napredek joba
- ``GET  /api/jobs/{id}/results``                   – rezultati validacije
- ``GET  /api/jobs/{id}/files/{idx}/report/{name}`` – prenos generiranega poročila
- ``GET  /api/jobs/{id}/report/{name}``             – prenos skupnega (batch) poročila

Frontend (React brez build koraka) se postreže iz ``../frontend``.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .jobs import JobManager
from .rules_catalog import get_rules_catalog
from .schemas import JobResults, JobStatus, RulesCatalog, ValidationConfigIn
from .settings import Settings, get_settings

logger = logging.getLogger("mes_web")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Dovoljene končnice po vrsti naložene datoteke (varnostna zahteva – intranet)
RECIPE_EXTENSIONS = {".xlsx", ".xlsm"}
SOP_EXTENSIONS = {".docx"}
CATALOG_EXTENSIONS = {".xlsx", ".xlsm"}


def create_app(settings: Settings | None = None) -> FastAPI:
    """Tovarna FastAPI aplikacije."""
    settings = settings or get_settings()
    settings.ensure_dirs()

    app = FastAPI(
        title="MES Excel Validator – Web",
        description="Spletna plast nad obstoječim ValidatorEngine za validacijo IPO receptur.",
        version=get_rules_catalog().version,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    job_manager = JobManager(max_workers=settings.max_workers, jobs_dir=settings.jobs_dir)
    app.state.job_manager = job_manager
    app.state.settings = settings

    _start_cleanup_thread(job_manager, settings)
    _register_routes(app, job_manager, settings)
    _mount_frontend(app, settings)
    return app


def _register_routes(app: FastAPI, job_manager: JobManager, settings: Settings) -> None:
    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/rules", response_model=RulesCatalog)
    def rules() -> RulesCatalog:
        return get_rules_catalog()

    @app.post("/api/validate")
    async def validate(
        recipes: list[UploadFile] = File(..., description="Ena ali več Excel receptur (.xlsx/.xlsm)"),
        config: str | None = Form(None, description="JSON konfiguracija validacije"),
        sop: UploadFile | None = File(None, description="Opcijski SOP .docx"),
        catalog_raztopine: UploadFile | None = File(None, description="Opcijski šifrant raztopin (.xlsx)"),
        catalog_kemikalije: UploadFile | None = File(None, description="Opcijski šifrant kemikalij (.xlsx)"),
    ) -> JSONResponse:
        if not recipes:
            raise HTTPException(status_code=400, detail="Naloži vsaj eno recepturo.")

        try:
            cfg = (
                ValidationConfigIn.model_validate_json(config)
                if config
                else ValidationConfigIn()
            )
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Neveljavna konfiguracija: {exc}") from exc

        for up in recipes:
            _check_extension(up, RECIPE_EXTENSIONS, "receptura")
        if sop:
            _check_extension(sop, SOP_EXTENSIONS, "SOP dokument")
        if catalog_raztopine:
            _check_extension(catalog_raztopine, CATALOG_EXTENSIONS, "šifrant raztopin")
        if catalog_kemikalije:
            _check_extension(catalog_kemikalije, CATALOG_EXTENSIONS, "šifrant kemikalij")

        recipe_payloads = await _read_uploads(recipes, settings.max_upload_bytes)
        sop_payload = (await _read_single(sop, settings.max_upload_bytes)) if sop else None
        razt_payload = (
            await _read_single(catalog_raztopine, settings.max_upload_bytes)
            if catalog_raztopine
            else None
        )
        kem_payload = (
            await _read_single(catalog_kemikalije, settings.max_upload_bytes)
            if catalog_kemikalije
            else None
        )

        job_id = job_manager.create_job(
            config=cfg,
            recipe_files=recipe_payloads,
            sop_file=sop_payload,
            catalog_raztopine=razt_payload,
            catalog_kemikalije=kem_payload,
        )
        return JSONResponse({"job_id": job_id}, status_code=202)

    @app.get("/api/jobs/{job_id}", response_model=JobStatus)
    def job_status(job_id: str) -> JobStatus:
        status = job_manager.status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Job ne obstaja.")
        return status

    @app.get("/api/jobs/{job_id}/results", response_model=JobResults)
    def job_results(job_id: str) -> JobResults:
        results = job_manager.results(job_id)
        if results is None:
            raise HTTPException(status_code=404, detail="Job ne obstaja.")
        return results

    @app.get("/api/jobs/{job_id}/files/{file_index}/report/{filename}")
    def download_report(job_id: str, file_index: int, filename: str) -> FileResponse:
        path = job_manager.report_path(job_id, file_index, filename)
        if path is None:
            raise HTTPException(status_code=404, detail="Poročilo ne obstaja.")
        return FileResponse(path, filename=path.name)

    @app.get("/api/jobs/{job_id}/report/{filename}")
    def download_combined_report(job_id: str, filename: str) -> FileResponse:
        path = job_manager.combined_report_path(job_id, filename)
        if path is None:
            raise HTTPException(status_code=404, detail="Poročilo ne obstaja.")
        return FileResponse(path, filename=path.name)


def _mount_frontend(app: FastAPI, settings: Settings) -> None:
    if not settings.serve_frontend:
        return
    static_dir = FRONTEND_DIR / "static"
    index_file = FRONTEND_DIR / "index.html"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    if index_file.is_file():
        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(index_file)


def _check_extension(up: UploadFile, allowed: set[str], kind: str) -> None:
    """Zavrne datoteko z napačno končnico (413/415 zaščita pred poljubnimi tipi)."""
    ext = Path(up.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Datoteka '{up.filename}' ni veljaven tip za {kind}. "
                f"Dovoljene končnice: {', '.join(sorted(allowed))}."
            ),
        )


async def _read_uploads(uploads: list[UploadFile], max_bytes: int) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    for up in uploads:
        out.append(await _read_single(up, max_bytes))
    return out


async def _read_single(up: UploadFile, max_bytes: int) -> tuple[str, bytes]:
    data = await up.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Datoteka '{up.filename}' presega največjo dovoljeno velikost.",
        )
    return up.filename or "datoteka", data


def _start_cleanup_thread(job_manager: JobManager, settings: Settings) -> None:
    ttl_seconds = max(60, settings.job_ttl_minutes * 60)

    def _loop() -> None:
        while True:
            time.sleep(300)
            try:
                removed = job_manager.cleanup_expired(ttl_seconds)
                if removed:
                    logger.info("Počiščenih %d poteklih jobov.", removed)
            except Exception:  # pragma: no cover
                logger.debug("Čiščenje jobov ni uspelo", exc_info=True)

    thread = threading.Thread(target=_loop, name="mes-web-cleanup", daemon=True)
    thread.start()


app = create_app()
