# Risk Assessment
## MES Recipe Validator

---

## Document Control

| Field | Value |
|---|---|
| **Document Title** | Risk Assessment |
| **System / Application** | MES Recipe Validator (validator_oop) |
| **Document ID** | VAL-RA-001 |
| **Version** | 1.0 |
| **Date** | 2026-02-04 |
| **Author** | ______________________ |
| **Reviewed by (QA)** | ______________________ |
| **Approved by** | ______________________ |

---

## 1. Purpose

The purpose of this Risk Assessment is to systematically identify, evaluate, and document risks associated with the use of the MES Recipe Validator, and to define appropriate risk controls to reduce risks to acceptable levels.

## 2. Scope and System Context

### 2.1 System Description

The MES Recipe Validator is an offline software tool for validating Excel recipe workbooks and (optionally) verifying compliance with SOP specifications.

### 2.2 Risk Assessment Boundaries

**Included in assessment:**
- Validator software operation (GUI and CLI modes)
- Data integrity risks (input files, validation logic, output reports)
- User interaction risks (incorrect operation, misinterpretation of results)
- SOP compliance validation (optional functionality)

**Excluded from assessment:**
- MES system operation and production equipment control (Validator has no direct interface)
- Electronic signature systems (not implemented in Validator)
- Automated recipe approval workflows (Validator is decision support only)

### 2.3 Intended Use Statement

The Validator is a **decision support tool**. Validation results provide input to qualified personnel for review and decision-making. Final responsibility for recipe approval and import into MES rests with designated process owners following established quality procedures.

## 3. Risk Assessment Methodology

### 3.1 Qualitative Risk Scoring

This risk assessment employs a qualitative risk evaluation method using the following scales:

**S (Severity):** Impact of failure mode on product quality, patient safety, or data integrity
- 1 = Negligible impact
- 2 = Minor impact (limited scope, easily corrected)
- 3 = Moderate impact (potential quality impact, no patient safety risk)
- 4 = Serious impact (quality impact, potential patient safety concern)
- 5 = Critical impact (direct patient safety risk or significant quality impact)

**P (Probability):** Likelihood of failure mode occurring
- 1 = Rare (< 0.1% of operations)
- 2 = Unlikely (0.1% - 1% of operations)
- 3 = Possible (1% - 10% of operations)
- 4 = Likely (10% - 50% of operations)
- 5 = Frequent (> 50% of operations)

**D (Detectability):** Ability to detect failure before impact occurs
- 1 = Certain detection (automatic detection with clear alert)
- 2 = High detection probability (detection likely during normal review)
- 3 = Moderate detection probability (may be detected during review)
- 4 = Low detection probability (detection requires specific checking)
- 5 = Unlikely detection (failure difficult to detect before impact)

**RPN (Risk Priority Number):** \( \text{RPN} = S \times P \times D \)

### 3.2 Risk Acceptability Criteria

The following risk acceptability thresholds are applied (subject to organizational policy approval):

| RPN Range | Risk Level | Acceptance Criteria |
|---|---|---|
| 1 – 20 | Low | Acceptable without additional controls |
| 21 – 40 | Medium | Acceptable with documented justification and defined risk controls |
| 41 – 125 | High | Requires additional risk controls or system/process modification |

### 3.3 Residual Risk Evaluation

After implementation of risk controls, residual risk shall be re-evaluated and documented in Section 6.

## 4. GAMP Classification (Informational)

**GAMP 5 Category:** The Validator is a custom/configurable tool with embedded validation logic. Based on GAMP 5 guidance, this system is classified as **Category 4** (configured software with custom extensions).

**Rationale:** The system employs standard libraries (`openpyxl`, `python-docx`, `tkinter`) with custom validation rule implementations specific to MES recipe structure.

**Validation Approach:** Proportionate validation approach consisting of URS, FS, Risk Assessment, and OQ, with formal change control for validation logic modifications.

## 5. Risk Identification and Control Measures

### 5.1 Risk Register

| Risk ID | Hazard / Failure Mode | Cause | Potential Impact | S | P | D | RPN |
|---|---|---|---|:---:|:---:|:---:|:---:|
| **RA-01** | False negative: Validator fails to detect error in recipe | Defect in validation rule logic; unexpected Excel format variation; worksheet filtering excludes relevant data | Invalid recipe proceeds to production use; potential impact on batch quality, compliance, or patient safety | 5 | 2 | 4 | 40 |
| **RA-02** | False positive: Validator reports error in valid recipe | Validation rule excessively strict; format variation not anticipated; rule logic error | Unnecessary corrections required; production delays; resource waste | 2 | 3 | 2 | 12 |
| **RA-03** | Incorrect Excel report generation | Defect in `ReportWriter` logic; incompatible `openpyxl` version; file write permissions issue | User misinterprets results; loss of validation evidence; incorrect corrective actions | 3 | 2 | 3 | 18 |
| **RA-04** | Runtime failure during Excel reading | Corrupted input file; missing software dependencies; file locked by another process | Validation cannot execute; production delays; manual verification required | 2 | 3 | 1 | 6 |
| **RA-05** | Incorrect formula interpretation | Formula loading disabled (`include_formulas=False`); formula parser does not support all Excel formula types | Rules dependent on formulas produce incorrect results; potential false negative or false positive | 4 | 2 | 4 | 32 |
| **RA-06** | SOP Word document incorrectly parsed | Non-standard SOP document structure; OCR artifacts; `python-docx` limitations; encoding issues | Incorrect SOP compliance errors; valid recipes flagged incorrectly; or non-compliant recipes not detected | 4 | 2 | 4 | 32 |
| **RA-07** | Inappropriate use of rule bypass (`--bypass`) | User excludes critical validation rule without QA approval; lack of bypass documentation | Critical errors not detected; invalid recipe proceeds to use | 5 | 2 | 4 | 40 |
| **RA-08** | Apply fixes modifies incorrect cells | Incorrect `target_cell` mapping; incorrect `proposed_value` calculation in rule | Corrupted recipe copy; potential use of incorrect recipe if manual verification skipped | 4 | 1 | 3 | 12 |
| **RA-09** | Insufficient result traceability | No centralized logging; user identity not captured; reports not archived in controlled location | Difficulty establishing who validated what and when; audit trail gaps | 3 | 2 | 4 | 24 |
| **RA-10** | Character encoding issues in console output | Non-UTF-8 Windows console; special characters in data | Console output unreadable; user confusion; however Excel/text reports remain readable | 1 | 3 | 1 | 3 |

### 5.2 Risk Control Measures

**RA-01: False Negative (RPN 40 – Medium Risk)**

**Preventive Controls:**
- Formal change control for validation rule modifications (URS-COM-02)
- Operational Qualification with representative test data (VAL-OQ-001)
- Periodic review of validation rules against current recipe formats

**Detective Controls:**
- Human review of all recipes is mandatory before MES import (procedural control)
- Validation reports include detailed error locations for verification
- Independent QA review for critical recipes

**Residual Risk:** Medium (dependent on procedural controls)

---

**RA-02: False Positive (RPN 12 – Low Risk)**

**Preventive Controls:**
- Rule bypass capability for approved exceptions (`--bypass` parameter with QA approval)
- Formal process for rule tuning based on user feedback

**Detective Controls:**
- Deviation management process for systematic review of false positives
- Strict mode comparison testing in OQ (OQ-005)

**Residual Risk:** Low

---

**RA-03: Incorrect Excel Report (RPN 18 – Low Risk)**

**Preventive Controls:**
- OQ test case for Excel report structure verification (OQ-003)
- Multiple report format options (Excel, JSON, text) for redundancy

**Detective Controls:**
- Visual inspection of report structure during validation review
- Log file provides backup evidence of validation results

**Residual Risk:** Low

---

**RA-04: Runtime Failure (RPN 6 – Low Risk)**

**Preventive Controls:**
- Clear error messages with corrective action guidance
- Dependency check and installation instructions in SOP
- Fallback between GUI and CLI modes

**Detective Controls:**
- Immediate user notification of runtime errors
- Log file captures detailed error information

