# MES Validator - Orodje za validacijo receptur

## Namen orodja

MES Validator je Python aplikacija za avtomatizirano preverjanje kakovosti in skladnosti Excel receptur pred njihovo uporabo v proizvodnem MES sistemu. Orodje deluje kot podpora odločanju, kjer identificira napake in odstopanja v recepturah, končno odgovornost za odobritev pa ostaja pri usposobljenem osebju QA/proizvodnje.

## Ključne funkcionalnosti

- **Avtomatska validacija** Excel receptur proti 20+ vnaprej definiranim pravilom
- **Dvojni vmesnik**: grafični (GUI) in ukazna vrstica (CLI) za različne uporabniške profile
- **Generiranje poročil** v formatih Excel, JSON in tekst z natančno lokacijo napak (list, vrstica, stolpec)
- **Kategorije validacije**: strukturna pravila, nadzor tipov podatkov, relacijska pravila (podvajanje ključev), kontrole MES parametrov
- **Opcijska SOP skladnost**: preverjanje proti Word SOP dokumentom
- **Apply fixes funkcija**: avtomatsko generiranje popravljene kopije recepture

---

## Struktura projekta po modulih

### 1. Core (`core/`) – Validacijsko jedro

Centralni modul, ki vsebuje ključne komponente validacijskega sistema:

- **`validator_engine.py`**: Glavni orkestratorski mehanizem, ki koordinira nalaganje Excel datotek, izvajanje pravil in generiranje poročil. Filtrira liste z recepturnimi podatki in upravlja celotni tok validacije.

- **`rule_engine.py`**: Motor za izvajanje pravil, ki upravlja tri tipe pravil (RowRule, SheetRule, WorkbookRule), skrbi za vrstni red izvajanja (priority), dependency injection in SharedContext gradnjo. Implementira bypass logiko in strogi način.

- **`config.py`**: Konfiguracijski sistem z ValidatorConfig objektom za nastavitve (bypass_rules, strict_mode, row_offset, stop_on_first_error).

- **`shared_context.py`**: Kontekst podatkovni objekt, ki pre-procesira in deli podatke med pravili (indeksi ključev, stolpci, agregati) za optimizacijo izvajanja.

- **`error.py`**: Definicije ValidationError objektov in Severity levelov (ERROR, WARNING, INFO).

- **`report.py`**: ValidationReport razred za agregacijo napak, metadata in export v različne formate.

- **`constants.py`**: Globalne konstante (REQUIRED_COLUMNS, verzija).

### 2. Rules (`rules/`) – Validacijska pravila

Modularni sistem pravil z baznimi razredi in vgrajenimi implementacijami:

- **`base_rule.py`**: Abstraktni bazni razredi (BaseRule, RowRule, SheetRule, WorkbookRule) z RuleContext objektom za prenos metadata.

- **`rule_registry.py`**: Registracijski sistem za pravila z dependency injection, decorator pattern registracijo in instanciacijo pravil sortiranih po prioriteti.

- **`builtin/`**: Vgrajena pravila v štirih kategorijah:
  - **`structural.py`**: Preverjanje obveznih stolpcev, števičenje korakov, pravilnost stolpčne strukture
  - **`field.py`**: Validacija tipov podatkov (Tip objekta, Tip podatka), formatov ključev, formul, enot
  - **`relational.py`**: Unikatnost ključev, pari kemikalija-masa, datum/čas sklopi, kontekst kontrol
  - **`control.py`**: Validacija MES kontrol (imena, parametri interval/čas, logika zaklenipolja)
  - **`sop_compliance_rule.py`**: Opcijska validacija skladnosti s SOP Word dokumenti

### 3. Excel (`excel/`) – Excel I/O operacije

Modul za branje in pisanje Excel datotek:

- **`excel_loader.py`**: Glavna točka za nalaganje Excel datotek z LoadedWorkbook dataclass kontejnerjem. Uporablja openpyxl za branje .xlsx datotek.

- **`workbook_parser.py`**: Parser, ki normalizira Excel strukture v slovarje (sheet → rows → dict[column: value]). Podpira vrednosti in formule.

- **`report_writer.py`**: ReportWriter za generiranje validacijskih poročil v Excel formatu z oblikovanim izpisom napak, kode napak in povzetkov.

- **`workbook_fixer.py`**: WorkbookFixer za apply-fixes funkcionalnost – avtomatsko apliciranje popravkov v novo kopijo recepture.

- **`sop_loader.py`**: Opcijski modul za branje SOP specifikacij iz Word (.docx) datotek z python-docx knjižnico.

### 4. UI (`ui/`) – Grafični vmesnik

Tkinter-based GUI komponente:

- **`main_window.py`**: Glavno okno aplikacije ValidatorApp z:
  - File selection dialogi za izbiro ene ali več receptur
  - Output location izbira
  - Real-time progress tracking
  - Results display z barvno kodirano resnostjo napak
  - Export funkcionalnost
  - Sheet comparison orodje

- **`run_validator.py`**: Entry point funkcija `run_gui()` za zagon GUI moda.

### 5. Utils (`utils/`) – Pomožne funkcije

Utility modul z podpornimi funkcijami:

- **`logger.py`**: Konfiguracijski sistem za logging (setup_logger, get_logger) s formatirano konzolo in file output podporo.

- **`file_paths.py`**: Utility funkcije za delo s potmi datotek, normalizacijo in validacijo.

- **`helpers.py`**: Splošne helper funkcije za normalizacijo podatkov, string operacije, konverzije.

### 6. Tests (`tests/`) – Testna infrastruktura

Celovita pytest test suite:

- **`conftest.py`**: Pytest fixtures za setup/teardown, test data generation, mock objekti.

- **Test moduli**:
  - `test_engines.py`: Testiranje ValidatorEngine in RuleEngine
  - `test_structural_rules.py`, `test_field_rules.py`, `test_relational_rules.py`, `test_control_rules.py`: Testiranje posameznih kategorij pravil
  - `test_excel_loader.py`: Testiranje Excel loading logike
  - `test_shared_context.py`: Testiranje SharedContext gradnje
  - `test_sop_compliance_rule.py`: Testiranje SOP validacije

- **Coverage**: Unit tests za kritične komponente, edge case handling, error recovery.

### 7. Docs (`docs/`) – Dokumentacija

Kvalifikacijska in uporabniška dokumentacija:

- **`Dokumentacija/SL/`**: Slovenska GxP dokumentacija
  - `URS_Validator_SL.md`: User Requirements Specification
  - `FS_Validator_SL.md`: Functional Specification
  - `OQ_Validator_SL.md`: Operational Qualification
  - `SOP_Uporaba_Validator_SL.md`: Standard Operating Procedure
  - `Risk_Assessment_Validator_SL.md`: Ocena tveganja

- **`Dokumentacija/EN/`**: Angleška verzija GxP dokumentacije (REVISED)

- **`Dokumentacija/GPT.5.2/`**: Predhodni draft verzije

- **Conversion utilities**: `convert_md_to_docx.py` za pretvorbo Markdown → Word format

---

## Tehnična implementacija

- **Arhitektura**: Čista objektno-orientirana zasnova z SOLID principi, dependency injection, strategy pattern za pravila
- **Razširljivost**: Plugin-like sistem pravil omogoča dodajanje novih validacij brez spreminjanja jedra
- **Zmogljivost**: SharedContext pre-procesiranje za optimizacijo, lazy loading, memory-efficient parsing
- **Error handling**: Graceful degradation, jasna error sporočila, stack traces v logih
- **Distribucija**: PyInstaller support za standalone .exe Windows aplikacijo

## Uporabna vrednost

- **Prihranek časa**: Identificira napake v minutah, ki bi sicer zahtevale ročni pregled
- **Preprečevanje napak**: Odkriva kritične napake pred vnosom v proizvodnjo
- **Sledljivost**: Standardizirana poročila z jasno dokumentacijo ugotovitev
- **Skladnost**: Pripravljena infrastruktura za GxP kvalifikacijo in audit trail
- **Konsistentnost**: Zagotavlja enotne standarde preverjanja across vseh receptur

---

**KONEC DOKUMENTA**
