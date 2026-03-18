# Standard Operating Procedure (SOP)
## Operation of MES Recipe Validator

---

## Document Control

| Field | Value |
|---|---|
| **Document Title** | Standard Operating Procedure – Validator Operation |
| **System / Application** | MES Recipe Validator (validator_oop) |
| **Document ID** | VAL-SOP-USE-001 |
| **Version** | 1.0 |
| **Effective Date** | To be determined upon approval |
| **Date** | 2026-02-04 |
| **SOP Owner** | ______________________ |
| **Approved by (QA)** | ______________________ |

---

## 1. Purpose

This Standard Operating Procedure defines the standardized process for using the MES Recipe Validator to verify Excel recipe files and generate validation reports documenting identified errors and warnings.

## 2. Scope

This SOP applies to all personnel responsible for pre-validation of MES recipes (QA, Production, Process departments) using the Validator in Windows environments via GUI or CLI interfaces.

## 3. Responsibilities

| Role | Responsibility |
|---|---|
| **End User** | Correct input file selection, validation execution, report review, corrective action initiation |
| **QA** | Define validation expectations, review validation results when required, approve bypass usage |
| **System Administrator** | Installation support, diagnostics, software updates, user training |

## 4. Equipment and Prerequisites

### 4.1 Required Equipment and Software

- Windows 10 or Windows 11 operating system
- MES Recipe Validator (Python environment or EXE distribution)

### 4.2 Software Dependencies (Python Environment Only)

| Dependency | Status | Purpose |
|---|---|---|
| `openpyxl` | Required | Excel file operations |
| `python-docx` | Optional | SOP Word document parsing |
| `tkinter` | Optional | GUI functionality |

### 4.3 Training Requirements

Users shall be trained on:
- Validator operation (GUI or CLI as applicable)
- Report interpretation
- Error code meanings and corrective actions
- Escalation procedures for unresolved errors

## 5. Procedure – GUI Operation (Recommended for Most Users)

### 5.1 Launching the GUI

**Applicable to:** Python environment installations

