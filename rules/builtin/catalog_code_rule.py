"""Catalog code validation rule.

Validates that recipe codes exist in external catalog files:
- kemikalija: Ključ preverjanja
- raztopina: Param1 pri kontroliustreznostiraztopine; če je INDEX/MATCH,
  se šifre berejo iz ustreznega stolpca zavihka Podatki (vse velikosti)
- repro/reproodpis: Param1 pri kontroliustreznostirepro; enako INDEX/MATCH → Podatki
"""

from __future__ import annotations

import re
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from validator_oop.core.error import Severity
from validator_oop.excel.catalog_loader import (
    RECIPE_TIP_TO_CATALOG,
    REPRO_TIPS,
    CatalogData,
    extract_raztopina_catalog_code,
    extract_repro_catalog_code,
    match_key,
)
from validator_oop.rules import RuleContext, WorkbookRule, register
from validator_oop.utils import (
    base_key_no_trailing_number,
    coerce_str,
    norm_text,
    parse_index_match_formula,
)

VALIDATED_TYPES = frozenset(RECIPE_TIP_TO_CATALOG)
_PODATKI_NAME = "podatki"
_HEADER_FIRST_CELL = frozenset({"receptura", "recipe"})
_KLJUC_HEADER_RE = re.compile(r"^ključ\s*\d*$", re.I)
Param1Extractor = Callable[[Mapping[str, object]], tuple[str, str]]


def _context_extra(context: RuleContext) -> Mapping[str, Any]:
    extra: dict[str, Any] = dict(context.extra or {})
    if context.shared and getattr(context.shared, "extra", None):
        extra = {**context.shared.extra, **extra}
    return extra


def _find_sheet(
    workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
    wanted: str,
) -> str | None:
    target = wanted.casefold().strip()
    for name in workbook_data:
        if str(name).casefold().strip() == target:
            return name
    return None


def _control_param1(
    extractor: Param1Extractor,
    value_row: Mapping[str, object],
    formula_row: Mapping[str, object] | None = None,
) -> tuple[str, str]:
    if formula_row is not None:
        code, column = extractor(formula_row)
        if code:
            return code, column
    return extractor(value_row)


def _podatki_column_from_param1(param1: str) -> int | None:
    parsed = parse_index_match_formula(param1) if param1 else None
    if not parsed:
        return None
    index_sheet, col_num, _lookup = parsed
    if index_sheet.casefold().strip() == _PODATKI_NAME:
        return col_num
    return None


def _is_podatki_label_row(
    row: Mapping[str, object],
    first_key: str,
    col_key: str,
) -> bool:
    """True for Podatki name/number header rows (Excel rows 1–2 after parse)."""
    first = coerce_str(row.get(first_key, "")).strip()
    value = coerce_str(row.get(col_key, "")).strip()
    if not first and not value:
        return True
    if first.casefold() in _HEADER_FIRST_CELL:
        return True
    if _KLJUC_HEADER_RE.match(value):
        return True
    if first.isdigit() and (not value or value.isdigit()):
        return True
    return False


def _podatki_column_key(headers: Sequence[str], column_num: int) -> str | None:
    if column_num < 1:
        return None
    if column_num <= len(headers):
        return str(headers[column_num - 1])
    as_str = str(column_num)
    for header in headers:
        if str(header).strip() == as_str:
            return str(header)
    return as_str


