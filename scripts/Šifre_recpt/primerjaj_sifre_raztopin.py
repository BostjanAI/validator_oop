#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Primerja oznake raztopin in kemikalij iz receptur (stolpec „Ključ preverjanja“,
vrstice tipa raztopina/kemikalija) s šiframi iz dveh katalogov:
- raztopine: Izvoz_sifre_razt.xlsx
- kemikalije: Izvoz_kem.xlsx
(stolpec kataloskestevilke_sifra).

Uporaba:
  python primerjaj_sifre_raztopin.py
  python primerjaj_sifre_raztopin.py Receptura2.xlsm --izvoz-raztopine Izvoz_sifre_razt.xlsx --izvoz-kemikalije Izvoz_kem.xlsx -o porocilo.xlsx

Privzeto išče *.xlsm v mapi skripte (razen ~$), Izvoz_sifre_razt.xlsx
in Izvoz_kem.xlsx.
Izhod: primerjava_sifre_raztopin.xlsx v mapi skripte.

Odvisnosti: pip install openpyxl
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook

# GUI importe
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

COL_TIP = "Tip podatka"
COL_KLJUC = "Ključ preverjanja"
COL_SIFRA = "kataloskestevilke_sifra"
TIPI_PRIMERJAVE = ("raztopina", "kemikalija")
TIPI_PRIMERJAVE_KEYS = {str(v).strip().casefold() for v in TIPI_PRIMERJAVE}
MAX_HEADER_SCAN = 30
TIP_RAZTOPINA = "raztopina"
TIP_KEMIKALIJA = "kemikalija"
DEFAULT_IZVOZ_RAZTOPINE = "Izvoz_sifre_razt.xlsx"
DEFAULT_IZVOZ_KEMIKALIJE = "Izvoz_kem.xlsx"
DEFAULT_OUTPUT = "primerjava_sifre_raztopin.xlsx"
CATALOG_LOOKUP_COLUMNS_BY_TIP = {
    TIP_RAZTOPINA: (COL_SIFRA, "material_kataloske"),
    TIP_KEMIKALIJA: (
        COL_SIFRA,
        "material_sifra",
        "material_naziv_kratki",
        "material_naziv_dolgi",
        "material_kataloske",
    ),
}

_HYPHEN_LETTER_INSTANCE = re.compile(r"(-[A-Za-z]+)\d+$")
_SHORT_CODE_INSTANCE = re.compile(r"^[A-Za-z]{2,}\d+$")
_UNDERSCORE_NUM_SUFFIX = re.compile(r"^(.+)_(\d+)$")
_NUMERIC = re.compile(r"\d+\.\d+|\d+")


def norm(s: object) -> str:
    if s is None:
        return ""
    return str(s).strip()


def norm_key(s: object) -> str:
    return norm(s).casefold()


def strip_instance_suffix(s: str) -> str:
    """GK1, EtOH1, -GK10 … -> GK / EtOH (večkratna uporaba iste šifre; ne posega v pH5.0 / H2SO4)."""
    s = s.strip()
    m = _HYPHEN_LETTER_INSTANCE.search(s)
    if m:
        return s[: m.end(1)]
    if _SHORT_CODE_INSTANCE.fullmatch(s):
        return re.sub(r"\d+$", "", s)
    m_und = _UNDERSCORE_NUM_SUFFIX.match(s)
    if m_und:
        return m_und.group(1)
    stripped = re.sub(r"[_\-]\d+$", "", s)
    return stripped if stripped else s


def norm_num(m: re.Match[str]) -> str:
    v = float(m.group(0))
    if v == int(v):
        return str(int(v))
    return f"{v:g}"

def normalize_concentrations(s: str) -> str:
    """Normalizira številke v nizu (npr. 0.9 -> 0, 1.0 -> 1)."""
    return _NUMERIC.sub(norm_num, s.casefold())

