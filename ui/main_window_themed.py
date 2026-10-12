"""Themed main window (black/yellow) for the Validator GUI.

Same functionality as main_window.ValidatorApp, with a Sartorius-style
black and yellow header and accent styling.
"""

from __future__ import annotations

import datetime
import logging
import os
import platform
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, Any

from validator_oop.core.config import ValidatorConfig
from validator_oop.core.constants import VERSION, VERSION_REPORT
from validator_oop.core.rule_engine import RuleEngine
from validator_oop.core.validator_engine import ValidatorEngine
from validator_oop.excel.excel_loader import ExcelLoader
from validator_oop.excel.report_writer import ReportWriter, WorkbookFixer
from validator_oop.excel.sop_loader import SOPData
from validator_oop.rules.rule_registry import default_registry
from validator_oop.rules.builtin import register_all
from validator_oop.ui.catalog_ui import (
    load_catalog_for_validation,
    log_catalog_summary_from_report,
    merge_catalog_summaries,
)
from validator_oop.ui.input_files import (
    discover_recipe_workbooks,
    filter_workbooks_with_required_columns,
    format_no_valid_workbooks_message,
    merge_unique_paths,
)
from validator_oop.utils.logger import get_logger
from validator_oop.utils.validation_progress import record_run as record_validation_progress

if TYPE_CHECKING:
    from validator_oop.core.error import ValidationError

# Theme colors (black / yellow) – true yellow, not orange
COLOR_BLACK = "#000000"
COLOR_YELLOW = "#FFE600"   # bright yellow (Sartorius-style)
COLOR_WHITE = "#FFFFFF"
COLOR_DARK = "#1a1a1a"
COLOR_CONTENT_BG = "#f5f5f5"


def _apply_black_yellow_theme(root: tk.Tk) -> None:
    """Apply black/yellow ttk style to the window."""
    style = ttk.Style(root)
    style.theme_use("clam")  # So our colors are applied
    style.configure(
        "TFrame",
        background=COLOR_CONTENT_BG,
    )
    style.configure(
        "TLabel",
        background=COLOR_CONTENT_BG,
        foreground=COLOR_DARK,
        font=("TT Norms Pro", 9),
    )
    style.configure(
        "TButton",
        background=COLOR_YELLOW,
        foreground=COLOR_DARK,
        font=("TT Norms Pro", 9),
        padding=(10, 4),
    )
    style.map(
        "TButton",
        background=[("active", "#FFF176"), ("pressed", "#FFD54F")],
        foreground=[("active", COLOR_DARK)],
    )
    style.configure(
        "TEntry",
        fieldbackground=COLOR_WHITE,
        foreground=COLOR_DARK,
        insertcolor=COLOR_DARK,
    )
    style.configure(
        "TRadiobutton",
        background=COLOR_CONTENT_BG,
        foreground=COLOR_DARK,
        font=("TT Norms Pro", 9),
    )
    style.configure(
        "Vertical.TScrollbar",
        background=COLOR_CONTENT_BG,
        troughcolor=COLOR_CONTENT_BG,
    )


