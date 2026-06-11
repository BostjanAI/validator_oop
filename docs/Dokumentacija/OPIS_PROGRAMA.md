# MES Excel Validator — Tehnični opis za programerja

**Verzija:** 1.1.0+ | **Python:** 3.12 | **Datum:** junij 2026

---

## TL;DR

Validacijski engine za MES (Manufacturing Execution System) recepture v Excel formatu. Naloži `.xlsx`/`.xlsm`, razčleni liste v `list[dict]`, nad njimi poganja ~40 pluggable pravil (row-level, sheet-level, workbook-level), zbira tipizirana `ValidationError` sporočila in na koncu generira Excel poročilo. Cel pipeline je čist OOP z registry pattern, DI, template method in builder pattern za shared state.

---

## 1. Domena in namen

V farmacevtski proizvodnji se recepture (IPO — Interne Proizvodne Operacije) vodijo kot strukturirani Excel dokumenti. Vsak list (sheet) je zaporedje korakov, vsak korak ima: tip objekta, tip podatka, ključ, navodilo, kontrolne stolpce itd.

Validator preverja:
- **Strukturo** — ali so prisotni vsi zahtevani stolpci, ali so koraki pravilno oštevilčeni
- **Polja** — ali so ključi v pravilnem formatu, ali so tipi objektov dovoljeni, ali je enota veljavna
- **Relacije** — ali ima vsaka kemikalija ustrezno maso, ali so ključi unikatni, ali so časovni pari konsistentni
- **Kontrole** — kompleksna logika kontrolnih stolpcev (zaklenipolja, kontrolaInterval, kontrolaMase, kontrolaCasa, aliObstajaPogoj...)
- **SOP skladnost** — navzkrižno preverjanje z Word SOP dokumenti
- **Katalogi** — preverjanje šifer kemikalij/raztopin proti zunanjim šifrantom

---

## 2. Arhitektura — 30.000 ft

```
┌──────────────────────────────────────────────────────────────┐
│  main.py / UI (Tkinter / Qt)                                 │
│  ─── vstopna točka, CLI parser, GUI launcher ───             │
└───────────────────────────┬──────────────────────────────────┘
                            │ konstruira
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  ValidatorEngine                                             │
│  ─── orkestrator: load → filter → validate → report ───     │
│                                                              │
│  ┌───────────────┐     ┌──────────────┐                     │
│  │ ExcelLoader   │     │ RuleEngine   │                     │
│  │ + Parser      │     │ + Registry   │                     │
│  └───────┬───────┘     └──────┬───────┘                     │
│          │                    │                              │
└──────────┼────────────────────┼──────────────────────────────┘
           │                    │
           ▼                    ▼
┌─────────────────┐   ┌────────────────────────────────────────┐
│ LoadedWorkbook  │   │ SharedContextBuilder → SharedContext   │
│ .values         │   │ (pre-computed indices per sheet)       │
│ .formulas       │   ├────────────────────────────────────────┤
│ .headers        │   │ RowRule / SheetRule / WorkbookRule     │
└─────────────────┘   │ (40+ concrete implementations)        │
                      └──────────────────────┬─────────────────┘
                                             │ yield
                                             ▼
                      ┌────────────────────────────────────────┐
                      │ list[ValidationError]                   │
                      │ → ValidationReport                     │
                      │ → ReportWriter (.xlsx / .json)         │
                      └────────────────────────────────────────┘
```

---

## 3. Moduli v detajlu

### 3.1 `core/` — Jedro ogrodja

| Datoteka | Kaj dela |
|----------|----------|
| `validator_engine.py` | Top-level orkestrator. Sprejme pot, koordinira load, filter, run, report. |
| `rule_engine.py` | Iterira liste, gradi `SharedContext`, razvrsti pravila po tipu (Row/Sheet/Workbook), poganja jih, zbira errore, aplicira bypass/strict. |
| `shared_context.py` | `SharedContext` dataclass + `SharedContextBuilder`. Pre-computed lookup tabele, ki jih pravila samo berejo. |
| `config.py` | `ValidatorConfig` — vsi runtime knobs: bypass rules, bypass codes, strict mode, domenske zastavice. |
| `error.py` | `ValidationError` (slots dataclass) + `Severity` enum. |
| `report.py` | `ValidationReport` — agregator errorjev s filtriranjem in statistiko. |
| `constants.py` | ~470 vrstic: regex patterni, dovoljene vrednosti, prevodi kod, mapping-i. |

