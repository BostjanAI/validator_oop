# Validator OOP - Cheat Sheet 🚀

> Hitra referenca za najpogostejše operacije

---

## ⚡ Hitri ukazi

```bash
# CLI validacija
python -m validator_oop receptura.xlsx

# GUI
python -m validator_oop

# Verbose
python -m validator_oop receptura.xlsx --verbose

# Apply fixes
python -m validator_oop receptura.xlsx --apply-fixes
```

---

## 🏗️ Arhitektura v 30 sekundah

```
main.py
  ↓
ValidatorEngine  ← Orkestracija
  ↓
RuleEngine       ← Izvajanje pravil (+ SharedContext)
  ↓
Rules            ← RowRule/SheetRule/WorkbookRule (30+ pravil)
  ↓
ExcelLoader      ← Branje Excel
```

**Ključni razredi:**
- `ValidatorEngine` - glavni orkestrator
- `RuleEngine` - izvaja pravila
- `SharedContext` - deljeni podatki (checkpoint, keys, steps)
- `ValidationReport` - rezultat validacije

---

## 📁 Kje najti...?

| Kaj | Kje |
|-----|-----|
| **Nova pravila** | `rules/builtin/*.py` |
| **Parsanje časa/števil** | `utils/helpers.py` |
| **Dovoljene vrednosti** | `core/constants.py` |
| **Regex vzorci** | `core/constants.py` |
| **Excel operacije** | `excel/*.py` |
| **GUI** | `ui/*.py` |
| **Testi** | `tests/*.py` |

---

## ➕ Dodaj novo pravilo (5 korakov)

```python
# 1. Uvozi
from validator_oop.rules import RowRule, register
from validator_oop.utils.helpers import coerce_str

# 2. Definiraj
@register
class MyRule(RowRule):
    name = "My Rule"
    code = "MY_CODE"
    priority = 100
    
    # 3. Implementiraj
    def evaluate(self, row, context):
        value = coerce_str(row.get("Stolpec", ""))
        
        # 4. Preveri
        if not value:
            # 5. Vrni napako
            yield self.build_error(
                "Sporočilo napake",
                context=context,
                column="Stolpec"
            )
```

---

## 🔍 Uporaba SharedContext

```python
# V pravilu:
def evaluate(self, row, context):
    # Dostop do predizračunanih podatkov
    checkbox_states = context.shared.checkbox_states
    existing_steps = context.shared.existing_steps
    keys_by_type = context.shared.keys_by_type
    control_columns = context.shared.control_columns
    
    # Preveri, če korak obstaja
    if context.shared.has_step(5):
        print("Korak 5 obstaja")
    
    # Dobi kontrole pri koraku
    controls = context.shared.get_controls_at_step(3)
```

---

## 🎯 Tri tipe pravil

### RowRule (najpogostejše)
```python
class MyRowRule(RowRule):
    def evaluate(self, row, context):
        # Validacija ENE vrstice
        yield error
```

### SheetRule (cross-row)
```python
class MySheetRule(SheetRule):
    def evaluate_sheet(self, rows, context, row_offset):
        # Validacija CELOTNEGA lista
        # (npr. podvajanja, pari)
        yield error
```

### WorkbookRule (cross-sheet)
```python
class MyWorkbookRule(WorkbookRule):
    def evaluate_workbook(self, workbook_data, context, row_offset):
        # Validacija CELOTNE knjige
        yield error
```

---

## ⚙️ Konfiguracija

```python
from validator_oop.core import ValidatorConfig

config = ValidatorConfig(
    bypass_rules=frozenset(["KeyValidationRule"]),
    strict_mode=False,  # True: WARNING → ERROR
    row_offset=2,
    include_formulas=False,
)
```

---

## 🧪 Testiranje

```bash
# Vse teste
pytest

# En test
pytest tests/test_rules.py::test_key_validation

# Verbose
pytest -v

# Coverage
pytest --cov=validator_oop
```

---

## 📊 Uporaba v kodi

