# FS – Functional Specification (Validator MES Receptur)

## Dokumentni podatki

- **Naziv**: FS – Functional Specification (Validator MES Receptur)
- **Sistem / aplikacija**: Validator (`validator_oop`)
- **ID dokumenta**: VAL-FS-001
- **Verzija**: 1.0
- **Datum**: 2026-02-04
- **Pripravil**: ______________________
- **Pregledal (QA)**: ______________________
- **Odobril (Lastnik procesa)**: ______________________

## 1. Namen

Namen dokumenta je opisati funkcionalno implementacijo Validatorja (kaj sistem dela in kako), vključno z arhitekturo, komponentami, vhodno/izhodnimi podatki, uporabniškimi načini uporabe (GUI/CLI) ter naborom validacijskih pravil.

## 2. Sklici in kontekst

- **URS**: `VAL-URS-001`
- **Implementacija**: Python paket `validator_oop`
- **Verzija aplikacije**: povzeta iz konstante `VERSION` (npr. `v 113 – 2025-11-25` v `core/constants.py`)

## 3. Pregled sistema

Validator je sestavljen iz naslednjih glavnih delov:

- **UI sloj**:
  - GUI (Tkinter) – `ui/main_window.py`
  - CLI – `main.py` (zagon preko `python -m validator_oop`)
- **Jedro validacije**:
  - `core/validator_engine.py`: orkestracija nalaganja in zagona pravil
  - `core/rule_engine.py`: izvajanje pravil (Row/Sheet/Workbook) + SharedContext
  - `core/report.py`: agregacija napak v `ValidationReport`
- **Vhod/izhod datotek**:
  - `excel/excel_loader.py`: branje Excel (openpyxl), opcijsko tudi formule
  - `excel/report_writer.py`: zapis poročil v `.xlsx`, `.txt`, `.json` (delno)
  - `excel/sop_loader.py`: branje SOP `.docx` in ekstrakcija zahtev (opcijsko)
- **Pravila**:
  - `rules/builtin/*`: vnaprej vgrajena pravila
  - registracija: `rules/builtin/__init__.py` in `rules/rule_registry.py`

## 3.1 Tehnologija in OOP zasnova (kako je Validator narejen)

- **Tehnologija**: Validator je implementiran v **programskem jeziku Python** kot paket `validator_oop` (modularna struktura map `core/`, `excel/`, `rules/`, `ui/`).
- **OOP pristop**: logika je razdeljena v razrede z jasno odgovornostjo:
  - **Orkestracija**: `ValidatorEngine` (nadzira potek validacije: load → filter → run rules → report)
  - **Izvajanje pravil**: `RuleEngine` (instanciranje pravil, SharedContext, izvajanje Row/Sheet/Workbook pravil)
  - **Pravila kot razredi**: `RowRule`, `SheetRule`, `WorkbookRule` (dedovanje + polimorfizem)
  - **Registracija pravil**: `RuleRegistry` (centralni register pravil; instanciranje po prioriteti; “plugin” pristop)
  - **Vhod/izhod**: `ExcelLoader` (branje workbooka), `ReportWriter` (pisanje poročil), `WorkbookFixer` (opcijski autofix)
  - **Model napak**: `ValidationError` + `ValidationReport` (standardiziran zapis napak in agregacija)
- **Uporabljeni vzorci (na funkcionalni ravni)**:
  - **Strategy / Plugin**: posamezna validacijska pravila so zamenljive strategije (razredi pravil v registru).
  - **Factory/DI**: `RuleRegistry.instantiate()` instancira pravila in injicira odvisnosti (npr. `sop_data`).
  - **Pipeline**: validacija je zaporedje korakov (load → priprava konteksta → rules → report → export).

## 3.2 Glavni tok izvajanja (od zagona do poročila)

### 3.2.1 CLI tok

1. Uporabnik zažene `python -m validator_oop ...` ali `python main.py ...`
2. Program pripravi konfiguracijo (`ValidatorConfig`) in registrira vgrajena pravila (`register_all()`).
3. `ExcelLoader` prebere Excel (opcijsko tudi formule).
4. `ValidatorEngine` filtrira liste in pokliče `RuleEngine.run()`.
5. `RuleEngine`:
   - instancira pravila iz `RuleRegistry`,
   - zgradi `SharedContext`,
   - izvede pravila (Row → Sheet → Workbook, odvisno od tipa),
   - zbere `ValidationError` zapise.