**Procedure:**
1. Navigate to directory `validator_oop\` in file explorer
2. Execute: `python main.py` (without parameters)
3. Verify GUI window opens with title "Validator MES Receptur ..."

**If GUI fails to launch:** Verify `tkinter` is installed or use CLI procedure (Section 6).

### 5.2 Input File Selection

**Procedure:**
1. Click button **"Izberi…"** (Select)
2. Navigate to recipe file location
3. Select one or more Excel files (`.xlsx` or `.xlsm` format)
4. Verify file paths appear in "Vhodna Excel datoteka" field
5. If multiple files are selected, paths are displayed separated by semicolons

**To clear selection:** Click **"Počisti seznam"** (Clear list)

### 5.3 Output Report Configuration

**Procedure:**
1. Select report mode using radio buttons:
   - **"Ena skupna datoteka"** (Combined report): Single report file for all input files
   - **"Ločeno poročilo za vsako datoteko"** (Separate reports): Individual report per input file

2. Configure output location:
   - **For combined report:** Click **"Shrani kot…"**, select `.xlsx` or `.txt` format
   - **For separate reports:** Click **"Shrani kot…"**, select output directory

### 5.4 SOP Document Selection (Optional)

**Procedure:**
1. Click button **"Izberi SOP…"**
2. Select SOP Word document (`.docx` format)
3. If SOP loading fails:
   - System displays warning message in status window
   - Validation continues without SOP compliance checks

**SOP functionality requires `python-docx` library.**

### 5.5 Executing Validation

**Procedure:**
1. Click button **"Zaženi validacijo"** (Execute validation)
2. Monitor status window for progress messages
3. Upon completion, review status message:
   - **"OK: brez napak"**: No ERROR-level findings (warnings may be present)
   - **"Končano z napakami"**: ERROR-level findings detected; review report

### 5.6 Report Review and Access

**Accessing report folder:**
1. Click button **"Odpri mapo poročila"** (Open report folder)
2. System opens output directory in Windows Explorer

**Reviewing Excel reports:**
1. Open report file in Microsoft Excel
2. Review worksheet **"Povzetek"** for error details
3. Review worksheet **"Število napak"** for error summary by code

## 6. Procedure – CLI Operation (Command Line Interface)

### 6.1 Basic Validation Execution

**Working directory:** `validator_oop\`

**Command syntax:**
```
python main.py "<path\to\recipe.xlsx>"
```

**Default behavior:** Generates Excel report with filename `<recipe_name>_VALIDATION_REPORT.xlsx` in same directory as input file.

### 6.2 Report Format Selection

**Excel report with custom output path:**
```
python main.py "recipe.xlsx" --format excel --output "output_folder\report.xlsx"
```

**JSON output to console:**
```
python main.py "recipe.xlsx" --format json
```

**Text report:**
```
python main.py "recipe.xlsx" --format text --output "report.txt"
```

**Summary output:**
```
python main.py "recipe.xlsx" --format summary
```

### 6.3 Advanced Options

**Strict mode (WARNING → ERROR):**
```
python main.py "recipe.xlsx" --strict --format json
```

**Rule bypass (requires QA approval for critical rules):**
```
python main.py "recipe.xlsx" --bypass <rule_name_or_code> --format json
```

Example (multiple rules):
```
python main.py "recipe.xlsx" --bypass step_numbering required_columns --format json
```

**Formula loading:**
```
python main.py "recipe.xlsx" --include-formulas --format json
```

**Apply fixes (creates corrected copy):**
```
python main.py "recipe.xlsx" --apply-fixes --format summary
```

**NOTE:** Number of applied corrections may be zero if validation rules do not generate fix proposals.

### 6.4 Exit Code Interpretation

| Exit Code | Meaning | User Action |
|---|---|---|
| `0` | Validation successful (no ERROR findings) | Proceed with recipe approval process |
| `1` | Validation errors detected | Review report, correct errors, re-validate |
| `2` | Runtime error | Check log file (`MESValidator.log`), verify file accessibility, verify dependencies |

## 7. Report Interpretation and Corrective Actions

### 7.1 Excel Report Structure

**Worksheet "Povzetek" (Summary):**
- Columns: List (sheet), Vrstica (row), Stolpec (column), Napaka (error code), Opis napake (description)
- Each row represents one validation finding
- Use auto-filter to sort/filter by sheet, error code, or severity

**Worksheet "Število napak" (Error Count):**
- Columns: Koda (code), Opis (description), Število (count)
- Aggregated summary by error code
- Use for prioritization of corrective actions

### 7.2 Common Error Scenarios and Corrective Actions

| Error Code Pattern | Probable Cause | Corrective Action |
|---|---|---|
| `MISSING_COLUMN` | Missing required column | Add required column header to worksheet |
| `STEP_*` | Step numbering issues | Remove duplicates, fill gaps, ensure numbering starts at 1 |
| `CTRL_*`, `ZAKLENI_*` | Control definition issues | Verify control names, parameters, and context (data type/object type) |
| `SOP_*` | SOP non-compliance | Align "Podatki" worksheet with SOP requirements or verify correct SOP document selected |
| `KEY_FORMAT` | Invalid key characters | Remove invalid characters from "Ključ preverjanja" |
| `OBJ_MISMATCH` | Type incompatibility | Correct "Tip objekta" to match "Tip podatka" requirements |

## 8. Diagnostics and Troubleshooting

### 8.1 Log File Location

The Validator creates diagnostic log file:
- **Filename:** `MESValidator.log`
- **Location:** User HOME directory (e.g., `C:\Users\<username>\MESValidator.log`)

**Use log file for:**
- Detailed error diagnostics
- Troubleshooting runtime errors
- Debugging EXE distribution issues

### 8.2 Common Error Messages and Resolutions

| Error Message | Cause | Resolution |
|---|---|---|
| `openpyxl is required` | Missing Python library | Install: `pip install openpyxl` |
| `python-docx is required` | Missing Python library (SOP validation) | Install: `pip install python-docx` or disable SOP validation |
| `Error: tkinter is required for the GUI` | Missing GUI library | Use CLI mode or install Python distribution with tkinter |
| File not readable / corrupted | Invalid Excel file or file locked | Verify file opens in Excel; check file is not locked by another process |
| Permission denied writing report | Output path not writable | Verify write permissions on output directory; select alternative location |

## 9. Change Control and Periodic Review

### 9.1 Change Control Requirements

Changes to the Validator affecting validation logic, rules, or output formats shall be:
- Documented in formal change record
- Impact-assessed for effect on validation outcomes
- Reviewed and approved by QA
- Followed by re-execution of relevant OQ test cases

### 9.2 Periodic Review

This SOP shall be reviewed:
- At minimum annually
- Following significant system changes
- Following major updates to validation rules
- When regulatory requirements change

## 10. References

### 10.1 Related Documents

- User Requirements Specification: VAL-URS-001
- Functional Specification: VAL-FS-001
- Operational Qualification Protocol: VAL-OQ-001
- Risk Assessment: VAL-RA-001

### 10.2 Supporting Information

- Test data location: `validator_oop/samples/*`
- Reference reports: `validator_oop/samples/*_VALIDATION_REPORT.xlsx`

---

## Approval Signatures

| Role | Name | Signature | Date |
|---|---|---|---|
| **SOP Owner** | | | |
| **Reviewed by (QA)** | | | |
| **Approved by** | | | |

---

**Revision History**

| Version | Date | Author | Description of Changes |
|---|---|---|---|
| 1.0 | 2026-02-04 | | Initial release |

---

**END OF DOCUMENT**