def catalog_lookup_keys(raw_sifra: str) -> list[str]:
    """Vse oblike ključa za iskanje v katalogu."""
    keys: list[str] = []
    for variant in (raw_sifra, strip_instance_suffix(raw_sifra)):
        if not variant:
            continue
        keys.append(norm_key(variant))
        keys.append(normalize_concentrations(variant))
    out: list[str] = []
    seen: set[str] = set()
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def recipe_lookup_keys(raw_kljuc: str) -> list[str]:
    keys: list[str] = []
    for variant in (raw_kljuc, strip_instance_suffix(raw_kljuc)):
        if not variant:
            continue
        keys.append(norm_key(variant))
        keys.append(normalize_concentrations(variant))
    out: list[str] = []
    seen: set[str] = set()
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def split_catalog_values(value: object) -> list[str]:
    values: list[str] = []
    for part in norm(value).split(","):
        cleaned = norm(part)
        if not cleaned:
            continue
        values.append(cleaned)
        if " - " in cleaned:
            values.append(norm(cleaned.split(" - ", 1)[0]))

    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def is_matching_tip(tip: str) -> bool:
    return norm_key(tip) in TIPI_PRIMERJAVE_KEYS


def locate_headers(ws, max_row: int) -> tuple[int, dict[str, int]] | None:
    limit = min(max_row, MAX_HEADER_SCAN)
    for r in range(1, limit + 1):
        headers: dict[str, int] = {}
        for cell in ws[r]:
            v = norm(cell.value)
            if v:
                headers[v] = cell.column
        if COL_TIP in headers and COL_KLJUC in headers:
            return r, headers
    return None