6. `ValidationReport` agregira rezultat (`is_valid`, `counts`, `errors`).
7. `ReportWriter` zapiše poročilo (npr. `.xlsx`) ali CLI izpiše JSON/summary.

### 3.2.2 GUI tok

1. Uporabnik izbere vhodne datoteke in izhodno pot poročila.
2. (Opcijsko) izbere SOP `.docx`, ki se prebere v `SOPData`.
3. GUI sestavi engine-je in sproži validacijo; rezultat prikaže v status oknu in zapiše poročilo.

## 4. Sledljivost URS → FS (high-level)

| URS | FS referenca |
|---|---|
| URS-FR-01/03 | FS-IO-01, FS-VAL-02 |
| URS-FR-04 | FS-RULES-01 … FS-RULES-05 |
| URS-FR-05 | FS-SOP-01 … FS-SOP-03 |
| URS-FR-06 | FS-REP-01, FS-REP-02 |
| URS-FR-07/08/09 | FS-REP-03 … FS-REP-06 |
| URS-FR-10/11/12 | FS-CONF-01 … FS-CONF-04 |
| URS-FR-13 | FS-AUTOFIX-01 |
| URS-FR-14 | FS-CLI-03 |
| URS-NFR-* | FS-NFR-01 … FS-NFR-06 |

## 5. Funkcionalne specifikacije

### 5.1 Vhodni podatki in nalaganje

- **FS-IO-01 (Branje Excel)**: Excel se bere z `openpyxl` preko `ExcelLoader.load()`:
  - `data_only=True` za vrednosti,
  - opcijsko `data_only=False` za formule (če `include_formulas=True`).
- **FS-IO-02 (Headerji in row_offset)**:
  - privzeti `header_row_index=1` (1-based),
  - `row_offset = header_row_index + 1` (privzeto 2).
- **FS-IO-03 (Filtriranje listov)**:
  - `ValidatorEngine` validira samo liste, ki vsebujejo vsaj en “required column” (`REQUIRED_COLUMNS`).
  - seznam obveznih stolpcev: `core/constants.py -> REQUIRED_COLUMNS`.

### 5.2 Konfiguracija

- **FS-CONF-01 (ValidatorConfig)**: konfiguracija v `core/config.py` podpira:
  - `bypass_rules` (izključitev pravil po imenu ali kodi),
  - `bypass_codes` (suppress izpis po kodi),
  - `strict_mode` (WARNING → ERROR),
  - `include_formulas` (nalaganje formul),
  - “zaklenipolja” bypass zastavice (compat z legacy),
  - SOP nastavitve (`sop_data_path`, `enable_sop_validation`).
- **FS-CONF-02 (Strict mode)**: v `RuleEngine.run()` se WARNING pretvori v ERROR, ko je `strict_mode=True`.
- **FS-CONF-03 (Bypass pravil)**: pravila se filtrirajo pred izvajanjem (po `display_name` ali `error_code`).

### 5.3 Izvajanje validacije

- **FS-VAL-01 (Orkestracija)**:
  - `ValidatorEngine.validate(path)`:
    - naloži workbook,
    - filtrira liste,
    - zažene `RuleEngine.run()` nad filtriranimi listi,
    - sestavi `ValidationReport`.
- **FS-VAL-02 (SharedContext)**:
  - za vsak list se izgradi `SharedContext` (stolpci, mapiranja, pred-izračuni).
  - `SharedContext.extra` nosi dodatne objekte (npr. workbook_values, parsed_formulas, all_workbook_data…).
- **FS-VAL-03 (Tipi pravil)**:
  - `RowRule`: evaluacija na nivoju vrstice
  - `SheetRule`: evaluacija na nivoju lista
  - `WorkbookRule`: evaluacija nad celotnim workbookom
- **FS-VAL-04 (Zaporedje)**:
  - pravila se instancirajo in sortirajo po `priority` (nižja → prej).

### 5.4 Validacijska pravila (builtin)

> Opomba: spodaj je povzetek; dejanski nabor je določen z importom modulov v `rules/builtin/__init__.py`.

#### FS-RULES-01 Structural

- **RequiredColumnsRule**: manjkajoči obvezni stolpci → `MISSING_COLUMN`
- **StepNumberingRule**:
  - ne-celo število → `STEP_NOT_INT`
  - manjka korak v vrstici z vsebino → `STEP_MISSING`
  - podvojeni koraki (po zavihku/sekciji) → `STEP_DUPLICATE`
  - koraki se ne začnejo z 1 → `STEP_TAB_START_NOT_ONE`
  - manjkajoči vmesni koraki → `STEP_GAPS`

