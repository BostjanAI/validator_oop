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
    bypass_zakleni_require_pogoj_for_param1_steps: bool = True
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


class JobResults(BaseModel):
    """Združeni rezultati celotnega joba."""

    job_id: str
    state: str
    totals: dict[str, int]
    files: list[FileResult]
    combined_reports: list[ReportRef] = Field(default_factory=list)
