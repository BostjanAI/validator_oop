# Validator OOP - MES Excel Validator

> Sistem za validacijo Excel receptur za farmacevtsko proizvodnjo (MES)

**Verzija:** v 122 – 2026-02-06

---

## 📋 Hitri pregled

Validator OOP preverja skladnost Excel receptur s pravili za MES (Manufacturing Execution System). Aplikacija zazna napake v strukturi, formatih, kontrolah in relacijah med podatki.

### Ključne funkcionalnosti
- ✅ Validacija strukturnih pravil (stolpci, koraki)
- ✅ Preverjanje formatov polj (ključi, formule, tipi)
- ✅ Relacijska validacija (pari kemikalija-masa, podvajanja)
- ✅ Kontrolne validacije (intervali, pogoji, zaklenjenja)
- ✅ SOP compliance validacija (opcijsko)
- ✅ GUI in CLI vmesnik
- ✅ JSON/Excel poročila

---

## 🚀 Hitri začetek

### CLI uporaba
```bash
# Osnovna validacija
python -m validator_oop receptura.xlsx

# Validacija z JSON poročilom
python -m validator_oop receptura.xlsx --output report.json --format json

# Validacija z verbose logom
python -m validator_oop receptura.xlsx --verbose

# Aplikacija popravkov
python -m validator_oop receptura.xlsx --apply-fixes
```

### GUI uporaba
```bash
# Klasični GUI
python -m validator_oop

# Tematski GUI (črno-rumeni)
python -m validator_oop --gui-style themed
```

### Programska uporaba
```python
from validator_oop.core import ValidatorEngine, RuleEngine, ValidatorConfig
from validator_oop.excel import ExcelLoader
from validator_oop.rules import default_registry
from validator_oop.rules.builtin import register_all

# Registriraj pravila
register_all()

# Ustvari motorje
loader = ExcelLoader()
config = ValidatorConfig()
rule_engine = RuleEngine(default_registry, config=config)
validator = ValidatorEngine(rule_engine, loader)

# Validiraj
report = validator.validate("receptura.xlsx")

if report.is_valid():
    print("✓ Receptura je veljavna")
else:
    print(f"✗ Najdenih {len(report.errors)} napak")
    for error in report.errors:
        print(f"  - {error.message}")
```

---

## 📊 Spremljanje napredka

Validator ob vsaki validaciji (GUI ali CLI) samodejno zapiše rezultat v **enotno datoteko napredka**, da lahko spremljate:

- **delež pregledanih receptur** (glede na skupno število receptur),
- **število zaznanih napak** (skupaj po vseh validacijah).

- **Datoteka:** `validation_progress.json` v mapi projekta (koren validator_oop).
- **Vsebina:** `total_recipes` (skupno število receptur – nastavite ročno) in `runs` (seznam validacij: zaporedna_stevilka, path, datum, errors, warnings, valid).

**Nastavitev skupnega števila receptur:** v datoteki `validation_progress.json` nastavite polje `"total_recipes"` na število vseh receptur. Delež pregledanih se izračuna kot (število unikatnih pregledanih datotek) / `total_recipes`.

**Kazalniki v kodi:**

```python
from validator_oop.utils.validation_progress import get_metrics, set_total_recipes

metrics = get_metrics()
# metrics["unique_files"], metrics["total_errors"], metrics["total_warnings"],
# metrics["total_recipes"], metrics["coverage_ratio"]

set_total_recipes(100)  # nastavi skupno število receptur
```

---

## 🏗️ Arhitektura (High-Level)

