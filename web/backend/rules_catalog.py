"""Katalog razpoložljivih pravil in error kod za konfiguracijski UI.

Bere obstoječi register pravil (``default_registry``) in prevode kod iz
``core/constants.py``. Ne definira nobene validacijske logike.
"""

from __future__ import annotations

import functools

from validator_oop.core.constants import CODE_TRANSLATIONS
from validator_oop.rules import default_registry
from validator_oop.rules.base_rule import RowRule, SheetRule, WorkbookRule
from validator_oop.rules.builtin import register_all

from .schemas import CodeInfo, RuleInfo, RulesCatalog

try:
    from validator_oop.core.constants import VERSION_REPORT as _VERSION
except Exception:  # pragma: no cover
    _VERSION = "?"


def _rule_type(rule_cls: type) -> str:
    if issubclass(rule_cls, WorkbookRule):
        return "workbook"
    if issubclass(rule_cls, SheetRule):
        return "sheet"
    if issubclass(rule_cls, RowRule):
        return "row"
    return "rule"


def _short_doc(rule_cls: type) -> str:
    doc = (rule_cls.__doc__ or "").strip()
    if not doc:
        return ""
    return doc.splitlines()[0].strip()


@functools.lru_cache(maxsize=1)
def get_rules_catalog() -> RulesCatalog:
    """Zgradi katalog pravil + kod (z lru predpomnilnikom).

    Pokliče ``register_all()`` (idempotentno – pravila so že registrirana,
    a klic je varen, ker preskoči ponovno registracijo prek izjeme).
    """
    _ensure_registered()

    rules: list[RuleInfo] = []
    for rule_cls in default_registry.all():
        severity = getattr(rule_cls, "severity", None)
        severity_val = getattr(severity, "value", str(severity)) if severity else "error"
        rules.append(
            RuleInfo(
                name=getattr(rule_cls, "name", rule_cls.__name__) or rule_cls.__name__,
                code=getattr(rule_cls, "code", "") or "",
                severity=severity_val,
                priority=int(getattr(rule_cls, "priority", 100) or 100),
                type=_rule_type(rule_cls),
                description=_short_doc(rule_cls),
            )
        )
    rules.sort(key=lambda r: (r.priority, r.name))

    codes = [
        CodeInfo(code=code, description=desc)
        for code, desc in sorted(CODE_TRANSLATIONS.items())
    ]

    return RulesCatalog(rules=rules, codes=codes, version=str(_VERSION))


def _ensure_registered() -> None:
    """Zagotovi, da so vgrajena pravila registrirana (idempotentno)."""
    if default_registry.count() > 0:
        return
    try:
        register_all()
    except ValueError:
        # Pravila so že registrirana (dvojna registracija) – varno ignoriramo.
        pass
