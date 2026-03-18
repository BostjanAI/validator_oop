# Funkcionalna specifikacija (FS)
## Validator MES receptur

---

## Nadzor nad dokumentom

| Polje | Vrednost |
|---|---|
| **Naslov dokumenta** | Funkcionalna specifikacija (FS) |
| **Sistem / Aplikacija** | Validator MES receptur (validator_oop) |
| **ID dokumenta** | VAL-FS-001 |
| **Verzija** | 1.0 |
| **Datum** | 2026-02-04 |
| **Pripravil** | ______________________ |
| **Pregledal (QA)** | ______________________ |
| **Odobril (Lastnik procesa)** | ______________________ |

---

## 1. Namen

Ta dokument opisuje funkcionalno implementacijo sistema Validator, vključno s sistemsko arhitekturo, komponentami, strukturami vhodnih/izhodnih podatkov, načini interakcije uporabnika (GUI/CLI) in celotnim naborom validacijskih pravil.

## 2. Reference in kontekst

### 2.1 Povezani dokumenti

- **Specifikacija uporabniških zahtev**: VAL-URS-001
- **Protokol operacijske kvalifikacije**: VAL-OQ-001
- **Ocena tveganja**: VAL-RA-001
- **Uporabniški SOP**: VAL-SOP-USE-001

### 2.2 Podrobnosti implementacije

- **Programski paket**: `validator_oop` (Python paket)
- **Verzija aplikacije**: Definirana v konstanti `VERSION` v `core/constants.py` (npr. "v 113 – 2025-11-25")

## 3. Pregled sistema

### 3.1 Komponente sistema

Sistem Validator je sestavljen iz naslednjih arhitekturnih plasti:

#### 3.1.1 Plast uporabniškega vmesnika

- **GUI (grafični uporabniški vmesnik)**: Vmesnik, ki temelji na Tkinter, implementiran v `ui/main_window.py`
- **CLI (vmesnik ukazne vrstice)**: Implementiran v `main.py`, izvaja se preko `python -m validator_oop`

#### 3.1.2 Jedro validacije

- **Validator Engine** (`core/validator_engine.py`): Orkestrira nalaganje delovnega zvezka in izvajanje validacijskih pravil
- **Rule Engine** (`core/rule_engine.py`): Upravlja instanciranje pravil, konstrukcijo SharedContext in izvajanje pravil Row/Sheet/Workbook
- **Validation Report** (`core/report.py`): Agregira validacijske napake in zagotavlja metode za povzetke

#### 3.1.3 Plast vhoda/izhoda datotek

- **Excel Loader** (`excel/excel_loader.py`): Bere Excel delovne zvezke z uporabo knjižnice openpyxl, z opcijskim parsiranjem formul
- **Report Writer** (`excel/report_writer.py`): Piše validacijska poročila v formate `.xlsx`, `.txt` in `.json`
- **SOP Loader** (`excel/sop_loader.py`): Parsira SOP Word dokumente in ekstrahira zahteve (opcijska funkcionalnost)

#### 3.1.4 Validacijska pravila

- **Vgrajena pravila** (`rules/builtin/*`): Vnaprej definirane implementacije validacijskih pravil
- **Rule Registry** (`rules/rule_registry.py`): Centralni mehanizem za registracijo in instanciranje
- **Registracija pravil** (`rules/builtin/__init__.py`): Avtomatska registracija vgrajenih pravil

### 3.2 Tehnološki sklad in objektno-orientirana zasnova

#### 3.2.1 Tehnologija implementacije

Validator je implementiran v programskem jeziku **Python** kot paket `validator_oop` z modularno strukturo direktorijev:
- `core/` – validacijski motor in poslovna logika
- `excel/` – operacije V/I datotek
- `rules/` – definicije validacijskih pravil
- `ui/` – implementacije uporabniškega vmesnika
- `utils/` – skupne utilitete

#### 3.2.2 Objektno-orientirana arhitektura

Sistem uporablja objektno-orientirane načrtovalske principe z jasno ločitvijo odgovornosti:

**Jedro razredov:**
- `ValidatorEngine`: Orkestrira potek validacije (load → filter → execute rules → generate report)
- `RuleEngine`: Upravlja instanciranje pravil, konstrukcijo SharedContext in izvajanje pravil
- `ExcelLoader`: Enkapsulira operacije nalaganja Excel delovnih zvezkov
- `ReportWriter`: Enkapsulira operacije generiranja poročil
- `WorkbookFixer`: Obravnava opcijske operacije avtomatskih popravkov

**Hierarhija razredov pravil:**
- `BaseRule`: Abstraktni bazni razred
- `RowRule`: Evalvira posamezne vrstice (dedovanje + polimorfizem)
- `SheetRule`: Evalvira celotne delovne liste
- `WorkbookRule`: Evalvira celotne delovne zvezke čez več listov

**Razredi podatkovnega modela:**
- `ValidationError`: Standardizirana struktura zapisa napake
- `ValidationReport`: Agregacija napak in povzetek
- `RuleRegistry`: Centralizirana registracija pravil in injiciranje odvisnosti

#### 3.2.3 Načrtovalski vzorci

- **Vzorec strategije / plugin**: Posamezna validacijska pravila so zamenljive strategije registrirane v `RuleRegistry`
- **Vzorec tovarne**: `RuleRegistry.instantiate()` ustvarja instance pravil z injiciranjem odvisnosti
- **Injiciranje odvisnosti**: Pravila prejemajo odvisnosti (npr. `sop_data`, `logger`) preko injiciranja v konstruktor
- **Vzorec cevovoda**: Validacija sledi zaporednim fazam: load → prepare context → execute rules → aggregate report → export

### 3.3 Potek izvajanja

#### 3.3.1 Potek izvajanja CLI

1. Uporabnik izvede: `python -m validator_oop [workbook.xlsx] [options]`
2. Sistem ustvari `ValidatorConfig` iz argumentov ukazne vrstice
3. Sistem registrira vgrajena validacijska pravila preko `register_all()`
4. `ExcelLoader` prebere Excel delovni zvezek (z opcijskim nalaganjem formul)
5. `ValidatorEngine` filtrira delovne liste glede na zahtevane stolpce
6. `ValidatorEngine` izvede `RuleEngine.run()` na filtriranih delovnih listih
7. `RuleEngine` izvede:
   - Instanciranje pravil iz `RuleRegistry`
   - Konstrukcijo `SharedContext` za vsak delovni list
   - Zaporedno izvajanje pravil (Row pravila → Sheet pravila → Workbook pravila)
   - Zbiranje `ValidationError` zapisov
8. `ValidationReport` agregira rezultate (`is_valid`, števila napak, podrobnosti napak)
9. `ReportWriter` izvozi poročilo v določen format (`.xlsx`, `.json` ali `.txt`), ali CLI izpiše povzetek v konzolo

#### 3.3.2 Potek izvajanja GUI

1. Uporabnik izbere vhodne Excel datoteke preko dialoga za izbiro datotek
2. Uporabnik določi izhodno pot poročila in format
3. (Opcijsko) Uporabnik izbere SOP Word dokument (`.docx`), ki se parsira v strukturo `SOPData`
4. GUI instancira komponente validacijskega motorja
5. GUI sproži validacijo preko `ValidatorEngine.validate()`
6. Rezultati so prikazani v statusnem oknu
7. Validacijsko poročilo je zapisano na določeno izhodno lokacijo

## 4. Matrika sledljivosti URS → FS