```
┌──────────────────────────────────────────────────────────┐
│                     UI Layer                              │
│  (tkinter GUI / CLI)                                      │
└───────────────────────────┬──────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│                  ValidatorEngine                          │
│  • Orkestracija celotnega procesa                        │
│  • Filtriranje listov (samo z REQUIRED_COLUMNS)          │
└───────────────────────────┬──────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│                    RuleEngine                             │
│  • Izvajanje pravil (RowRule/SheetRule/WorkbookRule)     │
│  • Gradnja SharedContext                                  │
│  • Bypass mehanizem                                       │
└───────────────────────────┬──────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│              Validation Rules (30+ pravil)                │
│  • Structural: Stolpci, koraki                           │
│  • Field: Tipi, ključi, formule                          │
│  • Relational: Pari, podvajanja                          │
│  • Control: Intervali, pogoji, zaklenjenja               │
└───────────────────────────┬──────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│                    ExcelLoader                            │
│  • Branje Excel (openpyxl)                               │
│  • Pretvorba v slovarje                                   │
└──────────────────────────────────────────────────────────┘
```

### Ključni koncepti

1. **ValidatorEngine**: Glavna orkestracijska točka
2. **RuleEngine**: Koordinator izvajanja pravil
3. **SharedContext**: Predizračunani podatki deljeni med pravili
4. **Registry Pattern**: Dinamična registracija pravil z `@register`
5. **Strategy Pattern**: RowRule/SheetRule/WorkbookRule

---

## 📁 Struktura projekta

```
validator_oop/
├── core/                    # Jedro sistema
│   ├── validator_engine.py # Glavna orkestracijska točka
│   ├── rule_engine.py      # Izvajanje pravil
│   ├── shared_context.py   # Deljeni podatki
│   ├── config.py           # Konfiguracija
│   ├── error.py            # ValidationError, Severity
│   ├── report.py           # ValidationReport
│   └── constants.py        # Konstante, regex, dovoljene vrednosti
│
├── rules/                   # Validacijska pravila
│   ├── base_rule.py        # Bazni razredi
│   ├── rule_registry.py    # RuleRegistry
│   └── builtin/            # Vgrajena pravila
│       ├── structural.py   # 2 pravila (stolpci, koraki)
│       ├── field.py        # 7 pravil (tipi, ključi, formule)
│       ├── relational.py   # 6 pravil (pari, podvajanja)
│       ├── control.py      # 13 pravil (intervali, pogoji)
│       └── sop_compliance_rule.py  # 1 pravilo (SOP)
│
├── excel/                   # Excel operacije
│   ├── excel_loader.py     # Branje Excel
│   ├── workbook_parser.py  # Pretvorba v slovarje
│   ├── report_writer.py    # Pisanje poročil
│   └── sop_loader.py       # Branje SOP Word
│
├── ui/                      # Grafični vmesnik
│   ├── main_window.py      # Klasični GUI
│   ├── main_window_themed.py  # Tematski GUI
│   └── run_validator.py    # GUI launcher
│
├── utils/                   # Pomožne funkcije
│   ├── helpers.py          # 70+ funkcij (parsanje, normalizacija)
│   ├── logger.py           # Logging
│   └── file_paths.py       # Delo z datotekami
│
├── tests/                   # Testi (pytest)
├── samples/                 # Primeri receptur
├── docs/                    # Dokumentacija
└── main.py                  # Glavna vstopna točka
```

---

## 🔧 Kako dodati pravilo varno

### 1. Dodaj novo pravilo

```python
# Lokacija: rules/builtin/xxx.py

from validator_oop.rules import RowRule, register
from validator_oop.core.error import Severity
from validator_oop.utils.helpers import coerce_str

@register
class MyNewRule(RowRule):
    """Opis pravila."""
    
    name = "My New Rule"
    code = "MY_NEW_RULE"
    priority = 100  # Manjše = prej
    severity = Severity.ERROR
    
    def evaluate(self, row, context):
        """Validacija za eno vrstico."""
        value = coerce_str(row.get("Stolpec", ""))
        
        if not value:
            yield self.build_error(
                "Manjka vrednost v stolpcu",
                context=context,
                column="Stolpec"
            )
```

