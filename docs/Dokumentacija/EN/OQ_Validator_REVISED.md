# Operational Qualification (OQ) Protocol
## MES Recipe Validator

---

## Document Control

| Field | Value |
|---|---|
| **Document Title** | Operational Qualification (OQ) Protocol |
| **System / Application** | MES Recipe Validator (validator_oop) |
| **Document ID** | VAL-OQ-001 |
| **Version** | 1.0 |
| **Date** | 2026-02-04 |
| **Author** | ______________________ |
| **Executed by** | ______________________ |
| **Reviewed by (QA)** | ______________________ |
| **Approved by** | ______________________ |

---

## 1. Purpose

The purpose of this Operational Qualification is to provide documented evidence that the Validator system operates correctly in its intended operational environment and that critical functions (loading, validation, reporting, configuration options) produce expected results.

## 2. Scope

This OQ protocol covers the following functional areas:

- CLI validation execution and exit code verification
- Report generation in multiple formats (Excel, JSON, text)
- Rule bypass and strict mode functionality
- SOP compliance validation with Word documents (optional)
- Apply fixes functionality (optional)
- GUI application launch and basic operation (optional)

## 3. Responsibilities

| Role | Responsibility |
|---|---|
| **OQ Executor** | Execute test cases, collect evidence (console outputs, generated files), document results |
| **QA Reviewer** | Review test results, assess deviations, approve/reject OQ outcome |
| **Process Owner** | Approve OQ completion and system release for operational use |

## 4. Prerequisites and Test Environment

### 4.1 Test Environment Specification

**Operating System:**
- Windows 10 or Windows 11

**Software Environment:**
- Python 3.12 (or equivalent version as specified in deployment documentation)

**Required Dependencies:**
- `openpyxl` (mandatory for Excel operations)

**Optional Dependencies:**
- `python-docx` (required only for SOP validation tests)
- `tkinter` (required only for GUI tests; typically included in standard Python distributions)

### 4.2 Test Data

**Test Data Location:** `validator_oop/samples/`

**Primary Test Files:**
- `receptura_brez_napak.xlsx` (valid recipe without errors)
- `receptura_z_napakami.xlsx` (recipe with known errors)

**Reference Outputs:**
- `receptura_brez_napak_report.json` (expected output for valid recipe)
- `receptura_z_napakami_report.json` (expected output for invalid recipe)

### 4.3 Test Output Directory

**Recommendation:** Create a dedicated output directory `oq_output\` to prevent overwriting sample reference files.

**Execution Note:**
- If working directory is `validator_oop\`, use: `python main.py ...`
- If working directory is parent of `validator_oop\`, use: `python -m validator_oop ...`

All test cases below assume execution from within `validator_oop\` directory.

## 5. URS → OQ Traceability Matrix

| URS Requirement | OQ Test Case(s) |
|---|---|
| URS-FR-01, URS-FR-03, URS-FR-04, URS-FR-06, URS-FR-14 | OQ-001, OQ-002 |
| URS-FR-07, URS-FR-08, URS-FR-09 | OQ-001, OQ-002, OQ-003 |
| URS-FR-10, URS-FR-11 | OQ-004, OQ-005 |
| URS-FR-12 | OQ-006 |
| URS-FR-13 | OQ-007 |
| URS-FR-05 | OQ-008 |
| URS-FR-02 | OQ-009 |
| URS-NFR-07 | Evidence from all test cases (log files, console outputs) |

## 6. Test Cases

### Test Case OQ-001: CLI Validation – Valid Recipe (JSON Format)

**Objective:** Verify correct file loading and validation for a recipe without errors.

**URS Traceability:** URS-FR-01, URS-FR-03, URS-FR-04, URS-FR-06, URS-FR-08, URS-FR-14

**Input File:** `samples\receptura_brez_napak.xlsx`

**Test Steps:**

1. Execute command:
   ```
   python main.py "samples\receptura_brez_napak.xlsx" --format json
   ```
2. Capture complete console output
3. Record exit code

**Expected Results:**

- JSON output contains: `"is_valid": true`
- Error counts: `"counts": {"error": 0, "warning": 0, "info": 0}`
- Exit code: `0`

**Evidence Requirements:**
- Console output (text file or screenshot)
- Recorded exit code

**Test Result:** ☐ PASS  ☐ FAIL

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

### Test Case OQ-002: CLI Validation – Invalid Recipe (JSON Format)

**Objective:** Verify error detection and correct error code/location reporting.

**URS Traceability:** URS-FR-01, URS-FR-03, URS-FR-04, URS-FR-06, URS-FR-08, URS-FR-14

**Input File:** `samples\receptura_z_napakami.xlsx`

**Test Steps:**

1. Execute command:
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format json
   ```
2. Capture complete console output
3. Record exit code
4. Compare output structure with reference file `samples\receptura_z_napakami_report.json`

**Expected Results (based on reference file):**

