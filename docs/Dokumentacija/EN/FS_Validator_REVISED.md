# Functional Specification (FS)
## MES Recipe Validator

---

## Document Control

| Field | Value |
|---|---|
| **Document Title** | Functional Specification (FS) |
| **System / Application** | MES Recipe Validator (validator_oop) |
| **Document ID** | VAL-FS-001 |
| **Version** | 1.0 |
| **Date** | 2026-02-04 |
| **Author** | ______________________ |
| **Reviewed by (QA)** | ______________________ |
| **Approved by (Process Owner)** | ______________________ |

---

## 1. Purpose

This document describes the functional implementation of the Validator system, including system architecture, components, input/output data structures, user interaction modes (GUI/CLI), and the complete set of validation rules.

## 2. References and Context

### 2.1 Related Documents

- **User Requirements Specification**: VAL-URS-001
- **Operational Qualification Protocol**: VAL-OQ-001
- **Risk Assessment**: VAL-RA-001
- **User SOP**: VAL-SOP-USE-001

### 2.2 Implementation Details

- **Software Package**: `validator_oop` (Python package)
- **Application Version**: Defined in constant `VERSION` in `core/constants.py` (e.g., "v 113 – 2025-11-25")

## 3. System Overview

### 3.1 System Components

The Validator system comprises the following architectural layers:

#### 3.1.1 User Interface Layer

- **GUI (Graphical User Interface)**: Tkinter-based interface implemented in `ui/main_window.py`
- **CLI (Command Line Interface)**: Implemented in `main.py`, invoked via `python -m validator_oop`

#### 3.1.2 Validation Core

- **Validator Engine** (`core/validator_engine.py`): Orchestrates workbook loading and validation rule execution
- **Rule Engine** (`core/rule_engine.py`): Manages rule instantiation, SharedContext construction, and execution of Row/Sheet/Workbook rules
- **Validation Report** (`core/report.py`): Aggregates validation errors and provides summary methods

#### 3.1.3 File Input/Output Layer

- **Excel Loader** (`excel/excel_loader.py`): Reads Excel workbooks using openpyxl library, with optional formula parsing
- **Report Writer** (`excel/report_writer.py`): Writes validation reports to `.xlsx`, `.txt`, and `.json` formats
- **SOP Loader** (`excel/sop_loader.py`): Parses SOP Word documents and extracts requirements (optional functionality)

#### 3.1.4 Validation Rules

- **Built-in Rules** (`rules/builtin/*`): Pre-defined validation rule implementations
- **Rule Registry** (`rules/rule_registry.py`): Central registration and instantiation mechanism
- **Rule Registration** (`rules/builtin/__init__.py`): Automatic registration of built-in rules

### 3.2 Technology Stack and Object-Oriented Design

#### 3.2.1 Implementation Technology

The Validator is implemented in **Python** programming language as package `validator_oop` with modular directory structure:
- `core/` – validation engine and business logic
- `excel/` – file I/O operations
- `rules/` – validation rule definitions
- `ui/` – user interface implementations
- `utils/` – shared utilities

#### 3.2.2 Object-Oriented Architecture

The system employs object-oriented design principles with clear separation of responsibilities:

**Core Classes:**
- `ValidatorEngine`: Orchestrates validation workflow (load → filter → execute rules → generate report)
- `RuleEngine`: Manages rule instantiation, SharedContext construction, and rule execution
- `ExcelLoader`: Encapsulates Excel workbook loading operations
- `ReportWriter`: Encapsulates report generation operations
- `WorkbookFixer`: Handles optional automatic correction operations

**Rule Class Hierarchy:**
- `BaseRule`: Abstract base class
- `RowRule`: Evaluates individual rows (inheritance + polymorphism)
- `SheetRule`: Evaluates entire worksheets
- `WorkbookRule`: Evaluates entire workbooks across multiple sheets

**Data Model Classes:**
- `ValidationError`: Standardized error record structure
- `ValidationReport`: Error aggregation and summary
- `RuleRegistry`: Centralized rule registration and dependency injection

#### 3.2.3 Design Patterns

- **Strategy / Plugin Pattern**: Individual validation rules are interchangeable strategies registered in `RuleRegistry`
- **Factory Pattern**: `RuleRegistry.instantiate()` creates rule instances with dependency injection
- **Dependency Injection**: Rules receive dependencies (e.g., `sop_data`, `logger`) via constructor injection
- **Pipeline Pattern**: Validation follows sequential stages: load → prepare context → execute rules → aggregate report → export

### 3.3 Execution Flow

#### 3.3.1 CLI Execution Flow

1. User invokes: `python -m validator_oop [workbook.xlsx] [options]`
2. System creates `ValidatorConfig` from command-line arguments
3. System registers built-in validation rules via `register_all()`
4. `ExcelLoader` reads Excel workbook (with optional formula loading)
5. `ValidatorEngine` filters worksheets based on required columns
6. `ValidatorEngine` invokes `RuleEngine.run()` on filtered worksheets
7. `RuleEngine` performs:
   - Rule instantiation from `RuleRegistry`
   - `SharedContext` construction for each worksheet
   - Sequential rule execution (Row rules → Sheet rules → Workbook rules)
   - `ValidationError` collection
8. `ValidationReport` aggregates results (`is_valid`, error counts, error details)
9. `ReportWriter` exports report to specified format (`.xlsx`, `.json`, or `.txt`), or CLI outputs summary to console

#### 3.3.2 GUI Execution Flow

1. User selects input Excel files via file selection dialog
2. User specifies output report path and format
3. (Optional) User selects SOP Word document (`.docx`), which is parsed into `SOPData` structure
4. GUI instantiates validation engine components
5. GUI triggers validation via `ValidatorEngine.validate()`
6. Results are displayed in status window
7. Validation report is written to specified output location

## 4. URS → FS Traceability Matrix

| URS Requirement | FS Specification |
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

## 5. Functional Specifications

### 5.1 Input Data and Loading

**FS-IO-01: Excel Workbook Loading**
- Excel workbooks are read using `openpyxl` library via `ExcelLoader.load()` method
- Values are loaded with `data_only=True` parameter
- Formulas are optionally loaded with `data_only=False` when `include_formulas=True` configuration is set

**FS-IO-02: Header Row and Row Offset**
- Default header row: Row 1 (1-based Excel indexing)
- Data row offset: `row_offset = header_row_index + 1` (default: 2)

**FS-IO-03: Worksheet Filtering**
- `ValidatorEngine` validates only worksheets containing at least one required column
- Required columns are defined in `core/constants.py` constant `REQUIRED_COLUMNS`

**FS-IO-04: SOP Document Loading (Optional)**
- SOP documents in Word format (`.docx`) are parsed via `SOPLoader.from_word()`
- SOP data structure (`SOPData`) contains IPO codes, volume/flow limits, and other requirements
- SOP loading failures are logged and validation continues without SOP compliance checks

### 5.2 Configuration Management

**FS-CONF-01: Validator Configuration Object**

Configuration is managed via `ValidatorConfig` class (`core/config.py`) with the following parameters:

| Parameter | Type | Description |
|---|---|---|
| `bypass_rules` | frozenset[str] | Rule names or codes to exclude from validation |
| `bypass_codes` | frozenset[str] | Error codes to suppress in output |
| `strict_mode` | bool | Convert warnings to errors when True |
| `include_formulas` | bool | Enable formula loading and validation |
| `bypass_zakleni_require_empty_for_checkbox` | bool | Legacy compatibility flag |
| `bypass_zakleni_require_pogoj_for_param1_steps` | bool | Legacy compatibility flag |
| `bypass_zakleni_inverse_pogoj_requirement` | bool | Legacy compatibility flag |
| `sop_data_path` | Path \| None | Path to SOP Word document |
| `enable_sop_validation` | bool | Enable/disable SOP compliance checks |

**FS-CONF-02: Strict Mode Implementation**
- When `strict_mode=True`, `RuleEngine.run()` converts all `Severity.WARNING` to `Severity.ERROR`

**FS-CONF-03: Rule Bypass Mechanism**
- Rules are filtered before execution based on `display_name` or `error_code` matching
- Filtering logic implemented in `ValidatorConfig.should_skip_rule()`

### 5.3 Validation Execution

**FS-VAL-01: Validation Orchestration**

`ValidatorEngine.validate(path)` method performs the following sequence:
1. Load workbook via `ExcelLoader`
2. Filter worksheets based on required columns
3. Invoke `RuleEngine.run()` on filtered worksheets
4. Construct and return `ValidationReport`

**FS-VAL-02: Shared Context Construction**