class ValidatorAppThemed(tk.Tk):
    """Themed (black/yellow) main window for the MES Recipe Validator.

    Same behaviour as ValidatorApp; only the look differs.
    """

    def __init__(
        self,
        *,
        config: ValidatorConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()

        self._config = config or ValidatorConfig()
        self._logger = logger or get_logger(self.__class__.__name__)

        try:
            import validator_oop.rules.builtin.structural
            import validator_oop.rules.builtin.field
            import validator_oop.rules.builtin.relational
            import validator_oop.rules.builtin.control
            import validator_oop.rules.builtin.catalog_code_rule
        except ImportError as e:
            self._logger.error("CRITICAL: Failed to import rule modules: %s", e, exc_info=True)
            import traceback
            traceback.print_exc()
            raise

        rule_count = register_all()
        self._logger.info("Registered %d built-in rules (total: %d)", rule_count, default_registry.count())

        self._loader = ExcelLoader()
        self._registry = default_registry
        self._report_writer = ReportWriter(logger=self._logger)
        self._workbook_fixer = WorkbookFixer(logger=self._logger)

        self.title("Validator")
        self.geometry("900x640")
        self.minsize(860, 560)
        self.configure(bg=COLOR_CONTENT_BG)

        _apply_black_yellow_theme(self)

        self.input_var = tk.StringVar()
        self.report_var = tk.StringVar()
        self.sop_var = tk.StringVar()
        self.catalog_razt_var = tk.StringVar()
        self.catalog_kem_var = tk.StringVar()
        self.catalog_repro_var = tk.StringVar()
        self.sheet_var = tk.StringVar()
        self.report_mode_var = tk.StringVar(value="combined")

        self._last_catalog_summary: dict[str, Any] | None = None

        self._build_ui()
        self._log_startup()

    def _build_ui(self) -> None:
        """Build UI with black header, yellow bar, then content."""
        # ---- Black header band ----
        header_black = tk.Frame(self, bg=COLOR_BLACK, height=36)
        header_black.pack(fill=tk.X)
        header_black.pack_propagate(False)
        tk.Label(
            header_black,
            text=f"Validator IPO Receptur  {VERSION}",
            bg=COLOR_BLACK,
            fg=COLOR_WHITE,
            font=("TT Norms Pro", 10),
        ).pack(side=tk.LEFT, padx=12, pady=6)
        tk.Label(
            header_black,
            text="SL",
            bg=COLOR_BLACK,
            fg=COLOR_WHITE,
            font=("TT Norms Pro", 10),
        ).pack(side=tk.RIGHT, padx=12, pady=6)

        # ---- Yellow bar ----
        bar_yellow = tk.Frame(self, bg=COLOR_YELLOW, height=40)
        bar_yellow.pack(fill=tk.X)
        bar_yellow.pack_propagate(False)
        tk.Label(
            bar_yellow,
            text="Sartorius BIA Separations",
            bg=COLOR_YELLOW,
            fg=COLOR_DARK,
            font=("TT Norms Pro", 12, "bold"),
        ).pack(side=tk.LEFT, padx=12, pady=8)

        # ---- Main content ----
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        ttk.Label(frm, text="Vhodna Excel datoteka (receptura):").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Entry(frm, textvariable=self.input_var).grid(
            row=1, column=0, columnspan=2, sticky="we"
        )
        ttk.Button(frm, text="Izberi...", command=self._pick_input).grid(
            row=1, column=2, sticky="e"
        )
        ttk.Button(frm, text="Izberi mapo...", command=self._pick_input_folder).grid(
            row=1, column=3, sticky="e"
        )
        ttk.Button(frm, text="Počisti seznam", command=self._clear_input_list).grid(
            row=1, column=4, sticky="e"
        )

        ttk.Label(frm, text="Izhodno poročilo (.xlsx ali .txt):").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Entry(frm, textvariable=self.report_var).grid(
            row=3, column=0, columnspan=2, sticky="we"
        )
        ttk.Button(frm, text="Shrani kot...", command=self._pick_report).grid(
            row=3, column=2, sticky="e"
        )

        ttk.Label(frm, text="SOP datoteka (Word .docx):").grid(row=4, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.sop_var).grid(
            row=5, column=0, columnspan=2, sticky="we"
        )
        ttk.Button(frm, text="Izberi...", command=self._pick_sop).grid(
            row=5, column=2, sticky="e"
        )

        ttk.Label(frm, text="Šifrant raztopin (Excel):").grid(row=6, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.catalog_razt_var).grid(
            row=7, column=0, columnspan=2, sticky="we"
        )
        ttk.Button(frm, text="Izberi...", command=self._pick_catalog_razt).grid(
            row=7, column=2, sticky="e"
        )

        ttk.Label(frm, text="Šifrant kemikalij (Excel):").grid(row=8, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.catalog_kem_var).grid(
            row=9, column=0, columnspan=2, sticky="we"
        )
        ttk.Button(frm, text="Izberi...", command=self._pick_catalog_kem).grid(
            row=9, column=2, sticky="e"
        )

        ttk.Label(frm, text="Šifrant repro materiala (Excel):").grid(row=10, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.catalog_repro_var).grid(
            row=11, column=0, columnspan=2, sticky="we"
        )
        ttk.Button(frm, text="Izberi...", command=self._pick_catalog_repro).grid(
            row=11, column=2, sticky="e"
        )

        ttk.Label(frm, text="Način poročila:").grid(row=12, column=0, sticky="w")
        ttk.Radiobutton(
            frm,
            text="Ena skupna datoteka",
            variable=self.report_mode_var,
            value="combined",
        ).grid(row=13, column=0, sticky="w")
        ttk.Radiobutton(
            frm,
            text="Ločeno poročilo za vsako datoteko",
            variable=self.report_mode_var,
            value="per_file",
        ).grid(row=13, column=1, sticky="w")

        ttk.Button(frm, text="Zaženi validacijo", command=self._run_validation).grid(
            row=14, column=0, sticky="w", pady=12
        )
        ttk.Button(
            frm, text="Zaženi validacijo s SOP", command=self._run_validation_with_sop
        ).grid(row=14, column=1, sticky="w", pady=12)
        ttk.Button(
            frm, text="Primerjaj razdelke med listi", command=self._run_section_compare
        ).grid(row=14, column=2, sticky="w", pady=12)
        ttk.Button(
            frm, text="Odpri mapo poročila", command=self._open_report_folder
        ).grid(row=14, column=3, sticky="e")

        ttk.Label(frm, text="Status:").grid(row=17, column=0, sticky="w")
        self.txt = tk.Text(
            frm, height=12, wrap="word",
            bg="#ffffff", fg=COLOR_DARK,
            insertbackground=COLOR_DARK,
            font=("TT Norms Pro", 9),
        )
        self.txt.grid(row=18, column=0, columnspan=3, sticky="nsew")
        scr = ttk.Scrollbar(frm, command=self.txt.yview)
        self.txt.configure(yscrollcommand=scr.set)
        scr.grid(row=18, column=3, sticky="ns")

        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(2, weight=0)
        frm.columnconfigure(3, weight=0)
        frm.columnconfigure(4, weight=0)
        frm.rowconfigure(18, weight=1)

    def _log_startup(self) -> None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = (
            f"Validator IPO Receptur ({VERSION_REPORT})\n"
            f"Avtor procesa: B. Komac\n"
            f"Uporaba: interna QA/Production skupina.\n"
            f"Zagon: {now}\n"
        )
        self.log(header)

    def log(self, msg: str) -> None:
        self.txt.insert(tk.END, msg + "\n")
        self.txt.see(tk.END)
        self.update_idletasks()
        self._logger.info(msg)

    def _clear_input_list(self) -> None:
        self.input_var.set("")
        self.log("Seznam vhodnih datotek je bil počiščen.")

    def _pick_input(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Izberi eno ali več Excel datotek (recepture)",
            filetypes=[("Excel files", "*.xlsx *.xlsm *.xls"), ("All files", "*.*")],
        )
        if not paths:
            return
        existing_raw = self.input_var.get().strip()
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
        self.input_var.set(text)
        if len(deduped) == 1:
            self.log(f"Izbrana datoteka: {deduped[0]}")
        else:
            self.log("Izbrane datoteke:")
            for p in deduped:
                self.log(f"  - {p}")

    def _pick_input_folder(self) -> None:
        """Open folder dialog and add all Excel files (except inside `staro`)."""
        folder = filedialog.askdirectory(
            title="Izberi mapo z Excel datotekami (mapa 'staro' se preskoči)"
        )
        if not folder:
            return
        self._append_excel_files_from_folders([Path(folder)], source_label=f"mape: {folder}")

    def _append_excel_files_from_folders(
        self,
        folders: list[Path],
        *,
        source_label: str,
    ) -> None:
        """Append recipe workbooks from folders; skip `staro` and non-recipe Excel files."""
        existing_raw = self.input_var.get().strip()
        existing_parts = [
            p.strip() for p in existing_raw.replace("\n", ";").split(";") if p.strip()
        ]

        discovered = discover_recipe_workbooks(
            folders,
            self._loader,
            log=self.log,
        )
        deduped = merge_unique_paths(existing_parts, discovered)
        self.input_var.set("; ".join(deduped))

        if not discovered and not existing_parts:
            self.log(
                f"V {source_label} ni najdenih Excel receptur (noben stolpec recepture)."
            )

    def _pick_sop(self) -> None:
        path = filedialog.askopenfilename(
            title="Izberi SOP datoteko (Word)",
            filetypes=[
                ("Word documents", "*.docx"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.sop_var.set(path)
            self.log(f"SOP datoteka: {path}")

    def _pick_catalog_razt(self) -> None:
        path = filedialog.askopenfilename(
            title="Izberi šifrant raztopin (Excel)",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if path:
            self.catalog_razt_var.set(path)
            self.log(f"Šifrant raztopin: {path}")

    def _pick_catalog_kem(self) -> None:
        path = filedialog.askopenfilename(
            title="Izberi šifrant kemikalij (Excel)",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if path:
            self.catalog_kem_var.set(path)
            self.log(f"Šifrant kemikalij: {path}")

    def _pick_catalog_repro(self) -> None:
        path = filedialog.askopenfilename(
            title="Izberi šifrant repro materiala (Excel)",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if path:
            self.catalog_repro_var.set(path)
            self.log(f"Šifrant repro materiala: {path}")

    def _pick_report(self) -> None:
        mode = self.report_mode_var.get()
        if mode == "combined":
            path = filedialog.asksaveasfilename(
                title="Shrani poročilo kot",
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel report (*.xlsx)", "*.xlsx"),
                    ("Text report (*.txt)", "*.txt"),
                ],
            )
            if path:
                self.report_var.set(path)
                self.log(f"Izhodno poročilo bo: {path}")
        else:
            folder = filedialog.askdirectory(
                title="Izberi mapo za poročila (ena datoteka na vhodno datoteko)"
            )
            if folder:
                self.report_var.set(folder)
                self.log(f"Mapa za posamezna poročila: {folder}")

    def _open_report_folder(self) -> None:
        p = self.report_var.get().strip()
        if not p:
            messagebox.showinfo("Info", "Najprej generiraj poročilo.")
            return
        folder = str(Path(p).resolve().parent)
        try:
            if platform.system() == "Windows":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
            self.log(f"Odprta mapa: {folder}")
        except Exception as e:
            messagebox.showerror("Napaka", f"Ne morem odpreti mape: {e}")
            self.log(f"NAPAKA odprtja mape: {e}")

    def _parse_input_paths(self) -> list[Path] | None:
        raw_in = self.input_var.get().strip()
        if not raw_in:
            messagebox.showerror("Napaka", "Najprej izberi vsaj eno vhodno datoteko.")
            self.log("NAPAKA: Manjkajo vhodne datoteke.")
            return None
        parts = [
            p.strip() for p in raw_in.replace("\n", ";").split(";") if p.strip()
        ]
        non_dir_paths: list[Path] = []
        folder_inputs: list[Path] = []
        for p in parts:
            parsed = Path(p)
            if parsed.is_dir():
                folder_inputs.append(parsed)
            else:
                non_dir_paths.append(parsed)

        if folder_inputs:
            self._append_excel_files_from_folders(
                folder_inputs,
                source_label="ročno vnesenih map",
            )
            updated = self.input_var.get().strip()
            parts = [
                p.strip() for p in updated.replace("\n", ";").split(";") if p.strip()
            ]
            non_dir_paths = [Path(p) for p in parts]

        in_paths = non_dir_paths
        if not in_paths:
            messagebox.showerror("Napaka", "Ni veljavnih poti do vhodnih datotek.")
            self.log("NAPAKA: Ni veljavnih poti do vhodnih datotek.")
            return None
        missing = [str(p) for p in in_paths if not p.exists()]
        if missing:
            messagebox.showerror(
                "Napaka",
                "Naslednje datoteke ne obstajajo:\n" + "\n".join(missing),
            )
            for m in missing:
                self.log(f"NAPAKA: Datoteka ne obstaja: {m}")
            return None
        return in_paths

    def _validate_output_path(self) -> tuple[Path | None, str]:
        out_raw = self.report_var.get().strip()
        mode = self.report_mode_var.get()
        if not out_raw:
            if mode == "combined":
                messagebox.showerror(
                    "Napaka", "Najprej izberi pot za izhodno poročilo."
                )
            else:
                messagebox.showerror(
                    "Napaka", "Najprej izberi mapo za posamezna poročila."
                )
            self.log("NAPAKA: Manjka pot za poročilo.")
            return None, mode
        return Path(out_raw), mode

    def _run_validation(self) -> None:
        self._run_validation_impl(sop_data=None)

    def _run_validation_with_sop(self) -> None:
        sop_path_str = self.sop_var.get().strip()
        if not sop_path_str:
            messagebox.showerror(
                "Napaka",
                "Za validacijo s SOP izberi najprej SOP datoteko (Word .docx).",
            )
            self.log("NAPAKA: Manjka izbira SOP datoteke.")
            return
        sop_path = Path(sop_path_str)
        if not sop_path.exists():
            messagebox.showerror("Napaka", f"SOP datoteka ne obstaja:\n{sop_path}")
            self.log(f"NAPAKA: SOP datoteka ne obstaja: {sop_path}")
            return
        try:
            sop_data = SOPData.from_word(sop_path, logger=self._logger)
            self.log(f"SOP naložen: {sop_data.sop_id or 'N/A'}, verzija {sop_data.version or 'N/A'}")
        except Exception as e:
            messagebox.showerror(
                "Napaka nalaganja SOP",
                f"Ne morem naložiti SOP datoteke:\n{sop_path}\n\n{e}",
            )
            self.log(f"NAPAKA nalaganja SOP: {e}")
            return
        self._run_validation_impl(sop_data=sop_data)

    def _run_validation_impl(
        self,
        sop_data: SOPData | None = None,
    ) -> None:
        in_paths = self._parse_input_paths()
        if in_paths is None:
            return
        filter_result = filter_workbooks_with_required_columns(
            in_paths,
            self._loader,
            log=self.log,
        )
        if not filter_result.valid:
            dialog_msg, log_msg = format_no_valid_workbooks_message(filter_result)
            messagebox.showinfo("Info", dialog_msg)
            self.log(log_msg)
            return

        in_paths = filter_result.valid
        out_path, mode = self._validate_output_path()
        if out_path is None:
            return
        sheet_name = self.sheet_var.get().strip()
        self.txt.delete("1.0", tk.END)
        self._log_startup()

        catalog_data = None
        catalog_paths: dict[str, str] = {}
        if self._config.enable_catalog_validation:
            catalog_data, catalog_paths = load_catalog_for_validation(
                self.catalog_razt_var.get(),
                self.catalog_kem_var.get(),
                self.catalog_repro_var.get(),
                log=self.log,
            )
        else:
            self.log("Preverjanje šifrantov je v konfiguraciji izklopljeno.")

        all_issues: list[dict[str, Any]] = []
        catalog_summaries: list[dict[str, Any]] = []
        if mode == "combined":
            if out_path.suffix.lower() not in {".xlsx", ".txt"}:
                messagebox.showerror("Napaka", "Poročilo mora biti .xlsx ali .txt")
                self.log("NAPAKA: Poročilo mora biti .xlsx ali .txt")
                return
            for in_path in in_paths:
                issues, cat_meta = self._validate_single_file(
                    in_path,
                    sheet_name,
                    sop_data=sop_data,
                    catalog_data=catalog_data,
                    catalog_paths=catalog_paths,
                )
                all_issues.extend(issues)
                if cat_meta:
                    catalog_summaries.append(cat_meta)
                self._record_progress(in_path, issues)
            self._last_catalog_summary = merge_catalog_summaries(catalog_summaries)
            log_catalog_summary_from_report(self._last_catalog_summary, self.log)
            self._write_report(out_path, all_issues, self._last_catalog_summary)
        else:
            try:
                out_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror(
                    "Napaka", f"Ne morem ustvariti mape za poročila:\n{e}"
                )
                self.log(f"NAPAKA ustvarjanja mape za poročila: {e}")
                return
            for in_path in in_paths:
                issues, cat_meta = self._validate_single_file(
                    in_path,
                    sheet_name,
                    sop_data=sop_data,
                    catalog_data=catalog_data,
                    catalog_paths=catalog_paths,
                )
                all_issues.extend(issues)
                if cat_meta:
                    catalog_summaries.append(cat_meta)
                self._record_progress(in_path, issues)
                out_file = out_path / f"por_{in_path.stem}.xlsx"
                file_summary = cat_meta or merge_catalog_summaries(catalog_summaries)
                self._write_report(out_file, issues, file_summary)
            self._last_catalog_summary = merge_catalog_summaries(catalog_summaries)
            log_catalog_summary_from_report(self._last_catalog_summary, self.log)
        self._show_summary(all_issues, out_path, mode)

    def _validate_single_file(
        self,
        in_path: Path,
        sheet_name: str = "",
        *,
        sop_data: SOPData | None = None,
        catalog_data=None,
        catalog_paths: dict[str, str] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        self.log(f"Berem: {in_path} ...")
        try:
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
                sop_data=sop_data,
                catalog_data=catalog_data,
                catalog_paths=catalog_paths,
            )
            report = engine.validate(str(in_path))
            cat_meta = report.metadata.get("catalog_validation")
            if cat_meta and cat_meta.get("enabled"):
                log_catalog_summary_from_report(cat_meta, self.log)
            self.log(f"Excel uspešno prebran: {in_path}")
            if sop_data:
                sop_errors = [e for e in report.errors if e.code.startswith("SOP_")]
                self.log(f"Validacija končana. Skupaj napak: {len(report.errors)}, SOP napak: {len(sop_errors)}")
                if sop_errors:
                    self.log("SOP validacija - najdene napake:")
                    for error in sop_errors:
                        self.log(f"  - {error.message} (vrstica {error.row_index}, stolpec {error.column or 'N/A'})")
                else:
                    self.log("SOP validacija: Vsi podatki iz zavihka 'Podatki' so skladni s SOP-om")
            else:
                self.log(f"Validacija končana. Najdenih napak: {len(report.errors)}")
            issues: list[dict[str, Any]] = []
            for error in report.errors:
                issues.append(self._error_to_dict(error, in_path.name))
            return issues, cat_meta if isinstance(cat_meta, dict) else None
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self._logger.error(f"Validation error for {in_path}: {error_details}")
            messagebox.showerror(
                "Napaka branja",
                f"Ne morem prebrati Excel datoteke:\n{in_path}\n\n{type(e).__name__}: {e}\n\nPodrobnosti:\n{error_details}",
            )
            self.log(f"NAPAKA branja ({in_path}): {e}")
            return [], None

    def _record_progress(self, in_path: Path, issues: list[dict[str, Any]]) -> None:
        """Zapiše rezultat validacije v napredek (delež pregledanih, število napak)."""
        try:
            err_count = sum(1 for i in issues if i.get("severity") == "ERROR")
            warn_count = sum(1 for i in issues if i.get("severity") == "WARNING")
            record_validation_progress(in_path, err_count, warn_count)
        except OSError:
            pass

    def _error_to_dict(
        self,
        error: ValidationError,
        filename: str,
    ) -> dict[str, Any]:
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

    def _write_report(
        self,
        out_path: Path,
        issues: list[dict[str, Any]],
        catalog_summary: dict[str, Any] | None = None,
    ) -> None:
        try:
            if out_path.suffix.lower() == ".xlsx":
                self._report_writer.write_excel_report(
                    out_path, issues, catalog_summary=catalog_summary
                )
            else:
                self._report_writer.write_text_report(
                    out_path, issues, catalog_summary=catalog_summary
                )
            self.log(f"Poročilo zapisano: {out_path}")
        except Exception as e:
            messagebox.showerror("Napaka pisanja", f"Ne morem zapisati poročila:\n{e}")
            self.log(f"NAPAKA pisanja poročila: {e}")

    def _show_summary(
        self,
        issues: list[dict[str, Any]],
        out_path: Path,
        mode: str,
    ) -> None:
        errors = sum(1 for i in issues if i.get("severity") == "ERROR")
        warns = sum(1 for i in issues if i.get("severity") == "WARNING")
        if errors == 0:
            self.log(f"OK: brez napak (opozoril: {warns}).")
            if mode == "combined":
                messagebox.showinfo(
                    "Končano", f"Brez napak (opozoril: {warns}).\nPoročilo:\n{out_path}"
                )
            else:
                messagebox.showinfo(
                    "Končano",
                    f"Brez napak (opozoril: {warns}).\nMapa poročil:\n{out_path}",
                )
        else:
            self.log(f"Končano z napakami: {errors} (opozoril: {warns}).")
            if mode == "combined":
                messagebox.showwarning(
                    "Končano",
                    f"Najdene napake: {errors}\nOpozorila: {warns}\nPoročilo:\n{out_path}",
                )
            else:
                messagebox.showwarning(
                    "Končano",
                    f"Najdene napake: {errors}\nOpozorila: {warns}\nMapa poročil:\n{out_path}",
                )

    def _run_section_compare(self) -> None:
        raw_in = self.input_var.get().strip()
        if not raw_in:
            messagebox.showerror("Napaka", "Najprej izberi vhodno datoteko.")
            self.log("NAPAKA: Manjka vhodna datoteka.")
            return
        parts = [
            p.strip() for p in raw_in.replace("\n", ";").split(";") if p.strip()
        ]
        if not parts:
            messagebox.showerror("Napaka", "Ni veljavnih poti do vhodnih datotek.")
            return
        in_path = Path(parts[0])
        if not in_path.exists():
            messagebox.showerror("Napaka", f"Datoteka ne obstaja:\n{in_path}")
            self.log(f"NAPAKA: Datoteka ne obstaja: {in_path}")
            return
        out_path, _ = self._validate_output_path()
        if out_path is None:
            return
        if out_path.suffix.lower() not in {".xlsx", ".txt"}:
            messagebox.showerror("Napaka", "Poročilo mora biti .xlsx ali .txt")
            self.log("NAPAKA: Poročilo mora biti .xlsx ali .txt")
            return
        self.txt.delete("1.0", tk.END)
        self.log(f"Berem (primerjava razdelkov): {in_path} ...")
        try:
            from validator_oop.excel.section_compare import (
                compare_sections,
                write_section_compare_report,
            )

            result = compare_sections(in_path)
            self.log(
                f"Primerjani listi: {', '.join(result.sheets)} "
                f"(referenčni: {result.base_sheet})"
            )
            for issue in result.issues:
                self.log(
                    f"  [{issue['severity'].upper()}] {issue['code']} "
                    f"({issue['sheet']}:{issue['row']}): {issue['message']}"
                )
            write_section_compare_report(result, out_path)
            self.log(f"Poročilo primerjave: {out_path}")

            if result.is_match:
                messagebox.showinfo(
                    "Primerjava razdelkov",
                    f"Razdelki se ujemajo med listi.\nPoročilo:\n{out_path}",
                )
            else:
                counts = result.counts
                messagebox.showwarning(
                    "Primerjava razdelkov",
                    f"Najdene razlike: {counts.get('error', 0)} "
                    f"(opozoril: {counts.get('warning', 0)})\nPoročilo:\n{out_path}",
                )
        except ValueError as e:
            messagebox.showerror("Napaka", str(e))
            self.log(f"NAPAKA primerjave razdelkov: {e}")
        except Exception as e:
            messagebox.showerror("Napaka", f"Napaka pri primerjavi razdelkov:\n{e}")
            self.log(f"NAPAKA primerjave razdelkov: {e}")


def run_app_themed(config: ValidatorConfig | None = None) -> None:
    """Run the themed (black/yellow) validator application."""
    app = ValidatorAppThemed(config=config)
    app.mainloop()