| Zahteva URS | Specifikacija FS |
|---|---|
| URS-FR-01 | FS-IO-01 |
| URS-FR-02 | FS-GUI-01 |
| URS-FR-03 | FS-IO-03 |
| URS-FR-04 | FS-RULES-01, FS-RULES-02, FS-RULES-03, FS-RULES-04 |
| URS-FR-05 | FS-RULES-05, FS-IO-04 |
| URS-FR-06 | FS-REP-01, FS-REP-02 |
| URS-FR-07 | FS-REP-02 |
| URS-FR-08 | FS-REP-03, FS-REP-04 |
| URS-FR-09 | FS-CLI-02, FS-GUI-02 |
| URS-FR-10 | FS-CONF-02 |
| URS-FR-11 | FS-CONF-03 |
| URS-FR-12 | FS-IO-01, FS-CONF-01 |
| URS-FR-13 | FS-AUTOFIX-01 |
| URS-FR-14 | FS-CLI-03 |
| URS-NFR-01 | FS-GUI-04 |
| URS-NFR-02 | FS-NFR-01 |
| URS-NFR-03 | FS-NFR-03 |
| URS-NFR-04 | FS-NFR-05 |
| URS-NFR-05 | FS-REP-01 |
| URS-NFR-06 | FS-NFR-04, FS-AUTOFIX-01 |
| URS-NFR-07 | FS-CLI-04, FS-NFR-06 |

## 5. Funkcionalne specifikacije

### 5.1 Vhodni podatki in nalaganje

**FS-IO-01: Nalaganje Excel delovnega zvezka**
- Excel delovni zvezki se berejo z uporabo knjižnice `openpyxl` preko metode `ExcelLoader.load()`
- Vrednosti se naložijo s parametrom `data_only=True`
- Formule se opcijsko naložijo z `data_only=False`, ko je nastavljena konfiguracija `include_formulas=True`

**FS-IO-02: Vrstica glave in odmik vrstic**
- Privzeta vrstica glave: Vrstica 1 (1-bazirano Excel indeksiranje)
- Odmik vrstice podatkov: `row_offset = header_row_index + 1` (privzeto: 2)

**FS-IO-03: Filtriranje delovnih listov**
- `ValidatorEngine` validira samo delovne liste, ki vsebujejo vsaj en zahtevani stolpec
- Zahtevani stolpci so definirani v konstanti `REQUIRED_COLUMNS` v `core/constants.py`

**FS-IO-04: Nalaganje SOP dokumenta (opcijsko)**
- SOP dokumenti v Word formatu (`.docx`) se parsirajo preko `SOPLoader.from_word()`
- Podatkovna struktura SOP (`SOPData`) vsebuje IPO kode, omejitve volumna/pretoka in druge zahteve
- Napake pri nalaganju SOP so beležene v log, validacija se nadaljuje brez preverjanja skladnosti s SOP

### 5.2 Upravljanje konfiguracije

**FS-CONF-01: Objekt konfiguracije validatorja**

Konfiguracija se upravlja preko razreda `ValidatorConfig` (`core/config.py`) z naslednjimi parametri:

| Parameter | Tip | Opis |
|---|---|---|
| `bypass_rules` | frozenset[str] | Imena pravil ali kode za izključitev iz validacije |
| `bypass_codes` | frozenset[str] | Kode napak za izpust v izhodu |
| `strict_mode` | bool | Pretvori opozorila v napake, ko je True |
| `include_formulas` | bool | Omogoči nalaganje in validacijo formul |
| `bypass_zakleni_require_empty_for_checkbox` | bool | Zastavica za združljivost s starejšo verzijo |
| `bypass_zakleni_require_pogoj_for_param1_steps` | bool | Zastavica za združljivost s starejšo verzijo |
| `bypass_zakleni_inverse_pogoj_requirement` | bool | Zastavica za združljivost s starejšo verzijo |
| `sop_data_path` | Path \| None | Pot do SOP Word dokumenta |
| `enable_sop_validation` | bool | Omogoči/onemogoči preverjanje skladnosti s SOP |

**FS-CONF-02: Implementacija strogega načina**
- Ko je `strict_mode=True`, `RuleEngine.run()` pretvori vse `Severity.WARNING` v `Severity.ERROR`

**FS-CONF-03: Mehanizem bypass pravil**
- Pravila se filtrirajo pred izvajanjem na podlagi ujemanja `display_name` ali `error_code`
- Logika filtriranja implementirana v `ValidatorConfig.should_skip_rule()`

### 5.3 Izvajanje validacije

**FS-VAL-01: Orkestracija validacije**