### 3.2 `rules/` — Validacijska pravila

| Datoteka | Tip | # Pravil | Fokus |
|----------|-----|----------|-------|
| `base_rule.py` | ABC hierarhija | - | `BaseRule` → `RowRule` / `SheetRule` / `WorkbookRule` |
| `rule_registry.py` | Singleton register | - | `@register` dekorator, DI pri instanciranju |
| `builtin/structural.py` | SheetRule | 2 | Prisotnost stolpcev, sekvenčnost korakov |
| `builtin/field.py` | RowRule | 10 | Format ključev, tip objekta, enote, navodilo |
| `builtin/relational.py` | SheetRule | 6 | Duplikat ključev, pari kemikalija-masa, časovni pari |
| `builtin/control.py` | Row+Sheet | 21 | Kontrolni stolpci (zakleni, interval, masa, čas...) |
| `builtin/sop_compliance_rule.py` | WorkbookRule | 1 | Cross-check z Word SOP |
| `builtin/catalog_code_rule.py` | RowRule | 1 | Preverjanje šifer proti šifrantom |

### 3.3 `excel/` — I/O plast

| Datoteka | Naloga |
|----------|--------|
| `excel_loader.py` | Odpre `.xlsx` z `openpyxl` (enkrat data_only, enkrat surove formule), vrne `LoadedWorkbook` |
| `workbook_parser.py` | Pretvori `openpyxl.Worksheet` → `list[dict[header, value]]` |
| `report_writer.py` | Zapiše validacijski report kot Excel (2 lista: issues + summary) ali JSON |
| `catalog_loader.py` | Naloži eksterne šifrante kemikalij/raztopin za cross-validation |
| `sop_loader.py` | Razčleni `.docx` SOP prek `python-docx` |

### 3.4 `ui/` — GUI

Tri implementacije z fallback verigo: **Qt → Themed Tkinter → Classic Tkinter**. Vse kličejo isti `ValidatorEngine` — logika ni prepletena z UI.

### 3.5 `utils/` — Helpers

`helpers.py` centralizira vso regex-heavy logiko: parsanje intervalov, časovnih fraz, enot, ključev, formul. Ostalo: logger setup, file paths, progress tracking.

---

## 4. Ključni design patterns

### 4.1 Template Method

```python
class RowRule(BaseRule):
    def run(self, rows, **kwargs) -> list[ValidationError]:
        # skeleton: iterira vrstice, kliče evaluate(), zbere errore
        for index, row in enumerate(rows):
            for error in self.evaluate(row, context):  # ← podrazred implementira
                errors.append(error)
        return errors

    @abstractmethod
    def evaluate(self, row, context) -> Iterable[ValidationError] | None: ...
```

Konkreten razred nikoli ne overrida `run()`. Samo implementira `evaluate()` / `evaluate_sheet()` / `evaluate_workbook()`.

### 4.2 Registry + Auto-registration

```python
# rules/rule_registry.py
@register   # dekorator na nivoju modula
class MyRule(RowRule):
    name = "my_rule"
    code = "MY"
    ...
```

Ob uvozu modula se razred registrira v `default_registry`. `register_all()` triggerja import vseh modulov. `RuleEngine` nikoli ne sklicuje na konkreten razred — pozna samo `registry.instantiate()`.

### 4.3 Dependency Injection (reflection-based)

```python
# RuleRegistry.instantiate() pogleda __init__ signature:
class CatalogCodeRule(RowRule):
    def __init__(self, *, catalog_data=None, logger=None):
        ...
```

`inspect.signature` ugotovi kateri parametri obstajajo in injicira samo tiste iz `rule_dependencies` dict-a. Zero config — pravilom ni treba vedeti za DI container.

### 4.4 Builder (SharedContext)

`SharedContextBuilder.build(rows, columns)` pokliče 7+ privatnih `_build_*` metod, ki iz flat list vrstic zgradijo indeksirane lookup tabele:

| Index | Namen |
|-------|-------|
| `step_to_controls` | Korak → set kontrolnih imen (O(1) lookup namesto O(n) scan) |
| `step_to_row_indices` | Korak → vrstice (za relacijska pravila) |
| `keys_by_type` | Tip podatka → ključ → vrstice |
| `checkbox_states` | Ključ → 0/1 |
| `zakleni_param1_steps_by_tab` | Zavihek → ključ → zaklenjeni koraki |
| `equipment_keys` | Set ključev, ki so oprema |