@register
class CatalogCodeRule(WorkbookRule):
    """Validate recipe codes against external catalog codes.

    For kemikalija the value in "Ključ preverjanja" is checked.
    For raztopina the Param1 of kontrolaustreznostiraztopine is checked.
    For repro/reproodpis the Param1 of kontrolaustreznostirepro is checked.
    When Param1 is INDEX/MATCH into Podatki, every data row of that column
    is checked (all recipe sizes), not only the currently selected dropdown.
    If no catalog data is provided, the rule is silently skipped.
    """

    name = "catalog_code_rule"
    description = "Šifra raztopine/kemikalije/repro materiala mora obstajati v šifrantu."
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

    def evaluate_workbook(
        self,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        if not self._catalog_data:
            return []

        extra = _context_extra(context)
        all_data = extra.get("all_workbook_data") or workbook_data
        all_headers = extra.get("all_workbook_headers") or {}
        parsed_formulas = extra.get("parsed_formulas") or {}

        errors: list = []
        reported_bases: set[tuple[str, str]] = set()
        podatki_columns_raztopina: set[int] = set()
        podatki_columns_repro: set[int] = set()

        for sheet_name, rows in workbook_data.items():
            formula_rows = parsed_formulas.get(sheet_name)
            sheet_ctx = context.with_sheet(sheet_name)
            for idx, row in enumerate(rows):
                excel_row = idx + row_offset
                formula_row = None
                if formula_rows is not None and idx < len(formula_rows):
                    formula_row = formula_rows[idx]

                tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
                razt_param1, razt_p1_column = _control_param1(
                    extract_raztopina_catalog_code, row, formula_row
                )
                repro_param1, repro_p1_column = _control_param1(
                    extract_repro_catalog_code, row, formula_row
                )
                razt_col = _podatki_column_from_param1(razt_param1)
                repro_col = _podatki_column_from_param1(repro_param1)
                if razt_col is not None:
                    podatki_columns_raztopina.add(razt_col)
                if repro_col is not None:
                    podatki_columns_repro.add(repro_col)

                if tip_data not in VALIDATED_TYPES:
                    continue

                catalog_key = RECIPE_TIP_TO_CATALOG[tip_data]
                catalog = self._catalog_data.get(catalog_key)
                if catalog is None:
                    continue

                if tip_data in REPRO_TIPS:
                    sifra, error_column = self._sifra_from_param1(
                        repro_col is not None,
                        repro_param1,
                        repro_p1_column,
                        extract_repro_catalog_code(row),
                    )
                    if sifra is None:
                        continue
                elif tip_data == "raztopina":
                    sifra, error_column = self._sifra_from_param1(
                        razt_col is not None,
                        razt_param1,
                        razt_p1_column,
                        extract_raztopina_catalog_code(row),
                    )
                    if sifra is None:
                        continue
                else:
                    sifra = coerce_str(row.get("Ključ preverjanja", "")).strip()
                    error_column = "Ključ preverjanja"

                error = self._mismatch_error(
                    catalog,
                    sifra,
                    tip_data,
                    sheet_ctx.with_row(excel_row),
                    error_column,
                    reported_bases,
                )
                if error is not None:
                    errors.append(error)

        raztopina_catalog = self._catalog_data.get("raztopina")
        if raztopina_catalog and podatki_columns_raztopina:
            errors.extend(
                self._check_podatki_columns(
                    all_data,
                    all_headers,
                    podatki_columns_raztopina,
                    raztopina_catalog,
                    "raztopina",
                    context,
                    reported_bases,
                    row_offset=row_offset,
                )
            )
        repro_catalog = self._catalog_data.get("repro")
        if repro_catalog and podatki_columns_repro:
            errors.extend(
                self._check_podatki_columns(
                    all_data,
                    all_headers,
                    podatki_columns_repro,
                    repro_catalog,
                    "repro",
                    context,
                    reported_bases,
                    row_offset=row_offset,
                )
            )

        return errors

    @staticmethod
    def _sifra_from_param1(
        is_index: bool,
        param1: str,
        p1_column: str,
        computed: tuple[str, str],
    ) -> tuple[str | None, str]:
        """Literal Param1, or cached value when Param1 is INDEX/MATCH."""
        computed_sifra, computed_col = computed
        if is_index:
            if not computed_sifra or computed_sifra.startswith("="):
                return None, p1_column
            return computed_sifra, computed_col or p1_column
        if param1.startswith("="):
            return None, p1_column
        return param1, p1_column

    def _check_podatki_columns(
        self,
        all_data: Mapping[str, Sequence[Mapping[str, object]]],
        all_headers: Mapping[str, Sequence[str]],
        column_nums: set[int],
        catalog: CatalogData,
        tip_data: str,
        context: RuleContext,
        reported_bases: set[tuple[str, str]],
        *,
        row_offset: int,
    ) -> list:
        podatki_name = _find_sheet(all_data, _PODATKI_NAME)
        if not podatki_name:
            return []

        rows = all_data[podatki_name]
        headers = list(all_headers.get(podatki_name) or ())
        if not headers and rows:
            headers = [str(key) for key in rows[0].keys()]
        if not headers:
            return []

        first_key = str(headers[0])
        sheet_ctx = context.with_sheet(podatki_name)
        errors = []
        for column_num in sorted(column_nums):
            col_key = _podatki_column_key(headers, column_num)
            if not col_key:
                continue
            for idx, row in enumerate(rows):
                if _is_podatki_label_row(row, first_key, col_key):
                    continue
                sifra = coerce_str(row.get(col_key, "")).strip()
                error = self._mismatch_error(
                    catalog,
                    sifra,
                    tip_data,
                    sheet_ctx.with_row(idx + row_offset),
                    col_key,
                    reported_bases,
                )
                if error is not None:
                    errors.append(error)
        return errors

    def _mismatch_error(
        self,
        catalog: CatalogData,
        sifra: str,
        tip_data: str,
        row_ctx: RuleContext,
        error_column: str,
        reported_bases: set[tuple[str, str]],
    ):
        if not sifra:
            return None
        is_match, _matched_code, _method = match_key(sifra, catalog)
        if is_match:
            return None

        base_kljuc = base_key_no_trailing_number(sifra)
        dedupe_key = (tip_data, base_kljuc.casefold())
        if dedupe_key in reported_bases:
            return None
        reported_bases.add(dedupe_key)

        display = (
            base_kljuc
            if base_kljuc.casefold() != sifra.casefold()
            else sifra
        )
        return self.build_error(
            f"Šifra '{display}' (tip: {tip_data}) ni najdena v šifrantu.",
            context=row_ctx,
            column=error_column,
        )