- JSON output contains: `"is_valid": false`
- Total error count: Minimum 4 errors with `severity: "error"`
- Required error codes present (minimum one occurrence each):
  - `TIP_OBJEKTA_UNKNOWN`
  - `CTRL_UNKNOWN`
  - `ZAKLENI_PAR1_FORMAT`
  - `STEP_DUPLICATE`
- Exit code: `1`

**Evidence Requirements:**
- Console output
- Exit code verification
- (Optional) JSON output saved to file for detailed comparison

**Test Result:** ☐ PASS  ☐ FAIL

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

### Test Case OQ-003: Excel Report Generation

**Objective:** Verify Excel report generation with required worksheets and structure.

**URS Traceability:** URS-FR-07, URS-FR-09

**Input File:** `samples\receptura_z_napakami.xlsx`

**Test Steps:**

1. Create output directory: `oq_output\`
2. Execute command:
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format excel --output "oq_output\OQ003_report.xlsx"
   ```
3. Open generated file `oq_output\OQ003_report.xlsx` in Microsoft Excel
4. Verify worksheet structure and content

**Expected Results:**

- File `oq_output\OQ003_report.xlsx` is created
- Worksheet "Povzetek" contains columns: List, Vrstica, Stolpec, Napaka, Opis napake
- Worksheet "Število napak" contains columns: Koda, Opis, Število
- Worksheet "Povzetek" contains minimum 4 error records (consistent with OQ-002)
- Auto-filter is enabled on both worksheets

**Evidence Requirements:**
- Copy of generated Excel file
- (Optional) Screenshot of opened report showing worksheet structure

**Test Result:** ☐ PASS  ☐ FAIL

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

### Test Case OQ-004: Rule Bypass Functionality

**Objective:** Verify that `--bypass` parameter excludes specified rules from execution.

**URS Traceability:** URS-FR-11

**Input File:** `samples\receptura_z_napakami.xlsx`

**Test Steps:**

1. Execute baseline validation (no bypass):
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format json > oq_output\OQ004_baseline.json
   ```
2. Execute validation with rule bypass:
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format json --bypass step_numbering > oq_output\OQ004_bypass.json
   ```
3. Compare error codes in both outputs

**Expected Results:**

- Baseline output contains error code `STEP_DUPLICATE`
- Bypass output does NOT contain error code `STEP_DUPLICATE`
- Other error codes remain present in bypass output: `CTRL_UNKNOWN`, `TIP_OBJEKTA_UNKNOWN`, `ZAKLENI_PAR1_FORMAT`
- Exit code for both executions: `1`

**Evidence Requirements:**
- Both JSON outputs saved to files
- Comparison summary documenting presence/absence of `STEP_DUPLICATE`

**Test Result:** ☐ PASS  ☐ FAIL

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

### Test Case OQ-005: Strict Mode (WARNING to ERROR Conversion)

**Objective:** Verify that strict mode converts WARNING-level findings to ERROR-level.

**URS Traceability:** URS-FR-10

**Prerequisite:** Identify or prepare an Excel file that generates at least one WARNING (e.g., error code `KEY_NUM_DUPLICATE_ONE` or `CTRL_EXPECTED_MISSING`). If sample data does not contain warnings, this test case shall be executed during routine use with appropriate test data.

**Input File:** `<file_with_warnings.xlsx>` (to be specified by executor)

**Test Steps:**

1. Execute normal validation:
   ```
   python main.py "<file_with_warnings.xlsx>" --format json > oq_output\OQ005_normal.json
   ```
2. Execute strict validation:
   ```
   python main.py "<file_with_warnings.xlsx>" --format json --strict > oq_output\OQ005_strict.json
   ```
3. Compare `severity` and `counts` fields in both outputs

**Expected Results:**

- Normal mode output contains findings with `"severity": "warning"`
- Strict mode output converts same findings to `"severity": "error"`
- `counts.error` increases in strict mode output
- `counts.warning` decreases to 0 in strict mode output

**Evidence Requirements:**
- Both JSON outputs
- Comparison table showing severity conversion

**Test Result:** ☐ PASS  ☐ FAIL  ☐ DEFERRED (pending test data)

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

### Test Case OQ-006: Formula Loading and Validation

**Objective:** Verify that system can load cell formulas and use them in validation where applicable.

**URS Traceability:** URS-FR-12