Ta pre-computation eliminira O(n²) vzorce v pravilih. Vsako pravilo dobi `SharedContext` read-only pred izvajanjem.

### 4.5 Value Objects (Immutable dataclasses)

`ValidationError`, `RuleContext` — frozen, slots-based. `RuleContext.with_row()` vrne nov primerek (functional update).

### 4.6 Strategy (implicitna)

`RuleEngine` razvrsti pravila z `isinstance` check-om v tri kategorije in pokliče ustrezno metodo:
- `RowRule` → `rule.run(rows)` (interno iterira vrstice)
- `SheetRule` → `rule.run(rows)` (dobi cel list naenkrat)
- `WorkbookRule` → `rule.run_workbook(all_sheets)` (dobi vse liste)

---

## 5. Podatkovni tok — korak za korakom

```
1. main.py: parse CLI args
2. register_all()  → import-time registration v default_registry
3. ValidatorConfig(...) iz CLI args
4. ExcelLoader.load(path)
   ├── openpyxl.load_workbook(data_only=True)  → computed values
   ├── openpyxl.load_workbook(data_only=False) → raw formulas (optional)
   └── WorkbookParser.parse(wb) → dict[sheet_name, list[dict[col, val]]]
5. ValidatorEngine._filter_sheets_by_required_columns()
   └── ohrani samo liste z "št. Koraka", "Navodilo" ipd.
6. RuleEngine.run(filtered_data):
   ├── registry.instantiate(**deps) → sorted list[BaseRule]
   ├── filter out bypassed rules
   ├── FOR EACH sheet:
   │   ├── SharedContextBuilder.build(rows, columns) → SharedContext
   │   ├── inject SharedContext into all rules
   │   ├── run RowRules → collect errors
   │   └── run SheetRules → collect errors
   ├── run WorkbookRules → collect errors
   ├── apply strict_mode (WARNING → ERROR promotion)
   └── return list[ValidationError]
7. ValidationReport.extend(errors)
8. ReportWriter.write_excel_report(path, issues)
   └── 2 lista: "Napake" (vse issues) + "Povzetek" (count po kodi)
```

---

## 6. Kako dodaš novo pravilo

1. Ustvari razred v ustrezni datoteki (`field.py`, `control.py`, ...):

```python
from validator_oop.rules import register

@register
class MojeNovoRule(RowRule):
    name = "moje_novo_pravilo"
    code = "NOVO"
    severity = Severity.WARNING
    priority = 150

    def evaluate(self, row, context):
        val = row.get("Navodilo", "")
        if nekaLogika(val):
            yield self.build_error("Opis napake", context=context, column="Navodilo")
```

2. To je vse. Ni spremembe v `RuleEngine`, ni factory-ja, ni config-a. `@register` + import v `register_all()` je dovolj.

Če praviš `SheetRule`, implementiraš `evaluate_sheet(rows, context)`. Če praviš `WorkbookRule`, implementiraš `evaluate_workbook(workbook_data, context)`.

---

## 7. SharedContext — zakaj obstaja

Problem: Pravilo "zaklenipolja" mora vedeti, kateri koraki imajo kontrolo "zaklenipolja" v Param1 (cross-row lookup). Brez shared context-a bi vsaka vrstica naredila linearni scan čez vse ostale vrstice → O(n²).

Rešitev: `SharedContextBuilder` pred izvajanjem pravil enkrat zgradi indekse. Vsa pravila nato delajo O(1) dict lookup namesto O(n) scan.

Primer:
```python
# V pravilu:
zakleni_steps = self.shared.zakleni_param1_steps_by_tab.get(tab, {})
if step in zakleni_steps.get(key, []):
    # ta korak je zaklenjen za ta ključ
```

---

## 8. Error model

```python
@dataclass(slots=True)
class ValidationError:
    rule_name: str          # "zaklenipolja"
    message: str            # "Korak 5: polje 'Navodilo' mora biti prazno..."
    code: str               # "CTRL_ZAKLENI"
    severity: Severity      # ERROR / WARNING / INFO
    sheet: str | None       # "Receptura 1"
    workbook: str | None    # "MOD-QA.xlsx"
    row_index: int | None   # 7 (Excel row)
    column: str | None      # "Navodilo"
    payload: dict | None    # arbitrary debug data
```

