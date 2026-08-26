"""Pydantic sheme za API (vhod/izhod).

Validacijska konfiguracija se prejme kot JSON niz v multipart obrazcu
(skupaj z naloženimi datotekami) in se razčleni z ``ValidationConfigIn``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ValidationConfigIn(BaseModel):
    """Konfiguracija validacije, kot jo pošlje brskalnik."""

    strict_mode: bool = False
    include_formulas: bool = False
    bypass_rules: list[str] = Field(default_factory=list)
    bypass_codes: list[str] = Field(default_factory=list)
    # Zaklenipolja domenske zastavice (privzeto kot v ValidatorConfig)
    bypass_zakleni_require_empty_for_checkbox: bool = True
    bypass_zakleni_require_pogoj_for_param1_steps: bool = False
    bypass_zakleni_inverse_pogoj_requirement: bool = False
    # SOP / katalogi
    enable_sop_validation: bool = True
    enable_catalog_validation: bool = True
    # Auto-fix (faza 2 – privzeto izklopljeno)
    apply_fixes: bool = False


class RuleInfo(BaseModel):
    """Opis enega pravila za konfiguracijski UI."""

    name: str
    code: str
    severity: str
    priority: int
    type: str
    description: str


class CodeInfo(BaseModel):
    """Koda napake in njen slovenski opis (za filtre / bypass)."""

    code: str
    description: str


class RulesCatalog(BaseModel):
    """Katalog pravil in kod za konfiguracijski UI."""

    rules: list[RuleInfo]
    codes: list[CodeInfo]
    version: str


class FileStatus(BaseModel):
    """Stanje posamezne datoteke znotraj joba."""

    index: int
    filename: str
    state: Literal["queued", "running", "done", "error"] = "queued"
    error: str | None = None


class JobStatus(BaseModel):
    """Stanje validacijskega joba (za polling napredka)."""

    job_id: str
    state: Literal["queued", "running", "done", "error"]
    progress: float = 0.0
    message: str = ""
    created_at: float
    total_files: int
    processed_files: int
    files: list[FileStatus]
    error: str | None = None


class Issue(BaseModel):
    """Ena validacijska napaka za prikaz v tabeli rezultatov."""

    file: str
    sheet: str
    row: Any | None = None
    col: Any | None = None
    code: str = ""
    code_desc: str = ""
    severity: str = "error"
    rule: str = ""
    message: str = ""


class ReportRef(BaseModel):
    """Sklic na generirano poročilo, ki ga je mogoče prenesti."""

    kind: str
    label: str
    filename: str
    available: bool = True


class FileResult(BaseModel):
    """Rezultat validacije ene recepture."""

    index: int
    filename: str
    is_valid: bool
    counts: dict[str, int]
    counts_by_code: dict[str, int]
    counts_by_sheet: dict[str, int]
    catalog_validation: dict[str, Any] | None = None
    issues: list[Issue]
    reports: list[ReportRef]
    error: str | None = None
    # MES/MySQL vir: id zapisa v validation_runs, če so bili rezultati shranjeni
    db_run_id: int | None = None


class JobResults(BaseModel):
    """Združeni rezultati celotnega joba."""

    job_id: str
    state: str
    totals: dict[str, int]
    files: list[FileResult]
    combined_reports: list[ReportRef] = Field(default_factory=list)


# =============================================================================
# Faza 2: avtentikacija, zgodovina, audit, primerjave
# =============================================================================


class LoginIn(BaseModel):
    """Prijavni podatki (AD/LDAP ali lokalni uporabnik)."""

    username: str
    password: str


class UserOut(BaseModel):
    """Prijavljen uporabnik za frontend."""

    username: str
    display_name: str
    role: str
    role_label: str
    source: str


class AuthStatus(BaseModel):
    """Stanje avtentikacije (za inicializacijo frontenda)."""

    auth_enabled: bool
    user: UserOut | None = None


class HistoryRecord(BaseModel):
    """En vnos trajne zgodovine validacij (povzetek)."""

    job_id: str
    username: str
    created_at: str
    finished_at: str | None = None
    state: str
    total_files: int
    invalid_files: int
    errors: int
    warnings: int
    infos: int
    files: list[dict[str, Any]] = Field(default_factory=list)
    combined_reports: list[dict[str, Any]] = Field(default_factory=list)
    config: dict[str, Any] | None = None


class HistoryList(BaseModel):
    """Stran zgodovine validacij."""

    records: list[HistoryRecord]
    total: int
    limit: int
    offset: int


class HistoryDetail(BaseModel):
    """Podrobnosti enega vnosa zgodovine (z rezultati, če so na voljo)."""

    record: HistoryRecord
    results: dict[str, Any] | None = None


class AuditEntry(BaseModel):
    """En vnos revizijske sledi."""

    id: int
    ts: str
    username: str
    role: str
    ip: str
    action: str
    detail: str


class AuditList(BaseModel):
    """Stran revizijske sledi."""

    entries: list[AuditEntry]
    total: int
    limit: int
    offset: int


# =============================================================================
# MES/MySQL integracija (endpointi /api/db/*, za MES_WEB_ENABLE_DB=1)
# =============================================================================


class DBHealthOut(BaseModel):
    """Stanje povezave na MES bazo (brez poverilnic v odgovoru)."""

    status: Literal["ok", "error", "unconfigured"]
    host: str = ""
    database: str = ""
    detail: str = ""


class DBRecipeMeta(BaseModel):
    """Metapodatki ene recepture iz MES baze."""

    recipe_id: int
    name: str = ""
    version: str = ""
    date: str = ""


class DBRecipeList(BaseModel):
    """Stran seznama receptur iz MES baze."""

    recipes: list[DBRecipeMeta]
    limit: int
    offset: int


class DBValidateIn(BaseModel):
    """Zahteva za validacijo recepture neposredno iz MES baze."""

    recipe_id: int
    config: ValidationConfigIn = Field(default_factory=ValidationConfigIn)
    save_results: bool = False


class SectionCompareOut(BaseModel):
    """Rezultat primerjave razdelkov med listi ene recepture."""

    filename: str
    base_sheet: str
    sheets: list[str]
    is_match: bool
    counts: dict[str, int]
    sections: dict[str, list[dict[str, Any]]]
    issues: list[dict[str, Any]]


class DiffOut(BaseModel):
    """Rezultat primerjave dveh verzij recepture."""

    file_a: str
    file_b: str
    has_changes: bool
    summary: dict[str, int]
    sheets: list[dict[str, Any]]
