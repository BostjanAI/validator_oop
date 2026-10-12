"""Validacijski servis – tanka ovojnica okrog obstoječega ValidatorEngine.

Ne vsebuje validacijske logike. Za vsako naloženo recepturo:
1. zgradi ``ValidatorConfig`` iz uporabnikove konfiguracije,
2. konstruira ``ValidatorEngine`` (z opcijskim SOP in šifranti),
3. zažene ``validate()`` in pretvori rezultat v API obliko,
4. generira poročila (Excel, JSON, TXT, opcijsko auto-fix).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from validator_oop.core import RuleEngine, ValidatorConfig, ValidatorEngine
from validator_oop.core.constants import translate_code
from validator_oop.excel import ExcelLoader
from validator_oop.excel.report_writer import ReportWriter, WorkbookFixer
from validator_oop.rules import default_registry

from .rules_catalog import _ensure_registered
from .schemas import FileResult, Issue, ReportRef, ValidationConfigIn

try:
    from validator_oop.excel.catalog_loader import load_catalogs
except Exception:  # pragma: no cover
    load_catalogs = None  # type: ignore

try:
    from validator_oop.excel.sop_loader import SOPData
except Exception:  # pragma: no cover
    SOPData = None  # type: ignore


logger = logging.getLogger("mes_web.service")


def build_config(cfg: ValidationConfigIn) -> ValidatorConfig:
    """Pretvori uporabnikovo konfiguracijo v ``ValidatorConfig``."""
    return ValidatorConfig(
        bypass_rules=frozenset(cfg.bypass_rules),
        bypass_codes=frozenset(cfg.bypass_codes),
        strict_mode=cfg.strict_mode,
        include_formulas=cfg.include_formulas,
        bypass_zakleni_require_empty_for_checkbox=cfg.bypass_zakleni_require_empty_for_checkbox,
        bypass_zakleni_require_pogoj_for_param1_steps=cfg.bypass_zakleni_require_pogoj_for_param1_steps,
        bypass_zakleni_inverse_pogoj_requirement=cfg.bypass_zakleni_inverse_pogoj_requirement,
        enable_sop_validation=cfg.enable_sop_validation,
        enable_catalog_validation=cfg.enable_catalog_validation,
    )


def load_sop(sop_path: Path | None) -> Any | None:
    """Naloži SOP (.docx) če je podan in je modul na voljo."""
    if not sop_path or SOPData is None:
        return None
    try:
        return SOPData.from_word(sop_path, logger=logger)
    except Exception as exc:  # SOP je opcijski – ne ubijemo validacije
        logger.warning("SOP nalaganje ni uspelo (%s): %s", sop_path, exc)
        return None


def load_catalog_data(
    raztopine_path: Path | None,
    kemikalije_path: Path | None,
    repro_path: Path | None = None,
) -> tuple[dict[str, Any] | None, dict[str, str]]:
    """Naloži šifrante kemikalij/raztopin/repro materiala (vsi opcijski)."""
    catalog_paths: dict[str, str] = {}
    if load_catalogs is None or (not raztopine_path and not kemikalije_path and not repro_path):
        return None, catalog_paths
    try:
        data = load_catalogs(
            raztopine_path=raztopine_path,
            kemikalije_path=kemikalije_path,
            repro_path=repro_path,
        )
    except Exception as exc:
        logger.warning("Nalaganje šifrantov ni uspelo: %s", exc)
        return None, catalog_paths
    if raztopine_path:
        catalog_paths["raztopina"] = str(raztopine_path)
    if kemikalije_path:
        catalog_paths["kemikalija"] = str(kemikalije_path)
    if repro_path:
        catalog_paths["repro"] = str(repro_path)
    return data, catalog_paths


def _sheet_label(workbook_name: str, sheet_name: str) -> str:
    if workbook_name and sheet_name:
        return f"{workbook_name}:{sheet_name}"
    return sheet_name or workbook_name


def _issues_for_writer(report_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """Pretvori napake v format, ki ga pričakuje ReportWriter (kot v main.py)."""
    issues: list[dict[str, Any]] = []
    for e in report_dict.get("errors", []):
        sheet_label = _sheet_label(e.get("workbook", "") or "", e.get("sheet", "") or "")
        issue: dict[str, Any] = {
            "sheet": sheet_label,
            "row": e.get("row", ""),
            "col": e.get("col", ""),
            "code": e.get("code", ""),
            "message": e.get("message", ""),
            "severity": e.get("severity", "error"),
        }
        payload = e.get("payload") or {}
        # Prenos morebitnih auto-fix metapodatkov
        for key in ("target_cell", "proposed_value", "fix_kind"):
            if key in payload:
                issue[key] = payload[key]
        issues.append(issue)
    return issues


class ValidationService:
    """Validira posamezne recepture in generira poročila."""

    REPORT_LABELS = {
        "excel": "Excel poročilo (.xlsx)",
        "json": "JSON poročilo (.json)",
        "txt": "Besedilno poročilo (.txt)",
        "autofix": "Popravljena receptura (.xlsx)",
    }

    def __init__(self) -> None:
        _ensure_registered()

    def validate_file(
        self,
        *,
        index: int,
        recipe_path: Path,
        config: ValidationConfigIn,
        output_dir: Path,
        sop_data: Any | None = None,
        catalog_data: dict[str, Any] | None = None,
        catalog_paths: dict[str, str] | None = None,
    ) -> FileResult:
        """Validira eno recepturo in vrne strukturiran rezultat."""
        output_dir.mkdir(parents=True, exist_ok=True)
        validator_config = build_config(config)

        rule_engine = RuleEngine(default_registry, config=validator_config, logger=logger)
        engine = ValidatorEngine(
            rule_engine,
            ExcelLoader(),
            logger=logger,
            include_formulas=config.include_formulas,
            sop_data=sop_data if config.enable_sop_validation else None,
            catalog_data=catalog_data if config.enable_catalog_validation else None,
            catalog_paths=catalog_paths or {},
        )

        report = engine.validate(recipe_path)
        report_dict = report.to_dict()
        counts = {str(k): int(v) for k, v in report_dict.get("counts", {}).items()}
        counts_by_code = {str(k): int(v) for k, v in report_dict.get("counts_by_code", {}).items()}
        catalog_summary = report.metadata.get("catalog_validation")

        issues_writer = _issues_for_writer(report_dict)
        ui_issues, counts_by_sheet = self._build_ui_issues(report_dict, recipe_path.name)

        reports = self._write_reports(
            recipe_path=recipe_path,
            output_dir=output_dir,
            report_dict=report_dict,
            issues_writer=issues_writer,
            catalog_summary=catalog_summary if isinstance(catalog_summary, dict) else None,
            apply_fixes=config.apply_fixes,
        )

        return FileResult(
            index=index,
            filename=recipe_path.name,
            is_valid=bool(report_dict.get("is_valid", False)),
            counts=counts,
            counts_by_code=counts_by_code,
            counts_by_sheet=counts_by_sheet,
            catalog_validation=catalog_summary if isinstance(catalog_summary, dict) else None,
            issues=ui_issues,
            reports=reports,
        )

    def validate_db_recipe(
        self,
        *,
        index: int,
        recipe_id: int,
        config: ValidationConfigIn,
        output_dir: Path,
        save_results: bool = False,
    ) -> FileResult:
        """Validira recepturo neposredno iz MES MySQL baze.

        Vir podatkov je ``MySQLLoader`` (vrne ``LoadedWorkbook``), validacija
        in poročila pa tečejo skozi isto infrastrukturo kot pri Excel viru.
        SOP/šifranti in auto-fix pri DB viru niso podprti (ni datoteke).
        """
        # Lazy import: db paket je opcijski (MySQL driver ni osnovna odvisnost)
        from validator_oop.db import DBConfig, MySQLLoader, MySQLReportWriter, load_mapping

        output_dir.mkdir(parents=True, exist_ok=True)
        validator_config = build_config(config)

        db_config = DBConfig.from_env()
        mapping = load_mapping(db_config.mapping_file)
        loader = MySQLLoader(db_config, mapping, logger_=logger)
        loaded = loader.load_recipe(recipe_id)

        rule_engine = RuleEngine(default_registry, config=validator_config, logger=logger)
        engine = ValidatorEngine(rule_engine, ExcelLoader(), logger=logger)
        report = engine.validate_loaded(loaded)
        report_dict = report.to_dict()

        db_run_id: int | None = None
        if save_results:
            writer = MySQLReportWriter(db_config, logger_=logger)
            db_run_id = writer.save(
                report,
                recipe_id=recipe_id,
                config=validator_config,
            )

        counts = {str(k): int(v) for k, v in report_dict.get("counts", {}).items()}
        counts_by_code = {str(k): int(v) for k, v in report_dict.get("counts_by_code", {}).items()}
        issues_writer = _issues_for_writer(report_dict)

        filename = f"MES_receptura_{recipe_id}"
        ui_issues, counts_by_sheet = self._build_ui_issues(report_dict, filename)

        reports = self._write_reports(
            recipe_path=output_dir / f"{filename}.xlsx",  # samo za poimenovanje poročil
            output_dir=output_dir,
            report_dict=report_dict,
            issues_writer=issues_writer,
            catalog_summary=None,
            apply_fixes=False,  # auto-fix zahteva izvorno Excel datoteko
        )

        return FileResult(
            index=index,
            filename=filename,
            is_valid=bool(report_dict.get("is_valid", False)),
            counts=counts,
            counts_by_code=counts_by_code,
            counts_by_sheet=counts_by_sheet,
            issues=ui_issues,
            reports=reports,
            db_run_id=db_run_id,
        )

    def _build_ui_issues(
        self, report_dict: dict[str, Any], workbook_name: str
    ) -> tuple[list[Issue], dict[str, int]]:
        ui_issues: list[Issue] = []
        counts_by_sheet: dict[str, int] = {}
        for e in report_dict.get("errors", []):
            sheet = e.get("sheet", "") or "(neznano)"
            counts_by_sheet[sheet] = counts_by_sheet.get(sheet, 0) + 1
            code = e.get("code", "") or ""
            ui_issues.append(
                Issue(
                    file=workbook_name,
                    sheet=sheet,
                    row=e.get("row"),
                    col=e.get("col"),
                    code=code,
                    code_desc=translate_code(code) if code else "",
                    severity=str(e.get("severity", "error")),
                    rule=e.get("rule", "") or "",
                    message=e.get("message", "") or "",
                )
            )
        return ui_issues, counts_by_sheet

    def _write_reports(
        self,
        *,
        recipe_path: Path,
        output_dir: Path,
        report_dict: dict[str, Any],
        issues_writer: list[dict[str, Any]],
        catalog_summary: dict[str, Any] | None,
        apply_fixes: bool,
    ) -> list[ReportRef]:
        stem = recipe_path.stem
        writer = ReportWriter(logger=logger)
        refs: list[ReportRef] = []

        # Excel
        excel_path = output_dir / f"{stem}_porocilo.xlsx"
        try:
            writer.write_excel_report(excel_path, issues_writer, catalog_summary=catalog_summary)
            refs.append(ReportRef(kind="excel", label=self.REPORT_LABELS["excel"], filename=excel_path.name))
        except Exception as exc:
            logger.warning("Excel poročilo ni uspelo: %s", exc)

        # JSON
        json_path = output_dir / f"{stem}_porocilo.json"
        try:
            json_path.write_text(
                json.dumps(report_dict, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            refs.append(ReportRef(kind="json", label=self.REPORT_LABELS["json"], filename=json_path.name))
        except Exception as exc:
            logger.warning("JSON poročilo ni uspelo: %s", exc)

        # TXT
        txt_path = output_dir / f"{stem}_porocilo.txt"
        try:
            writer.write_text_report(txt_path, issues_writer, catalog_summary=catalog_summary)
            refs.append(ReportRef(kind="txt", label=self.REPORT_LABELS["txt"], filename=txt_path.name))
        except Exception as exc:
            logger.warning("TXT poročilo ni uspelo: %s", exc)

        # Auto-fix (opcijsko)
        if apply_fixes:
            fix_path = output_dir / f"{stem}_AUTOFIX.xlsx"
            try:
                n = WorkbookFixer(logger=logger).apply_fixes(recipe_path, fix_path, issues_writer)
                logger.info("Auto-fix: uveljavljenih %d popravkov", n)
                refs.append(
                    ReportRef(kind="autofix", label=self.REPORT_LABELS["autofix"], filename=fix_path.name)
                )
            except Exception as exc:
                logger.warning("Auto-fix ni uspel: %s", exc)

        return refs

    def write_combined_reports(
        self, output_dir: Path, results: list[FileResult]
    ) -> list[ReportRef]:
        """Zapiše skupna poročila za celoten batch (več receptur v enem jobu).

        Napake vseh datotek se združijo, list pa se označi kot
        ``datoteka:list``, da je izvor jasen tudi v skupnem poročilu.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        issues_writer: list[dict[str, Any]] = []
        for fr in results:
            for iss in fr.issues:
                issues_writer.append(
                    {
                        "sheet": _sheet_label(fr.filename, iss.sheet),
                        "row": iss.row if iss.row is not None else "",
                        "col": iss.col if iss.col is not None else "",
                        "code": iss.code,
                        "message": iss.message,
                        "severity": iss.severity,
                    }
                )

        writer = ReportWriter(logger=logger)
        refs: list[ReportRef] = []
        stem = "skupno_porocilo"

        excel_path = output_dir / f"{stem}.xlsx"
        try:
            writer.write_excel_report(excel_path, issues_writer)
            refs.append(ReportRef(kind="excel", label="Skupno Excel poročilo (.xlsx)", filename=excel_path.name))
        except Exception as exc:
            logger.warning("Skupno Excel poročilo ni uspelo: %s", exc)

        json_path = output_dir / f"{stem}.json"
        try:
            payload = {
                "files": [
                    {"filename": fr.filename, "is_valid": fr.is_valid, "counts": fr.counts}
                    for fr in results
                ],
                "issues": issues_writer,
            }
            json_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            refs.append(ReportRef(kind="json", label="Skupno JSON poročilo (.json)", filename=json_path.name))
        except Exception as exc:
            logger.warning("Skupno JSON poročilo ni uspelo: %s", exc)

        txt_path = output_dir / f"{stem}.txt"
        try:
            writer.write_text_report(txt_path, issues_writer)
            refs.append(ReportRef(kind="txt", label="Skupno TXT poročilo (.txt)", filename=txt_path.name))
        except Exception as exc:
            logger.warning("Skupno TXT poročilo ni uspelo: %s", exc)

        return refs