Metoda `ValidatorEngine.validate(path)` izvede naslednjo sekvenco:
1. Naloži delovni zvezek preko `ExcelLoader`
2. Filtrira delovne liste glede na zahtevane stolpce
3. Izvede `RuleEngine.run()` na filtriranih delovnih listih
4. Konstruira in vrne `ValidationReport`

**FS-VAL-02: Konstrukcija skupnega konteksta**

Za vsak delovni list se konstruira objekt `SharedContext`, ki vsebuje:
- Seznam stolpcev in mapiranja
- Pred-izračunane indekse (številke korakov, ključe po tipih, mapiranja stolpcev kontrol)
- Dodatne objekte shranjene v slovarju `SharedContext.extra` (npr. `workbook_values`, `parsed_formulas`, `all_workbook_data`)

**FS-VAL-03: Tipi pravil**

Podprti so trije tipi pravil:
- `RowRule`: Evalvira vsako vrstico individualno
- `SheetRule`: Evalvira celoten delovni list (za validacijo čez vrstice)
- `WorkbookRule`: Evalvira celoten delovni zvezek (za validacijo čez liste)

**FS-VAL-04: Zaporedje izvajanja pravil**

Pravila se instancirajo in izvajajo po vrstnem redu prioritete (naraščajoča vrednost atributa `priority`).

### 5.4 Vgrajena validacijska pravila

**OPOMBA:** Celoten nabor pravil je definiran z uvozi modulov v `rules/builtin/__init__.py`. Naslednje je povzetek implementiranih kategorij pravil.

#### 5.4.1 FS-RULES-01: Strukturna pravila (raven lista)

**RequiredColumnsRule**
- Validira prisotnost vseh zahtevanih stolpcev
- Koda napake: `MISSING_COLUMN`

**StepNumberingRule**
- Validira številčenje korakov v stolpcu "št. Koraka"
- Kode napak:
  - `STEP_NOT_INT`: Številka koraka ni celo število
  - `STEP_MISSING`: Manjkajoča številka koraka v vrstici z vsebino
  - `STEP_DUPLICATE`: Podvojena številka koraka (znotraj zavihka/sekcije)
  - `STEP_TAB_START_NOT_ONE`: Koraki se ne začnejo z 1
  - `STEP_GAPS`: Manjkajoče vmesne številke korakov

#### 5.4.2 FS-RULES-02: Pravila na ravni polj (raven vrstice)

**ObjectTypeRule**
- Kode napak: `TIP_OBJEKTA_EMPTY`, `TIP_OBJEKTA_UNKNOWN`

**DataObjectCompatibilityRule**
- Koda napake: `OBJ_MISMATCH`

**LabelRequirementsRule**
- Kode napak: `LABELA_KODA`, `UNIT_MISMATCH`

**KeyValidationRule**
- Kode napak: `KEY_FORMAT`, `KEY_REQUIRED_MAIN_TYPES`

**FormulaSyntaxRule**
- Kode napak: `FORMULA_SYNTAX`, `FORMULA_NOREF`

**FormulaReferenceRule**
- Koda napake: `FORMULA_BAD_REF`

**CommaNumberRule**
- Koda napake: `COMMA_NOT_ALLOWED`

#### 5.4.3 FS-RULES-03: Relacijska pravila (raven lista)

**DuplicateKeyRule**
- Kode napak: `KEY_DUP_KEM`, `KEY_DUP_RAZT`, `KEY_DUP_TIME_START`, `KEY_DUP_TIME_END`, `KEY_DUP_MASA`

**MassOwnerRule**
- Kode napak: `PAIR_MASA_NO_OWNER`, `PAIR_MASA_WRONG_SECTION`

**TimePairRule**
- Kode napak: `PAIR_TIME_NO_START`, `PAIR_TIME_NO_END`, `KEY_DUP_TIME_PAIR`

**KeyNumberingRule**
- Kode napak: `KEY_NUM_START`, `KEY_NUM_GAP`, `KEY_NUM_DUPLICATE_ONE` (resnost: WARNING)

**TehtnicaMasaPairRule**
- Koda napake: `CTRL_TEHTNICA_NO_MASA`

**TehtnicaVrednostFromFormulaRule**
- Kode napak: `TEHTNICA_VREDNOST_INVALID_HIGH`, `TEHTNICA_VREDNOST_INVALID_LOW`

#### 5.4.4 FS-RULES-04: Pravila kontrol (raven vrstice/lista)

**UnknownControlsRule**
- Koda napake: `CTRL_UNKNOWN`

**ControlContextRule**
- Koda napake: `CTRL_BAD_CONTEXT`

**RequiredControlsRule**
- Kode napak: `CTRL_REQUIRED_EMPTY`, `CTRL_CHECKBOX_EMPTY`, `CTRL_LOCKED_NO_EMPTY`, `CTRL_LOCKED_NO_CHECK`

**ExpectedControlsRule**
- Koda napake: `CTRL_EXPECTED_MISSING` (resnost: WARNING)

**ZakleniParamRule**
- Kode napak: `ZAKLENI_PAR1_EXCEL_ERR`, `ZAKLENI_PAR1_FORMAT`, `ZAKLENI_P1_STEP_MISSING`, `ZAKLENI_P1_NO_POGOJ`

**AliObstajaPogojCombinationRule**
- Koda napake: `ZAKLENI_POGOJ_P1P2`

**ZakleniUniqueKeyRule**
- Koda napake: `ZAKLENI_KEY_DUPLICATE`

**ZakleniInverseRule**
- Koda napake: `ZAKLENI_P1_MISSING_FOR_POGOJ`

**AliObkljukanParamRule**
- Kode napak: `CHECKBOX_PARAM`, `CHECKBOX_STATE`

**KontrolaIntervalParamRule / KontrolaIntervalAdvancedRule**
- Kode napak: `CTRL_INTERVAL_PARAMS`, `CTRL_INTERVAL_NUM`, `CTRL_INTERVAL_ORDER`, `CTRL_INTERVAL_RANGE_P1_EXACT`, `CTRL_INTERVAL_RANGE_P2_EXACT`, `CTRL_INTERVAL_PM_P1_EXACT`, `CTRL_INTERVAL_PM_P2_EXACT`, `CTRL_INTERVAL_TARGET_P1_EXACT`, `CTRL_INTERVAL_TARGET_P2_EXACT`, `CTRL_INTERVAL_TARGET_P1_MAX`, `CTRL_INTERVAL_TARGET_P2_MIN`

**KontrolaCasaRule**
- Kode napak: `CTRL_CASA_MIN`, `CTRL_CASA_MIN_NUM`, `CTRL_CASA_MAX_NUM`, `CTRL_CASA_ORDER`, `CTRL_CASA_P1_FROM_NAV`, `CTRL_CASA_P2_FROM_NAV`

#### 5.4.5 FS-RULES-05: Pravilo skladnosti s SOP (raven delovnega zvezka, opcijsko)

**SOPComplianceRule** (izvaja se samo, ko so naloženi SOP podatki)

Validira naslednje glede na SOP zahteve:
- IPO kode iz delovnega lista "Podatki": Kode napak `SOP_IPO_MISMATCH`, `SOP_IPO_MISSING`, `SOP_IPO_NOT_ALLOWED`
- Obsegi volumna (upoštevaje volumen stolpca iz "V monolita"): Kode napak `SOP_VOLUME_TOO_LOW`, `SOP_VOLUME_TOO_HIGH`
- Hitrosti pretoka (ujemanje z volumnom stolpca): Kode napak `SOP_FLOW_TOO_LOW`, `SOP_FLOW_TOO_HIGH`
- Tipi raztopin: Koda napake `SOP_TYPE_NOT_ALLOWED`
- Specifikacije vzorcev, tSST, Vr, N, tlak, distribucijski koeficient (D): Kode napak `SOP_SAMPLE_NOT_ALLOWED`, `SOP_TSST_*`, `SOP_VR_*`, `SOP_N_TOO_LOW`, `SOP_PRESSURE_*`, `SOP_D_*`
- Skladnost medija (PM1/PM23/TK/endotoksini): Koda napake `SOP_MEDIUM_MISMATCH`

### 5.5 Izhodni podatki (validacijska poročila)

**FS-REP-01: Struktura internega validacijskega poročila**

Objekt `ValidationReport` vsebuje:
- `is_valid` (logična vrednost): True, če ne obstajajo ugotovitve na ravni ERROR
- `errors` (seznam): Niz objektov `ValidationError` s polji:
  - `sheet`: Ime delovnega lista
  - `row`: Številka vrstice Excel (1-bazirano)
  - `col`: Ime stolpca
  - `code`: Koda napake
  - `severity`: `ERROR`, `WARNING` ali `INFO`
  - `message`: Opisno sporočilo
- `counts`: Število napak po ravni resnosti
- `metadata`: Dodatne informacije (imena delovnih listov, števila vrstic)

**FS-REP-02: Format Excel poročila**

`ReportWriter.write_excel_report()` generira Excel delovni zvezek, ki vsebuje:

- **Delovni list "Povzetek"**:
  - Stolpci: List, Vrstica, Stolpec, Napaka (Koda napake), Opis napake
  - Omogočen avtomatski filter
  
- **Delovni list "Število napak"**:
  - Stolpci: Koda, Opis, Število
  - Agregirano po kodi napake
  - Omogočen avtomatski filter

**FS-REP-03: Format besedilnega poročila**

Format: `sheet | vrstica X | stolpec Y | CODE – opis`

Ena vrstica na napako, kodirano z UTF-8.

**FS-REP-04: Format JSON poročila**

JSON struktura, ki ustreza izhodu `ValidationReport.to_dict()`:
```json
{
  "source_path": "<pot>",
  "is_valid": true|false,
  "errors": [...],
  "counts": {"error": N, "warning": N, "info": N},
  "counts_by_code": {...},
  "metadata": {...}
}
```

### 5.6 Vmesnik ukazne vrstice (CLI)

**FS-CLI-01: Izvajanje CLI**

Sintaksa: `python -m validator_oop [workbook.xlsx] [možnosti]`

**FS-CLI-02: CLI parametri**

| Parameter | Tip | Opis |
|---|---|---|
| `workbook` | pozicijski | Pot do Excel delovnega zvezka (opcijsko; izpustite za zagon GUI) |
| `--output POT` | možnost | Izhodna pot datoteke za validacijsko poročilo |
| `--format {json,text,summary,excel}` | možnost | Format poročila (privzeto: excel) |
| `--verbose` | zastavica | Omogoči podroben izpis v konzolo |
| `--strict` | zastavica | Obravnavaj opozorila kot napake |
| `--bypass PRAVILO [PRAVILO ...]` | možnost | Imena pravil ali kode za izključitev iz validacije |
| `--include-formulas` | zastavica | Naloži in validiraj formule celic |
| `--apply-fixes` | zastavica | Ustvari kopijo delovnega zvezka s predlaganimi popravki |
| `--gui` | zastavica | Zaženi GUI način |

**FS-CLI-03: Izhodne kode**

| Izhodna koda | Pomen |
|---|---|
| `0` | Validacija uspešna (brez ugotovitev na ravni ERROR) |
| `1` | Odkrite validacijske napake (prisotne ugotovitve na ravni ERROR) |
| `2` | Napaka pri izvajanju (datoteka ni najdena, manjkajoče odvisnosti, izjema med izvajanjem) |

**FS-CLI-04: Log datoteka**

Log datoteka `MESValidator.log` se ustvari v HOME direktoriju uporabnika za diagnostične namene. Raven logiranja je DEBUG. To velja za CLI in GUI načine.

### 5.7 Grafični uporabniški vmesnik (GUI)

**FS-GUI-01: Izbira vhodne datoteke**
- Podpira izbiro ene ali več Excel vhodnih datotek
- Poti datotek prikazane v polju za vnos besedila (ločene s podpičjem)
- Funkcija "Počisti seznam" za ponastavitev izbire

**FS-GUI-02: Konfiguracija izhoda**
- Izbira radio gumba med:
  - Način "Kombiniranega poročila": Ena datoteka poročila (`.xlsx` ali `.txt`)
  - Način "Poročilo na datoteko": Ločeno poročilo na vhodno datoteko v izbrani mapi
