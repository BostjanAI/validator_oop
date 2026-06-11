"""Main entry point for the MES Excel Validator.

This module provides a CLI interface for validating Excel workbooks.

Usage:
    python -m validator_oop                              # Launch GUI
    python -m validator_oop path/to/workbook.xlsx        # CLI validation
    python -m validator_oop path/to/workbook.xlsx --output report.json
    python -m validator_oop path/to/workbook.xlsx --verbose
    python -m validator_oop path/to/workbook.xlsx --apply-fixes
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

# Add project root to Python path for direct execution (when running as script, not as module)
# This allows running main.py directly with "Run" button in VS Code, just like MES_validator.py
# Check if running as script (not as module) by checking if __package__ is None
if __package__ is None:
    # Get the project root (parent of validator_oop directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    # Add to path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from validator_oop.core import RuleEngine, ValidatorConfig, ValidatorEngine
from validator_oop.excel import ExcelLoader
from validator_oop.excel.report_writer import ReportWriter, WorkbookFixer
from validator_oop.rules import default_registry
from validator_oop.rules.builtin import register_all
from validator_oop.utils.logger import setup_logger
from validator_oop.utils.validation_progress import record_run as record_validation_progress


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments (default: sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="validator_oop",
        description="MES Excel Validator - Validate MES Excel workbooks",
    )

    parser.add_argument(
        "workbook",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the Excel workbook to validate (omit to launch GUI)",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output file for validation report (JSON format)",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    parser.add_argument(
        "--bypass",
        type=str,
        nargs="*",
        default=[],
        help="Rule names or codes to bypass",
    )

    parser.add_argument(
        "--include-formulas",
        action="store_true",
        help="Load and validate cell formulas",
    )

    parser.add_argument(
        "--format",
        choices=["json", "text", "summary", "excel"],
        default="excel",  # Default to Excel format (matching MES_validator.py behavior)
        help="Output format (default: excel)",
    )

    parser.add_argument(
        "--apply-fixes",
        action="store_true",
        help="Apply proposed fixes to a copy of the workbook",
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch GUI mode",
    )

    parser.add_argument(
        "--gui-style",
        choices=["classic", "themed", "qt"],
        default="classic",
        help="GUI style: 'classic' (default), 'themed' (black/yellow) or 'qt' (PyQt6). Used when launching GUI.",
    )

    parser.add_argument(
        "--catalog-raztopine",
        type=Path,
        default=None,
        help="Excel šifrant raztopin (Izvoz_sifre_razt.xlsx) za preverjanje šifer",
    )

    parser.add_argument(
        "--catalog-kemikalije",
        type=Path,
        default=None,
        help="Excel šifrant kemikalij (Izvoz_kem.xlsx) za preverjanje šifer",
    )

    return parser.parse_args(args)


def format_report_text(report: Mapping[str, Any]) -> str:
    """Format a report as human-readable text.

    Args:
        report: Report dictionary.

    Returns:
        Formatted text string.
    """
    lines: list[str] = []

    lines.append(f"Validation Report: {report['source_path']}")
    lines.append("=" * 60)

    counts = report.get("counts", {})
    lines.append(f"Errors: {counts.get('error', 0)}")
    lines.append(f"Warnings: {counts.get('warning', 0)}")
    lines.append(f"Info: {counts.get('info', 0)}")
    lines.append("")

    if report.get("is_valid"):
        lines.append("✓ Workbook is valid")
    else:
        lines.append("✗ Workbook has validation errors")

    lines.append("")

    for error in report.get("errors", []):
        severity = error.get("severity", "ERROR").upper()
        code = error.get("code", "")
        message = error.get("message", "")
        sheet = error.get("sheet", "")
        row = error.get("row", "")
        col = error.get("col", "")

        location = ""
        if sheet:
            location = f"[{sheet}"
            if row:
                location += f":{row}"
            if col:
                location += f":{col}"
            location += "] "

        lines.append(f"  {severity} {code}: {location}{message}")

    return "\n".join(lines)


def format_report_summary(report: Mapping[str, Any]) -> str:
    """Format a report as a brief summary.

    Args:
        report: Report dictionary.

    Returns:
        Summary text string.
    """
    counts = report.get("counts", {})
    status = "VALID" if report.get("is_valid") else "INVALID"

    return (
        f"{status}: {counts.get('error', 0)} errors, "
        f"{counts.get('warning', 0)} warnings, "
        f"{counts.get('info', 0)} info"
    )


def main(args: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        args: Command-line arguments (default: sys.argv[1:]).

    Returns:
        Exit code (0 = success, 1 = validation errors, 2 = runtime error).
    """
    import logging
    import traceback
    
    # Setup file logging for exe debugging (always enabled)
    log_file = Path.home() / "MESValidator.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Get root logger and add file handler
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("MESValidator started")
    logger.info("Python version: %s", sys.version)
    logger.info("Executable: %s", sys.executable)
    
    # CRITICAL: Explicitly import all rule modules before registering
    # This ensures PyInstaller includes them in the exe
    try:
        logger.info("Importing rule modules...")
        import validator_oop.rules.builtin.structural
        import validator_oop.rules.builtin.field
        import validator_oop.rules.builtin.relational
        import validator_oop.rules.builtin.control
        import validator_oop.rules.builtin.catalog_code_rule
        logger.info("Rule modules imported successfully")
    except ImportError as e:
        logger.error("CRITICAL: Failed to import rule modules: %s", e, exc_info=True)
        print(f"CRITICAL: Failed to import rule modules: {e}", file=sys.stderr)
        traceback.print_exc()
        return 2
    
    parsed = parse_args(args)

    # Launch GUI if no workbook specified or --gui flag used
    if parsed.workbook is None or parsed.gui:
        try:
            from validator_oop.ui import run_gui

            return run_gui(gui_style=parsed.gui_style)
        except ImportError:
            print(
                "Error: GUI requires tkinter. "
                "Please provide a workbook path for CLI mode.",
                file=sys.stderr,
            )
            return 2

    # Setup logging (additional console handler)
    log_level = 10 if parsed.verbose else 20  # DEBUG or INFO
    logger = setup_logger("validator", log_level)
    # Also add file handler to the validator logger
    logger.addHandler(file_handler)

    # Check workbook exists
    if not parsed.workbook.exists():
        logger.error("Workbook not found: %s", parsed.workbook)
        return 2

    try:
        # Register built-in rules
        logger.info("Registering built-in rules...")
        rule_count = register_all()
        total_rules = default_registry.count()
        logger.info("Registered %d built-in rules (total: %d)", rule_count, total_rules)
        
        if rule_count == 0:
            logger.warning("WARNING: No rules were registered! This may indicate a problem.")
            print("WARNING: No rules were registered!", file=sys.stderr)

        # Create configuration
        config = ValidatorConfig(
            bypass_rules=frozenset(parsed.bypass),
            strict_mode=parsed.strict,
            include_formulas=parsed.include_formulas,
            catalog_raztopine_path=parsed.catalog_raztopine,
            catalog_kemikalije_path=parsed.catalog_kemikalije,
        )

        catalog_data = None
        catalog_paths: dict[str, str] = {}
        if config.enable_catalog_validation and (
            config.catalog_raztopine_path or config.catalog_kemikalije_path
        ):
            from validator_oop.excel.catalog_loader import load_catalogs

            catalog_data = load_catalogs(
                raztopine_path=config.catalog_raztopine_path,
                kemikalije_path=config.catalog_kemikalije_path,
            )
            if config.catalog_raztopine_path:
                catalog_paths["raztopina"] = str(config.catalog_raztopine_path)
            if config.catalog_kemikalije_path:
                catalog_paths["kemikalija"] = str(config.catalog_kemikalije_path)
            if catalog_data:
                logger.info("Catalogs loaded for validation: %s", ", ".join(catalog_data))

        # Create engines
        loader = ExcelLoader()
        rule_engine = RuleEngine(default_registry, config=config, logger=logger)
        validator = ValidatorEngine(
            rule_engine,
            loader,
            logger=logger,
            include_formulas=parsed.include_formulas,
            catalog_data=catalog_data,
            catalog_paths=catalog_paths,
        )

        # Run validation
        logger.info("Validating %s", parsed.workbook)
        report = validator.validate(parsed.workbook)
        report_dict = report.to_dict()

        cat_summary = report.metadata.get("catalog_validation")
        if cat_summary and cat_summary.get("enabled"):
            from validator_oop.excel.catalog_loader import format_catalog_summary_log_line

            print(format_catalog_summary_log_line(cat_summary))

        # Zapiši v napredek (delež pregledanih, število napak)
        counts = report_dict.get("counts", {})
        try:
            record_validation_progress(
                parsed.workbook,
                counts.get("error", 0),
                counts.get("warning", 0),
            )
        except OSError:
            pass

        # Convert errors to issue format for report writer (matching MES_validator.py format)
        issues = []
        for e in report_dict.get("errors", []):
            sheet_name = e.get("sheet", "")
            workbook_name = e.get("workbook", "")
            if workbook_name and sheet_name:
                sheet_label = f"{workbook_name}:{sheet_name}"
            else:
                sheet_label = sheet_name or workbook_name
            issues.append(
                {
                    "sheet": sheet_label,
                    "row": e.get("row", ""),
                    "col": e.get("col", ""),
                    "code": e.get("code", ""),
                    "message": e.get("message", ""),
                    "severity": e.get("severity", "ERROR"),
                }
            )

        # Determine output path (matching MES_validator.py behavior)
        if parsed.output:
            output_path = parsed.output
        elif parsed.format == "excel":
            # Default Excel report path (matching MES_validator.py)
            output_path = parsed.workbook.with_name(
                parsed.workbook.stem + "_VALIDATION_REPORT.xlsx"
            )
        else:
            output_path = None

        # Write report to file
        if output_path:
            if parsed.format == "excel" or (output_path and output_path.suffix.lower() == ".xlsx"):
                report_writer = ReportWriter(logger=logger)
                report_writer.write_excel_report(
                    output_path,
                    issues,
                    catalog_summary=cat_summary if isinstance(cat_summary, dict) else None,
                )
                logger.info("Report written to %s", output_path)
            elif parsed.format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report_dict, f, indent=2, ensure_ascii=False)
                logger.info("Report written to %s", output_path)
            else:  # text format
                report_writer = ReportWriter(logger=logger)
                report_writer.write_text_report(
                    output_path,
                    issues,
                    catalog_summary=cat_summary if isinstance(cat_summary, dict) else None,
                )
                logger.info("Report written to %s", output_path)

        # Apply fixes if requested
        if parsed.apply_fixes:
            fixer = WorkbookFixer(logger=logger)
            out_fix = parsed.workbook.with_name(
                parsed.workbook.stem + "_AUTOFIX.xlsx"
            )
            n = fixer.apply_fixes(parsed.workbook, out_fix, issues)
            logger.info("Applied %d fixes to %s", n, out_fix)
            print(f"Uveljavljenih popravkov: {n} → {out_fix}")

        # Print output based on format
        if parsed.format == "json":
            print(json.dumps(report_dict, indent=2, ensure_ascii=False))
        elif parsed.format == "summary":
            print(format_report_summary(report_dict))
        elif parsed.format == "excel":
            if output_path:
                # Use ASCII-safe message to avoid Windows console encoding issues
                print(f"Koncano. Porocilo: {output_path}")
            else:
                print(format_report_summary(report_dict))
        else:  # text format
            print(format_report_text(report_dict))

        # Return exit code based on validation result
        if report.has_errors():
            return 1
        return 0

    except Exception as e:
        logger.exception("Validation failed: %s", e)
        return 2


if __name__ == "__main__":
    sys.exit(main())

