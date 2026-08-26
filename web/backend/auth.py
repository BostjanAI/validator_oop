"""Avtentikacija in avtorizacija (faza 2): AD/LDAP + lokalni fallback.

Načini (``MES_WEB_AUTH_MODE``):
- ``ldap``  – samo AD/LDAP (potrebuje paket ``ldap3`` in ``MES_WEB_LDAP_*``),
- ``local`` – samo lokalni uporabniki (JSON datoteka ali dev env),
- ``mixed`` – najprej LDAP, ob neuspehu lokalni uporabniki (privzeto).

Role: ``tehnolog`` < ``qa`` < ``admin``.

Seje so strežniške (žeton v SQLite + HttpOnly piškotek ``mes_session``);
brez zunanjih odvisnosti (JWT ni potreben za intranet).
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .db import Database
from .settings import Settings

logger = logging.getLogger("mes_web.auth")

try:  # pragma: no cover - opcijska odvisnost (samo za AD/LDAP)
    import ldap3  # type: ignore
except ImportError:  # pragma: no cover
    ldap3 = None  # type: ignore

SESSION_COOKIE = "mes_session"

ROLES = ("tehnolog", "qa", "admin")
_ROLE_RANK = {"tehnolog": 0, "qa": 1, "admin": 2}

ROLE_LABELS = {
    "tehnolog": "Tehnolog",
    "qa": "QA",
    "admin": "Administrator",
}

_PBKDF2_ITERATIONS = 240_000


@dataclass(slots=True)
class User:
    """Prijavljen uporabnik (iz seje)."""

    username: str
    display_name: str
    role: str
    source: str = "local"  # "ldap" | "local" | "dev" | "none" (auth izklopljen)

    def has_role(self, minimum: str) -> bool:
        """Ali ima uporabnik vsaj zahtevano rolo (tehnolog < qa < admin)."""
        return _ROLE_RANK.get(self.role, -1) >= _ROLE_RANK.get(minimum, 99)

    def to_dict(self) -> dict[str, str]:
        return {
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role,
            "role_label": ROLE_LABELS.get(self.role, self.role),
            "source": self.source,
        }


ANONYMOUS_USER = User(
    username="anonimno",
    display_name="Anonimni uporabnik (avtentikacija izklopljena)",
    role="admin",
    source="none",
)


# ----------------------------------------------------------------- gesla

def hash_password(password: str, *, iterations: int = _PBKDF2_ITERATIONS) -> str:
    """Vrne PBKDF2-SHA256 hash v obliki ``pbkdf2_sha256$iter$salt$hash``."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Preveri geslo proti shranjenemu hashu (podprt tudi ``plain$`` za dev)."""
    if stored.startswith("plain$"):
        return secrets.compare_digest(stored[len("plain$"):], password)
    try:
        scheme, iterations_s, salt, digest = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        computed = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations_s)
        ).hex()
        return secrets.compare_digest(computed, digest)
    except (ValueError, TypeError):
        return False


# ------------------------------------------------------------- lokalni users

def _load_local_users(settings: Settings) -> dict[str, dict[str, str]]:
    """Naloži lokalne uporabnike iz JSON datoteke in/ali dev env spremenljivke.

    Oblika datoteke::

        {
          "mnovak": {
            "password_hash": "pbkdf2_sha256$...",
            "role": "tehnolog",
            "display_name": "Miha Novak"
          }
        }

    Dev env (``MES_WEB_DEV_USERS``): ``uporabnik:geslo:rola,...``
    """
    users: dict[str, dict[str, str]] = {}

    if settings.local_users_file:
        path = Path(settings.local_users_file)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for username, info in data.items():
                if not isinstance(info, dict) or "password_hash" not in info:
                    continue
                role = str(info.get("role", "tehnolog"))
                if role not in ROLES:
                    logger.warning("Lokalni uporabnik %s ima neznano rolo '%s' – preskočen.", username, role)
                    continue
                users[str(username)] = {
                    "password_hash": str(info["password_hash"]),
                    "role": role,
                    "display_name": str(info.get("display_name", username)),
                }
        except FileNotFoundError:
            logger.warning("Datoteka lokalnih uporabnikov ne obstaja: %s", path)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Napaka pri branju lokalnih uporabnikov (%s): %s", path, exc)

    if settings.dev_users:
        for entry in settings.dev_users.split(","):
            parts = entry.strip().split(":")
            if len(parts) != 3:
                continue
            username, password, role = (p.strip() for p in parts)
            if role not in ROLES:
                logger.warning("Dev uporabnik %s ima neznano rolo '%s' – preskočen.", username, role)
                continue
            users[username] = {
                "password_hash": f"plain${password}",
                "role": role,
                "display_name": username,
            }

    return users


# ------------------------------------------------------------------ LDAP

