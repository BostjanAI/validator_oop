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

    @property
    def jobs_dir(self) -> Path:
        return self.workdir / "jobs"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Vrne singleton nastavitev (lazy)."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings
