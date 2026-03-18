# User Requirements Specification (URS)
## MES Recipe Validator

---

## Document Control

| Field | Value |
|---|---|
| **Document Title** | User Requirements Specification (URS) |
| **System / Application** | MES Recipe Validator (validator_oop) |
| **Document ID** | VAL-URS-001 |
| **Version** | 1.0 |
| **Date** | 2026-02-04 |
| **Author** | ______________________ |
| **Reviewed by (QA)** | ______________________ |
| **Approved by (Process Owner)** | ______________________ |

---

## 1. Purpose

This document defines the User Requirements Specification (URS) for the MES Recipe Validator application. The system validates compliance and data quality in MES Excel workbooks (recipes) and generates validation reports identifying deviations from defined quality standards.

## 2. Scope

### 2.1 Included

- Validation of Excel recipe workbooks (multiple sheets) against predefined rule sets
- Graphical User Interface (GUI) and Command Line Interface (CLI)
- Report generation in Excel (`.xlsx`), text (`.txt`), and JSON (`.json`) formats
- Optional validation against SOP specifications from Word documents (`.docx`)
- Optional "apply fixes" function (creates corrected copy of input workbook)

### 2.2 Excluded

- Direct control or interface with production equipment or MES systems
- Automatic import of recipes into MES or automatic recipe approval workflows
- User management, access control, or electronic signature functionality within the application

## 3. Definitions and Abbreviations

| Term | Definition |
|---|---|
| **Validator** | Software tool for verifying data quality and structural correctness of MES Excel recipes |
| **Recipe (Receptura)** | Excel workbook containing structured process data with defined columns (e.g., Step Number, Instruction, Data Type, etc.) |
| **Rule** | Validation logic that generates errors or warnings (e.g., missing column, duplicate steps, interval control) |
| **OQ** | Operational Qualification – evidence that the system operates correctly in its intended operational environment |
| **SOP** | Standard Operating Procedure – reference document containing requirements that may be used for additional validation |
| **MES** | Manufacturing Execution System |

## 4. Intended Use

The Validator is intended for **internal use** by QA, Production, and Process personnel as a **decision support tool** for identifying errors in recipes prior to use in MES or production environments. Validation results serve as input to user review and decision-making processes. Final responsibility for recipe approval and import rests with qualified personnel following established procedures.

## 5. Assumptions and Constraints

- Input files are managed in accordance with internal document control procedures (version control, archiving, access control)
- Excel files are treated as read-only input data. The Validator shall not modify input files unless explicitly using the "apply fixes" function
- The "apply fixes" function creates a new copy of the workbook with a distinct filename. The original input file shall not be overwritten
- GUI functionality requires `tkinter` library availability
- SOP validation requires `python-docx` library availability
- Excel read/write operations require `openpyxl` library availability

## 6. User Roles

| Role ID | Role Name | Responsibilities |
|---|---|---|
| **URS-ROLE-01** | End User (QA/Production) | File selection, validation execution, report review, results interpretation, corrective action initiation |
| **URS-ROLE-02** | System Administrator / Power User | Configuration management (CLI parameters), diagnostics (log review), user support, bypass approval |

## 7. User Requirements

### 7.1 Functional Requirements

