"""Connection handling for the MES MySQL database.

The MySQL driver (``mysql-connector-python``) is an optional dependency:
it is imported lazily so the rest of the validator works without it
(same pattern as openpyxl in ``excel/excel_loader.py``).
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator

from .config import DBConfig
from .errors import DBConnectionError, DBDriverMissingError

logger = logging.getLogger(__name__)

# Number of connection attempts on transient failures.
_CONNECT_ATTEMPTS = 2
_RETRY_DELAY_S = 0.5


def _import_driver() -> Any:
    """Lazily import mysql.connector; raise a clear error when missing."""
    try:
        import mysql.connector  # type: ignore
    except ImportError as exc:
        raise DBDriverMissingError() from exc
    return mysql.connector


class ConnectionFactory:
    """Creates MySQL connections from a :class:`DBConfig`.

    A new connection is opened per operation (recipes are small; pooling is
    unnecessary for this workload) and always closed via context managers.
    """

    def __init__(self, config: DBConfig, *, logger_: logging.Logger | None = None) -> None:
        self._config = config
        self._logger = logger_ or logger

    @property
    def config(self) -> DBConfig:
        return self._config

    def connect(self, *, for_results: bool = False) -> Any:
        """Open a new connection (caller is responsible for closing it).

        Args:
            for_results: Connect with the (optional) write user for results.

        Raises:
            DBDriverMissingError: When mysql-connector-python is not installed.
            DBConnectionError: When the connection cannot be established.
        """
        driver = _import_driver()
        self._config.validate()
        kwargs = self._config.connect_kwargs(for_results=for_results)

        last_exc: Exception | None = None
        for attempt in range(1, _CONNECT_ATTEMPTS + 1):
            try:
                return driver.connect(**kwargs)
            except Exception as exc:  # driver-specific errors are not importable lazily
                last_exc = exc
                self._logger.warning(
                    "Povezava na MES bazo ni uspela (poskus %d/%d): %s",
                    attempt,
                    _CONNECT_ATTEMPTS,
                    type(exc).__name__,
                )
                if attempt < _CONNECT_ATTEMPTS:
                    time.sleep(_RETRY_DELAY_S)

        raise DBConnectionError(
            self._config.host,
            self._config.port,
            self._config.database,
            cause=type(last_exc).__name__ if last_exc else "",
        ) from last_exc

    @contextmanager
    def connection(self, *, for_results: bool = False) -> Iterator[Any]:
        """Context manager yielding an open connection, closed on exit."""
        conn = self.connect(for_results=for_results)
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:  # pragma: no cover - defensive close
                pass

    @contextmanager
    def cursor(self, *, dictionary: bool = True, for_results: bool = False) -> Iterator[Any]:
        """Context manager yielding a cursor; connection and cursor are closed on exit."""
        with self.connection(for_results=for_results) as conn:
            cur = conn.cursor(dictionary=dictionary)
            try:
                yield cur
            finally:
                try:
                    cur.close()
                except Exception:  # pragma: no cover - defensive close
                    pass

    def ping(self) -> bool:
        """Return True when a connection can be established (health check)."""
        try:
            with self.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return True
        except (DBDriverMissingError, DBConnectionError, ValueError):
            return False