- Dialogi za izbiro datoteke/direktorija

**FS-GUI-03: Izbira SOP dokumenta (opcijsko)**
- Opcijska izbira Word dokumenta (`.docx`) za validacijo skladnosti s SOP
- Če nalaganje SOP ne uspe, sistem zabeleži opozorilo in nadaljuje validacijo brez preverjanj SOP

**FS-GUI-04: Prikaz statusa in rezultatov**
- Statusno besedilno območje prikazuje:
  - Začetno sporočilo z verzijo
  - Napredek nalaganja datoteke
  - Status izvajanja validacije
  - Status nalaganja SOP (če je uporabno)
  - Povzetek števila napak
- Končno statusno sporočilo označuje rezultat validacije (uspeh/neuspeh)

### 5.8 Funkcionalnost Apply Fixes

**FS-AUTOFIX-01: Avtomatski popravki**

Metoda `WorkbookFixer.apply_fixes()` aplicira popravke, ko validacijska pravila zagotovijo predloge popravkov:

- Popravki se aplicirajo samo, ko zapis napake vsebuje:
  - `target_cell`: Referenco celice Excel
  - `proposed_value`: Popravljeno vrednost
  - `fix_kind="set_value"`: Indikator tipa popravka
- Konvencija poimenovanja izhodne datoteke: `<izvorno_ime>_AUTOFIX.xlsx`
- Izvorna vhodna datoteka ni nikoli spremenjena
- Število apliciranih popravkov je beleženo

## 6. Nefunkcionalne specifikacije

**FS-NFR-01: Združljivost platforme**
- Ciljna platforma: Operacijski sistem Windows
- Načini uporabe: Python okolje ali samostojni izvršljivi program (EXE)

**FS-NFR-02: Programske odvisnosti**

| Odvisnost | Status | Namen |
|---|---|---|
| `openpyxl` | Zahtevano | Branje in pisanje Excel datotek |
| `python-docx` | Opcijsko | Parsiranje SOP Word dokumentov |
| `tkinter` | Opcijsko | Funkcionalnost GUI (vključeno v standardnih Python distribucijah) |

**FS-NFR-03: Obravnava napak**
- Neveljavne ali poškodovane Excel datoteke: Jasno sporočilo o napaki, izhodna koda 2
- Manjkajoče odvisnosti: Jasne navodila za namestitev, izhodna koda 2
- Napaka pri nalaganju SOP: Zabeleženo opozorilo, validacija se nadaljuje brez SOP

**FS-NFR-04: Integriteta podatkov**
- Izvorne vhodne datoteke niso spremenjene z validacijskimi operacijami
- Datoteke poročil in autofix datoteke so ločeni izhodi z razločljivimi imeni datotek

**FS-NFR-05: Zmogljivost**
- Validacijske operacije se izvajajo sinhrono
- Zmogljivost je odvisna od velikosti delovnega zvezka, števila pravil in kompleksnosti formul
- Ni določenega specifičnega cilja zmogljivosti (glej URS-NFR-04 za ciljne smernice)

**FS-NFR-06: Beleženje in diagnostika**
- Konzolno beleženje s konfigurabilno podrobnostjo (zastavica `--verbose`)
- Datotečno beleženje v `MESValidator.log` v HOME direktoriju uporabnika
- Format loga: časovni žig, ime loggerja, raven, sporočilo

## 7. Znane omejitve

Dokumentirane so naslednje omejitve:

1. **Funkcionalnost primerjave sekcij delovnih listov** v GUI ni implementirana (prisoten element označevalnika v UI)
2. **Izvoz JSON poročila**: CLI uporablja direkten `json.dump()` namesto metode `ReportWriter.write_json_report()` (ohranjena funkcionalna ekvivalentnost)

Te omejitve ne vplivajo na skladnost z zahtevami URS.

---

## Podpisi za odobritev

| Vloga | Ime | Podpis | Datum |
|---|---|---|---|
| **Pripravil** | | | |
| **Pregledal (QA)** | | | |
| **Odobril (Lastnik procesa)** | | | |

---

**KONEC DOKUMENTA**