**Residual Risk:** Low

---

**RA-05: Formula Interpretation Error (RPN 32 – Medium Risk)**

**Preventive Controls:**
- GUI default configuration enables formula loading (`include_formulas=True`)
- OQ test case with formula validation (OQ-006)
- Documented limitation for unsupported formula types (FS Section 7)

**Detective Controls:**
- Manual verification of formula-dependent validation results for critical recipes
- SOP requires user review of validation logic applicability

**Residual Risk:** Medium (mitigated by manual verification for critical cases)

---

**RA-06: SOP Parsing Error (RPN 32 – Medium Risk)**

**Preventive Controls:**
- SOP validation is optional functionality
- SOP loading process is logged with detailed extraction information
- OQ test case with reference SOP document (OQ-008)
- QA review of SOP mapping logic

**Detective Controls:**
- SOP loading failure results in clear warning; validation continues
- Deviation management process for SOP-related validation discrepancies

**Residual Risk:** Medium (mitigated by optional nature and manual review)

---

**RA-07: Inappropriate Rule Bypass (RPN 40 – Medium Risk)**

**Preventive Controls:**
- SOP restricts bypass usage to System Administrator / Power User role (VAL-SOP-USE-001)
- Bypass usage shall be documented and justified
- QA approval required for bypass of critical rules

**Detective Controls:**
- OQ includes baseline vs. bypass comparison (OQ-004)
- Validation reports document configuration used (including bypassed rules)

**Residual Risk:** Medium (dependent on procedural controls)

---

**RA-08: Apply Fixes Error (RPN 12 – Low Risk)**

**Preventive Controls:**
- Apply fixes operates only on workbook copy (never modifies original)
- Clear filename distinction (`_AUTOFIX.xlsx`)
- OQ test case verifies original file integrity (OQ-007)

**Detective Controls:**
- SOP requires mandatory manual verification of autofix output before use
- Number of applied corrections is logged and displayed

**Residual Risk:** Low

---

**RA-09: Insufficient Traceability (RPN 24 – Medium Risk)**

**Preventive Controls:**
- SOP requires storage of validation reports in controlled location
- Log file `MESValidator.log` provides execution history

**Detective Controls:**
- Procedural control: SOP defines report archiving requirements
- Periodic audit of validation report availability and completeness

**Residual Risk:** Medium (mitigated by procedural controls)

---

**RA-10: Encoding Issues (RPN 3 – Low Risk)**

**Preventive Controls:**
- Excel and text reports are primary evidence artifacts (not console output)
- CLI uses ASCII-safe status messages where applicable

**Detective Controls:**
- Immediate visibility of garbled output (user can switch to report file review)

**Residual Risk:** Low

---

## 6. Residual Risk Summary and Conclusion

### 6.1 Summary of Residual Risks

| Risk Level | Count | Risk IDs |
|---|:---:|---|
| Low | 5 | RA-02, RA-03, RA-04, RA-08, RA-10 |
| Medium | 5 | RA-01, RA-05, RA-06, RA-07, RA-09 |
| High | 0 | None |

### 6.2 Risk Acceptability Conclusion

With the implementation of defined risk controls (OQ qualification, procedural controls via SOP, change control, mandatory human review), residual risks are evaluated as **acceptable** for the intended use as a decision support tool.

**Critical control dependencies:**
- Validator is used as decision support only (not for autonomous decisions)
- Qualified personnel review all validation results
- Formal change control is maintained for validation rule modifications
- OQ re-testing is performed following significant changes

### 6.3 Recommendations

For medium-risk items (RA-01, RA-05, RA-06, RA-07, RA-09), the following enhanced controls are recommended:
- QA review of validation results for critical recipes
- Documentation of rule bypass justifications
- Periodic review of validation rule performance (false positive/negative rates)
- Retention of validation reports as quality records

---

## Approval Signatures

| Role | Name | Signature | Date |
|---|---|---|---|
| **Prepared by** | | | |
| **Reviewed by (QA)** | | | |
| **Approved by** | | | |

---

**END OF DOCUMENT**