For each worksheet, a `SharedContext` object is constructed containing:
- Column list and mappings
- Pre-computed indexes (step numbers, keys by type, control column mappings)
- Additional objects stored in `SharedContext.extra` dictionary (e.g., `workbook_values`, `parsed_formulas`, `all_workbook_data`)

**FS-VAL-03: Rule Types**

Three rule types are supported:
- `RowRule`: Evaluates each row individually
- `SheetRule`: Evaluates entire worksheet (for cross-row validation)
- `WorkbookRule`: Evaluates entire workbook (for cross-sheet validation)

**FS-VAL-04: Rule Execution Sequence**

Rules are instantiated and executed in priority order (ascending `priority` attribute value).

### 5.4 Built-in Validation Rules

**NOTE:** The complete rule set is defined by module imports in `rules/builtin/__init__.py`. The following is a summary of implemented rule categories.

#### 5.4.1 FS-RULES-01: Structural Rules (Sheet-level)

**RequiredColumnsRule**
- Validates presence of all required columns
- Error code: `MISSING_COLUMN`

**StepNumberingRule**
- Validates step numbering in "št. Koraka" column
- Error codes:
  - `STEP_NOT_INT`: Step number is not an integer
  - `STEP_MISSING`: Missing step number in row with content
  - `STEP_DUPLICATE`: Duplicate step number (within tab/section)
  - `STEP_TAB_START_NOT_ONE`: Steps do not start with 1
  - `STEP_GAPS`: Missing intermediate step numbers

#### 5.4.2 FS-RULES-02: Field-Level Rules (Row-level)

**ObjectTypeRule**
- Error codes: `TIP_OBJEKTA_EMPTY`, `TIP_OBJEKTA_UNKNOWN`

**DataObjectCompatibilityRule**
- Error code: `OBJ_MISMATCH`

**LabelRequirementsRule**
- Error codes: `LABELA_KODA`, `UNIT_MISMATCH`

**KeyValidationRule**
- Error codes: `KEY_FORMAT`, `KEY_REQUIRED_MAIN_TYPES`

**FormulaSyntaxRule**
- Error codes: `FORMULA_SYNTAX`, `FORMULA_NOREF`

**FormulaReferenceRule**
- Error code: `FORMULA_BAD_REF`

**CommaNumberRule**
- Error code: `COMMA_NOT_ALLOWED`

#### 5.4.3 FS-RULES-03: Relational Rules (Sheet-level)

**DuplicateKeyRule**
- Error codes: `KEY_DUP_KEM`, `KEY_DUP_RAZT`, `KEY_DUP_TIME_START`, `KEY_DUP_TIME_END`, `KEY_DUP_MASA`

**MassOwnerRule**
- Error codes: `PAIR_MASA_NO_OWNER`, `PAIR_MASA_WRONG_SECTION`

**TimePairRule**
- Error codes: `PAIR_TIME_NO_START`, `PAIR_TIME_NO_END`, `KEY_DUP_TIME_PAIR`

**KeyNumberingRule**
- Error codes: `KEY_NUM_START`, `KEY_NUM_GAP`, `KEY_NUM_DUPLICATE_ONE` (severity: WARNING)

**TehtnicaMasaPairRule**
- Error code: `CTRL_TEHTNICA_NO_MASA`

**TehtnicaVrednostFromFormulaRule**
- Error codes: `TEHTNICA_VREDNOST_INVALID_HIGH`, `TEHTNICA_VREDNOST_INVALID_LOW`

#### 5.4.4 FS-RULES-04: Control Rules (Row/Sheet-level)

**UnknownControlsRule**
- Error code: `CTRL_UNKNOWN`

**ControlContextRule**
- Error code: `CTRL_BAD_CONTEXT`

**RequiredControlsRule**
- Error codes: `CTRL_REQUIRED_EMPTY`, `CTRL_CHECKBOX_EMPTY`, `CTRL_LOCKED_NO_EMPTY`, `CTRL_LOCKED_NO_CHECK`

**ExpectedControlsRule**
- Error code: `CTRL_EXPECTED_MISSING` (severity: WARNING)

**ZakleniParamRule**
- Error codes: `ZAKLENI_PAR1_EXCEL_ERR`, `ZAKLENI_PAR1_FORMAT`, `ZAKLENI_P1_STEP_MISSING`, `ZAKLENI_P1_NO_POGOJ`

**AliObstajaPogojCombinationRule**
- Error code: `ZAKLENI_POGOJ_P1P2`

**ZakleniUniqueKeyRule**
- Error code: `ZAKLENI_KEY_DUPLICATE`