#### FS-RULES-02 Field (Row-based)

- **ObjectTypeRule**:
  - prazen tip objekta → `TIP_OBJEKTA_EMPTY`
  - neznan tip objekta → `TIP_OBJEKTA_UNKNOWN`
- **DataObjectCompatibilityRule**: nekompatibilen `Tip podatka` vs `Tip objekta` → `OBJ_MISMATCH`
- **LabelRequirementsRule**:
  - `Labela` mora biti `koda` za določene tipe → `LABELA_KODA`
  - neujemanje enot labela/navodilo → `UNIT_MISMATCH`
- **KeyValidationRule**:
  - nedovoljeni znaki v ključu → `KEY_FORMAT`
  - obvezen ključ za glavne tipe → `KEY_REQUIRED_MAIN_TYPES`
- **FormulaSyntaxRule** (formula tipi objekta):
  - manjkajoč `=` → `FORMULA_SYNTAX`
  - ni `$` sklicev → `FORMULA_NOREF`
- **FormulaReferenceRule**: sklic na neobstoječ korak → `FORMULA_BAD_REF`
- **CommaNumberRule**: decimalna vejica (kjer ni dovoljeno) → `COMMA_NOT_ALLOWED`

#### FS-RULES-03 Relational (Sheet-based)

- **DuplicateKeyRule**:
  - duplikati kemikalija/raztopina/čas → `KEY_DUP_*`
  - mase: posebna logika po bazi ključa/sekcijah → `KEY_DUP_MASA`
- **MassOwnerRule**:
  - masa brez lastnika → `PAIR_MASA_NO_OWNER`
  - masa ključ se ne ujema z najbližjim ownerjem → `PAIR_MASA_WRONG_SECTION`
- **TimePairRule**:
  - manjka par časa → `PAIR_TIME_NO_START` / `PAIR_TIME_NO_END`
  - podvojen ključ para → `KEY_DUP_TIME_PAIR`
- **KeyNumberingRule**:
  - oštevilčenje se ne začne z 1 → `KEY_NUM_START`
  - preskok v zaporedju → `KEY_NUM_GAP`
  - nekonsistenten stil (`base` in `base1`) → `KEY_NUM_DUPLICATE_ONE` (WARNING)
- **TehtnicaMasaPairRule**:
  - tehtnica brez mase ne sme imeti določene kontrole → `CTRL_TEHTNICA_NO_MASA`
- **TehtnicaVrednostFromFormulaRule**:
  - validacija “Vrednost” tehtnice glede na maso (tudi INDEX/MATCH) → `TEHTNICA_VREDNOST_INVALID_*`

#### FS-RULES-04 Controls (Row/Sheet)

- **UnknownControlsRule**: kontrola ni v dovoljenem naboru → `CTRL_UNKNOWN`
- **ControlContextRule**: kontrola v napačnem kontekstu → `CTRL_BAD_CONTEXT`
- **RequiredControlsRule**:
  - pri vnosnih poljih manjka `kontrolaPraznoPolje` → `CTRL_REQUIRED_EMPTY`
  - checkbox ne sme imeti `kontrolaPraznoPolje` → `CTRL_CHECKBOX_EMPTY`
  - posebnosti `zaklenipolja` + checkbox → `CTRL_LOCKED_NO_EMPTY`, `CTRL_LOCKED_NO_CHECK`
- **ExpectedControlsRule**: priporočene kontrole manjkajo → `CTRL_EXPECTED_MISSING` (WARNING)
- **ZakleniParamRule**: Param1 format/seznam korakov + obstoj korakov → `ZAKLENI_*`
- **AliObstajaPogojCombinationRule**: kombinacije Param1/Param2 morajo slediti pravilom → `ZAKLENI_POGOJ_P1P2`
- **ZakleniUniqueKeyRule**: unikaten ključ pri `zaklenipolja` → `ZAKLENI_KEY_DUPLICATE`
- **ZakleniInverseRule**: koraki z `aliObstajaPogoj` morajo biti v Param1 `zaklenipolja` → `ZAKLENI_P1_MISSING_FOR_POGOJ`
- **AliObkljukanParamRule**: Param1 DA/NE + skladnost checkbox stanja → `CHECKBOX_PARAM`, `CHECKBOX_STATE`
- **KontrolaIntervalParamRule / AdvancedRule**: numerika + ujemanje z navodili → `CTRL_INTERVAL_*`
- **KontrolaCasaRule**: parametri (sekunde) + ujemanje z navodili → `CTRL_CASA_*`

