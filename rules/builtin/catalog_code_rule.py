"""Catalog code validation rule.

Validates that recipe keys (Ključ preverjanja) for rows of type
"raztopina" or "kemikalija" exist in the corresponding external
catalog files (Izvoz_sifre_razt.xlsx / Izvoz_kem.xlsx).
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional, Sequence

from validator_oop.core.error import Severity
from validator_oop.excel.catalog_loader import CatalogData, match_key
from validator_oop.rules import RuleContext, SheetRule, register
from validator_oop.utils import base_key_no_trailing_number, coerce_str, norm_text

VALIDATED_TYPES = frozenset({"raztopina", "kemikalija"})


@register
class CatalogCodeRule(SheetRule):
    """Validate recipe keys against external catalog codes.

    For each row where "Tip podatka" is "raztopina" or "kemikalija",
    checks that the "Ključ preverjanja" value exists in the corresponding
    catalog. If no catalog data is provided, the rule is silently skipped.
    """

    name = "catalog_code_rule"
    description = "Šifra raztopine/kemikalije mora obstajati v šifrantu."
    code = "CATALOG_CODE_MISMATCH"
    priority = 150
    severity = Severity.ERROR

    def __init__(
        self,
        catalog_data: Optional[dict[str, CatalogData]] = None,
        *,
        logger=None,
    ):
        super().__init__(logger=logger)
        self._catalog_data = catalog_data

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        if not self._catalog_data:
            return []

        errors = []
        reported_bases: set[tuple[str, str]] = set()
        for idx, row in enumerate(rows):
            excel_row = idx + row_offset
            tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
            if tip_data not in VALIDATED_TYPES:
                continue

            kljuc = coerce_str(row.get("Ključ preverjanja", "")).strip()
            if not kljuc:
                continue

            catalog = self._catalog_data.get(tip_data)
            if catalog is None:
                continue

            is_match, _matched_code, _method = match_key(kljuc, catalog)
            if is_match:
                continue

            base_kljuc = base_key_no_trailing_number(kljuc)
            dedupe_key = (tip_data, base_kljuc.casefold())
            if dedupe_key in reported_bases:
                continue
            reported_bases.add(dedupe_key)

            display = (
                base_kljuc
                if base_kljuc.casefold() != kljuc.casefold()
                else kljuc
            )
            row_ctx = context.with_row(excel_row)
            errors.append(
                self.build_error(
                    f"Šifra '{display}' (tip: {tip_data}) ni najdena v šifrantu.",
                    context=row_ctx,
                    column="Ključ preverjanja",
                )
            )

        return errors
