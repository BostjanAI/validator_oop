"""SQLite podatkovna plast za spletno aplikacijo (faza 2).

Hrani samo podatke spletne plasti (uporabniki, seje, audit trail, zgodovina
validacij) — validacijska logika in poročila ostajajo v obstoječem engine-u.

Uporablja stdlib ``sqlite3`` (brez novih odvisnosti), en proces, več niti
(ThreadPoolExecutor + FastAPI) → ena povezava z zaklepom in WAL načinom.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("mes_web.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username     TEXT PRIMARY KEY,
    display_name TEXT NOT NULL DEFAULT '',
    role         TEXT NOT NULL,
    source       TEXT NOT NULL DEFAULT 'local',
    created_at   TEXT NOT NULL,
    last_login   TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    token        TEXT PRIMARY KEY,
    username     TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    role         TEXT NOT NULL,
    source       TEXT NOT NULL DEFAULT 'local',
    created_at   REAL NOT NULL,
    expires_at   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       TEXT NOT NULL,
    username TEXT NOT NULL DEFAULT '',
    role     TEXT NOT NULL DEFAULT '',
    ip       TEXT NOT NULL DEFAULT '',
    action   TEXT NOT NULL,
    detail   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log (ts);
CREATE INDEX IF NOT EXISTS idx_audit_username ON audit_log (username);

CREATE TABLE IF NOT EXISTS validation_history (
    job_id        TEXT PRIMARY KEY,
    username      TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL,
    finished_at   TEXT,
    state         TEXT NOT NULL,
    total_files   INTEGER NOT NULL DEFAULT 0,
    invalid_files INTEGER NOT NULL DEFAULT 0,
    errors        INTEGER NOT NULL DEFAULT 0,
    warnings      INTEGER NOT NULL DEFAULT 0,
    infos         INTEGER NOT NULL DEFAULT 0,
    files_json    TEXT NOT NULL DEFAULT '[]',
    combined_json TEXT NOT NULL DEFAULT '[]',
    config_json   TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_history_created ON validation_history (created_at);
CREATE INDEX IF NOT EXISTS idx_history_username ON validation_history (username);
"""


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Database:
    """Tanka, nitno varna ovojnica okrog sqlite3 za spletno plast."""

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------ users

    def upsert_user(self, username: str, display_name: str, role: str, source: str) -> None:
        now = _now_iso()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO users (username, display_name, role, source, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    display_name = excluded.display_name,
                    role = excluded.role,
                    source = excluded.source,
                    last_login = excluded.last_login
                """,
                (username, display_name, role, source, now, now),
            )
            self._conn.commit()

    # --------------------------------------------------------------- sessions

    def create_session(
        self,
        token: str,
        username: str,
        display_name: str,
        role: str,
        source: str,
        ttl_seconds: int,
    ) -> None:
        now = time.time()
        with self._lock:
            self._conn.execute(
                "INSERT INTO sessions (token, username, display_name, role, source, created_at, expires_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (token, username, display_name, role, source, now, now + ttl_seconds),
            )
            self._conn.commit()

    def get_session(self, token: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM sessions WHERE token = ?", (token,)
            ).fetchone()
        if row is None:
            return None
        if row["expires_at"] < time.time():
            self.delete_session(token)
            return None
        return dict(row)

    def delete_session(self, token: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            self._conn.commit()

    def purge_expired_sessions(self) -> int:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM sessions WHERE expires_at < ?", (time.time(),)
            )
            self._conn.commit()
            return cur.rowcount

    # ------------------------------------------------------------------ audit

    def add_audit(
        self,
        *,
        username: str,
        role: str,
        ip: str,
        action: str,
        detail: str = "",
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO audit_log (ts, username, role, ip, action, detail)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (_now_iso(), username, role, ip, action, detail),
            )
            self._conn.commit()

    def list_audit(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        username: str | None = None,
        action: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Vrne (vnosi, skupno število) za straničenje."""
        where: list[str] = []
        params: list[Any] = []
        if username:
            where.append("username = ?")
            params.append(username)
        if action:
            where.append("action = ?")
            params.append(action)
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""

        with self._lock:
            total = self._conn.execute(
                f"SELECT COUNT(*) AS n FROM audit_log{where_sql}", params
            ).fetchone()["n"]
            rows = self._conn.execute(
                f"SELECT * FROM audit_log{where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
        return [dict(r) for r in rows], int(total)

    # ---------------------------------------------------------------- history

    def add_history(
        self,
        *,
        job_id: str,
        username: str,
        created_at: float,
        finished_at: float | None,
        state: str,
        total_files: int,
        invalid_files: int,
        errors: int,
        warnings: int,
        infos: int,
        files: list[dict[str, Any]],
        combined_reports: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO validation_history
                    (job_id, username, created_at, finished_at, state, total_files,
                     invalid_files, errors, warnings, infos, files_json, combined_json, config_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    username,
                    datetime.fromtimestamp(created_at).isoformat(timespec="seconds"),
                    datetime.fromtimestamp(finished_at).isoformat(timespec="seconds")
                    if finished_at
                    else None,
                    state,
                    total_files,
                    invalid_files,
                    errors,
                    warnings,
                    infos,
                    json.dumps(files, ensure_ascii=False),
                    json.dumps(combined_reports, ensure_ascii=False),
                    json.dumps(config, ensure_ascii=False),
                ),
            )
            self._conn.commit()

    def get_history(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM validation_history WHERE job_id = ?", (job_id,)
            ).fetchone()
        return self._history_row_to_dict(row) if row else None

    def list_history(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        username: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Vrne (vnosi, skupno število); username omeji na enega uporabnika."""
        where_sql = " WHERE username = ?" if username else ""
        params: list[Any] = [username] if username else []

        with self._lock:
            total = self._conn.execute(
                f"SELECT COUNT(*) AS n FROM validation_history{where_sql}", params
            ).fetchone()["n"]
            rows = self._conn.execute(
                f"SELECT * FROM validation_history{where_sql}"
                " ORDER BY created_at DESC LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
        return [self._history_row_to_dict(r) for r in rows], int(total)

    def delete_history_older_than(self, cutoff_iso: str) -> list[str]:
        """Izbriše stare vnose zgodovine; vrne job_id-je izbrisanih."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT job_id FROM validation_history WHERE created_at < ?",
                (cutoff_iso,),
            ).fetchall()
            ids = [r["job_id"] for r in rows]
            if ids:
                self._conn.execute(
                    "DELETE FROM validation_history WHERE created_at < ?",
                    (cutoff_iso,),
                )
                self._conn.commit()
        return ids

    @staticmethod
    def _history_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        for key, target in (("files_json", "files"), ("combined_json", "combined_reports"), ("config_json", "config")):
            try:
                d[target] = json.loads(d.pop(key) or "null")
            except (json.JSONDecodeError, TypeError):
                d[target] = None
        return d