| Requirement ID | Title | Description |
|---|---|---|
| **URS-FR-01** | Excel Input File Support | The system shall support selection and loading of Excel workbooks in `.xlsx` and `.xlsm` formats (`.xls` support is optional where technically feasible) |
| **URS-FR-02** | Multiple File Processing (GUI) | The GUI shall support selection of one or more input recipe files and batch validation execution |
| **URS-FR-03** | Sheet Filtering | The system shall validate only worksheets containing required recipe columns as defined in system configuration |
| **URS-FR-04** | Validation Rules Execution | The system shall execute validation rules covering:<br>• Structural requirements (required columns, step numbering)<br>• Field-level requirements (object type, data type, key format, formulas, units)<br>• Relational requirements (key uniqueness, date/time pairs, mass ownership)<br>• Control requirements (control names, control context, interval/time parameters, zaklenipolja logic) |
| **URS-FR-05** | SOP Compliance (Optional) | The system shall support optional loading of SOP specification documents from Word format (`.docx`) and execute additional compliance validation against SOP requirements |
| **URS-FR-06** | Validation Results Display | The system shall display validation status (valid/invalid) and provide a list of errors and warnings including location (sheet, row, column) and error code |
| **URS-FR-07** | Excel Report Generation | The system shall generate validation reports in Excel format (`.xlsx`) containing minimum:<br>• Error list with locations and descriptions<br>• Error count summary by error code |
| **URS-FR-08** | Alternative Report Formats | The system shall support report export in text (`.txt`) and JSON (`.json`) formats |
| **URS-FR-09** | Output Path Configuration | Users shall have the ability to specify output report file paths via CLI parameters or GUI file selection dialogs |
| **URS-FR-10** | Strict Mode | The system shall provide a strict validation mode that treats warnings as errors |
| **URS-FR-11** | Rule Bypass Capability | The system shall support exclusion of selected validation rules by name or error code |
| **URS-FR-12** | Formula Support (Optional) | The system shall support optional validation with cell formula evaluation (e.g., formulas in "Vrednost" column) |
| **URS-FR-13** | Apply Fixes (Optional) | The system shall provide optional functionality to create a modified copy of the input workbook with proposed corrections applied where defined by validation rules |
| **URS-FR-14** | CLI Exit Codes | The CLI shall return standardized exit codes:<br>• `0` = validation successful (no ERROR-level findings)<br>• `1` = validation errors detected<br>• `2` = runtime error (file not readable, missing dependencies, etc.) |

### 7.2 Non-Functional Requirements

| Requirement ID | Title | Description |
|---|---|---|
| **URS-NFR-01** | Usability | The GUI shall enable users to execute validation without CLI knowledge, providing clear status messages and results |
| **URS-NFR-02** | OS Compatibility | The system shall operate on Windows environments (Windows 10 and Windows 11) |
| **URS-NFR-03** | Error Handling | The system shall handle invalid or corrupted input files gracefully and provide clear error messages |
| **URS-NFR-04** | Performance | Validation of typical recipe workbooks shall complete within acceptable timeframe (target: minutes, dependent on file size and complexity) |
| **URS-NFR-05** | Results Traceability | Validation reports shall contain sufficient information to enable reproducible review (error code, description, precise location) |
| **URS-NFR-06** | Data Integrity | <br>• Original input files shall not be modified by validation operations<br>• When "apply fixes" is used, output shall be clearly distinguished from input via filename and location |
| **URS-NFR-07** | Diagnostics and Logging | The system shall provide diagnostic capabilities via log files or console output, particularly for standalone executable distributions |

### 7.3 Compliance and Quality Requirements

**NOTE:** Final GxP classification is an organizational decision. This URS assumes use as a decision support tool for data review.

| Requirement ID | Title | Description |
|---|---|---|
| **URS-COM-01** | Decision Support Function | The system shall not make autonomous production decisions. Validation results shall be interpreted by qualified personnel. Final approval authority rests with designated process owners |
| **URS-COM-02** | Change Control | Changes to validation rules or algorithms shall be managed through formal change control procedures including change documentation, impact assessment, and re-testing as appropriate |
| **URS-COM-03** | Qualification Evidence | Operational Qualification shall provide documented evidence that critical functions operate correctly in the intended operational environment |

## 8. Acceptance Criteria

- All URS-FR and URS-NFR requirements shall have documented traceability to FS specifications and OQ test cases
- OQ test cases shall execute without deviations, or with deviations documented, impact-assessed, and approved by QA

## 9. Traceability

Traceability shall be maintained through:
- URS → FS mapping (documented in FS Section 4)
- URS/FS → OQ mapping (documented in OQ Section 5)

**Minimum traceability requirement:** Each URS-FR shall reference at least one FS specification element and at least one OQ test case.

## 10. References and Appendices

### 10.1 Related Documents

- Functional Specification: VAL-FS-001
- Operational Qualification Protocol: VAL-OQ-001
- Risk Assessment: VAL-RA-001
- User SOP: VAL-SOP-USE-001

### 10.2 Test Data Location

- Sample files for OQ: `validator_oop/samples/*`
- Reference report outputs: `validator_oop/samples/*_VALIDATION_REPORT.xlsx`

---

## Approval Signatures

| Role | Name | Signature | Date |
|---|---|---|---|
| **Prepared by** | | | |
| **Reviewed by (QA)** | | | |
| **Approved by (Process Owner)** | | | |

---

**END OF DOCUMENT**
