"""Static constants and regex patterns for MES validation.

This module contains all static configuration that does not change at runtime:
- Required column names
- Allowed values for fields (tip_objekta, tip_podatka, controls)
- Regex patterns for parsing keys, formulas, units, time expressions
- Data-object compatibility mappings
- Error code translations
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, FrozenSet

# ==============================================================================
# VERSION (imported from _version.py - single source of truth)
# ==============================================================================

from ._version import (
    BUILD,
    BUILD_DATE,
    MAJOR,
    MINOR,
    PATCH,
    VERSION,
    VERSION_REPORT,
    VERSION_UI,
    __version__,
    __version_full__,
)

# ==============================================================================
# BYPASS FLAGS (moved from global vars – now in ValidatorConfig)
# These are kept here as default values for reference / backward compatibility
# ==============================================================================

DEFAULT_BYPASS_ZAKLENI_REQUIRE_EMPTY_FOR_CHECKBOX = True
DEFAULT_BYPASS_ZAKLENI_REQUIRE_POGOJ_FOR_PARAM1_STEPS = True
DEFAULT_BYPASS_ZAKLENI_INVERSE_POGOJ_REQUIREMENT = False

# ==============================================================================
# REQUIRED COLUMNS (IPO structure)
# ==============================================================================

REQUIRED_COLUMNS: List[str] = [
    "št. Koraka",
    "Navodilo",
    "Tip podatka",
    "Ključ preverjanja",
    "Vrednost",
    "Labela",
    "Tip objekta",
    "Kontrola 1",
    "Kontrola 1 - par 1",
    "Kontrola 1 - par 2",
    "Kontrola 2",
    "Kontrola 2 - par 1",
    "Kontrola 2 - par 2",
    "Kontrola 3",
    "Kontrola 3 - par 1",
    "Kontrola 3 - par 2",
    "Kontrola 4",
    "Kontrola 4 - par 1",
    "Kontrola 4 - par 2",
]

# Stolpci, ki se pri validaciji ignorirajo (npr. rezerviran prazen naslovni stolpec → column_0)
VALIDATION_EXCLUDED_COLUMNS: FrozenSet[str] = frozenset({"column_0"})

# ==============================================================================
# ALLOWED VALUES
# ==============================================================================

FORMULA_REF_ALLOWED_OBJECT_TYPES: FrozenSet[str] = frozenset({
    "edit", "formula", "formula0", "formula1", "klictehtnice1",
})

ALLOWED_TIP_OBJEKTA: FrozenSet[str] = frozenset({
    "edit", "checkbox", "crta",
    "formula", "formula0", "formula1",
    "gumbdatumcas", "izberidatumcas",
    "spustniseznam", "memo",
    "klictehtnice1",
    "naslov",
})

STANDARD_TIP_PODATKA: FrozenSet[str] = frozenset({
    "kemikalija", "masa", "embalaza",
    "datumcas", "datumcaszacetek", "datumcaskonec",
    "tehtnica", "termometer", "kopel", "pH_meter", "sušilnik", "vak_sušilnik", "merilnik", "naprava",
    "zaposleni",
    "summasa", "masakonec",
    "monomerna", "monolit", "raztopina",
    "checkbox", "naslov", "crta", "memo", "formula",
    "repro", "reproodpis",
})

# Mapping: tip_podatka -> allowed tip_objekta values
DATA_OBJECT_MAPPING: Dict[str, FrozenSet[str]] = {
    "kemikalija": frozenset({"edit"}),
    "raztopina": frozenset({"edit"}),
    "zaposleni": frozenset({"edit"}),
    "monolit": frozenset({"edit"}),
    "repro": frozenset({"edit"}),
    "reproodpis": frozenset({"edit"}),
    "masa": frozenset({"edit", "klictehtnice1"}),
    "embalaza": frozenset({"edit"}),
    "monomerna": frozenset({"edit"}),
    "tehtnica": frozenset({"edit", "spustniseznam"}),
    "termometer": frozenset({"edit", "spustniseznam"}),
    "kopel": frozenset({"edit", "spustniseznam"}),
    "pH_meter": frozenset({"edit", "spustniseznam"}),
    "sušilnik": frozenset({"edit", "spustniseznam"}),
    "vak_sušilnik": frozenset({"edit", "spustniseznam"}),
    "merilnik": frozenset({"edit", "spustniseznam"}),
    "naprava": frozenset({"edit", "spustniseznam"}),
    "summasa": frozenset({"edit", "formula", "formula0", "formula1"}),
    "masakonec": frozenset({"edit"}),
    "datumcas": frozenset({"gumbdatumcas", "izberidatumcas"}),
    "datumcaszacetek": frozenset({"gumbdatumcas", "izberidatumcas"}),
    "datumcaskonec": frozenset({"gumbdatumcas", "izberidatumcas"}),
    "checkbox": frozenset({"checkbox"}),
    "naslov": frozenset({"naslov"}),
    "crta": frozenset({"crta"}),
    "memo": frozenset({"memo"}),
    "formula": frozenset({"formula", "formula0", "formula1"}),
}

# Types that require Labela = 'koda'
LABELA_KODA_TYPES: FrozenSet[str] = frozenset({
    "kemikalija", "zaposleni", "monolit", "repro", "reproodpis"
})

# Dovoljeni vrednosti Labela za Tip objekta checkbox (po normalizaciji: lowercase, collapse spaces)
LABELA_CHECKBOX_ALLOWED: FrozenSet[str] = frozenset({
    "da (kljukica)",
    "da (kljukica)/ne (prazno)",
})

# ==============================================================================
# ALLOWED CONTROLS
# ==============================================================================

ALLOWED_CONTROLS: FrozenSet[str] = frozenset({
    "kontrolapraznopolje", "kontrolaintervala", "kontrolainterval", "kontrolacasa",
    "aliobstajapogoj", "aliobstajapogoj_ali", "aliobkljukan", "aliniobkljukan",
    "kdoizpolni", "alipravavloga", "alipravavlogakoda",
    "zaklenipolja",
    "kontrolaveljavnostikemikalije", "kontrolaustreznostikemikalije",
    "kontrolamase", "kontrolarazmerjakemikalij",
    "kontrolaembalaze", "kontrolaprazneembalaze",
    "kontrolaveljavnostiopreme", "kontrolaustreznostiopreme", "kontrolaustreznostiopremeizmase",
    "kontrolaveljavnostimonolita", "kontrolaustreznostimonolita",
    "kontrolaveljavnostiraztopine", "kontrolaustreznostiraztopine",
    "kontrolaveljavnostirepro", "kontrolaustreznostirepro", "kontrolaprimernostirepro",
    "kontrolaprimernostitelesainpokrova", "prenosrepro", "prenosset",
    "kontrolarazlika", "aliisto", "kontrolaistizapis",
    "kontrolaustreznostimonomerne", "kontrolaveljavnostimonomerne",
    "kontrolaustreznostiseta", "kontrolaveljavnostiseta", "kontrolaustreznostilinije", "odpispraznemm",
})

# Normalized version (lowercase, no spaces)
ALLOWED_CONTROLS_NORMALIZED: FrozenSet[str] = frozenset({
    c.lower().replace(" ", "") for c in ALLOWED_CONTROLS
})

# ==============================================================================
# EXCEL ERROR TOKENS
# ==============================================================================

EXCEL_ERROR_TOKENS: FrozenSet[str] = frozenset({
    "#REF!", "#N/A", "#DIV/0!", "#NAME?", "#NULL!", "#NUM!", "#VALUE!"
})

# ==============================================================================
# REGEX PATTERNS
# ==============================================================================

# Key format validation
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_\-.]*$")

# Formula reference extraction ($step_number)
FORMULA_REF = re.compile(r"\$([0-9]+)")

# Numeric token extraction
NUMERIC_TOKEN_RE = re.compile(r"[+-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?")

# Control column header patterns (Kontrola N - Param 1, etc.)
CTRL_PAR1_PATTERNS = [
    re.compile(r"^kontrola\s*(?P<n>\d+)\s*(?:[-–:])?\s*par(?:am)?\s*1\s*$", re.IGNORECASE),
    re.compile(r"^p(?:ar|aram|m)\s*1\s*[,._-]?\s*(?P<n>\d+)\s*$", re.IGNORECASE),
]

CTRL_PAR2_PATTERNS = [
    re.compile(r"^kontrola\s*(?P<n>\d+)\s*(?:[-–:])?\s*par(?:am)?\s*2\s*$", re.IGNORECASE),
    re.compile(r"^p(?:ar|aram|m)\s*2\s*[,._-]?\s*(?P<n>\d+)\s*$", re.IGNORECASE),
]

# ==============================================================================
# EQUIPMENT DETECTION
# ==============================================================================

EQUIPMENT_KEYWORDS = [
    r"črpalka", r"crpalka", r"tehtnica", r"termometer",
    r"\bHPLC\b", r"pH[\s_]*meter", r"\bVK\b", r"kopel", r"vk", r"VK",
    r"pipeta", r"pipette", r"FE", r"manometer",
    r"sušilnik", r"susilnik",
    r"vak_sušilnik", r"vak_susilnik",
    r"merilnik",
    r"naprava",
    r"konduktometer",
]

EQUIPMENT_REGEX = re.compile("|".join(EQUIPMENT_KEYWORDS), flags=re.IGNORECASE)

EQUIPMENT_TIP_PODATKA: FrozenSet[str] = frozenset({
    "tehtnica", "termometer", "kopel", "pipeta", "pipette",
    "ph meter", "ph_meter", "phmeter", "fe", "manometer",
    "sušilnik", "susilnik",
    "vak_sušilnik", "vak_susilnik",
    "merilnik",
    "naprava",
    "konduktometer",
})

# ==============================================================================
# TIME PARSING PATTERNS
# ==============================================================================

_TIME_NUMBER = r"(?P<num>[0-9]+(?:[.,][0-9]+)?)"

TIME_HOUR_PATTERN = re.compile(
    rf"\b{_TIME_NUMBER}\s*(?:h|hour|hours|ura|ure|ur)\b", flags=re.IGNORECASE
)
TIME_MINUTE_PATTERN = re.compile(
    rf"\b{_TIME_NUMBER}\s*(?:min|minute|minuta|minuti|minut)\b", flags=re.IGNORECASE
)
TIME_DAY_PATTERN = re.compile(
    rf"\b{_TIME_NUMBER}\s*(?:d|dan|dni|dnevi|dneh|dnevih|day|days)\b", flags=re.IGNORECASE
)
TIME_RANGE_SEPARATOR = re.compile(r"\s*[-–—]\s*")
TIME_INEQUALITY_RE = re.compile(r"(>=|≥|>)")

# ==============================================================================
# UNIT PATTERNS
# ==============================================================================

WHITELIST_UNITS: List[str] = [
    # concentrations
    "mol/L", "mmol/L", "µmol/L", "umol/L", "ppm", "ppb",
    # mass/volume
    "µg", "ug", "mg", "g", "kg", "µL", "uL", "mL", "L", "g/L", "mg/mL",
    # temperature
    "°C", "C", "K",
    # time
    "min", "h",
    "d", "dan", "dni", "dnevi", "dneh", "dnevih", "day", "days",
    # flow, conductivity, pressure, speed
    "mL/min", "L/min", "µS/cm", "uS/cm", "mS/cm", "S/m",
    "mbar", "bar", "kPa", "Pa", "MPa", "rpm",
]

# Sorted by length (longest first) for correct regex matching
_UNIT_TOKENS = sorted(WHITELIST_UNITS, key=len, reverse=True)
_UNIT_ALT = "|".join(re.escape(u) for u in _UNIT_TOKENS)
_UNIT_BOUNDARY = rf"(?<![A-Za-zµ])(?:{_UNIT_ALT})(?![A-Za-z])"

UNIT_TOKEN_RE = re.compile(_UNIT_BOUNDARY, flags=re.IGNORECASE)

UNIT_AFTER_NUMBER_RE = re.compile(
    rf"(?P<num>[+-]?\d+(?:[.,]\d+)?)(?:\s*)(?P<unit>(?<![A-Za-zµ0-9])(?:{_UNIT_ALT})(?![A-Za-z0-9]))",
    flags=re.IGNORECASE
)

# ==============================================================================
# NAVODILO PARSING PATTERNS (range, ±, inequality, single value)
# ==============================================================================

RANGE_RE = re.compile(
    rf"(?P<a>[+-]?\d+(?:[.,]\d+)?)\s*[-–—]\s*(?P<b>[+-]?\d+(?:[.,]\d+)?)(?:\s*(?P<unit>{_UNIT_BOUNDARY}))?",
    flags=re.IGNORECASE
)

PM_RE = re.compile(
    rf"(?P<x>[+-]?\d+(?:[.,]\d+)?)\s*(?:±|\+/-|\+\s*/\s*-)\s*(?P<t>\d+(?:[.,]\d+)?)(?:\s*(?P<unit>{_UNIT_BOUNDARY}))?",
    flags=re.IGNORECASE
)

SINGLE_RE = re.compile(
    rf"\b(?P<x>[+-]?\d+(?:[.,]\d+)?)(?:\s*(?P<unit>{_UNIT_BOUNDARY}))?\b",
    flags=re.IGNORECASE
)

INEQ_RE = re.compile(
    rf"(?P<op>>=|≥|>|<=|≤|<)\s*(?P<x>[+-]?\d+(?:[.,]\d+)?)(?:\s*(?P<unit>{_UNIT_BOUNDARY}))?",
    flags=re.IGNORECASE
)

# ==============================================================================
# INVISIBLE WHITESPACE CHARACTERS (for normalization)
# ==============================================================================

INVISIBLE_WHITESPACE: tuple[str, ...] = (
    "\u00A0",  # non-breaking space
    "\u200B",  # zero-width space
    "\u200C",  # zero-width non-joiner
    "\u200D",  # zero-width joiner
    "\u2060",  # word joiner
)

# ==============================================================================
# ERROR CODE TRANSLATIONS (Slovenian)
# ==============================================================================

CODE_TRANSLATIONS: Dict[str, str] = {
    # --- Structural ---
    "MISSING_COLUMN": "Manjka obvezen stolpec",
    "STEP_NOT_INTEGER": "Številka koraka ni celo število",
    "STEP_DUPLICATE": "Podvojena številka koraka",
    "STEP_GAPS": "Manjkajo vmesni koraki",
    "STEP_TAB_NOT_FROM_ONE": "Koraki v zavihku se ne začnejo s 1",
    "STEP_MISSING": "Manjka številka koraka v vrstici",
    # --- Field: object type ---
    "OBJECT_TYPE_EMPTY": "Tip objekta ni določen",
    "OBJECT_TYPE_UNKNOWN": "Neznan tip objekta",
    "OBJECT_TYPE_MISMATCH": "Tip objekta ne ustreza tipu podatka",
    # --- Field: label ---
    "LABEL_MUST_BE_KODA": "Labela mora biti 'koda'",
    "LABEL_CHECKBOX_FORMAT": "Pri tipu objekta checkbox mora biti Labela 'DA (kljukica)' ali 'DA (kljukica)/NE (prazno)'",
    # --- Field: key ---
    "KEY_INVALID_FORMAT": "Nepravilen zapis ključa",
    "KEY_REQUIRED": "Manjka ključ preverjanja za kemikalijo/raztopino/maso/tehtnico",
    # --- Field: formula ---
    "FORMULA_SYNTAX": "Nepravilen zapis formule",
    "FORMULA_NO_REFERENCE": "Formula nima sklica na korake",
    "FORMULA_INVALID_REFERENCE": "Formula se sklicuje na neobstoječi korak",
    "FORMULA_STEP_INVALID_TYPE": "Korak, na katerega se formula sklicuje, nima dovoljenega Tip objekta ('edit', 'formula', 'formula0', 'formula1' ali 'klictehtnice1')",
    # --- Field: value ---
    "CRTA_COLUMN_NOT_EMPTY": "Pri tipu podatka crta mora biti stolpec prazen",
    "SPUSTNISEZNAM_VREDNOST_EMPTY": "Pri spustnem seznamu mora biti stolpec Vrednost zapolnjen",
    "COMMA_NOT_ALLOWED": "Vrednost vsebuje nedovoljeno vejico v številu",
    "SPACE_NOT_ALLOWED": "Vrednost vsebuje nedovoljen presledek",
    # --- Field: unit ---
    "UNIT_MISMATCH": "Enota v 'Labela' se ne ujema z 'Navodilo'",
    # --- Relational: duplicate keys ---
    "KEY_DUP_CHEM": "Podvojen ključ za kemikalijo",
    "KEY_DUP_SOL": "Podvojen ključ za raztopino",
    "KEY_DUP_MASS": "Podvojen ključ za maso",
    "KEY_DUP_MASS_SECTION": "Isti ključ mase v več razdelkih (dovoljeno samo znotraj istega razdelka)",
    "KEY_DUP_TIME_START": "Podvojen ključ za datum_čas začetka",
    "KEY_DUP_TIME_END": "Podvojen ključ za datum_čas konca",
    "KEY_DUP_TIME_PAIR": "Podvojen ključ za par datumcaszacetek/datumcaskonec",
    # --- Relational: key numbering ---
    "KEY_NUM_NOT_FROM_ONE": "Oštevilčenje ključev se ne začne z 1",
    "KEY_NUM_GAP": "Manjkajoči ključ v zaporedju",
    "KEY_NUM_DUPLICATE_BASE": "Podvojen stil ključa ('base' in 'base1')",
    # --- Relational: pairs ---
    "PAIR_CHEM_WITHOUT_MASS": "Za kemikalijo manjka ustrezna masa",
    "PAIR_SOL_WITHOUT_MASS": "Za raztopino manjka ustrezna masa",
    "PAIR_MASS_WITHOUT_OWNER": "Masa nima pripadajoče kemikalije, raztopine ali monomerne",
    "PAIR_MASS_SECTION_MISMATCH": "Ključ preverjanja za 'masa' se ne ujema z lastnikom (kemikalija/raztopina/monomerna)",
    "PAIR_TIME_WITHOUT_END": "Manjka končni čas",
    "PAIR_TIME_WITHOUT_START": "Manjka začetni čas",
    # --- Relational: scale ---
    "SCALE_VALUE_TOO_HIGH": "Nepravilna vrednost pri tehtnici (masa >= 10)",
    "SCALE_VALUE_TOO_LOW": "Nepravilna vrednost pri tehtnici (masa < 10)",
    "CONTROL_SCALE_WITHOUT_MASS": "Tehtnica nima pripadajoče mase",
    # --- Control: general ---
    "CTRL_REQUIRED_EMPTY": "Manjka kontrola za prazno polje",
    "CTRL_CHECKBOX_EMPTY": "Checkbox ne sme imeti kontrole prazno polje",
    "CTRL_EXPECTED_MISSING": "Manjka pričakovana kontrola",
    "CTRL_UNKNOWN": "Neznano ime kontrole",
    "CTRL_INVALID_CONTEXT": "Kontrola je v napačnem kontekstu",
    "EXCEL_ERROR_TOKEN": "Celica vsebuje Excelovo napako",
    # --- Control: interval ---
    "CTRL_INTERVAL_PARAMS": "Kontrola interval brez mej",
    "CTRL_INTERVAL_NOT_NUMBER": "Meja intervala ni številčna",
    "CTRL_INTERVAL_RANGE": "Maksimalna meja je manjša ali enaka minimalni",
    "CTRL_INTERVAL_INSTRUCTION": "Parametra intervala ne sledita mejam iz navodila",
    "CTRL_INTERVAL_P1_BOUND": "Param1 ne sledi spodnji meji iz navodila",
    "CTRL_INTERVAL_P2_BOUND": "Param2 ne sledi zgornji meji iz navodila",
    "CTRL_INTERVAL_PM_P1": "Param1 ne sledi spodnji meji iz ±",
    "CTRL_INTERVAL_PM_P2": "Param2 ne sledi zgornji meji iz ±",
    "CTRL_INTERVAL_TARGET_P1": "Param1 ne sledi spodnji meji iz navodila",
    "CTRL_INTERVAL_TARGET_P1_STRICT": "Param1 ne sledi strogi spodnji meji iz navodila",
    "CTRL_INTERVAL_TARGET_P2_STRICT": "Param2 ne sledi strogi zgornji meji iz navodila",
    "CTRL_INTERVAL_TARGET_P2": "Param2 ne sledi zgornji meji iz navodila",
    "CTRL_INTERVAL_TARGET_P1_MAX": "Param1 je nad dovoljeno spodnjo mejo",
    "CTRL_INTERVAL_TARGET_P2_MIN": "Param2 je pod zahtevano zgornjo mejo",
    "CTRL_INTERVAL_REQUIRED": "Manjka kontrola 'kontrolaInterval'",
    # --- Control: time (casa) ---
    "CTRL_CASA_MIN": "Kontrola časa brez minimalne vrednosti",
    "CTRL_CASA_MIN_NOT_NUMBER": "Minimalna vrednost časa ni številčna",
    "CTRL_CASA_RANGE": "Maksimalni čas je manjši od minimalnega",
    "CTRL_CASA_MAX_NOT_NUMBER": "Maksimalna vrednost časa ni številčna",
    "CTRL_CASA_P1_INSTRUCTION": "Param1 časa ne sledi navodilu (sekunde)",
    "CTRL_CASA_P2_INSTRUCTION": "Param2 časa ne sledi navodilu (sekunde)",
    "CTRL_CASA_REQUIRED": "Manjka kontrola 'kontrolaCasa' pri tipu podatka 'datumcasKonec'",
    # --- Control: specific required ---
    "CTRL_ALIOBKLJUKAN_REQUIRED": "Manjka kontrola 'aliObkljukan' pri tipu podatka 'checkbox'",
    "CTRL_ALIPRAVAVLOGAKODA_REQUIRED": "Manjka kontrola 'aliPravavlogaKoda' pri tipu podatka 'zaposleni'",
    "CTRL_MONOLIT_VALIDITY_REQUIRED": "Manjka kontrola 'kontrolaVeljavnostiMonolita' pri tipu podatka 'monolit'",
    "CTRL_MONOLIT_SUITABILITY_REQUIRED": "Manjka kontrola 'kontrolaUstreznostiMonolita' pri tipu podatka 'monolit'",
    # --- Control: role / condition ---
    "CTRL_ROLE_PARAM": "Manjka parameter vloge",
    "CTRL_CONDITION_P1": "Pogoj brez referenčnega ključa (Param1)",
    "CTRL_CONDITION_P1_FORMAT": "Pogoj – neveljavni ključi v Param1",
    "CTRL_CONDITION_KEY": "Pogoj vsebuje neobstoječe ključe",
    "CTRL_CONDITION_P2": "Pogoj brez vrednosti 0/1 (Param2)",
    "CTRL_CONDITION_VALUE": "Param2 pri pogoju mora biti 0 ali 1",
    "CTRL_CONDITION_VALUE_REQUIRED": "Vrednost polja je zahtevana zaradi pogoja (aliObstajaPogoj)",
    # --- Control: lock (zakleni) ---
    "CTRL_LOCK_ALIOB_NOT_ALLOWED": "Pri 'zaklenipolja' ni dovoljena kontrola 'aliObkljukan'",
    "CTRL_CHECKBOX_DANE_ALIOB_NOT_ALLOWED": "Pri checkboxu z 'DA (kljukica)/NE (prazno)' ni dovoljena kontrola 'aliObkljukan'",
    "CTRL_LOCK_EMPTY_NOT_ALLOWED": "Pri 'zaklenipolja' na checkbox ne sme biti kontrola 'kontrolaPraznoPolje'",
    "CTRL_LOCK_EMPTY_REQUIRED": "Pri 'zaklenipolja' in checkbox tipu objekta mora biti kontrola 'kontrolaPraznoPolje'",
    "ALIOB_PARAM_CHECK": "aliObkljukan zahteva Param1 'DA' ali 'NE'",
    "CHECKBOX_STATE": "Stanje checkboxa se ne ujema s pričakovanim",
    "LOCK_P1_WITHOUT_CONDITION": "Korak iz Param1 nima kontrole 'aliObstajaPogoj'",
    "LOCK_P1_STEP_MISSING": "Korak iz Param1 ne obstaja",
    "LOCK_P1_MISSING_FOR_CONDITION": "Korak z 'aliObstajaPogoj' ni naveden v Param1 pri 'zaklenipolja'",
    "LOCK_CONDITION_P1P2": "Korak iz Param1 nima zahtevane kombinacije Param1/Param2 za 'aliObstajaPogoj'",
    "LOCK_P1_EXTRA_STEPS": "Pri zaklenipolja v Param1 so odvečni koraki",
    "LOCK_P1_EXCEL_ERROR": "Param1 pri 'zaklenipolja' vsebuje Excel napako",
    "LOCK_P1_FORMAT": "Param1 pri 'zaklenipolja' ni v pravilnem formatu",
    "LOCK_KEY_DUPLICATE": "Kontrola 'zaklenipolja' ima podvojen ključ preverjanja",
    "CTRL_ALIOB_NOT_ALLOWED": "Pri 'aliObstajaPogoj' na checkboxu ni dovoljena kontrola 'aliObkljukan'",
    # --- Control: solution (raztopina) ---
    "SOLUTION_KEY_MISSING": "Kontrola raztopine brez ključa v vrstici",
    "SOLUTION_P1_MISSING": "Kontrola raztopine brez baze ključa (Param1)",
    "SOLUTION_P1_BASE": "Param1 ne ustreza bazi ključa",
    "SOLUTION_P2_BASE": "Param2 ne ustreza bazi ključa",
    # --- Control: equipment (oprema) ---
    "EQUIPMENT_MONOMERIC": "Oprema 'monomerna' brez definicije mešanice",
    "EQUIPMENT_NO_LINK": "Oprema ni povezana z nobenim materialom/meritvijo",
    # --- Control: mass ---
    "CTRL_MASS_WITHOUT_VALUE": "Masa nima vrednosti",
    # --- Section ---
    "SECTION_STEP_COUNT_MISMATCH": "Razdelek ima različno število korakov med listi",
    "SECTION_INSTRUCTION_MISMATCH": "Razdelek ima različno besedilo navodil med listi",
    # --- SOP ---
    "SOP_IPO_MISMATCH": "Ključ preverjanja se ne ujema z IPO šifro iz SOP-a",
    "SOP_IPO_NOT_ALLOWED": "Ključ preverjanja ni dovoljen v SOP-u (ni v seznamu IPO šifer)",
    "SOP_IPO_MISSING": "Manjka zahtevana IPO šifra iz SOP-a v recepturi",
    "SOP_TYPE_NOT_ALLOWED": "Vrsta raztopine ni dovoljena v SOP-u",
    "SOP_VOLUME_TOO_LOW": "Volumen je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_VOLUME_TOO_HIGH": "Volumen presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_FLOW_TOO_LOW": "Pretok je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_FLOW_TOO_HIGH": "Pretok presega maksimalno dovoljeno vrednost iz SOP-a",
    "DATA_FLOW_MIN_MISMATCH": "Min. pretok se ne ujema z obsegom Pretok spiranje (pričakuje se spodnja meja − 1)",
    "DATA_FLOW_MAX_MISMATCH": "Max. pretok se ne ujema z obsegom Pretok spiranje (pričakuje se zgornja meja + 1)",
    "SOP_SAMPLE_NOT_ALLOWED": "Vzorec ni dovoljen v SOP-u",
    "SOP_TSST_TOO_LOW": "tSST je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_TSST_TOO_HIGH": "tSST presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_VR_TOO_LOW": "Vr je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_VR_TOO_HIGH": "Vr presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_N_TOO_LOW": "N > je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_PRESSURE_TOO_LOW": "Tlak je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_PRESSURE_TOO_HIGH": "Tlak presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_D_TOO_LOW": "Distribucijski koeficient D je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_D_TOO_HIGH": "Distribucijski koeficient D presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_MEDIUM_MISMATCH": "Medij za določeno fazo se ne ujema z medijem iz SOP-a",
    "SOP_REQUIREMENT_MISSING": "Manjka zahteva iz SOP-a",
    "SOP_LOAD_ERROR": "Napaka pri nalaganju SOP dokumenta",
    # --- Catalog (šifranti raztopin/kemikalij) ---
    "CATALOG_CODE_MISMATCH": "Šifra raztopine/kemikalije ni v šifrantu",
}


def translate_code(code: str) -> str:
    """Translate an error code to Slovenian description.

    Args:
        code: Koda napake (npr. 'MANJKA_STOLPEC').

    Returns:
        Slovenian translation or the original code if not found.
    """
    return CODE_TRANSLATIONS.get(code, code)

