"""PyQt6 main window (black/yellow) for the Validator GUI.

This module provides a PyQt6-based graphical user interface for the
MES Recipe Validator application, matching the Sartorius black/yellow theme.
"""

from __future__ import annotations

import datetime
import logging
import os
import platform
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QIcon, QFont, QColor, QPalette
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup,
        QFileDialog, QTextEdit, QMessageBox, QFrame, QScrollArea,
        QSizePolicy, QProgressBar
    )
except ImportError:
    # This module should only be imported if PyQt6 is available
    raise ImportError("PyQt6 is required for this GUI style")

from validator_oop.core.config import ValidatorConfig
from validator_oop.core.constants import VERSION, VERSION_REPORT
from validator_oop.core.rule_engine import RuleEngine
from validator_oop.core.validator_engine import ValidatorEngine
from validator_oop.excel.excel_loader import ExcelLoader
from validator_oop.excel.report_writer import ReportWriter, WorkbookFixer
from validator_oop.rules.rule_registry import default_registry
from validator_oop.rules.builtin import register_all
from validator_oop.utils.logger import get_logger
from validator_oop.utils.validation_progress import record_run as record_validation_progress

if TYPE_CHECKING:
    from validator_oop.core.error import ValidationError


# Theme colors
COLOR_BLACK = "#000000"
COLOR_YELLOW = "#FFE600"
COLOR_WHITE = "#FFFFFF"
COLOR_DARK = "#1a1a1a"
COLOR_CONTENT_BG = "#f5f5f5"

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_CONTENT_BG};
}}
QWidget {{
    background-color: {COLOR_CONTENT_BG};
    color: {COLOR_DARK};
    font-family: "TT Norms Pro", "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}}
QLabel {{
    color: {COLOR_DARK};
}}
QPushButton {{
    background-color: {COLOR_YELLOW};
    color: {COLOR_DARK};
    border: none;
    padding: 6px 12px;
    font-weight: bold;
    border-radius: 2px;
}}
QPushButton:hover {{
    background-color: #FFF176;
}}
QPushButton:pressed {{
    background-color: #FFD54F;
}}
QLineEdit {{
    background-color: {COLOR_WHITE};
    color: {COLOR_DARK};
    border: 1px solid #CCCCCC;
    padding: 4px;
    selection-background-color: {COLOR_YELLOW};
    selection-color: {COLOR_DARK};
}}
QTextEdit {{
    background-color: {COLOR_WHITE};
    color: {COLOR_DARK};
    border: 1px solid #CCCCCC;
    font-family: Consolas, monospace;
    font-size: 9pt;
}}
QRadioButton {{
    color: {COLOR_DARK};
    spacing: 8px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 1px solid #999;
    background-color: {COLOR_WHITE};
}}
QRadioButton::indicator:checked {{
    background-color: {COLOR_YELLOW};
    border: 1px solid {COLOR_DARK};
}}
QProgressBar {{
    border: 1px solid #CCCCCC;
    background-color: {COLOR_WHITE};
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {COLOR_YELLOW};
}}
"""


class MainWindowQt(QMainWindow):
    """PyQt6 main window for the MES Recipe Validator."""

    def __init__(
        self,
        *,
        config: ValidatorConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()

        self._config = config or ValidatorConfig()
        self._logger = logger or get_logger(self.__class__.__name__)

        # Ensure rules are registered
        try:
            import validator_oop.rules.builtin.structural
            import validator_oop.rules.builtin.field
            import validator_oop.rules.builtin.relational
            import validator_oop.rules.builtin.control
        except ImportError as e:
            self._logger.error("CRITICAL: Failed to import rule modules: %s", e, exc_info=True)
            import traceback
            traceback.print_exc()

        rule_count = register_all()
        self._logger.info("Registered %d built-in rules (total: %d)", rule_count, default_registry.count())

        # Initialize components
        self._loader = ExcelLoader()
        self._registry = default_registry
        self._report_writer = ReportWriter(logger=self._logger)
        self._workbook_fixer = WorkbookFixer(logger=self._logger)

        # UI Setup
        self.setWindowTitle(f"Validator IPO Receptur {VERSION}")
        self.resize(900, 600)
        self.setMinimumSize(860, 520)
        
        # Apply stylesheet
        self.setStyleSheet(STYLESHEET)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._build_ui()
        self._log_startup()

    def _build_ui(self) -> None:
        """Build the user interface."""
        
        # 1. Header (Black band)
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {COLOR_BLACK};")
        header_frame.setFixedHeight(40)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        title_label = QLabel(f"Validator IPO Receptur  {VERSION}")
        title_label.setStyleSheet(f"color: {COLOR_WHITE}; font-weight: bold; font-size: 11pt; background-color: {COLOR_BLACK};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.main_layout.addWidget(header_frame)

        # 2. Yellow Accent Bar
        yellow_bar = QFrame()
        yellow_bar.setStyleSheet(f"background-color: {COLOR_YELLOW};")
        yellow_bar.setFixedHeight(4)
        self.main_layout.addWidget(yellow_bar)

        # 3. Content Area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        self.main_layout.addWidget(content_widget)

        # -- Input Selection --
        input_group = QWidget()
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)
        
        input_layout.addWidget(QLabel("Vhodna Excel datoteka (receptura):"))
        
        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Izberi eno ali več datotek...")
        self.input_edit.setReadOnly(True)
        input_row.addWidget(self.input_edit)
        
        btn_browse = QPushButton("Izberi...")
        btn_browse.clicked.connect(self._pick_input)
        input_row.addWidget(btn_browse)
        
        btn_clear = QPushButton("Počisti seznam")
        btn_clear.clicked.connect(self._clear_input_list)
        input_row.addWidget(btn_clear)
        
        input_layout.addLayout(input_row)
        content_layout.addWidget(input_group)

        # -- Output Selection --
        output_group = QWidget()
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(5)
        
        output_layout.addWidget(QLabel("Izhodno poročilo (.xlsx ali .txt):"))
        
        output_row = QHBoxLayout()
        self.report_edit = QLineEdit()
        self.report_edit.setPlaceholderText("Pot do poročila...")
        output_row.addWidget(self.report_edit)
        
        btn_save = QPushButton("Shrani kot...")
        btn_save.clicked.connect(self._pick_report)
        output_row.addWidget(btn_save)
        
        output_layout.addLayout(output_row)
        content_layout.addWidget(output_group)

        # -- Report Mode --
        mode_group = QWidget()
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        
        mode_layout.addWidget(QLabel("Način poročila:"))
        
        self.btn_group_mode = QButtonGroup(self)
        
        self.rb_combined = QRadioButton("Ena skupna datoteka")
        self.rb_combined.setChecked(True)
        self.btn_group_mode.addButton(self.rb_combined, 1)
        mode_layout.addWidget(self.rb_combined)
        
        self.rb_per_file = QRadioButton("Ločeno poročilo za vsako datoteko")
        self.btn_group_mode.addButton(self.rb_per_file, 2)
        mode_layout.addWidget(self.rb_per_file)
        
        mode_layout.addStretch()
        content_layout.addWidget(mode_group)

        # -- Action Buttons --
        action_row = QHBoxLayout()
        
        btn_run = QPushButton("Zaženi validacijo")
        btn_run.setMinimumHeight(36)
        btn_run.setMinimumWidth(150)
        btn_run.clicked.connect(self._run_validation)
        action_row.addWidget(btn_run)
        
        btn_compare = QPushButton("Primerjaj razdelke med listi")
        btn_compare.clicked.connect(self._run_section_compare)
        action_row.addWidget(btn_compare)
        
        action_row.addStretch()
        
        btn_open = QPushButton("Odpri mapo poročila")
        btn_open.clicked.connect(self._open_report_folder)
        action_row.addWidget(btn_open)
        
        content_layout.addLayout(action_row)

        # -- Progress Bar (Optional addition for "advanced" feel) --
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)

        # -- Status Log --
        content_layout.addWidget(QLabel("Status:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        content_layout.addWidget(self.log_text)

    def log(self, msg: str) -> None:
        """Log a message to the status text area."""
        self.log_text.append(msg)
        # Scroll to bottom
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())
        QApplication.processEvents()
        self._logger.info(msg)

    def _log_startup(self) -> None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = (
            f"🧩 Validator IPO Receptur ({VERSION_REPORT})\n"
            f"Avtor procesa: B. Komac\n"
            f"Uporaba: interna QA/Production skupina.\n"
            f"Zagon: {now}\n"
            f"GUI: PyQt6 (Advanced)\n"
        )
        self.log(header)

    def _clear_input_list(self) -> None:
        self.input_edit.clear()
        self.log("Seznam vhodnih datotek je bil počiščen.")

    def _pick_input(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Izberi eno ali več Excel datotek (recepture)",
            "",
            "Excel files (*.xlsx *.xls);;All files (*.*)"
        )
        if not paths:
            return

        existing_raw = self.input_edit.text().strip()
        existing_parts = [
            p.strip() for p in existing_raw.replace("\n", ";").split(";") if p.strip()
        ]
        all_paths = existing_parts + list(paths)

        seen: set[str] = set()
        deduped: list[str] = []
        for p in all_paths:
            if p not in seen:
                seen.add(p)
                deduped.append(p)

        text = "; ".join(deduped)
        self.input_edit.setText(text)

        if len(deduped) == 1:
            self.log(f"Izbrana datoteka: {deduped[0]}")
        else:
            self.log("Izbrane datoteke:")
            for p in deduped:
                self.log(f"  - {p}")

    def _pick_report(self) -> None:
        mode_combined = self.rb_combined.isChecked()
        if mode_combined:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Shrani poročilo kot",
                "",
                "Excel report (*.xlsx);;Text report (*.txt)"
            )
            if path:
                self.report_edit.setText(path)
                self.log(f"Izhodno poročilo bo: {path}")
        else:
            folder = QFileDialog.getExistingDirectory(
                self,
                "Izberi mapo za poročila (ena datoteka na vhodno datoteko)"
            )
            if folder:
                self.report_edit.setText(folder)
                self.log(f"Mapa za posamezna poročila: {folder}")

    def _open_report_folder(self) -> None:
        p = self.report_edit.text().strip()
        if not p:
            QMessageBox.information(self, "Info", "Najprej generiraj poročilo.")
            return

        folder = str(Path(p).resolve().parent)
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
            self.log(f"Odprta mapa: {folder}")
        except Exception as e:
            QMessageBox.critical(self, "Napaka", f"Ne morem odpreti mape: {e}")
            self.log(f"NAPAKA odprtja mape: {e}")

    def _parse_input_paths(self) -> list[Path] | None:
        raw_in = self.input_edit.text().strip()
        if not raw_in:
            QMessageBox.critical(self, "Napaka", "Najprej izberi vsaj eno vhodno datoteko.")
            self.log("NAPAKA: Manjkajo vhodne datoteke.")
            return None

        parts = [
            p.strip() for p in raw_in.replace("\n", ";").split(";") if p.strip()
        ]
        in_paths = [Path(p) for p in parts]

        if not in_paths:
            QMessageBox.critical(self, "Napaka", "Ni veljavnih poti do vhodnih datotek.")
            self.log("NAPAKA: Ni veljavnih poti do vhodnih datotek.")
            return None

        missing = [str(p) for p in in_paths if not p.exists()]
        if missing:
            QMessageBox.critical(
                self,
                "Napaka",
                "Naslednje datoteke ne obstajajo:\n" + "\n".join(missing),
            )
            for m in missing:
                self.log(f"NAPAKA: Datoteka ne obstaja: {m}")
            return None

        return in_paths

    def _validate_output_path(self) -> tuple[Path | None, str]:
        out_raw = self.report_edit.text().strip()
        mode = "combined" if self.rb_combined.isChecked() else "per_file"

        if not out_raw:
            if mode == "combined":
                QMessageBox.critical(self, "Napaka", "Najprej izberi pot za izhodno poročilo.")
            else:
                QMessageBox.critical(self, "Napaka", "Najprej izberi mapo za posamezna poročila.")
            self.log("NAPAKA: Manjka pot za poročilo.")
            return None, mode

        return Path(out_raw), mode

    def _run_validation(self) -> None:
        in_paths = self._parse_input_paths()
        if in_paths is None:
            return

        out_path, mode = self._validate_output_path()
        if out_path is None:
            return

        self.log_text.clear()
        self.log("Začenjam validacijo...")
        
        # Setup progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(in_paths))
        self.progress_bar.setValue(0)

        all_issues: list[dict[str, Any]] = []

        if mode == "combined":
            if out_path.suffix.lower() not in {".xlsx", ".txt"}:
                QMessageBox.critical(self, "Napaka", "Poročilo mora biti .xlsx ali .txt")
                self.log("NAPAKA: Poročilo mora biti .xlsx ali .txt")
                self.progress_bar.setVisible(False)
                return

            for i, in_path in enumerate(in_paths):
                issues = self._validate_single_file(in_path)
                all_issues.extend(issues)
                self._record_progress(in_path, issues)
                self.progress_bar.setValue(i + 1)

            self._write_report(out_path, all_issues)

        else:
            try:
                out_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Napaka", f"Ne morem ustvariti mape za poročila:\n{e}")
                self.log(f"NAPAKA ustvarjanja mape za poročila: {e}")
                self.progress_bar.setVisible(False)
                return

            for i, in_path in enumerate(in_paths):
                issues = self._validate_single_file(in_path)
                all_issues.extend(issues)
                self._record_progress(in_path, issues)

                out_file = out_path / f"por_{in_path.stem}.xlsx"
                self._write_report(out_file, issues)
                self.progress_bar.setValue(i + 1)

        self.progress_bar.setVisible(False)
        self._show_summary(all_issues, out_path, mode)

    def _validate_single_file(self, in_path: Path) -> list[dict[str, Any]]:
        self.log(f"Validiram: {in_path.name} ...")
        QApplication.processEvents()

        try:
            # Match classic GUI behavior: ValidatorEngine loads the workbook internally.
            # include_formulas=True is required for formula-based rules.
            rule_engine = RuleEngine(
                self._registry,
                config=self._config,
                logger=self._logger,
            )
            engine = ValidatorEngine(
                rule_engine=rule_engine,
                excel_loader=self._loader,
                logger=self._logger,
                include_formulas=True,
                sop_data=None,
            )

            report = engine.validate(str(in_path))
            self.log(f"Excel uspešno prebran: {in_path}")
            
            # Convert to issues list
            issues: list[dict[str, Any]] = []
            for error in report.errors:
                issues.append(self._error_to_dict(error, in_path.name))
            
            err_count = sum(1 for i in issues if i["severity"] == "ERROR")
            warn_count = sum(1 for i in issues if i["severity"] == "WARNING")
            self.log(f"  -> {err_count} napak, {warn_count} opozoril")
            
            return issues

        except Exception as e:
            self.log(f"NAPAKA pri validaciji {in_path.name}: {e}")
            self._logger.exception("Validation failed for %s", in_path)
            return []

    def _error_to_dict(
        self,
        error: "ValidationError",
        filename: str,
    ) -> dict[str, Any]:
        """Convert a ValidationError to the report-writer issue format.

        This matches the classic Tkinter GUI mapping.
        """
        sheet = error.sheet or ""
        if filename and sheet:
            sheet = f"{filename}:{sheet}"
        elif filename:
            sheet = filename

        return {
            "sheet": sheet,
            "row": error.row_index or "",
            "col": error.column or "",
            "code": error.code or error.rule_name,
            "message": error.message,
            "severity": error.severity.name if error.severity else "ERROR",
        }

    def _record_progress(self, in_path: Path, issues: list[dict[str, Any]]) -> None:
        err_count = sum(1 for i in issues if i["severity"] == "ERROR")
        warn_count = sum(1 for i in issues if i["severity"] == "WARNING")
        try:
            record_validation_progress(in_path, err_count, warn_count)
        except Exception:
            pass

    def _write_report(self, path: Path, issues: list[dict[str, Any]]) -> None:
        try:
            if path.suffix.lower() == ".txt":
                self._report_writer.write_text_report(path, issues)
            else:
                self._report_writer.write_excel_report(path, issues)
            self.log(f"Poročilo shranjeno: {path}")
        except Exception as e:
            self.log(f"NAPAKA pri zapisovanju poročila: {e}")
            QMessageBox.critical(self, "Napaka", f"Napaka pri zapisovanju poročila:\n{e}")

    def _show_summary(self, issues: list[dict[str, Any]], out_path: Path, mode: str) -> None:
        err_count = sum(1 for i in issues if i["severity"] == "ERROR")
        warn_count = sum(1 for i in issues if i["severity"] == "WARNING")
        
        msg = (
            f"Validacija končana.\n\n"
            f"Skupaj napak: {err_count}\n"
            f"Skupaj opozoril: {warn_count}\n\n"
        )
        if mode == "combined":
            msg += f"Poročilo: {out_path}"
        else:
            msg += f"Poročila so v mapi: {out_path}"

        QMessageBox.information(self, "Povzetek", msg)

    def _run_section_compare(self) -> None:
        QMessageBox.information(
            self,
            "Info",
            "Primerjava razdelkov še ni implementirana v novi arhitekturi (PyQt6)."
        )


def run_app_qt() -> None:
    """Run the PyQt6 application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Good base style for custom coloring
    
    window = MainWindowQt()
    window.show()
    
    sys.exit(app.exec())