**ZakleniInverseRule**
- Error code: `ZAKLENI_P1_MISSING_FOR_POGOJ`

**AliObkljukanParamRule**
- Error codes: `CHECKBOX_PARAM`, `CHECKBOX_STATE`

**KontrolaIntervalParamRule / KontrolaIntervalAdvancedRule**
- Error codes: `CTRL_INTERVAL_PARAMS`, `CTRL_INTERVAL_NUM`, `CTRL_INTERVAL_ORDER`, `CTRL_INTERVAL_RANGE_P1_EXACT`, `CTRL_INTERVAL_RANGE_P2_EXACT`, `CTRL_INTERVAL_PM_P1_EXACT`, `CTRL_INTERVAL_PM_P2_EXACT`, `CTRL_INTERVAL_TARGET_P1_EXACT`, `CTRL_INTERVAL_TARGET_P2_EXACT`, `CTRL_INTERVAL_TARGET_P1_MAX`, `CTRL_INTERVAL_TARGET_P2_MIN`

**KontrolaCasaRule**
- Error codes: `CTRL_CASA_MIN`, `CTRL_CASA_MIN_NUM`, `CTRL_CASA_MAX_NUM`, `CTRL_CASA_ORDER`, `CTRL_CASA_P1_FROM_NAV`, `CTRL_CASA_P2_FROM_NAV`

#### 5.4.5 FS-RULES-05: SOP Compliance Rule (Workbook-level, Optional)

**SOPComplianceRule** (executes only when SOP data is loaded)

Validates the following against SOP requirements:
- IPO codes from "Podatki" worksheet: Error codes `SOP_IPO_MISMATCH`, `SOP_IPO_MISSING`, `SOP_IPO_NOT_ALLOWED`
- Volume ranges (considering column volume from "V monolita"): Error codes `SOP_VOLUME_TOO_LOW`, `SOP_VOLUME_TOO_HIGH`
- Flow rates (matched to column volume): Error codes `SOP_FLOW_TOO_LOW`, `SOP_FLOW_TOO_HIGH`
- Solution types: Error code `SOP_TYPE_NOT_ALLOWED`
- Sample specifications, tSST, Vr, N, pressure, distribution coefficient (D): Error codes `SOP_SAMPLE_NOT_ALLOWED`, `SOP_TSST_*`, `SOP_VR_*`, `SOP_N_TOO_LOW`, `SOP_PRESSURE_*`, `SOP_D_*`
- Medium compliance (PM1/PM23/TK/endotoxins): Error code `SOP_MEDIUM_MISMATCH`

### 5.5 Output Data (Validation Reports)

**FS-REP-01: Internal Validation Report Structure**

`ValidationReport` object contains:
- `is_valid` (boolean): True if no ERROR-level findings exist
- `errors` (list): Array of `ValidationError` objects with fields:
  - `sheet`: Worksheet name
  - `row`: Excel row number (1-based)
  - `col`: Column name
  - `code`: Error code
  - `severity`: `ERROR`, `WARNING`, or `INFO`
  - `message`: Descriptive message
- `counts`: Error count by severity level
- `metadata`: Additional information (worksheet names, row counts)

**FS-REP-02: Excel Report Format**

`ReportWriter.write_excel_report()` generates Excel workbook containing:

- **Worksheet "Povzetek" (Summary)**:
  - Columns: List (Sheet), Vrstica (Row), Stolpec (Column), Napaka (Error Code), Opis napake (Error Description)
  - Auto-filter enabled
  
- **Worksheet "Število napak" (Error Count)**:
  - Columns: Koda (Code), Opis (Description), Število (Count)
  - Aggregated by error code
  - Auto-filter enabled

**FS-REP-03: Text Report Format**

Format: `sheet | vrstica X | stolpec Y | CODE – description`

One line per error, UTF-8 encoded.

**FS-REP-04: JSON Report Format**

JSON structure matching `ValidationReport.to_dict()` output:
```json
{
  "source_path": "<path>",
  "is_valid": true|false,
  "errors": [...],
  "counts": {"error": N, "warning": N, "info": N},
  "counts_by_code": {...},
  "metadata": {...}
}
```

### 5.6 Command Line Interface (CLI)

**FS-CLI-01: CLI Invocation**

Syntax: `python -m validator_oop [workbook.xlsx] [options]`

**FS-CLI-02: CLI Parameters**

