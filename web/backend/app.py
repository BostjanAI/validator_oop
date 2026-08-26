"""FastAPI aplikacija za MES Excel Validator (spletna plast).

Endpointi (MVP):
- ``GET  /api/health``                              – zdravstveni pregled
- ``GET  /api/rules``                               – katalog pravil + kod
- ``POST /api/validate``                            – naloži recepture + konfiguracijo → job_id
- ``GET  /api/jobs/{id}``                           – stanje/napredek joba
- ``GET  /api/jobs/{id}/results``                   – rezultati validacije
- ``GET  /api/jobs/{id}/files/{idx}/report/{name}`` – prenos generiranega poročila
- ``GET  /api/jobs/{id}/report/{name}``             – prenos skupnega (batch) poročila

Endpointi (faza 2):
- ``POST /api/auth/login`` / ``POST /api/auth/logout`` / ``GET /api/auth/me``
- ``GET  /api/history`` (+ ``/{id}``, prenosi poročil iz zgodovine)
- ``GET  /api/audit``                               – revizijska sled (QA/admin)
- ``POST /api/section-compare``                     – primerjava razdelkov med listi
- ``POST /api/diff``                                – diff dveh verzij recepture
- ``WS   /api/ws/jobs/{id}``                        – napredek v realnem času

Frontend (React brez build koraka) se postreže iz ``../frontend``.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import threading
import time
import uuid
from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .auth import ANONYMOUS_USER, SESSION_COOKIE, AuthManager, User
from .db import Database
from .history import HistoryStore
from .jobs import Job, JobManager
from .rules_catalog import get_rules_catalog
from .schemas import (
    AuditList,
    AuthStatus,
    DBHealthOut,
    DBRecipeList,
    DBRecipeMeta,
    DBValidateIn,
    DiffOut,
    HistoryDetail,
    HistoryList,
    HistoryRecord,
    JobResults,
    JobStatus,
    LoginIn,
    RulesCatalog,
    SectionCompareOut,
    UserOut,
    ValidationConfigIn,
)
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
        title="IPO Excel Validator – Web",
        description="Spletna plast nad obstoječim ValidatorEngine za validacijo IPO receptur.",
        version=get_rules_catalog().version,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )

    db = Database(settings.db_path)
    auth_manager = AuthManager(settings, db)
    history_store = HistoryStore(db, settings.history_dir)

    def _on_job_complete(job: Job) -> None:
        """Ob zaključku joba trajno shrani rezultate in zabeleži audit vnos."""
        results = job_manager.results(job.job_id)
        if results is None:
            return
        history_store.persist_job(
            job_id=job.job_id,
            username=job.owner,
            created_at=job.created_at,
            finished_at=job.finished_at,
            state=job.state,
            config=job.config.model_dump(),
            results=results.model_dump(),
            job_dir=job.output_dir,
        )
        totals = results.totals
        db.add_audit(
            username=job.owner or ANONYMOUS_USER.username,
            role="",
            ip="",
            action="validacija_zakljucena",
            detail=(
                f"job={job.job_id}, datotek={totals.get('files', 0)}, "
                f"napak={totals.get('error', 0)}, opozoril={totals.get('warning', 0)}"
            ),
        )

    job_manager = JobManager(
        max_workers=settings.max_workers,
        jobs_dir=settings.jobs_dir,
        on_complete=_on_job_complete,
    )
    app.state.job_manager = job_manager
    app.state.settings = settings
    app.state.db = db
    app.state.auth_manager = auth_manager
    app.state.history_store = history_store

    _start_cleanup_thread(job_manager, history_store, db, settings)
    _register_routes(app, job_manager, settings, db, auth_manager, history_store)
    _mount_frontend(app, settings)
    return app


# ============================================================================
# Avtentikacija / avtorizacija (pomožne funkcije)
# ============================================================================


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _token_from_request(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        return token
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def _make_current_user(auth_manager: AuthManager):
    """Ustvari FastAPI dependency, ki vrne prijavljenega uporabnika (ali 401)."""

    def current_user(request: Request) -> User:
        if not auth_manager.enabled:
            return ANONYMOUS_USER
        user = auth_manager.user_from_token(_token_from_request(request))
        if user is None:
            raise HTTPException(status_code=401, detail="Prijava je obvezna.")
        return user

    return current_user


def _require_role(user: User, minimum: str) -> None:
    if not user.has_role(minimum):
        raise HTTPException(status_code=403, detail="Nimaš ustreznih pravic za to dejanje.")


def _job_accessible(user: User, job: Job) -> bool:
    """Tehnolog vidi samo svoje jobe; QA in admin vse."""
    if user.has_role("qa"):
        return True
    return not job.owner or job.owner == user.username


def _history_accessible(user: User, record: dict) -> bool:
    if user.has_role("qa"):
        return True
    owner = record.get("username") or ""
    return not owner or owner == user.username


# ============================================================================
# Poti (routes)
# ============================================================================


def _register_routes(
    app: FastAPI,
    job_manager: JobManager,
    settings: Settings,
    db: Database,
    auth_manager: AuthManager,
    history_store: HistoryStore,
) -> None:
    current_user = _make_current_user(auth_manager)

    def _audit(request: Request, user: User, action: str, detail: str = "") -> None:
        db.add_audit(
            username=user.username,
            role=user.role,
            ip=_client_ip(request),
            action=action,
            detail=detail,
        )

    # ------------------------------------------------------------- odprti API

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/rules", response_model=RulesCatalog)
    def rules() -> RulesCatalog:
        return get_rules_catalog()

    # ---------------------------------------------------------- avtentikacija

    @app.post("/api/auth/login", response_model=AuthStatus)
    def login(payload: LoginIn, request: Request, response: Response) -> AuthStatus:
        if not auth_manager.enabled:
            return AuthStatus(auth_enabled=False, user=UserOut(**ANONYMOUS_USER.to_dict()))

        result = auth_manager.login(payload.username, payload.password)
        if result is None:
            db.add_audit(
                username=payload.username.strip(),
                role="",
                ip=_client_ip(request),
                action="prijava_neuspesna",
                detail="Napačno uporabniško ime ali geslo.",
            )
            raise HTTPException(status_code=401, detail="Napačno uporabniško ime ali geslo.")

        user, token = result
        response.set_cookie(
            SESSION_COOKIE,
            token,
            httponly=True,
            samesite="lax",
            secure=settings.secure_cookies,
            max_age=max(60, settings.session_ttl_minutes * 60),
        )
        _audit(request, user, "prijava", f"vir={user.source}")
        return AuthStatus(auth_enabled=True, user=UserOut(**user.to_dict()))

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, str]:
        token = _token_from_request(request)
        if token:
            user = auth_manager.user_from_token(token)
            auth_manager.logout(token)
            if user:
                _audit(request, user, "odjava")
        response.delete_cookie(SESSION_COOKIE)
        return {"status": "ok"}

    @app.get("/api/auth/me", response_model=AuthStatus)
    def me(request: Request) -> AuthStatus:
        if not auth_manager.enabled:
            return AuthStatus(auth_enabled=False, user=UserOut(**ANONYMOUS_USER.to_dict()))
        user = auth_manager.user_from_token(_token_from_request(request))
        return AuthStatus(
            auth_enabled=True,
            user=UserOut(**user.to_dict()) if user else None,
        )

    # -------------------------------------------------------------- validacija

    @app.post("/api/validate")
    async def validate(
        request: Request,
        recipes: list[UploadFile] = File(..., description="Ena ali več Excel receptur (.xlsx/.xlsm)"),
        config: str | None = Form(None, description="JSON konfiguracija validacije"),
        sop: UploadFile | None = File(None, description="Opcijski SOP .docx"),
        catalog_raztopine: UploadFile | None = File(None, description="Opcijski šifrant raztopin (.xlsx)"),
        catalog_kemikalije: UploadFile | None = File(None, description="Opcijski šifrant kemikalij (.xlsx)"),
        user: User = Depends(current_user),
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
            owner=user.username,
        )
        _audit(
            request,
            user,
            "validacija_zagnana",
            f"job={job_id}, datoteke={', '.join(name for name, _ in recipe_payloads)}",
        )
        return JSONResponse({"job_id": job_id}, status_code=202)

    def _get_job_or_404(job_id: str, user: User) -> Job:
        job = job_manager.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job ne obstaja.")
        if not _job_accessible(user, job):
            raise HTTPException(status_code=403, detail="Nimaš dostopa do tega joba.")
        return job

    @app.get("/api/jobs/{job_id}", response_model=JobStatus)
    def job_status(job_id: str, user: User = Depends(current_user)) -> JobStatus:
        _get_job_or_404(job_id, user)
        status = job_manager.status(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Job ne obstaja.")
        return status

    @app.get("/api/jobs/{job_id}/results", response_model=JobResults)
    def job_results(job_id: str, user: User = Depends(current_user)) -> JobResults:
        _get_job_or_404(job_id, user)
        results = job_manager.results(job_id)
        if results is None:
            raise HTTPException(status_code=404, detail="Job ne obstaja.")
        return results

    @app.get("/api/jobs/{job_id}/files/{file_index}/report/{filename}")
    def download_report(
        job_id: str,
        file_index: int,
        filename: str,
        request: Request,
        user: User = Depends(current_user),
    ) -> FileResponse:
        _get_job_or_404(job_id, user)
        path = job_manager.report_path(job_id, file_index, filename)
        if path is None:
            raise HTTPException(status_code=404, detail="Poročilo ne obstaja.")
        _audit(request, user, "prenos_porocila", f"job={job_id}, datoteka={path.name}")
        return FileResponse(path, filename=path.name)

    @app.get("/api/jobs/{job_id}/report/{filename}")
    def download_combined_report(
        job_id: str,
        filename: str,
        request: Request,
        user: User = Depends(current_user),
    ) -> FileResponse:
        _get_job_or_404(job_id, user)
        path = job_manager.combined_report_path(job_id, filename)
        if path is None:
            raise HTTPException(status_code=404, detail="Poročilo ne obstaja.")
        _audit(request, user, "prenos_porocila", f"job={job_id}, datoteka={path.name}")
        return FileResponse(path, filename=path.name)

    # ------------------------------------------------------ WebSocket napredek

    @app.websocket("/api/ws/jobs/{job_id}")
    async def ws_job_progress(websocket: WebSocket, job_id: str) -> None:
        """Pošilja stanje joba v realnem času (namesto/ob HTTP pollingu)."""
        if auth_manager.enabled:
            user = auth_manager.user_from_token(websocket.cookies.get(SESSION_COOKIE))
            if user is None:
                await websocket.close(code=4401)
                return
        else:
            user = ANONYMOUS_USER

        job = job_manager.get_job(job_id)
        if job is None or not _job_accessible(user, job):
            await websocket.close(code=4404)
            return

        await websocket.accept()
        last_payload: dict | None = None
        try:
            while True:
                status = job_manager.status(job_id)
                if status is None:
                    break
                payload = status.model_dump()
                if payload != last_payload:
                    await websocket.send_json(payload)
                    last_payload = payload
                if status.state in {"done", "error"}:
                    break
                await asyncio.sleep(0.4)
        except WebSocketDisconnect:
            return
        except Exception:  # pragma: no cover - prekinjena povezava ipd.
            logger.debug("WebSocket za job %s prekinjen.", job_id, exc_info=True)
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    # ----------------------------------------------------------- zgodovina

    @app.get("/api/history", response_model=HistoryList)
    def history_list(
        request: Request,
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(current_user),
    ) -> HistoryList:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        username_filter = None if user.has_role("qa") else user.username
        records, total = history_store.list(
            limit=limit, offset=offset, username=username_filter
        )
        return HistoryList(
            records=[HistoryRecord(**r) for r in records],
            total=total,
            limit=limit,
            offset=offset,
        )

    def _get_history_or_404(job_id: str, user: User) -> dict:
        record = history_store.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Vnos zgodovine ne obstaja.")
        if not _history_accessible(user, record):
            raise HTTPException(status_code=403, detail="Nimaš dostopa do tega vnosa.")
        return record

    @app.get("/api/history/{job_id}", response_model=HistoryDetail)
    def history_detail(job_id: str, user: User = Depends(current_user)) -> HistoryDetail:
        record = _get_history_or_404(job_id, user)
        return HistoryDetail(
            record=HistoryRecord(**record),
            results=history_store.get_results(job_id),
        )

    @app.get("/api/history/{job_id}/files/{file_index}/report/{filename}")
    def history_report(
        job_id: str,
        file_index: int,
        filename: str,
        request: Request,
        user: User = Depends(current_user),
    ) -> FileResponse:
        _get_history_or_404(job_id, user)
        path = history_store.report_path(job_id, str(file_index), filename)
        if path is None:
            raise HTTPException(status_code=404, detail="Poročilo ne obstaja.")
        _audit(request, user, "prenos_porocila", f"zgodovina={job_id}, datoteka={path.name}")
        return FileResponse(path, filename=path.name)

    @app.get("/api/history/{job_id}/report/{filename}")
    def history_combined_report(
        job_id: str,
        filename: str,
        request: Request,
        user: User = Depends(current_user),
    ) -> FileResponse:
        _get_history_or_404(job_id, user)
        path = history_store.report_path(job_id, "combined", filename)
        if path is None:
            raise HTTPException(status_code=404, detail="Poročilo ne obstaja.")
        _audit(request, user, "prenos_porocila", f"zgodovina={job_id}, datoteka={path.name}")
        return FileResponse(path, filename=path.name)

    # -------------------------------------------------- primerjava razdelkov

    @app.post("/api/section-compare", response_model=SectionCompareOut)
    async def section_compare(
        request: Request,
        recipe: UploadFile = File(..., description="Receptura z vsaj dvema listoma (.xlsx/.xlsm)"),
        user: User = Depends(current_user),
    ) -> SectionCompareOut:
        from validator_oop.excel.section_compare import compare_sections

        _check_extension(recipe, RECIPE_EXTENSIONS, "receptura")
        name, data = await _read_single(recipe, settings.max_upload_bytes)

        tmp_dir = settings.workdir / "tmp" / uuid.uuid4().hex
        tmp_dir.mkdir(parents=True, exist_ok=True)
        try:
            path = tmp_dir / (Path(name).name or "receptura.xlsx")
            path.write_bytes(data)
            try:
                result = compare_sections(path)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            except Exception as exc:
                logger.exception("Primerjava razdelkov ni uspela: %s", exc)
                raise HTTPException(
                    status_code=500, detail="Primerjava razdelkov ni uspela."
                ) from exc
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        _audit(
            request,
            user,
            "primerjava_razdelkov",
            f"datoteka={result.filename}, listov={len(result.sheets)}, razlik={len(result.issues)}",
        )
        return SectionCompareOut(**result.to_dict())

    # --------------------------------------------------------- diff receptur

    @app.post("/api/diff", response_model=DiffOut)
    async def diff(
        request: Request,
        file_a: UploadFile | None = File(None, description="Verzija A (starejša)"),
        file_b: UploadFile | None = File(None, description="Verzija B (novejša)"),
        history_a: str | None = Form(None, description="ID vnosa zgodovine za stran A"),
        history_a_file: str | None = Form(None, description="Ime datoteke v zgodovini (A)"),
        history_b: str | None = Form(None, description="ID vnosa zgodovine za stran B"),
        history_b_file: str | None = Form(None, description="Ime datoteke v zgodovini (B)"),
        user: User = Depends(current_user),
    ) -> DiffOut:
        from validator_oop.excel.recipe_diff import diff_recipes

        tmp_dir = settings.workdir / "tmp" / uuid.uuid4().hex

        async def _resolve_side(
            side: str,
            upload: UploadFile | None,
            history_id: str | None,
            history_file: str | None,
        ) -> Path:
            if upload is not None and upload.filename:
                _check_extension(upload, RECIPE_EXTENSIONS, f"receptura ({side})")
                name, data = await _read_single(upload, settings.max_upload_bytes)
                tmp_dir.mkdir(parents=True, exist_ok=True)
                path = tmp_dir / f"{side}_{Path(name).name}"
                path.write_bytes(data)
                return path
            if history_id and history_file:
                record = _get_history_or_404(history_id, user)
                path = history_store.input_path(history_id, history_file)
                if path is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Datoteka '{history_file}' ne obstaja v zgodovini ({record['job_id']}).",
                    )
                return path
            raise HTTPException(
                status_code=422,
                detail=f"Za stran {side.upper()} naloži datoteko ali izberi vnos iz zgodovine.",
            )

        try:
            path_a = await _resolve_side("a", file_a, history_a, history_a_file)
            path_b = await _resolve_side("b", file_b, history_b, history_b_file)
            try:
                result = diff_recipes(path_a, path_b)
            except Exception as exc:
                logger.exception("Diff receptur ni uspel: %s", exc)
                raise HTTPException(status_code=500, detail="Primerjava verzij ni uspela.") from exc
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        _audit(
            request,
            user,
            "diff_receptur",
            f"A={result.file_a}, B={result.file_b}, razlike={result.has_changes}",
        )
        return DiffOut(**result.to_dict())

    # ------------------------------------------- MES/MySQL vir (opcijsko)
    # Endpointi so registrirani samo pri MES_WEB_ENABLE_DB=1, sicer so skriti.

    if settings.enable_db:
        _register_db_routes(app, job_manager, auth_manager, current_user, _audit)

    # ----------------------------------------------------------------- audit

    @app.get("/api/audit", response_model=AuditList)
    def audit_list(
        limit: int = 100,
        offset: int = 0,
        username: str | None = None,
        action: str | None = None,
        user: User = Depends(current_user),
    ) -> AuditList:
        _require_role(user, "qa")
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        entries, total = db.list_audit(
            limit=limit, offset=offset, username=username, action=action
        )
        return AuditList(entries=entries, total=total, limit=limit, offset=offset)


def _register_db_routes(
    app: FastAPI,
    job_manager: JobManager,
    auth_manager: AuthManager,
    current_user,
    audit,
) -> None:
    """Endpointi za validacijo neposredno iz MES MySQL baze (/api/db/*).

    Vsi db moduli se uvažajo lazy – MySQL driver je opcijska odvisnost in
    brez njega ostali del aplikacije (upload tok) deluje nespremenjeno.
    """

    def _db_error_to_http(exc: Exception) -> HTTPException:
        from validator_oop.db import (
            DBConnectionError,
            DBDriverMissingError,
            MappingError,
            RecipeNotFoundError,
        )

        if isinstance(exc, RecipeNotFoundError):
            return HTTPException(status_code=404, detail=str(exc))
        if isinstance(exc, (DBDriverMissingError, DBConnectionError)):
            return HTTPException(status_code=503, detail=str(exc))
        if isinstance(exc, (MappingError, ValueError)):
            return HTTPException(status_code=422, detail=str(exc))
        logger.exception("MES DB napaka: %s", exc)
        return HTTPException(status_code=500, detail="Napaka pri dostopu do MES baze.")

    def _make_loader():
        from validator_oop.db import DBConfig, MySQLLoader, load_mapping

        db_config = DBConfig.from_env()
        mapping = load_mapping(db_config.mapping_file)
        return MySQLLoader(db_config, mapping, logger_=logger)

    @app.get("/api/db/health", response_model=DBHealthOut)
    def db_health() -> DBHealthOut:
        from validator_oop.db import DBConfig
        from validator_oop.db.connection import ConnectionFactory

        db_config = DBConfig.from_env()
        try:
            db_config.validate()
        except ValueError as exc:
            return DBHealthOut(status="unconfigured", detail=str(exc))

        ok = ConnectionFactory(db_config).ping()
        return DBHealthOut(
            status="ok" if ok else "error",
            host=db_config.host,
            database=db_config.database,
            detail="" if ok else "Povezava na MES bazo ni uspela.",
        )

    @app.get("/api/db/recipes", response_model=DBRecipeList)
    def db_recipes(
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        user: User = Depends(current_user),
    ) -> DBRecipeList:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        try:
            recipes = _make_loader().list_recipes(
                limit=limit, offset=offset, name_filter=q
            )
        except Exception as exc:
            raise _db_error_to_http(exc) from exc
        return DBRecipeList(
            recipes=[DBRecipeMeta(**r.to_dict()) for r in recipes],
            limit=limit,
            offset=offset,
        )

    @app.post("/api/db/validate")
    def db_validate(
        payload: DBValidateIn,
        request: Request,
        user: User = Depends(current_user),
    ) -> JSONResponse:
        # Pisanje rezultatov v MES bazo je občutljivo – ob vklopljenem authu
        # ga dovolimo samo QA/admin vlogi.
        if payload.save_results and auth_manager.enabled:
            _require_role(user, "qa")

        try:
            if not _make_loader().recipe_exists(payload.recipe_id):
                raise HTTPException(
                    status_code=404,
                    detail=f"Receptura z id={payload.recipe_id} ne obstaja v MES bazi.",
                )
        except HTTPException:
            raise
        except Exception as exc:
            raise _db_error_to_http(exc) from exc

        job_id = job_manager.create_db_job(
            config=payload.config,
            recipe_id=payload.recipe_id,
            save_results=payload.save_results,
            owner=user.username,
        )
        audit(
            request,
            user,
            "validacija_zagnana",
            f"job={job_id}, vir=MES baza, receptura={payload.recipe_id}, "
            f"shrani_rezultate={payload.save_results}",
        )
        return JSONResponse({"job_id": job_id}, status_code=202)


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


def _start_cleanup_thread(
    job_manager: JobManager,
    history_store: HistoryStore,
    db: Database,
    settings: Settings,
) -> None:
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
            try:
                db.purge_expired_sessions()
                history_store.cleanup_older_than(settings.history_retention_days)
            except Exception:  # pragma: no cover
                logger.debug("Čiščenje sej/zgodovine ni uspelo", exc_info=True)

    thread = threading.Thread(target=_loop, name="mes-web-cleanup", daemon=True)
    thread.start()


app = create_app()
