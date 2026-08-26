"""Environment-driven configuration for the MES MySQL connection.

Credentials are never stored in code or git: they come from environment
variables or an (un-versioned) ``.env`` file. See ``.env.example`` in the
project root for the full list.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_env_file(path: Path) -> dict[str, str]:
    """Parse a simple ``KEY=VALUE`` .env file (no external dependency).

    Lines starting with ``#`` and blank lines are ignored. Values may be
    quoted with single or double quotes.
    """
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def _env(name: str, fallback: dict[str, str], default: str = "") -> str:
    """Read a value from os.environ first, then from the .env fallback."""
    raw = os.environ.get(name)
    if raw is not None:
        return raw.strip()
    return fallback.get(name, default).strip()


@dataclass(slots=True)
class DBConfig:
    """Connection settings for the MES MySQL database.

    Attributes:
        host: MySQL server host (required).
        port: MySQL server port (default 3306).
        database: Database name (required).
        user: User for reading recipes (recommended: read-only).
        password: Password for ``user`` (never logged).
        results_user: Optional separate user with write access for results.
        results_password: Password for ``results_user``.
        mapping_file: Optional path to a JSON mapping override file.
        charset: Connection charset (default utf8mb4).
        connect_timeout: Connection timeout in seconds.
        ssl_ca: Optional path to a CA certificate for TLS.
    """

    host: str = ""
    port: int = 3306
    database: str = ""
    user: str = ""
    password: str = field(default="", repr=False)
    results_user: str = ""
    results_password: str = field(default="", repr=False)
    mapping_file: Path | None = None
    charset: str = "utf8mb4"
    connect_timeout: int = 10
    ssl_ca: Path | None = None

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> DBConfig:
        """Build a config from environment variables (and optional .env file).

        Args:
            env_file: Explicit path to a .env file. When None, ``.env`` in the
                current working directory is used if present.

        Returns:
            DBConfig instance (may be incomplete – call :meth:`validate`).
        """
        fallback: dict[str, str] = {}
        candidate = Path(env_file) if env_file else Path.cwd() / ".env"
        if candidate.is_file():
            fallback = _load_env_file(candidate)

        def get(name: str, default: str = "") -> str:
            return _env(name, fallback, default)

        mapping_file = get("MES_DB_MAPPING_FILE")
        ssl_ca = get("MES_DB_SSL_CA")
        user = get("MES_DB_USER")
        return cls(
            host=get("MES_DB_HOST"),
            port=_to_int(get("MES_DB_PORT", "3306"), 3306),
            database=get("MES_DB_NAME"),
            user=user,
            password=get("MES_DB_PASSWORD"),
            results_user=get("MES_DB_RESULTS_USER") or user,
            results_password=get("MES_DB_RESULTS_PASSWORD") or get("MES_DB_PASSWORD"),
            mapping_file=Path(mapping_file) if mapping_file else None,
            charset=get("MES_DB_CHARSET", "utf8mb4") or "utf8mb4",
            connect_timeout=_to_int(get("MES_DB_CONNECT_TIMEOUT", "10"), 10),
            ssl_ca=Path(ssl_ca) if ssl_ca else None,
        )

    def validate(self) -> None:
        """Raise ValueError with a Slovenian message when required fields are missing."""
        missing = [
            name
            for name, value in (
                ("MES_DB_HOST", self.host),
                ("MES_DB_NAME", self.database),
                ("MES_DB_USER", self.user),
            )
            if not value
        ]
        if missing:
            # ASCII-safe message (printed to Windows cp1252 console in CLI mode)
            raise ValueError(
                "Manjkajoca konfiguracija MES baze: "
                + ", ".join(missing)
                + ". Nastavi okoljske spremenljivke ali .env datoteko "
                "(glej .env.example)."
            )

    def connect_kwargs(self, *, for_results: bool = False) -> dict[str, object]:
        """Build keyword arguments for ``mysql.connector.connect``.

        Args:
            for_results: Use the (optional) separate write user for results.
        """
        user = self.results_user if for_results and self.results_user else self.user
        password = (
            self.results_password if for_results and self.results_user else self.password
        )
        kwargs: dict[str, object] = {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": user,
            "password": password,
            "charset": self.charset,
            "connection_timeout": self.connect_timeout,
        }
        if self.ssl_ca:
            kwargs["ssl_ca"] = str(self.ssl_ca)
        return kwargs


def _to_int(raw: str, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default