**Tri tipe pravil:**
- `RowRule`: Validacija po vrsticah (najpogosteje)
- `SheetRule`: Validacija celotnega lista (za cross-row preverbe)
- `WorkbookRule`: Validacija celotne knjige (za cross-sheet preverbe)

### 2. Dodaj novo konstanto

```python
# Lokacija: core/constants.py

ALLOWED_TIP_OBJEKTA = frozenset({
    "edit", "checkbox", "formula",
    "moj_novi_tip",  # ← Dodaj novo
})
```

### 3. Dodaj novo pomožno funkcijo

```python
# Lokacija: utils/helpers.py

def my_helper_function(text: str) -> bool:
    """Opis funkcije."""
    # Tvoja logika
    return True
```

### 4. Dodaj test

```python
# Lokacija: tests/test_my_rule.py

def test_my_new_rule():
    """Test za MyNewRule."""
    from validator_oop.rules.builtin.xxx import MyNewRule
    
    rule = MyNewRule()
    row = {"Stolpec": ""}
    context = RuleContext(sheet="Test", row_index=2)
    
    errors = list(rule.evaluate(row, context))
    assert len(errors) == 1
    assert errors[0].code == "MY_NEW_RULE"
```

### 5. Obvezni checklist pred merge

- Posodobi ali dodaj ciljane teste v `tests/`
- Za produkcijski bug dodaj regresijski primer ali fixture
- Posodobi `CHANGELOG.md` pod `## [Unreleased]`
- Preveri pričakovano poročilo oziroma kodo napake
- Zaženi `python scripts/check_clean_workspace.py`

---

## 🧭 Navigacija po kodi

### Kje najti...?

| Kaj iščeš | Kje gledaš |
|-----------|-----------|
| Novo pravilo | `rules/builtin/*.py` |
| Parsanje časa/števil/enot | `utils/helpers.py` |
| Dovoljene vrednosti | `core/constants.py` → `ALLOWED_*` |
| Regex vzorce | `core/constants.py` → `*_PATTERN`, `*_RE` |
| Kako se pravilo registrira | `rules/base_rule.py`, `rules/rule_registry.py` |
| Kako deluje SharedContext | `core/shared_context.py` |
| Branje Excel | `excel/excel_loader.py` |
| Pisanje poročil | `excel/report_writer.py` |
| CLI argumenti | `main.py` → `parse_args()` |
| GUI | `ui/main_window*.py` |

### Pomembni koncepti v SharedContext

```python
# SharedContext vsebuje predizračunane podatke:
context.shared.checkbox_states        # dict[str, int|None]
context.shared.step_to_controls       # dict[int, set[str]]
context.shared.existing_steps         # set[int]
context.shared.zakleni_param1_steps   # set[int]
context.shared.keys_by_type           # dict[str, dict[str, list[int]]]
context.shared.control_columns        # list[str]
context.shared.param1_columns         # dict[int, str]
```

---

## ⚙️ Konfiguracija

### ValidatorConfig parametri

```python
config = ValidatorConfig(
    bypass_rules=frozenset(["KeyValidationRule"]),  # Preskoči pravilo
    bypass_codes=frozenset(["KEY_FORMAT"]),         # Potlači napako
    strict_mode=False,        # True: WARNING → ERROR
    row_offset=2,             # Prva vrstica podatkov
    include_formulas=False,   # Naloži formule (počasneje)
    stop_on_first_error=False,  # Ustavi ob prvi napaki
    
    # Bypass flagi za specifične situacije
    bypass_zakleni_require_empty_for_checkbox=True,
    bypass_zakleni_require_pogoj_for_param1_steps=True,
    bypass_zakleni_inverse_pogoj_requirement=False,
    
    # SOP validacija
    sop_data_path=Path("sop.docx"),
    enable_sop_validation=True,
)
```

---

## 🧪 Testiranje