#### FS-RULES-05 SOP (WorkbookRule, opcijsko)

- **SOPComplianceRule** (izvaja se, če je naložen SOP):
  - IPO šifre iz zavihka `Podatki` vs SOP IPO → `SOP_IPO_MISMATCH`, `SOP_IPO_MISSING`
  - volumni/pretoki vs SOP (z upoštevanjem “V monolita” volumna kolone) → `SOP_VOLUME_*`, `SOP_FLOW_*`
  - tipi raztopin → `SOP_TYPE_NOT_ALLOWED`
  - vzorci/TSST/Vr/N/tlak/D → `SOP_*`
  - medij (PM1/PM23/TK/endotoksini) → `SOP_MEDIUM_MISMATCH`

### 5.5 Izhodni podatki (poročila)

- **FS-REP-01 (ValidationReport)**: interno poročilo vsebuje:
  - `is_valid` (valid, če ni ERROR),
  - `errors[]` z `sheet`, `row`, `col`, `code`, `severity`, `message`,
  - `counts` po severity.
- **FS-REP-02 (Excel poročilo)**: `ReportWriter.write_excel_report()` generira workbook z listi:
  - `Povzetek`: seznam napak (List, Vrstica, Stolpec, Napaka, Opis napake)
  - `Število napak`: agregat po kodah (Koda, Opis, Število)
- **FS-REP-03 (Text poročilo)**: vrstica na napako, v slogu:
  - `sheet | vrstica X | stolpec Y | KODA – opis`
- **FS-REP-04 (JSON poročilo)**:
  - CLI omogoča izvoz JSON preko `--format json` ali `--output ...json`.

### 5.6 CLI (Command Line Interface)

- **FS-CLI-01 (Zagon)**: `python -m validator_oop [workbook.xlsx] [options]`
- **FS-CLI-02 (Parametri)** (povzetek):
  - `--output`, `--format {json,text,summary,excel}`, `--verbose`, `--strict`, `--bypass ...`,
  - `--include-formulas`, `--apply-fixes`, `--gui`.
- **FS-CLI-03 (Exit codes)**:
  - `0` OK,
  - `1` validacijske napake,
  - `2` runtime napaka.
- **FS-CLI-04 (Log datoteka)**: vedno se piše log v `MESValidator.log` v uporabnikov `HOME` (namen: diagnostika, posebej za EXE).

### 5.7 GUI (Tkinter)

- **FS-GUI-01**: izbira 1..n vhodnih Excel datotek
- **FS-GUI-02**: izbira izhoda:
  - “ena skupna datoteka” (določitev `.xlsx` ali `.txt`),
  - ali “ločeno poročilo na datoteko” (izbira mape).
- **FS-GUI-03**: opcijski SOP `.docx` (nalaganje in validacija, z nadaljevanjem brez SOP ob napaki).
- **FS-GUI-04**: statusno okno z logom in povzetkom rezultatov.

### 5.8 Apply fixes

- **FS-AUTOFIX-01**: `WorkbookFixer.apply_fixes()` uporabi popravke le, če so v “issue” zapisani:
  - `target_cell`, `proposed_value`, `fix_kind="set_value"`,
  - rezultat je nova datoteka z `_AUTOFIX.xlsx`.

## 6. Nefunkcionalne zahteve (implementacijski odziv)

- **FS-NFR-01 (Kompatibilnost)**: Windows, Python okolje ali EXE distribucija.
- **FS-NFR-02 (Odvisnosti)**:
  - `openpyxl` (obvezno za Excel),
  - `python-docx` (opcijsko za SOP),
  - `tkinter` (opcijsko za GUI; v standardni Python distribuciji, lahko manjka).
- **FS-NFR-03 (Integriteta)**: original se ne spreminja; poročila in autofix so ločeni izhodi.
- **FS-NFR-04 (Diagnostika)**: konzolni log + datotečni log za sledenje težavam.

## 7. Odprte točke / omejitve

- Sekcijska primerjava listov v GUI je označena kot *ni implementirano* (placeholder).
- JSON zapis poročil v `ReportWriter` je na voljo, vendar CLI delno uporablja direkten `json.dump`.