Error kode so prevedene v slovenščino za report (mapping v `constants.py`).

---

## 9. Dependency graph

```
main.py ──→ core/validator_engine ──→ core/rule_engine ──→ rules/rule_registry
                 │                         │                       │
                 │                         ├──→ core/shared_context
                 │                         ├──→ core/error
                 │                         └──→ core/config
                 │
                 └──→ excel/excel_loader ──→ excel/workbook_parser
                           │
                           └──→ openpyxl

rules/builtin/* ──→ rules/base_rule ──→ core/error
                 ──→ core/constants
                 ──→ utils/helpers
```

**Smer je strogo navzdol.** `core/` nikoli ne importa iz `rules/`, `excel/` ali `ui/`. `rules/` importa `core/` ampak ne `excel/`. To zagotavlja testabilnost — `core/` testiraš z mock podatki brez Excel datotek.

---

## 10. Zanimivi implementation details

### Dual workbook load
Excel se naloži dvakrat: `data_only=True` za computed values, `data_only=False` za surove formule. To je openpyxl limitation — ne moreš dobiti obojega iz enega load-a.

### Row offset
Excel šteje vrstice od 1, header je v row 1, podatki od row 2. `row_offset=2` se prišteje k indeksu v `list` da dobiš pravo Excel vrstico v error sporočilu.

### Priority ordering
Pravila se izvajajo po `priority` (nižje = prej). `structural` pravila imajo priority ~10 (preverijo ali stolpci sploh obstajajo), `field` ~50, `control` ~100. Tako se pri early-exit (`stop_on_first_error`) najprej ulovijo fundamentalni problemi.

### Bypass mehanizem
`ValidatorConfig` ima `bypass_rules` (preskoči celo pravilo) in `bypass_codes` (preskoči specifične error kode v outputu). Strogi način (`strict_mode`) promovira vse WARNING v ERROR.

### Auto-fix capability
`WorkbookFixer` lahko aplicira predlagane popravke nazaj v Excel datoteko (kopijo). Pravila lahko v `payload` vrnejo fix metadata.

---

## 11. Tech stack

| Komponenta | Knjižnica |
|------------|-----------|
| Excel I/O | `openpyxl` |
| GUI | `tkinter` (stdlib) / `PyQt6` |
| SOP parsing | `python-docx` |
| Testing | `pytest` |
| Packaging | PyInstaller (za .exe distribucijo) |

Brez frameworkov, brez ORM-ja, brez web layerja. Pure Python, single-process, sinhrono. Datoteka noter, report ven.

---

## 12. Znane trade-offs in tech debt

| Zadeva | Status |
|--------|--------|
| `control.py` = 2000+ vrstic | Monolitna datoteka z 21 pravili + helperji. Refactoring bi zahteval prestrukturiranje shared helpers. |
| `SharedContextBuilder` raste z vsakim novim pravilom | Vsako novo medvrstično stanje = nova `_build_*` metoda + novo polje v dataclass. |
| `register_all()` je implicitna zahteva | Če ga ne pokličeš, engine tiho procesira 0 pravil brez errora. |
| `constants.py` = flat file | 470+ vrstic brez subgrouping-a. |
| Ni concurrency zaščite | `validation_progress.json` se piše brez locka — problematično pri concurrent GUI validacijah. |

---

## 13. Kako pognaš

```bash
# CLI - validacija ene datoteke
python -m validator_oop receptura.xlsx

# CLI z outputom
python -m validator_oop receptura.xlsx --output report.xlsx --format excel

# CLI s katalogi
python -m validator_oop receptura.xlsx --catalog-raztopine sifrant.xlsx

# GUI
python -m validator_oop --gui

# Strict mode (warnings = errors)
python -m validator_oop receptura.xlsx --strict

# Apply auto-fixes
python -m validator_oop receptura.xlsx --apply-fixes
```

---

## 14. Zaključek

V bistvu je to **domain-specific linter za Excel recepture**. Analogija: ESLint za JavaScript, samo da je vhod Excel, pravila so farmacevtsko-specifična, in output je Excel report. Arhitektura je čista, razširljiva (plugin pattern), in dovolj preprosta da razumeš celoten flow v 10 minutah. Glavni complexity je v domenskem znanju — 40 pravil pokriva zelo specifično farmacevtsko logiko (kontrole, zakleni polja, SOP skladnost), ne v tehničnem ogrodju samem.