**Input File:** Excel recipe containing formulas in relevant fields (e.g., `INDEX/MATCH` formulas in "masa" cells). Sample files in `samples\` directory contain formula references.

**Test Steps:**

1. Execute validation with formula loading:
   ```
   python main.py "<recipe_with_formulas.xlsx>" --format json --include-formulas
   ```
2. Verify execution completes without runtime errors
3. Review log file for formula parsing messages

**Expected Results:**

- Validation completes successfully (no runtime exceptions)
- Exit code: `0` or `1` (depending on validation outcome)
- Log file contains formula loading messages (if `--verbose` is used)
- Rules dependent on formulas (e.g., `TehtnicaVrednostFromFormulaRule`) execute correctly

**Evidence Requirements:**
- Console output or log file excerpt
- Documentation of formula-dependent validation results

**Test Result:** ☐ PASS  ☐ FAIL

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

### Test Case OQ-007: Apply Fixes (Workbook Copy Creation)

**Objective:** Verify that "apply fixes" creates a corrected copy without modifying the original file.

**URS Traceability:** URS-FR-13, URS-NFR-06

**Input File:** `samples\receptura_z_napakami.xlsx`

**Test Steps:**

1. Record MD5 hash or file timestamp of input file (baseline)
2. Execute validation with apply fixes:
   ```
   python main.py "samples\receptura_z_napakami.xlsx" --format summary --apply-fixes
   ```
3. Verify output file creation
4. Verify original file unchanged (compare MD5 hash or timestamp)

**Expected Results:**

- Output file created with naming convention `receptura_z_napakami_AUTOFIX.xlsx`
- Console output reports number of applied corrections (may be 0 if no fixes are proposed)
- Original file `receptura_z_napakami.xlsx` remains unchanged
- Exit code: `0` or `1` (based on validation result)

**Evidence Requirements:**
- Console output showing correction count
- Screenshot or file listing showing both original and `_AUTOFIX.xlsx` files
- Verification that original file timestamp/hash is unchanged

**Test Result:** ☐ PASS  ☐ FAIL

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

### Test Case OQ-008: SOP Compliance Validation (Optional)

**Objective:** Verify SOP compliance validation including "Podatki" worksheet parsing.

**URS Traceability:** URS-FR-05

**Prerequisites:**
- `python-docx` library installed
- SOP Word document (`.docx`) available

**Test Mode:** GUI recommended

**Test Steps:**

1. Launch GUI:
   ```
   python main.py
   ```
2. Select input recipe file via "Izberi…" button
3. Select SOP document via "Izberi SOP…" button
4. Click "Zaženi validacijo"
5. Review status window for SOP loading and validation messages

**Expected Results:**

**If SOP loads successfully:**
- Status window displays: "SOP dokument uspešno naložen"
- Status window shows: Number of IPO codes, requirements loaded from SOP
- If non-compliance detected: Error codes beginning with `SOP_` appear in report (e.g., `SOP_IPO_MISMATCH`)

**If SOP loading fails:**
- Status window displays clear warning message
- Validation continues without SOP compliance checks
- No `SOP_*` error codes in output

**Evidence Requirements:**
- Screenshot of status window showing SOP loading messages
- Generated validation report (if SOP errors are present)
- Console log excerpt

**Test Result:** ☐ PASS  ☐ FAIL  ☐ NOT EXECUTED (SOP not available)

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

### Test Case OQ-009: GUI Application Launch (Smoke Test)

**Objective:** Verify GUI application launches and basic controls are functional.

**URS Traceability:** URS-FR-02, URS-NFR-01

**Test Steps:**

1. Launch GUI without parameters:
   ```
   python main.py
   ```
2. Verify window opens with title "Validator MES Receptur ..."
3. Verify presence of UI controls:
   - "Izberi…" button (input file selection)
   - "Shrani kot…" button (output file selection)
   - "Zaženi validacijo" button (execute validation)
   - Status text area
4. Test basic interaction:
   - Click "Izberi…" → file dialog opens
   - Click "Shrani kot…" → file save dialog opens

**Expected Results:**

- GUI window opens without exceptions
- All specified UI controls are visible and responsive
- File selection dialogs function correctly
- Application can be closed without errors

**Evidence Requirements:**
- Screenshot of GUI window showing all controls
- Documentation of successful dialog interactions

**Test Result:** ☐ PASS  ☐ FAIL  ☐ NOT EXECUTED (tkinter not available)

**Executed by:** ______________________ **Date:** ____________

**Deviations:** _________________________________________________________________

---

## 7. Deviation Management

For each test case deviation, document the following:

| Field | Description |
|---|---|
| **Test Case ID** | OQ-XXX |
| **Deviation Description** | Detailed description of observed vs. expected behavior |
| **Impact Assessment** | Impact on URS requirements (Critical / Major / Minor) |
| **Root Cause** | Analysis of deviation cause |
| **Corrective Action** | CAPA reference or description of corrective action |
| **Re-test Required** | Yes / No |

Use attached Deviation Log Form (if applicable) or document in this section.

---

## 8. OQ Summary and Conclusion

### 8.1 Test Execution Summary

| Metric | Value |
|---|---|
| Total test cases | 9 |
| Test cases executed | _____ |
| Test cases passed | _____ |
| Test cases failed | _____ |
| Test cases not executed | _____ |
| Deviations identified | _____ |
| Critical deviations | _____ |

### 8.2 OQ Outcome

**Overall Result:** ☐ PASS  ☐ PASS WITH DEVIATIONS  ☐ FAIL

**Justification:**

_____________________________________________________________________________

_____________________________________________________________________________

**Additional Comments:**

_____________________________________________________________________________

_____________________________________________________________________________

---

## Approval Signatures

| Role | Name | Signature | Date |
|---|---|---|---|
| **Executed by** | | | |
| **Reviewed by (QA)** | | | |
| **Approved by** | | | |

---

**END OF DOCUMENT**