```bash
# Zaženi vse teste
pytest

# Zaženi specifičen test
pytest tests/test_rules.py

# Zaženi z verbose
pytest -v

# Hitri PR nabor za control pravila
pytest tests/test_control_rules.py tests/test_control_rule_matrix.py

# Regresijski nabor za prej opažene edge-case scenarije
pytest -m regression
```

### Clean workspace check

Pred merge zaženi:

```bash
python scripts/check_clean_workspace.py
```

Skripta opozori na generated artefakte, kot so `__pycache__/`, `.pytest_cache/`, `analytics_out/` in `*.pyc`, da v commitih ostane manj šuma.

---

## 📊 Primeri uporabe

### Validacija z bypass-i

```python
config = ValidatorConfig(
    bypass_rules=frozenset(["SOPComplianceRule"]),
    strict_mode=False
)

validator = ValidatorEngine(rule_engine, loader)
report = validator.validate("receptura.xlsx")
```

### Aplikacija popravkov

```python
from validator_oop.excel.report_writer import WorkbookFixer

fixer = WorkbookFixer()
num_fixes = fixer.apply_fixes(
    source_path="receptura.xlsx",
    output_path="receptura_AUTOFIX.xlsx",
    issues=report.errors
)
print(f"Uveljavljenih {num_fixes} popravkov")
```

### Filtriranje napak po resnosti

```python
errors = report.filter_by_severity(Severity.ERROR)
warnings = report.filter_by_severity(Severity.WARNING)

print(f"Napake: {len(errors)}")
print(f"Opozorila: {len(warnings)}")
```

---

## 🔍 Debugging

### Log datoteke

- **GUI/exe**: `MESValidator.log` v home direktoriju (`Path.home()`)
- **CLI**: Console output + file log

### Verbose mode

```bash
python -m validator_oop receptura.xlsx --verbose
```

### Preverjanje registriranih pravil

```python
from validator_oop.rules import default_registry
from validator_oop.rules.builtin import register_all

count = register_all()
print(f"Registriranih {count} pravil")
print(f"Skupaj: {default_registry.count()} pravil")

# Izpiši vsa pravila
for rule_cls in default_registry.all():
    print(f"  - {rule_cls.name} (priority: {rule_cls.priority})")
```

---

## 📚 Dodatna dokumentacija

- **Funkcionalna specifikacija**: `docs/Dokumentacija/EN/FS_Validator_REVISED.md`
- **Operacijska kvalifikacija**: `docs/Dokumentacija/EN/OQ_Validator_REVISED.md`
- **User Requirements**: `docs/Dokumentacija/EN/URS_Validator_REVISED.md`
- **SOP**: `docs/Dokumentacija/EN/SOP_Uporaba_Validatorja_REVISED.md`

---

## 🛠️ Tehnologije

- **Python 3.x** (moderna sintaksa z type hints)
- **openpyxl** - Branje/pisanje Excel
- **tkinter** - GUI
- **pytest** - Testiranje
- **python-docx** - Branje Word (SOP)
- **PyInstaller** - Build exe

---

## 📝 Licenca

Interni projekt - MES farmacevtska proizvodnja

---

## 💡 Tips & Tricks

### Hitri test validacije

```bash
python -m validator_oop samples/receptura_brez_napak.xlsx --format summary
```

### Poišči vse kontrolne stolpce v recepturi

```python
from validator_oop.core.shared_context import SharedContextBuilder

builder = SharedContextBuilder()
context = builder.build(rows, columns)
print(f"Kontrolni stolpci: {context.control_columns}")
print(f"Param1 stolpci: {context.param1_columns}")
```

### Debug specifično pravilo

```python
from validator_oop.rules.builtin.field import KeyValidationRule

rule = KeyValidationRule()
errors = list(rule.evaluate(row, context))
print(f"Napake: {errors}")
```

---

**Za vprašanja ali težave**: Preveri `MESValidator.log` in si oglej test primere v `tests/`
