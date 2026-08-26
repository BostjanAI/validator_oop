"""Exception types for the MySQL/MES integration layer.

All user-facing messages are in Slovenian (consistent with the rest of the
validator); docstrings stay in English like the existing codebase.

Messages are intentionally ASCII-safe (no diacritics) because they are also
printed to the Windows cp1252 console in CLI mode (same convention as the
"Koncano. Porocilo:" messages in main.py).
"""

from __future__ import annotations


class DBError(Exception):
    """Base class for all database-layer errors."""


class DBDriverMissingError(DBError):
    """Raised when the optional MySQL driver is not installed."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or (
                "MySQL driver ni namescen. Namesti ga z: "
                "pip install -r requirements-db.txt "
                "(paket mysql-connector-python)."
            )
        )


class DBConnectionError(DBError):
    """Raised when a connection to the MES database cannot be established.

    The message never contains the password.
    """

    def __init__(self, host: str, port: int, database: str, cause: str = "") -> None:
        detail = f" ({cause})" if cause else ""
        super().__init__(
            f"Povezava na MES bazo ni uspela: {host}:{port}/{database}{detail}. "
            "Preveri host, port, ime baze, uporabnika/geslo in dostopnost "
            "streznika (firewall)."
        )
        self.host = host
        self.port = port
        self.database = database


class RecipeNotFoundError(DBError):
    """Raised when the requested recipe id does not exist in the database."""

    def __init__(self, recipe_id: int) -> None:
        super().__init__(f"Receptura z id={recipe_id} ne obstaja v MES bazi.")
        self.recipe_id = recipe_id


class MappingError(DBError):
    """Raised when the MES column mapping is incomplete or invalid."""

    def __init__(self, message: str, missing: list[str] | None = None) -> None:
        super().__init__(message)
        self.missing = missing or []
