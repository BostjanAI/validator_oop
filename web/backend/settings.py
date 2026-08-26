"""Nastavitve spletnega backenda.

Vse nastavitve se lahko prepišejo prek okoljskih spremenljivk, da je
deployment na internem strežniku (Docker / nginx) brez sprememb kode.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "da"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_list(name: str) -> list[str]:
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(slots=True)
class Settings:
    """Runtime nastavitve backenda."""

    workdir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("MES_WEB_WORKDIR")
            or (Path(tempfile.gettempdir()) / "mes_validator_web")
        )
    )
    max_workers: int = field(default_factory=lambda: _env_int("MES_WEB_MAX_WORKERS", 2))
    max_upload_mb: int = field(default_factory=lambda: _env_int("MES_WEB_MAX_UPLOAD_MB", 50))
    job_ttl_minutes: int = field(default_factory=lambda: _env_int("MES_WEB_JOB_TTL_MIN", 120))
    cors_origins: list[str] = field(default_factory=lambda: _env_list("MES_WEB_CORS_ORIGINS"))
    serve_frontend: bool = field(default_factory=lambda: _env_bool("MES_WEB_SERVE_FRONTEND", True))

    # --- Faza 2: avtentikacija (AD/LDAP + lokalni fallback) ------------------
    # Privzeto izklopljena (razvojni način brez prijave, kot MVP).
    auth_enabled: bool = field(default_factory=lambda: _env_bool("MES_WEB_AUTH_ENABLED", False))
    # "local" (samo lokalni uporabniki), "ldap" (samo AD/LDAP),
    # "mixed" (najprej LDAP, nato lokalni fallback)
    auth_mode: str = field(default_factory=lambda: _env_str("MES_WEB_AUTH_MODE", "mixed"))
    session_ttl_minutes: int = field(default_factory=lambda: _env_int("MES_WEB_SESSION_TTL_MIN", 480))
    secure_cookies: bool = field(default_factory=lambda: _env_bool("MES_WEB_SECURE_COOKIES", False))
    # Lokalni uporabniki: JSON datoteka {"user": {"password_hash": "...", "role": "...", ...}}
    local_users_file: str = field(default_factory=lambda: _env_str("MES_WEB_LOCAL_USERS_FILE"))
    # Dev fallback uporabniki: "uporabnik:geslo:rola,uporabnik2:geslo2:rola2"
    # (samo za razvoj / interne teste, gesla v čistopisu!)
    dev_users: str = field(default_factory=lambda: _env_str("MES_WEB_DEV_USERS"))

    # --- Faza 2: AD/LDAP -----------------------------------------------------
    ldap_server: str = field(default_factory=lambda: _env_str("MES_WEB_LDAP_SERVER"))
    ldap_use_ssl: bool = field(default_factory=lambda: _env_bool("MES_WEB_LDAP_USE_SSL", False))
    # Predloga za bind DN/UPN, npr. "PODJETJE\\{username}" ali "{username}@podjetje.local"
    ldap_user_dn_template: str = field(default_factory=lambda: _env_str("MES_WEB_LDAP_USER_DN", "{username}"))
    ldap_base_dn: str = field(default_factory=lambda: _env_str("MES_WEB_LDAP_BASE_DN"))
    # AD skupine → role (DN ali del DN-ja skupine; prazno = ni mapiranja)
    ldap_group_tehnolog: str = field(default_factory=lambda: _env_str("MES_WEB_LDAP_GROUP_TEHNOLOG"))
    ldap_group_qa: str = field(default_factory=lambda: _env_str("MES_WEB_LDAP_GROUP_QA"))
    ldap_group_admin: str = field(default_factory=lambda: _env_str("MES_WEB_LDAP_GROUP_ADMIN"))
    # Rola, če uporabnik ni v nobeni mapirani skupini ("" = prijava zavrnjena)
    ldap_default_role: str = field(default_factory=lambda: _env_str("MES_WEB_LDAP_DEFAULT_ROLE", "tehnolog"))

    # --- Faza 2: trajna zgodovina + audit ------------------------------------
    db_path_override: str = field(default_factory=lambda: _env_str("MES_WEB_DB_PATH"))
    history_retention_days: int = field(default_factory=lambda: _env_int("MES_WEB_HISTORY_TTL_DAYS", 0))

    # --- MES/MySQL integracija ------------------------------------------------
    # Endpointi /api/db/* so skriti, dokler ni MES_WEB_ENABLE_DB=1 in
    # konfigurirana MES baza (MES_DB_* spremenljivke, glej .env.example).
    enable_db: bool = field(default_factory=lambda: _env_bool("MES_WEB_ENABLE_DB", False))

    @property
    def jobs_dir(self) -> Path:
        return self.workdir / "jobs"

    @property
    def history_dir(self) -> Path:
        return self.workdir / "history"

    @property
    def db_path(self) -> Path:
        if self.db_path_override:
            return Path(self.db_path_override)
        return self.workdir / "validator_web.db"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Vrne singleton nastavitev (lazy)."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings
