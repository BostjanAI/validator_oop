# Validator OOP — Tehnična arhitekturna dokumentacija

**Verzija:** 1.1.0 (Build 125, 2026-02-20)  
**Jezik:** Python 3.12  
**Datum revizije:** 19. 3. 2026

---

## 1. Struktura projekta

```
validator_oop/
│
├── main.py                          ← CLI vstopna točka + zaganjanje GUI
├── requirements.txt
├── CHANGELOG.md
├── validation_progress.json         ← Sledilnik metrik izvajanja
│
├── core/                            ← Jedro validacijskega ogrodja
│   ├── _version.py
│   ├── constants.py
│   ├── config.py
│   ├── error.py
│   ├── report.py
│   ├── rule_engine.py
│   ├── validator_engine.py
│   └── shared_context.py
│
├── rules/                           ← Definicije pravil
│   ├── base_rule.py
│   ├── rule_registry.py
│   └── builtin/
│       ├── __init__.py              ← Nalagalnik register_all()
│       ├── structural.py
│       ├── field.py
│       ├── relational.py
│       ├── control.py
│       └── sop_compliance_rule.py
│
├── excel/                           ← Plast Excel I/O
│   ├── excel_loader.py
│   ├── workbook_parser.py
│   ├── report_writer.py
│   └── sop_loader.py
│
├── utils/                           ← Pomožne funkcije
│   ├── helpers.py
│   ├── logger.py
│   ├── file_paths.py
│   └── validation_progress.py
│
├── ui/                              ← Implementacije GUI
│   ├── main_window.py               ← Tkinter (klasičen)
│   ├── main_window_themed.py        ← Tkinter (črno/rumena tema)
│   ├── main_window_qt.py            ← PyQt6
│   └── run_validator.py             ← Usmerjevalnik GUI
│
├── tests/
│   ├── conftest.py
│   ├── test_control_rules.py
│   ├── test_field_rules.py
│   ├── test_relational_rules.py
│   ├── test_structural_rules.py
│   └── test_equipment_detection.py
│
└── scripts/
    ├── bump_version.py
    ├── analytics_report.py
    └── export_rules_to_docx.py
```

### Vloge modulov

| Modul | Vloga |
|-------|-------|
| `core/` | Jedro ogrodja: podatkovni modeli (`error.py`, `config.py`, `report.py`), izračun skupnega stanja (`shared_context.py`), pogon pravil (`rule_engine.py`), vrhnji orkestrator (`validator_engine.py`) |
| `rules/` | Osnovni razredi pravil, register in 30+ konkretnih implementacij pravil |
| `excel/` | Ves Excel I/O: nalaganje delovnih zvezkov z `openpyxl`, razčlenjevanje listov v slovarje, pisanje poročil, nalaganje SOP Word dokumentov |
| `utils/` | Čiste pomožne funkcije: normalizacija nizov, razčlenjevanje števil, ekstrakcija časa/enot, razčlenjevanje formul, sledenje napredku |
| `ui/` | Tri implementacije GUI (Tkinter klasičen, Tkinter s temo, PyQt6) z enotnim usmerjevalnikom |
| `scripts/` | Orodja za razvijalce: dvig verzije, generiranje analitičnih CSV/grafov, izvoz pravil v DOCX |
| `tests/` | pytest testna zbirka, ena datoteka na kategorijo pravil |

### Vstopne točke

- **`main.py`** — CLI vstopna točka. Razčleni argumente (`--gui`, `--input`, `--sop`, `--output`, `--gui-style`). Preusmeri na `run_gui()` ali neposredno konstruira `ValidatorEngine` in pokliče `validate()`.
- **`ui/run_validator.py` → `run_gui()`** — Usmerjevalnik GUI z rezervno verigo: Qt → Tkinter s temo → klasičen Tkinter.

---

## 2. Ključni razredi in OOP zasnova

### 2.1 `ValidatorEngine` (`core/validator_engine.py`)

**Odgovornost:** Vrhnja orkestrizacija — sprejme pot datoteke, koordinira nalaganje, filtriranje in izvajanje pravil, vrne `ValidationReport`.

**Ključni atributi:**
- `rule_engine: RuleEngine`
- `excel_loader: ExcelLoader`
- `include_formulas: bool`
- `sop_data: SOPData | None`

**Ključne metode:**
- `validate(workbook_path) → ValidationReport` — glavni javni API
- `validate_loaded(loaded: LoadedWorkbook) → ValidationReport` — sprejme predhodno naložen delovni zvezek
- `_filter_sheets_by_required_columns(values, headers)` — preskoči liste brez `REQUIRED_COLUMNS`

**Razmerja:** Sestavlja `RuleEngine` + `ExcelLoader`. Odvisno od `LoadedWorkbook`, `ValidationReport`.

---

### 2.2 `RuleEngine` (`core/rule_engine.py`)

**Odgovornost:** Iterira po listih, posreduje pravila po tipu (Row/Sheet/Workbook), zbira in filtrira napake.

**Ključni atributi:**
- `registry: RuleRegistry`
- `config: ValidatorConfig`
- `rule_dependencies: dict` — injicirano v pravila ob instanciranju

**Ključne metode:**
- `run(workbook_data, *, ...) → list[ValidationError]` — glavna zanka; gradi `SharedContext` na list, izvaja vse tipe pravil
- `_build_shared_context(rows, columns) → SharedContext`
- `_filter_errors(errors) → list[ValidationError]` — aplicira `bypass_codes`

**Razmerja:** Poseduje `RuleRegistry`, delegira na `SharedContextBuilder`. Producira `list[ValidationError]`.

---

### 2.3 `SharedContext` + `SharedContextBuilder` (`core/shared_context.py`)

**Odgovornost:** Vnaprej izračunano, nespremenljivo medvrstično stanje, ki ga pravila uporabljajo med vrednotenjem. Odpravlja ponavljajoče linearne preglede znotraj logike pravil.

**`SharedContext` je zamrznjen `@dataclass`** s predhodno indeksiranimi preslikavami:

| Atribut | Tip | Opis |
|---------|-----|------|
| `checkbox_states` | `dict[int, int]` | Indeks vrstice → stanje potrditvenega polja 0/1 |
| `step_to_controls` | `dict[int, list]` | Številka koraka → seznam prisotnih `ControlInstance` |
| `step_to_row_indices` | `dict[int, list[int]]` | Številka koraka → indeksi vrstic |
| `keys_by_type` | `dict[str, list[str]]` | Tip podatka → seznam ključev |
| `section_by_row` | `dict[int, str]` | Indeks vrstice → ime sekcije |
| `tab_by_row` | `dict[int, str]` | Indeks vrstice → ime zavihka |
| `zakleni_param1_steps_by_tab` | `dict[str, dict[str, list[int]]]` | Zavihek → ključ → zaklenjeni koraki |
| `ali_pogoj_step_locations_by_tab` | `dict[str, dict[str, list]]` | Zavihek → korak → vnosi pogoja |
| `equipment_keys` | `set[str]` | Ključi zaznani kot oprema |

**`SharedContextBuilder.build(rows, columns)`** pokliče 7 zasebnih `_build_*` metod zaporedoma, da zapolni vse indekse iz ravnega seznama slovarjev vrstic.

**Razmerja:** Porabljajo (samo za branje) vsi `RowRule` in `SheetRule` primerki prek `BaseRule.shared`.

---

### 2.4 Hierarhija `BaseRule` (`rules/base_rule.py`)

```
BaseRule (ABC)
├── RowRule (ABC)       — evaluate(row, context) na vrstico
├── SheetRule (ABC)     — evaluate_sheet(rows, context) na list
└── WorkbookRule (ABC)  — evaluate_workbook(workbook_data, context) čez vse liste
```

**Atributi na nivoju razreda `BaseRule`** (nastavljeni v vsaki podrazredu):

| Atribut | Namen |
|---------|-------|
| `name: str` | Enolični identifikator, uporabljen v registru in poročilih |
| `code: str` | Predpona kode napake (npr. `"CTRL"`, `"KEY"`) |
| `severity: Severity` | Privzeta resnost (`ERROR`/`WARNING`/`INFO`) |
| `priority: int` | Vrstni red izvajanja (nižje = prej) |
| `target_sheets: list[str] \| None` | Filter imen listov (`None` = vsi listi) |
| `tags: list[str]` | Iskalne oznake |

**`RowRule.run()`** iterira vrstice, pokliče `evaluate(row, context)`, zbere rezultate.  
**`SheetRule.run()`** pokliče `evaluate_sheet(rows, context)` enkrat na list.  
**`WorkbookRule.run_workbook()`** pokliče `evaluate_workbook(workbook_data, context)` enkrat skupaj.

**`RuleContext`** (zamrznjen dataclass) nosi `sheet`, `row_index`, `workbook`, `shared` — posredovan vsakemu klicu `evaluate()`. `with_row()` / `with_sheet()` vrneta nove primerke (nespremenljiva posodobitev).

---

### 2.5 `RuleRegistry` (`rules/rule_registry.py`)

**Odgovornost:** Shranjuje razrede pravil, jih izpostavlja za instanciranje z vbrizgavanjem odvisnosti.

**Ključne metode:**
- `register(rule_cls)` — shrani razred po `rule_cls.name`; uporabno tudi kot dekorator `@register`
- `instantiate(*, logger_factory, **dependencies) → list[BaseRule]` — uporablja `inspect.signature` za injiciranje samo deklariranih odvisnosti; razvrsti po `priority`
- `all() → tuple` — vrne vse registrirane razrede

**Globalni singleton:** `default_registry = RuleRegistry()` v `rules/rule_registry.py`.  
**Dekorator na nivoju modula:** `@register` v `rules/__init__.py` delegira na `default_registry.register`.  
**Nalagalnik:** `register_all()` v `rules/builtin/__init__.py` uvozi vseh 5 vgrajenih modulov pravil, kar sproži registracijo z dekoratorjem.

---

### 2.6 `ValidationError` (`core/error.py`)

```python
@dataclass(slots=True)
class ValidationError:
    rule_name: str
    message: str
    code: str
    severity: Severity
    sheet: str | None
    workbook: str | None
    row_index: int | None
    column: str | None
    payload: dict | None
```

Nespremenljiv vrednostni objekt (slots). Serializiran prek `to_dict()`. `Severity` je `str` Enum: `INFO < WARNING < ERROR`.

---

### 2.7 `ValidatorConfig` (`core/config.py`)

**Odgovornost:** Konfigurizacija med izvajanjem, posredovana skozi celoten cevovod. Nadzira, katera pravila/kode se preskočijo, strogi način, vedenjske zastavice.

Opazne zastavice:
- `bypass_rules: list[str]` — imena pravil za popolno preskočitev
- `bypass_codes: list[str]` — kode napak za zatiranje iz izhoda
- `strict_mode: bool` — promovira vsa `WARNING` v `ERROR`
- `bypass_zakleni_*` zastavice — domeno-specifični vedenjski obvodi za variante pravila `zaklenipolja`
- `sop_data_path: str | None`, `enable_sop_validation: bool`

`DEFAULT_CONFIG = ValidatorConfig()` je osnova brez operacij.

---

### 2.8 `ValidationReport` (`core/report.py`)

**Odgovornost:** Agregira vse primerke `ValidationError`; zagotavlja metode za filtriranje in povzetek.

**Ključne metode:**
- `add_error(error)`, `extend(errors)`
- `is_valid() → bool` — `True` če ni napak resnosti `ERROR`
- `counts_by_severity()`, `counts_by_code()`
- `errors_by_sheet() → dict[str, list]`
- `filter_by_severity(sev)`, `filter_by_code(code)`
- `to_dict() → dict` — popoln JSON-serializabilen izhod

---

### 2.9 Excel plast

**`ExcelLoader`** (`excel/excel_loader.py`) — odpre `.xlsx`/`.xlsm` prek `openpyxl`. Ko je `include_formulas=True`, pokliče `WorkbookParser` dvakrat (enkrat z `data_only=True` za vrednosti, enkrat za surove formule). Vrne `LoadedWorkbook`.

**`LoadedWorkbook`** (zamrznjen dataclass) — vsebuje `values`, `formulas`, `headers` kot `dict[sheet_name, list[dict]]`. Metode: `get_sheet_data(name)`, `get_headers(name)`.

**`WorkbookParser`** — pretvori `openpyxl` objekte `Worksheet` v `list[dict[ime_stolpca, vrednost]]`. Ustavi se pri praznih vrsticah. Normalizira imena glav.

**`ReportWriter`** — piše validacijski izhod kot Excel (2 lista: seznam težav + štetje po kodah s slovenskimi prevodi) ali JSON.

**`SOPLoader` / `SOPData`** — razčleni `.docx` SOP dokumente prek `python-docx`. Iz tabel in odstavkov ekstrahira strukturirane objekte `SOPRequirement`. Uporablja ga `SOPComplianceRule`.

---

## 3. Arhitektura validacijske logike

### 3.1 Kje so definirana pravila

Vsa pravila se nahajajo v `rules/builtin/` v 5 datotekah:

| Datoteka | Tip pravila | Število | Domena |
|----------|-------------|---------|--------|
| `structural.py` | `SheetRule` | 2 | Prisotnost stolpcev, številčenje korakov |
| `field.py` | `RowRule` | 10 | Validacija vrednosti na celico |
| `relational.py` | `SheetRule` | 6 | Medvrstična validacija ključev in parov |
| `control.py` | `RowRule` + `SheetRule` | ~18 | Logika kontrolnih stolpcev |
| `sop_compliance_rule.py` | `WorkbookRule` | 1 | Skladnost SOP dokumenta |

Vsak razred pravila je dekoriran z `@register` (iz `rules/__init__.py`), ki ga ob uvozu registrira v `default_registry`.

### 3.2 Kako se pravila izvajajo

`RuleEngine.run()` sledi tej sekvenci na list:

1. Zgradi `SharedContext` prek `SharedContextBuilder.build(rows, columns)`
2. Pokliče `SharedContext.set_shared_context(ctx)` na vsakem primerku pravila
3. Izvede vse primerke `RowRule` → pokliče `rule.run(rows, ...)`, ki interno iterira vrstice
4. Izvede vse primerke `SheetRule` → pokliče `rule.run(rows, ...)`
5. Po vseh listih: izvede vse primerke `WorkbookRule` → pokliče `rule.run_workbook(workbook_data, ...)`
6. Zbere vse vrnjene `list[ValidationError]`
7. Aplicira promocijo `strict_mode` in filtriranje `bypass_codes`

### 3.3 Kako se zbirajo rezultati

Vsaka metoda `evaluate()` / `evaluate_sheet()` / `evaluate_workbook()` vrne ali generira `Iterable[ValidationError]`. `RuleEngine.run()` jih akumulira v raven `list`. Seznam se posreduje `ValidationReport.extend()` v `ValidatorEngine`.

---

## 4. Tok podatkov — dejanska implementacija

```
[Vhod: pot .xlsx / .xlsm datoteke]
        │
        ▼
ExcelLoader.load(path)
  ├── openpyxl.load_workbook(data_only=True)  → delovni zvezek vrednosti
  └── openpyxl.load_workbook(data_only=False) → delovni zvezek formul (če include_formulas=True)
        │
        ▼
WorkbookParser.parse(workbook)
  ├── _normalize_headers(header_row)
  ├── Za vsako vrstico: zgradi dict {ime_stolpca: vrednost_celice}
  └── Ustavi se pri prvi prazni vrstici
        │
        ▼
LoadedWorkbook
  .values   = dict[ime_lista → list[dict]]
  .formulas = dict[ime_lista → list[dict]]
  .headers  = dict[ime_lista → list[str]]
        │
        ▼
ValidatorEngine._filter_sheets_by_required_columns()
  └── Ohrani samo liste z vsaj enim stolpcem REQUIRED_COLUMN
        │
        ▼
RuleEngine.run(workbook_data, ...)
  ├── Za vsak list:
  │     ├── SharedContextBuilder.build(rows, columns) → SharedContext
  │     │     (indeksi: korak→kontrole, korak→vrstice, ključi po tipu,
  │     │      zakleni koraki, lokacije aliObstajaPogoj, stanja potrditvenih polj, ...)
  │     ├── RowRules: za vsako vrstico → evaluate(row, RuleContext)
  │     └── SheetRules: evaluate_sheet(rows, RuleContext)
  └── WorkbookRules: evaluate_workbook(all_data, RuleContext)
        │
        ▼
list[ValidationError]
        │
        ▼
ValidationReport.extend(errors)
        │
        ├── ReportWriter.write_excel_report()  → .xlsx z 2 listoma
        ├── ReportWriter.write_json_report()   → .json
        └── UI: prikazano v povzetnem dialogu GUI
```

---

## 5. Načrtovalski vzorci

### 5.1 Metoda predloge (Template Method)

`BaseRule.run()` / `run_workbook()` definirata skelet algoritma (iteracija vrstic, zbiranje napak, obravnava izjem). Podrazredi implementirajo samo `evaluate()` / `evaluate_sheet()` / `evaluate_workbook()`. Konkretni razredi pravil nikoli ne prevladajo `run()`.

### 5.2 Register / Vtičnik (Registry / Plugin)

`RuleRegistry` + dekorator `@register` implementirata register vtičnikov. Pravila se samodejna registrirajo ob uvozu. `register_all()` deluje kot nalagalnik vtičnikov. `RuleEngine` nikoli neposredno ne sklicuje na noben konkreten razred pravila — pokliče samo `registry.instantiate()`.

### 5.3 Vbrizgavanje odvisnosti (Dependency Injection)

`RuleRegistry.instantiate()` z `inspect.signature` pregleda podpis `__init__` vsakega pravila in injicira samo deklarirane odvisnosti. Konstruktorji pravil deklarirajo, kaj potrebujejo (npr. `sop_data: SOPData | None`); neuporabljene odvisnosti so samodejno filtrirane.

### 5.4 Vrednostni objekt (Value Object)

`ValidationError` in `RuleContext` sta `@dataclass(slots=True, frozen=True)` — nespremenljiva, primerljiva po vrednosti, ne identiteti. `RuleContext.with_row()` / `with_sheet()` vrneta nove primerke namesto mutiranja.

### 5.5 Graditelj (Builder)

`SharedContextBuilder.build()` konstruira kompleksen objekt `SharedContext` skozi zaporedje zasebnih `_build_*` metod. Objekt se vrne šele ko je v celoti sestavljen.

### 5.6 Strategija (Strategy, implicitna)

Trije osnovni tipi pravil (`RowRule`, `SheetRule`, `WorkbookRule`) enkapsulirajo različne strategije izvajanja. `RuleEngine` izbere strategijo z `isinstance` preverjanjem tipa med izvajanjem in pokliče ustrezno metodo.

---

## 6. Odvisnosti med moduli

```
main.py
  └─ uvozi → ui/run_validator.py, core/validator_engine.py

core/validator_engine.py
  └─ uvozi → core/rule_engine.py, excel/excel_loader.py, core/report.py

core/rule_engine.py
  └─ uvozi → rules/rule_registry.py, core/shared_context.py, core/error.py, core/config.py

rules/builtin/*.py
  └─ uvozi → rules/base_rule.py, core/constants.py, utils/helpers.py, core/error.py

excel/excel_loader.py
  └─ uvozi → excel/workbook_parser.py

excel/report_writer.py
  └─ uvozi → core/constants.py (CODE_TRANSLATIONS), core/_version.py

excel/sop_loader.py
  └─ samostojen (python-docx); porablja ga samo SOPComplianceRule

utils/helpers.py
  └─ uvozi → core/constants.py (regex vzorci)

ui/main_window*.py
  └─ uvozi → core/validator_engine.py, excel/*, utils/*
```

**Smer odvisnosti je strogo od zgoraj navzdol.** `core/` nima uvozov iz `rules/`, `excel/` ali `ui/`. `rules/` uvozi `core/` ampak ne `excel/` ali `ui/`. To ustvarja čisto plastenje.

**Ena izjema:** `RuleEngine` ne uvaža `rules/builtin/` — klicatelj (`main.py` ali UI) je odgovoren za klic `register_all()` pred konstruiranjem `RuleEngine`. To je namerna inverzija nadzora, a ustvarja implicitno zahtevo po vrstnem redu inicializacije.

---

## 7. Prednosti in slabosti

### Prednosti

**Čista ločitev plasti.** `core/` je popolnoma neodvisen od `rules/`, `excel/` in `ui/`. Testiramo ga lahko izolirano z lažnimi podatki.

**Pred-izračun `SharedContext`.** Vsi medvrstični iskovi (korak → kontrole, ključi po tipu, zakleni preslikave) se izračunajo enkrat pred izvajanjem kateregakoli pravila, namesto da bi bili znova pregledani znotraj vsakega pravila. To odpravlja vzorce O(n²).

**Razširljivost na osnovi registra.** Dodajanje novega pravila zahteva samo: definiranje razreda, apliciranje `@register`. Nobene spremembe `RuleEngine`, nobenih pogojnih stavkov tovarne.

**Tipizirani vrednostni objekti.** `ValidationError`, `RuleContext`, `ValidatorConfig`, `SharedContext` vsi uporabljajo `@dataclass(slots=True)`, kar zagotavlja eksplicitne pogodbe, `__repr__` in učinkovitost pomnilnika.

**Domeno-specifičen `helpers.py`.** Vso z regex obremenjeno razčlenjevanje (intervali Navodilo, časovne fraze, žetoni enot, reference formul) je centralizirano v enem modulu z jasno poimenovanimi funkcijami, kar zmanjšuje podvajanje v pravilih.

**Tri implementacije GUI z rezervo.** Usmerjevalnik `run_gui()` poskusi Qt → Tkinter s temo → klasičen Tkinter. Logika validatorja ni prepletena z nobenim specifičnim ogrodjem UI.

### Slabosti

**`SharedContextBuilder` je 340-vrstični monolit.** Vseh 7 `_build_*` metod akumulira stanje v en sam spremenljiv objekt podoben slovarju pred zamrznitvijo. Dodajanje nove dimenzije konteksta zahteva spremembo polj `SharedContext`, `SharedContextBuilder` in vseh pravil, ki porabljajo novo polje — tri točke dotika.

**`control.py` je datoteka z 1500+ vrsticami.** Vsebuje 18 razredov pravil in samostojne pomožne funkcije (`_get_present_controls`, `_has_control` itd.). Pomočniki so funkcije na nivoju modula namesto skupne storitve, kar oteži njihovo posnemanje v testih.

**`SOPComplianceRule` je razred z 1000+ vrsticami.** Vključuje ekstrakcijo podatkov, normalizacijo in 7+ metod pod-validacije znotraj enega razreda. Meša razčlenjevalno logiko (ki spada v `SOPLoader`) z validacijsko logiko.

**Implicitna zahteva po klicu `register_all()`** Če `register_all()` ni poklican pred validacijo, motor tiho procesira nič pravil. Ni trditve ali zaščite.

**Dve implementaciji Tkinter.** `main_window.py` in `main_window_themed.py` sta skoraj identični po funkcionalnosti, razlikujeta se samo po stilu. Podvajanje logike je visoko.

**Zastavice obvoda `ValidatorConfig` so domeno-specifične.** Polja kot `bypass_zakleni_require_empty_for_checkbox` in `bypass_zakleni_inverse_pogoj_requirement` so trdo kodirana v dataclass konfigurizacije namesto generičnega mehanizma `{ime_pravila: {zastavica: vrednost}}`.

---

## 8. Tehnični dolg in tveganja

### Tveganja pri skaliranju

**`SharedContextBuilder` raste z vsakim novim pravilom.** Trenutno pri 340 vrsticah. Vsako novo pravilo, ki potrebuje medvrstično stanje, zahteva dodajanje polj v `SharedContext` (zamrznjen dataclass — zahteva ponovni prevod) in novo `_build_*` metodo. Ko število pravil raste, to postane ozko grlo pri vzdrževanju.

**`constants.py` je ena sama ravna datoteka z 500+ vrsticami.** Meša regex vzorce, dovoljene vrednosti, prevode in ključne besede opreme brez pod-grupiranja. Ko domensko znanje raste, bo navigacija težja.

**Datoteke pravil `control.py` ni mogoče razdeliti brez lomljenja uvozov.** Skupni pomočniki (`_get_present_controls`, `ControlInstance`) so na nivoju modula in jih uporabljajo vsa pravila kontrole. Premikanje bi zahtevalo prestrukturiranje odvisnosti med pravili.

### Težave z vzdrževanjem

**`SOPComplianceRule` meša razčlenjevanje in validacijo.** Metoda `_extract_all_podatki_data()` razčleni strukturirane podatke iz lista "Podatki" in vrne surove slovarje. Ta razčlenjevalna logika bi morala živeti v `WorkbookParser` ali namenskem ekstrahatorju, ne znotraj razreda pravila.

**`validation_progress.json` je spremenljiva JSON datoteka**, ki se neposredno piše med izvajanjem validacij. Sočasne validacije (možne v GUI) bi jo pokvarile. Ni zaklepanja datotek ali atomičnega pisanja.

**Ni vmesnika med `ValidatorEngine` in UI.** Razredi UI (`ValidatorApp`, `MainWindowQt`) konstruirajo `ValidatorEngine` neposredno inline s trdo kodiranimi parametri. Manjka tovarniska funkcija ali vbrizgavanje odvisnosti na meji UI.

**`WorkbookParser.stop_at_blank_row=True`** je vedenjska privzeta vrednost, ki tiho zavrže vse podatke po prvi prazni vrstici. Za napačno oblikovane vhode to povzroči tiho izgubo podatkov brez prikazane napake.

**Razčlenjevanje formul v `utils/helpers.py`** (`parse_index_match_formula`, `find_row_by_match`) je odvisno od živih objektov `openpyxl` delovnega zvezka, ki ostanejo odprti — implicitna stanjna odvisnost od `ExcelLoader.keep_workbooks_open=True`. Če ni nastavljeno, navzkrižne reference formul tiho spodletijo.

### Vrzeli v testiranju

Testna zbirka ima pokritost za vse štiri kategorije pravil, a nima integracijskega testa, ki bi preizkusil celoten cevovod `ValidatorEngine → RuleEngine → ReportWriter` na resničnih Excel datotekah. `SOPComplianceRule` nima namenske testne datoteke.