```python
from validator_oop.core import ValidatorEngine, RuleEngine, ValidatorConfig
from validator_oop.excel import ExcelLoader
from validator_oop.rules import default_registry
from validator_oop.rules.builtin import register_all

# Setup
register_all()
loader = ExcelLoader()
config = ValidatorConfig()
rule_engine = RuleEngine(default_registry, config=config)
validator = ValidatorEngine(rule_engine, loader)

# Validiraj
report = validator.validate("receptura.xlsx")

# Rezultat
print(f"Valid: {report.is_valid()}")
print(f"Errors: {len(report.errors)}")
for error in report.errors:
    print(f"  [{error.code}] {error.message}")
```

---

## 🔧 Najpogostejše pomožne funkcije

```python
from validator_oop.utils.helpers import (
    coerce_str,              # value → string
    norm_text,               # lowercase, trim
    norm_control_name,       # normalize kontrole
    parse_checkbox_state,    # "da" → 1, "ne" → 0
    base_key_no_trailing_number,  # "key_5" → "key"
    parse_time_phrase_to_seconds,  # "2 h" → 7200
    parse_numeric_value,     # "25 °C" → 25.0
    extract_unit_token,      # "25 °C" → "°c"
)
```

---

## 📝 Konstante (core/constants.py)

```python
REQUIRED_COLUMNS = [
    "št. Koraka", "Navodilo", "Tip podatka",
    "Ključ preverjanja", "Vrednost", "Labela", "Tip objekta"
]

ALLOWED_TIP_OBJEKTA = {
    "edit", "checkbox", "formula", "naslov", ...
}

STANDARD_TIP_PODATKA = {
    "kemikalija", "masa", "datumcas", "tehtnica", ...
}

ALLOWED_CONTROLS = {
    "kontrolapraznopolje", "kontrolaintervala",
    "aliobstajapogoj", "zaklenipolja", ...
}
```

---

## 🐛 Debugging

### Log datoteke
- GUI/exe: `MESValidator.log` v home direktoriju
- CLI: Console + file log

### Preveri registrirana pravila
```python
from validator_oop.rules import default_registry
from validator_oop.rules.builtin import register_all

count = register_all()
print(f"Pravil: {default_registry.count()}")
```

### Testiraj eno pravilo
```python
from validator_oop.rules.builtin.field import KeyValidationRule

rule = KeyValidationRule()
errors = list(rule.evaluate(row, context))
```

---

## 💡 Tipi & Triči

### Hitro testiranje
```bash
python -m validator_oop samples/receptura_brez_napak.xlsx --format summary
```

### Bypass specifično pravilo
```bash
python -m validator_oop receptura.xlsx --bypass KeyValidationRule
```

### Strict mode (WARNING → ERROR)
```bash
python -m validator_oop receptura.xlsx --strict
```

### JSON poročilo
```bash
python -m validator_oop receptura.xlsx --output report.json --format json
```

---

## 📚 30+ vgrajenih pravil

### Structural (2)
- RequiredColumnsRule
- StepNumberingRule

### Field (7)
- ObjectTypeRule
- DataObjectCompatibilityRule
- LabelRequirementsRule
- KeyValidationRule
- FormulaSyntaxRule
- CommaNumberRule
- FormulaReferenceRule

### Relational (6)
- DuplicateKeyRule
- MassOwnerRule
- TimePairRule
- KeyNumberingRule
- TehtnicaMasaPairRule
- TehtnicaVrednostFromFormulaRule

### Control (13)
- UnknownControlsRule
- ControlContextRule
- RequiredControlsRule
- ExpectedControlsRule
- ZakleniParamRule
- AliObstajaPogojCombinationRule
- ZakleniUniqueKeyRule
- ZakleniInverseRule
- ZakleniCheckboxRule
- AliObkljukanParamRule
- KontrolaIntervalParamRule
- KontrolaIntervalAdvancedRule
- KontrolaCasaRule

### SOP (1)
- SOPComplianceRule

---

**Verzija:** v 122 – 2026-02-06