| Parameter | Type | Description |
|---|---|---|
| `workbook` | positional | Path to Excel workbook (optional; omit to launch GUI) |
| `--output PATH` | option | Output file path for validation report |
| `--format {json,text,summary,excel}` | option | Report format (default: excel) |
| `--verbose` | flag | Enable verbose console output |
| `--strict` | flag | Treat warnings as errors |
| `--bypass RULE [RULE ...]` | option | Rule names or codes to exclude from validation |
| `--include-formulas` | flag | Load and validate cell formulas |
| `--apply-fixes` | flag | Create workbook copy with proposed corrections |
| `--gui` | flag | Launch GUI mode |

**FS-CLI-03: Exit Codes**

| Exit Code | Meaning |
|---|---|
| `0` | Validation successful (no ERROR-level findings) |
| `1` | Validation errors detected (ERROR-level findings present) |
| `2` | Runtime error (file not found, missing dependencies, exception during execution) |

**FS-CLI-04: Log File**

A log file `MESValidator.log` is created in the user's HOME directory for diagnostic purposes. Log level is DEBUG. This applies to both CLI and GUI modes.

### 5.7 Graphical User Interface (GUI)

**FS-GUI-01: Input File Selection**
- Supports selection of one or multiple Excel input files
- File paths displayed in text entry field (semicolon-separated)
- "Clear list" function to reset selection

**FS-GUI-02: Output Configuration**
- Radio button selection between:
  - "Combined report" mode: Single report file (`.xlsx` or `.txt`)
  - "Per-file report" mode: Separate report per input file in selected directory
- File/directory selection dialogs

**FS-GUI-03: SOP Document Selection (Optional)**
- Optional Word document (`.docx`) selection for SOP compliance validation
- If SOP loading fails, system logs warning and continues validation without SOP checks

**FS-GUI-04: Status Display and Results**
- Status text area displays:
  - Startup message with version
  - File loading progress
  - Validation execution status
  - SOP loading status (if applicable)
  - Error count summary
- Final status message indicates validation outcome (pass/fail)

### 5.8 Apply Fixes Functionality

**FS-AUTOFIX-01: Automatic Correction**

`WorkbookFixer.apply_fixes()` method applies corrections when validation rules provide fix proposals:

- Corrections are applied only when issue record contains:
  - `target_cell`: Excel cell reference
  - `proposed_value`: Corrected value
  - `fix_kind="set_value"`: Correction type indicator
- Output file naming convention: `<original_name>_AUTOFIX.xlsx`
- Original input file is never modified
- Number of applied corrections is logged

## 6. Non-Functional Specifications

**FS-NFR-01: Platform Compatibility**
- Target platform: Windows operating system
- Deployment modes: Python environment or standalone executable (EXE)

**FS-NFR-02: Software Dependencies**

| Dependency | Status | Purpose |
|---|---|---|
| `openpyxl` | Required | Excel file reading and writing |
| `python-docx` | Optional | SOP Word document parsing |
| `tkinter` | Optional | GUI functionality (included in standard Python distributions) |

**FS-NFR-03: Error Handling**
- Invalid or corrupted Excel files: Clear error message, exit code 2
- Missing dependencies: Clear installation instruction, exit code 2
- SOP loading failure: Warning logged, validation continues without SOP

**FS-NFR-04: Data Integrity**
- Original input files are not modified by validation operations
- Report files and autofix files are separate outputs with distinct filenames

**FS-NFR-05: Performance**
- Validation operations execute synchronously
- Performance is dependent on workbook size, number of rules, and formula complexity
- No specific performance target is defined (see URS-NFR-04 for target guidance)

**FS-NFR-06: Logging and Diagnostics**
- Console logging with configurable verbosity (`--verbose` flag)
- File logging to `MESValidator.log` in user HOME directory
- Log format: timestamp, logger name, level, message

## 7. Known Limitations

The following limitations are documented:

1. **Worksheet section comparison functionality** in GUI is not implemented (placeholder UI element present)
2. **JSON report export**: CLI uses direct `json.dump()` rather than `ReportWriter.write_json_report()` method (functional equivalence maintained)

These limitations do not affect compliance with URS requirements.

---

## Approval Signatures

| Role | Name | Signature | Date |
|---|---|---|---|
| **Prepared by** | | | |
| **Reviewed by (QA)** | | | |
| **Approved by (Process Owner)** | | | |

---

**END OF DOCUMENT**