def ldap_authenticate(username: str, password: str, settings: Settings) -> User | None:
    """Poskusi prijavo proti AD/LDAP; vrne User ali None.

    Bind se izvede z uporabnikovimi poverilnicami (predloga
    ``MES_WEB_LDAP_USER_DN``), rola pa se določi iz članstva v AD skupinah
    (``memberOf``) po nastavitvah ``MES_WEB_LDAP_GROUP_*``.
    """
    if not settings.ldap_server:
        return None
    if ldap3 is None:
        logger.error("Paket 'ldap3' ni nameščen – AD/LDAP prijava ni mogoča.")
        return None
    if not password:
        return None  # anonimni bind bi sicer lahko "uspel"

    user_dn = settings.ldap_user_dn_template.format(username=username)
    try:
        server = ldap3.Server(
            settings.ldap_server,
            use_ssl=settings.ldap_use_ssl,
            get_info=ldap3.NONE,
            connect_timeout=5,
        )
        conn = ldap3.Connection(
            server,
            user=user_dn,
            password=password,
            authentication=ldap3.SIMPLE,
            receive_timeout=10,
        )
        if not conn.bind():
            logger.info("LDAP prijava zavrnjena za '%s'.", username)
            return None
    except Exception as exc:  # ldap3 meče različne izjeme (LDAPException, socket…)
        logger.error("LDAP napaka pri prijavi '%s': %s", username, exc)
        return None

    display_name = username
    groups: list[str] = []
    try:
        if settings.ldap_base_dn:
            conn.search(
                search_base=settings.ldap_base_dn,
                search_filter=f"(&(objectClass=user)(sAMAccountName={_ldap_escape(username)}))",
                attributes=["memberOf", "displayName", "cn"],
            )
            if conn.entries:
                entry = conn.entries[0]
                display_name = (
                    str(entry.displayName) if "displayName" in entry else str(entry.cn)
                ) or username
                if "memberOf" in entry:
                    groups = [str(g).lower() for g in entry.memberOf.values]
    except Exception as exc:
        logger.warning("LDAP iskanje podatkov o '%s' ni uspelo: %s", username, exc)
    finally:
        try:
            conn.unbind()
        except Exception:
            pass

    role = _role_from_groups(groups, settings)
    if role is None:
        logger.info("Uporabnik '%s' ni v nobeni dovoljeni AD skupini.", username)
        return None

    return User(username=username, display_name=display_name, role=role, source="ldap")


def _ldap_escape(value: str) -> str:
    """Uide posebne znake v LDAP filtru (RFC 4515)."""
    out = []
    for ch in value:
        if ch in "\\*()\0":
            out.append(f"\\{ord(ch):02x}")
        else:
            out.append(ch)
    return "".join(out)


def _role_from_groups(groups: list[str], settings: Settings) -> str | None:
    """Določi rolo iz članstva v AD skupinah (najvišja zmaga)."""
    mapping = (
        ("admin", settings.ldap_group_admin),
        ("qa", settings.ldap_group_qa),
        ("tehnolog", settings.ldap_group_tehnolog),
    )
    for role, group_needle in mapping:
        needle = group_needle.strip().lower()
        if needle and any(needle in g for g in groups):
            return role
    return settings.ldap_default_role if settings.ldap_default_role in ROLES else None


# ---------------------------------------------------------------- manager

class AuthManager:
    """Prijava/odjava + upravljanje sej (žetoni v SQLite)."""

    def __init__(self, settings: Settings, db: Database) -> None:
        self._settings = settings
        self._db = db
        self._local_users = _load_local_users(settings)
        if settings.auth_enabled and settings.auth_mode in {"local", "mixed"} and not self._local_users:
            logger.warning(
                "Avtentikacija je vklopljena (%s), a ni lokalnih uporabnikov "
                "(MES_WEB_LOCAL_USERS_FILE / MES_WEB_DEV_USERS).",
                settings.auth_mode,
            )

    @property
    def enabled(self) -> bool:
        return self._settings.auth_enabled

    def authenticate(self, username: str, password: str) -> User | None:
        """Preveri poverilnice glede na auth_mode; vrne User ali None."""
        username = username.strip()
        if not username or not password:
            return None

        mode = self._settings.auth_mode
        if mode in {"ldap", "mixed"}:
            user = ldap_authenticate(username, password, self._settings)
            if user is not None:
                return user
            if mode == "ldap":
                return None

        info = self._local_users.get(username)
        if info and verify_password(password, info["password_hash"]):
            source = "dev" if info["password_hash"].startswith("plain$") else "local"
            return User(
                username=username,
                display_name=info["display_name"],
                role=info["role"],
                source=source,
            )
        return None

    def login(self, username: str, password: str) -> tuple[User, str] | None:
        """Prijava; ob uspehu vrne (uporabnik, žeton seje)."""
        user = self.authenticate(username, password)
        if user is None:
            return None

        self._db.purge_expired_sessions()
        self._db.upsert_user(user.username, user.display_name, user.role, user.source)

        token = secrets.token_urlsafe(32)
        self._db.create_session(
            token,
            user.username,
            user.display_name,
            user.role,
            user.source,
            ttl_seconds=max(60, self._settings.session_ttl_minutes * 60),
        )
        return user, token

    def logout(self, token: str) -> None:
        self._db.delete_session(token)

    def user_from_token(self, token: str | None) -> User | None:
        if not token:
            return None
        session = self._db.get_session(token)
        if session is None:
            return None
        return User(
            username=session["username"],
            display_name=session["display_name"],
            role=session["role"],
            source=session["source"],
        )


def generate_local_user_entry(username: str, password: str, role: str, display_name: str = "") -> dict[str, Any]:
    """Pomožna funkcija za pripravo vnosa v JSON datoteko lokalnih uporabnikov.

    Uporaba (npr. v Python konzoli)::

        from validator_oop.web.backend.auth import generate_local_user_entry
        print(generate_local_user_entry("mnovak", "geslo123", "qa", "Miha Novak"))
    """
    if role not in ROLES:
        raise ValueError(f"Neznana rola '{role}'. Dovoljene: {', '.join(ROLES)}")
    return {
        username: {
            "password_hash": hash_password(password),
            "role": role,
            "display_name": display_name or username,
        }
    }