def extract_raztopine_from_workbook(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    wb = load_workbook(path, data_only=True)
    try:
        for sheet in wb.worksheets:
            max_row = sheet.max_row or 0
            found = locate_headers(sheet, max_row)
            if not found:
                continue
            header_row, cols = found
            c_tip = cols[COL_TIP]
            c_kljuc = cols[COL_KLJUC]
            c_zavihek = cols.get("Zavihek")
            c_korak = cols.get("št. Koraka")
            c_navodilo = cols.get("Navodilo")
            for r in range(header_row + 1, max_row + 1):
                tip = norm(sheet.cell(row=r, column=c_tip).value)
                if not is_matching_tip(tip):
                    continue
                kljuc = norm(sheet.cell(row=r, column=c_kljuc).value)
                if not kljuc:
                    continue
                rows.append(
                    {
                        "datoteka": path.name,
                        "zavihek": sheet.title,
                        "vrstica": str(r),
                        "tip": norm_key(tip),
                        "korak": norm(sheet.cell(row=r, column=c_korak).value)
                        if c_korak
                        else "",
                        "navodilo": norm(sheet.cell(row=r, column=c_navodilo).value)
                        if c_navodilo
                        else "",
                        "kljuc": kljuc,
                    }
                )
    finally:
        wb.close()
    return rows


def load_catalog(
    path: Path,
    lookup_columns: tuple[str, ...] = (COL_SIFRA,),
) -> tuple[dict[str, str], list[str]]:
    """
    Vrne (lookup_norm_key -> originalna_sifra, urejen seznam vseh šifer).
    """
    wb = load_workbook(path, data_only=True)
    lookup: dict[str, str] = {}
    all_sifre: list[str] = []
    seen_display: set[str] = set()
    try:
        ws = wb.active
        assert ws is not None
        header_row = 1
        cols: dict[str, int] = {}
        for cell in ws[1]:
            v = norm(cell.value)
            if v:
                cols[v] = cell.column
        max_row = ws.max_row or 0

        if COL_SIFRA not in cols:
            raise ValueError(
                f"V {path.name} manjka stolpec „{COL_SIFRA}“. Najdeni: {', '.join(cols)}"
            )
        c_sifra = cols[COL_SIFRA]
        lookup_col_indexes = [cols[col] for col in lookup_columns if col in cols]
        for r in range(header_row + 1, max_row + 1):
            sifra = norm(ws.cell(row=r, column=c_sifra).value)
            if not sifra:
                continue
            if sifra not in seen_display:
                seen_display.add(sifra)
                all_sifre.append(sifra)
            for c_lookup in lookup_col_indexes:
                for value in split_catalog_values(ws.cell(row=r, column=c_lookup).value):
                    for k in catalog_lookup_keys(value):
                        lookup.setdefault(k, sifra)
    finally:
        wb.close()
    all_sifre.sort(key=str.casefold)
    return lookup, all_sifre


def match_kljuc(kljuc: str, catalog: dict[str, str]) -> tuple[str, str, str]:
    """
    Vrne (status, ujemajoca_sifra, nacin).
    status: ujemanje | brez_ujemanja
    Ujemanja: natančna ali brez številk na koncu (GK1 vs GK).
    Ni ujemanja: samo normalizacija koncentracij (2.00mp vs 2mp).
    """
    stripped_kljuc = strip_instance_suffix(kljuc)
    stripped_keys = {norm_key(stripped_kljuc), normalize_concentrations(stripped_kljuc)}
    for k in recipe_lookup_keys(kljuc):
        if k in catalog:
            if norm_key(kljuc) == k:
                return "ujemanje", catalog[k], "natančno"
            if stripped_kljuc != kljuc and k in stripped_keys:
                return "ujemanje", catalog[k], "brez številk na koncu"
            if normalize_concentrations(kljuc) == k:
                return "ujemanje", catalog[k], "normalizacija števil"
            return "ujemanje", catalog[k], "normalizirano"
    return "brez_ujemanja", "", ""


def find_receptura_files(folder: Path, explicit: list[Path]) -> list[Path]:
    if explicit:
        return explicit
    files = sorted(
        (
            p
            for p in folder.glob("*.xlsm")
            if p.is_file() and not p.name.startswith("~$")
        ),
        key=lambda p: p.name.casefold(),
    )
    return files


def find_files_in_folders(folders: list[Path]) -> list[Path]:
    """Najdi vse .xlsm datoteke v več folderjih, rekurzivno po podmapah.
    Izključi vse poti, ki vsebujejo mapo 'staro'."""
    found_files: list[Path] = []
    seen: set[Path] = set()

    def is_excluded(path: Path) -> bool:
        return any(part.casefold() == "staro" for part in path.parts)

    for folder in folders:
        if not folder.is_dir():
            continue
        for p in folder.rglob("*.xlsm"):
            if not p.is_file() or p.name.startswith("~$"):
                continue
            if is_excluded(p):
                continue
            if p not in seen:
                seen.add(p)
                found_files.append(p)

    return sorted(found_files, key=lambda p: str(p).casefold())


def sanitize_sheet_name(name: str) -> str:
    invalid_chars = set('[]:*?/\\')
    normalized = ''.join('_' if c in invalid_chars else c for c in name).strip()
    if not normalized:
        normalized = 'Sheet'
    return normalized[:31]


def unique_sheet_name(name: str, existing: set[str]) -> str:
    sheet_name = name[:31]
    if sheet_name not in existing:
        existing.add(sheet_name)
        return sheet_name

    base = sheet_name[:27].rstrip('_')
    suffix = 1
    while True:
        candidate = f"{base}_{suffix}"
        if len(candidate) > 31:
            candidate = candidate[:31]
        if candidate not in existing:
            existing.add(candidate)
            return candidate
        suffix += 1


def group_name_for_file(path: Path, roots: list[Path]) -> str:
    path = path.resolve()
    for root in sorted((r.resolve() for r in roots), key=lambda p: len(str(p)), reverse=True):
        try:
            rel = path.parent.relative_to(root)
        except ValueError:
            continue
        if rel == Path('.'):
            return root.name
        return rel.parts[0]
    return path.parent.name


def write_report(
    out_path: Path,
    detail_rows: list[dict[str, str]],
    catalog_all_by_tip: dict[str, list[str]],
    matched_sifre_by_tip: dict[str, set[str]],
    receptura_files: list[Path],
    izvoz_paths_by_tip: dict[str, Path],
    group_roots: list[Path] | None = None,
) -> None:
    wb = Workbook()

    def append_report_rows(ws, rows: list[dict[str, str]]) -> None:
        ws.append(
            [
                "Datoteka",
                "Zavihek",
                "Vrstica",
                "Tip podatka",
                "Korak",
                "Navodilo",
                "Ključ preverjanja",
                "Status",
                "Ujemajoča šifra (katalog)",
                "Način ujemanja",
            ]
        )
        for row in rows:
            ws.append(
                [
                    row["datoteka"],
                    row["zavihek"],
                    row["vrstica"],
                    row["tip"],
                    row["korak"],
                    row["navodilo"],
                    row["kljuc"],
                    row["status"],
                    row["sifra_katalog"],
                    row["nacin"],
                ]
            )
        ws.freeze_panes = "A2"

    ws = wb.active
    assert ws is not None
    ws.title = "Primerjava"
    append_report_rows(ws, detail_rows)

    group_roots = group_roots or []
    grouped_rows: dict[str, list[dict[str, str]]] = {}
    for row in detail_rows:
        group = row.get("_group") or "Skupaj"
        grouped_rows.setdefault(group, []).append(row)

    existing_names = {"Primerjava", "Unikatni ključi", "Povzetek", "Neuporabljene šifre"}
    for group, rows in sorted(grouped_rows.items(), key=lambda item: item[0].casefold()):
        if group == "Skupaj":
            continue
        sheet_name = unique_sheet_name(sanitize_sheet_name(group), existing_names)
        ws_group = wb.create_sheet(sheet_name)
        append_report_rows(ws_group, rows)

    unikatni_pari = sorted(
        {(r["tip"], r["kljuc"]) for r in detail_rows},
        key=lambda pair: (pair[0], pair[1].casefold()),
    )
    unikatne_baze = sorted(
        {
            (r["tip"], strip_instance_suffix(r["kljuc"]))
            for r in detail_rows
        },
        key=lambda pair: (pair[0], pair[1].casefold()),
    )
    brez = [
        (tip, baza)
        for tip, baza in unikatne_baze
        if all(
            r["status"] != "ujemanje"
            for r in detail_rows
            if r["tip"] == tip and strip_instance_suffix(r["kljuc"]) == baza
        )
    ]

    ws2 = wb.create_sheet("Unikatni ključi")
    ws2.append(["Tip podatka", "Ključ preverjanja", "Status", "Ujemajoča šifra", "Način"])
    for tip, kljuc in unikatni_pari:
        sample = next(r for r in detail_rows if r["tip"] == tip and r["kljuc"] == kljuc)
        ws2.append([tip, kljuc, sample["status"], sample["sifra_katalog"], sample["nacin"]])

    ws3 = wb.create_sheet("Povzetek")
    ws3.append(["Parameter", "Vrednost"])
    ws3.append(["Čas", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    ws3.append(
        ["Izvoz šifer raztopin", str(izvoz_paths_by_tip.get(TIP_RAZTOPINA, ""))]
    )
    ws3.append(
        ["Izvoz šifer kemikalij", str(izvoz_paths_by_tip.get(TIP_KEMIKALIJA, ""))]
    )
    ws3.append(["Recepture", ", ".join(p.name for p in receptura_files)])
    ws3.append(["Vrstic raztopin/kemikalij v recepturi", len(detail_rows)])
    ws3.append(["Unikatnih ključev (tip + ključ)", len(unikatni_pari)])
    ws3.append(["Unikatnih baz (brez instance GK1…)", len(unikatne_baze)])
    ws3.append(["Ujemanj (po bazi)", len(unikatne_baze) - len(brez)])
    ws3.append(["Brez ujemanja v katalogu (po bazi)", len(brez)])
    ws3.append(
        [
            "Šifer v katalogu raztopin",
            len(catalog_all_by_tip.get(TIP_RAZTOPINA, [])),
        ]
    )
    ws3.append(
        [
            "Šifer v katalogu kemikalij",
            len(catalog_all_by_tip.get(TIP_KEMIKALIJA, [])),
        ]
    )
    ws3.append(
        [
            "Uporabljenih šifer raztopin",
            len(matched_sifre_by_tip.get(TIP_RAZTOPINA, set())),
        ]
    )
    ws3.append(
        [
            "Uporabljenih šifer kemikalij",
            len(matched_sifre_by_tip.get(TIP_KEMIKALIJA, set())),
        ]
    )

    st_raztopin = sum(1 for r in detail_rows if r["tip"] == TIP_RAZTOPINA)
    st_kemikalij = sum(1 for r in detail_rows if r["tip"] == TIP_KEMIKALIJA)
    ws3.append(["Vrstic raztopin", st_raztopin])
    ws3.append(["Vrstic kemikalij", st_kemikalij])
    if brez:
        ws3.append([])
        ws3.append(["Ključi brez ujemanja (tip + ključ)"])
        for tip, kljuc in brez:
            ws3.append([f"{tip}: {kljuc}"])

    ws4 = wb.create_sheet("Neuporabljene šifre")
    ws4.append(["Tip podatka", "kataloskestevilke_sifra"])
    for tip in (TIP_RAZTOPINA, TIP_KEMIKALIJA):
        all_sifre = catalog_all_by_tip.get(tip, [])
        matched = matched_sifre_by_tip.get(tip, set())
        ne_uporabljene = sorted((s for s in all_sifre if s not in matched), key=str.casefold)
        for sifra in ne_uporabljene:
            ws4.append([tip, sifra])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)


def run_gui_mode() -> int:
    """GUI način za izbiro folderjev in datotek."""
    if not HAS_TKINTER:
        print("Napaka: tkinter ni dostopen. Uporabi CLI mode.", file=sys.stderr)
        return 1

    root = tk.Tk()
    root.title("Primerjava šifer raztopin in kemikalij - GUI")
    root.geometry("700x600")
    root.resizable(True, True)

    selected_folders: list[Path] = []
    izvoz_razt_path: list[Path] = [None]
    izvoz_kem_path: list[Path] = [None]
    output_path: list[Path] = [None]
    result: dict[str, int] = {"code": 0}

    def add_folder() -> None:
        folder = filedialog.askdirectory(title="Izberi mapo")
        if folder:
            selected_folders.append(Path(folder))
            update_folder_list()

    def remove_folder() -> None:
        selection = folder_listbox.curselection()
        if selection:
            idx = selection[0]
            selected_folders.pop(idx)
            update_folder_list()

    def update_folder_list() -> None:
        folder_listbox.delete(0, tk.END)
        for f in selected_folders:
            folder_listbox.insert(tk.END, str(f))
        files_listbox.delete(0, tk.END)
        found_files = find_files_in_folders(selected_folders)
        for f in found_files:
            files_listbox.insert(tk.END, f.name)
        selected_files_label.config(text=f"Najdenih datotek: {len(found_files)}")

    def select_izvoz_raztopine() -> None:
        file = filedialog.askopenfilename(
            title="Izberi Excel za raztopine",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if file:
            izvoz_razt_path[0] = Path(file)
            izvoz_razt_label.config(text=f"Raztopine: {izvoz_razt_path[0].name}")

    def select_izvoz_kemikalije() -> None:
        file = filedialog.askopenfilename(
            title="Izberi Excel za kemikalije",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if file:
            izvoz_kem_path[0] = Path(file)
            izvoz_kem_label.config(text=f"Kemikalije: {izvoz_kem_path[0].name}")

    def select_output() -> None:
        file = filedialog.asksaveasfilename(
            title="Izberi izhodno datoteko",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if file:
            output_path[0] = Path(file)
            output_label.config(text=f"Izhod: {output_path[0].name}")

    def run_comparison() -> None:
        if not selected_folders:
            messagebox.showerror("Napaka", "Izberi vsaj eno mapo!")
            return
        if not izvoz_razt_path[0]:
            messagebox.showerror("Napaka", "Izberi Excel šifer za raztopine!")
            return
        if not izvoz_kem_path[0]:
            messagebox.showerror("Napaka", "Izberi Excel šifer za kemikalije!")
            return
        if not output_path[0]:
            messagebox.showerror("Napaka", "Izberi izhodno datoteko!")
            return

        receptura_files = find_files_in_folders(selected_folders)
        if not receptura_files:
            messagebox.showerror("Napaka", "Ni datotek recepture v izbranih mapah!")
            return

        status_window = tk.Toplevel(root)
        status_window.title("Obdelava...")
        status_window.geometry("300x100")
        status_label = tk.Label(status_window, text="Obdelava v teku...", wraplength=280)
        status_label.pack(padx=10, pady=10)
        progress = ttk.Progressbar(status_window, mode="indeterminate", length=280)
        progress.pack(padx=10, pady=10)
        progress.start()
        status_window.update()

        try:
            catalogs: dict[str, dict[str, str]] = {}
            catalog_all_by_tip: dict[str, list[str]] = {}
            izvoz_paths_by_tip = {
                TIP_RAZTOPINA: izvoz_razt_path[0],
                TIP_KEMIKALIJA: izvoz_kem_path[0],
            }
            for tip, izvoz_path in izvoz_paths_by_tip.items():
                catalog, catalog_all = load_catalog(
                    izvoz_path,
                    CATALOG_LOOKUP_COLUMNS_BY_TIP.get(tip, (COL_SIFRA,)),
                )
                catalogs[tip] = catalog
                catalog_all_by_tip[tip] = catalog_all

            detail_rows: list[dict[str, str]] = []
            matched_sifre_by_tip: dict[str, set[str]] = {
                TIP_RAZTOPINA: set(),
                TIP_KEMIKALIJA: set(),
            }

            for rec_path in receptura_files:
                try:
                    extracted = extract_raztopine_from_workbook(rec_path)
                except OSError as e:
                    status_label.config(text=f"Napaka pri {rec_path.name}: {e}")
                    status_window.update()
                    continue
                group_label = group_name_for_file(rec_path, selected_folders)
                for item in extracted:
                    tip = item["tip"]
                    status_val, sifra_kat, nacin = match_kljuc(item["kljuc"], catalogs.get(tip, {}))
                    if sifra_kat:
                        matched_sifre_by_tip.setdefault(tip, set()).add(sifra_kat)
                    detail_rows.append(
                        {
                            **item,
                            "status": status_val,
                            "sifra_katalog": sifra_kat,
                            "nacin": nacin,
                            "_group": group_label,
                        }
                    )

            write_report(
                output_path[0],
                detail_rows,
                catalog_all_by_tip,
                matched_sifre_by_tip,
                receptura_files,
                izvoz_paths_by_tip,
                selected_folders,
            )
            status_window.destroy()
            unikatni = {(r["tip"], r["kljuc"]) for r in detail_rows}
            ujemanja = sum(
                1
                for tip, kljuc in unikatni
                if any(
                    r["status"] == "ujemanje"
                    for r in detail_rows
                    if r["tip"] == tip and r["kljuc"] == kljuc
                )
            )
            msg = (
                f"Obdelano receptur: {len(receptura_files)}\n"
                f"Vrstic raztopin/kemikalij: {len(detail_rows)}\n"
                f"Unikatnih ključev (tip + ključ): {len(unikatni)}\n"
                f"Ujemanj: {ujemanja}\n"
                f"Brez ujemanja: {len(unikatni) - ujemanja}\n\n"
                f"Poročilo: {output_path[0]}"
            )
            messagebox.showinfo("Uspeho", msg)
            result["code"] = 0
        except Exception as e:
            status_window.destroy()
            messagebox.showerror("Napaka", f"Napaka pri primerjavi: {e}")
            result["code"] = 1
            return

        root.quit()

    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill="both", expand=True)

    tk.Label(main_frame, text="Izbrane mape:", font=("Arial", 10, "bold")).pack(
        anchor="w", pady=(0, 5)
    )
    folder_listbox = tk.Listbox(main_frame, height=4)
    folder_listbox.pack(fill="both", expand=True, pady=(0, 5))

    folder_btn_frame = tk.Frame(main_frame)
    folder_btn_frame.pack(fill="x", pady=(0, 10))
    tk.Button(folder_btn_frame, text="Dodaj mapo", command=add_folder).pack(
        side="left", padx=5
    )
    tk.Button(folder_btn_frame, text="Odstrani mapo", command=remove_folder).pack(
        side="left", padx=5
    )

    selected_files_label = tk.Label(
        main_frame, text="Najdenih datotek: 0", font=("Arial", 9)
    )
    selected_files_label.pack(anchor="w", pady=(10, 5))

    files_listbox = tk.Listbox(main_frame, height=3)
    files_listbox.pack(fill="both", expand=True, pady=(0, 10))

    tk.Label(main_frame, text="Izvoz šifer raztopin:", font=("Arial", 10, "bold")).pack(
        anchor="w", pady=(10, 0)
    )
    izvoz_razt_label = tk.Label(main_frame, text="Ni izbrano", fg="gray")
    izvoz_razt_label.pack(anchor="w", pady=(0, 5))
    tk.Button(
        main_frame,
        text="Izberi Excel za raztopine",
        command=select_izvoz_raztopine,
    ).pack(
        fill="x", pady=(0, 10)
    )

    tk.Label(main_frame, text="Izvoz šifer kemikalij:", font=("Arial", 10, "bold")).pack(
        anchor="w", pady=(10, 0)
    )
    izvoz_kem_label = tk.Label(main_frame, text="Ni izbrano", fg="gray")
    izvoz_kem_label.pack(anchor="w", pady=(0, 5))
    tk.Button(
        main_frame,
        text="Izberi Excel za kemikalije",
        command=select_izvoz_kemikalije,
    ).pack(
        fill="x", pady=(0, 10)
    )

    tk.Label(main_frame, text="Izhodno datoteko:", font=("Arial", 10, "bold")).pack(
        anchor="w", pady=(10, 0)
    )
    output_label = tk.Label(main_frame, text="Ni izbrano", fg="gray")
    output_label.pack(anchor="w", pady=(0, 5))
    tk.Button(main_frame, text="Izberi izhodno datoteko", command=select_output).pack(
        fill="x", pady=(0, 10)
    )

    tk.Button(
        main_frame,
        text="Zaženi primerjavo",
        command=run_comparison,
        bg="green",
        fg="white",
        font=("Arial", 12, "bold"),
    ).pack(fill="x", pady=10)

    root.mainloop()
    return result["code"]


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Primerja ključe raztopin in kemikalij iz receptur "
            "s šiframi iz ločenih excel katalogov."
        )
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Zaženi v GUI modo (izbira folderjev, datotek in nastavitev).",
    )
    parser.add_argument(
        "receptura",
        nargs="*",
        type=Path,
        help="Ena ali več datotek recepture (.xlsm). Brez argumenta: vse .xlsm v mapi skripte.",
    )
    parser.add_argument(
        "--izvoz-raztopine",
        type=Path,
        default=script_dir / DEFAULT_IZVOZ_RAZTOPINE,
        help=f"Excel s šiframi raztopin (privzeto: {DEFAULT_IZVOZ_RAZTOPINE})",
    )
    parser.add_argument(
        "--izvoz-kemikalije",
        type=Path,
        default=script_dir / DEFAULT_IZVOZ_KEMIKALIJE,
        help=f"Excel s šiframi kemikalij (privzeto: {DEFAULT_IZVOZ_KEMIKALIJE})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=script_dir / DEFAULT_OUTPUT,
        help=f"Izhodno poročilo (privzeto: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    # Če ni nobenega dodatnega argumenta, zaženi GUI
    if args.gui or len(sys.argv) == 1:
        return run_gui_mode()

    izvoz_paths_by_tip = {
        TIP_RAZTOPINA: args.izvoz_raztopine.expanduser().resolve(),
        TIP_KEMIKALIJA: args.izvoz_kemikalije.expanduser().resolve(),
    }
    for tip, izvoz_path in izvoz_paths_by_tip.items():
        if not izvoz_path.is_file():
            print(
                f"Napaka: izvoz šifer za '{tip}' ne obstaja: {izvoz_path}",
                file=sys.stderr,
            )
            return 1

    receptura_files = find_receptura_files(
        script_dir,
        [p.expanduser().resolve() for p in args.receptura],
    )
    if not receptura_files:
        print(
            f"Napaka: ni datotek recepture (.xlsm) v {script_dir}",
            file=sys.stderr,
        )
        return 1

    try:
        catalogs: dict[str, dict[str, str]] = {}
        catalog_all_by_tip: dict[str, list[str]] = {}
        for tip, izvoz_path in izvoz_paths_by_tip.items():
            catalog, catalog_all = load_catalog(
                izvoz_path,
                CATALOG_LOOKUP_COLUMNS_BY_TIP.get(tip, (COL_SIFRA,)),
            )
            catalogs[tip] = catalog
            catalog_all_by_tip[tip] = catalog_all
    except (OSError, ValueError) as e:
        print(f"Napaka pri branju kataloga: {e}", file=sys.stderr)
        return 1

    detail_rows: list[dict[str, str]] = []
    matched_sifre_by_tip: dict[str, set[str]] = {
        TIP_RAZTOPINA: set(),
        TIP_KEMIKALIJA: set(),
    }

    for rec_path in receptura_files:
        try:
            extracted = extract_raztopine_from_workbook(rec_path)
        except OSError as e:
            print(f"Napaka pri {rec_path.name}: {e}", file=sys.stderr)
            continue
        group_label = group_name_for_file(rec_path, [script_dir])
        for item in extracted:
            tip = item["tip"]
            status, sifra_kat, nacin = match_kljuc(item["kljuc"], catalogs.get(tip, {}))
            if sifra_kat:
                matched_sifre_by_tip.setdefault(tip, set()).add(sifra_kat)
            detail_rows.append(
                {
                    **item,
                    "status": status,
                    "sifra_katalog": sifra_kat,
                    "nacin": nacin,
                    "_group": group_label,
                }
            )

    if not detail_rows:
        print(
            "Opozorilo: v recepturah ni vrstic tipa „raztopina“ ali „kemikalija“ s ključem preverjanja.",
            file=sys.stderr,
        )

    out_path = args.output.expanduser().resolve()
    try:
        write_report(
            out_path,
            detail_rows,
            catalog_all_by_tip,
            matched_sifre_by_tip,
            receptura_files,
            izvoz_paths_by_tip,
        )
    except OSError as e:
        print(f"Napaka pri shranjevanju: {e}", file=sys.stderr)
        return 1

    unikatni = {(r["tip"], r["kljuc"]) for r in detail_rows}
    ujemanja = sum(
        1
        for tip, kljuc in unikatni
        if any(
            r["status"] == "ujemanje"
            for r in detail_rows
            if r["tip"] == tip and r["kljuc"] == kljuc
        )
    )
    print(f"Obdelanih receptur: {len(receptura_files)}")
    print(f"Vrstic raztopin/kemikalij: {len(detail_rows)}")
    print(f"Unikatnih ključev (tip + ključ): {len(unikatni)}")
    print(f"Ujemanj z katalogom: {ujemanja}")
    print(f"Brez ujemanja: {len(unikatni) - ujemanja}")
    print(f"Poročilo: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
