"""Create/verify the results tables in the MES MySQL database.

Usage (env vars / .env must be configured, see .env.example):

    python -m validator_oop.db.migrate

The DDL lives in ``db/schema.sql`` and is idempotent
(``CREATE TABLE IF NOT EXISTS``), so re-running is safe.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from .config import DBConfig
from .connection import ConnectionFactory
from .errors import DBError

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

RESULT_TABLES = ("validation_runs", "validation_findings")


def _schema_statements() -> list[str]:
    """Split schema.sql into individual executable statements."""
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.strip().startswith("--")]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]


def ensure_results_tables(factory: ConnectionFactory) -> None:
    """Create the results tables when missing (idempotent)."""
    with factory.connection(for_results=True) as conn:
        cur = conn.cursor()
        try:
            for statement in _schema_statements():
                cur.execute(statement)
            conn.commit()
        finally:
            cur.close()


def verify_results_tables(factory: ConnectionFactory) -> list[str]:
    """Return the list of missing results tables (empty = OK)."""
    missing: list[str] = []
    with factory.connection(for_results=True) as conn:
        cur = conn.cursor()
        try:
            for table in RESULT_TABLES:
                cur.execute("SHOW TABLES LIKE %s", (table,))
                if cur.fetchone() is None:
                    missing.append(table)
        finally:
            cur.close()
    return missing


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        config = DBConfig.from_env()
        factory = ConnectionFactory(config)
        ensure_results_tables(factory)
        missing = verify_results_tables(factory)
    except (DBError, ValueError) as exc:
        print(f"Napaka: {exc}", file=sys.stderr)
        return 1

    if missing:
        print(f"Napaka: tabele niso bile ustvarjene: {', '.join(missing)}", file=sys.stderr)
        return 1
    print("Tabele za rezultate validacije so pripravljene (validation_runs, validation_findings).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
