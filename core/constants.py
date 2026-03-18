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
]

# ==============================================================================
# ALLOWED VALUES
# ==============================================================================

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
    "tehtnica", "termometer", "kopel", "pH_meter", "sušilnik", "vak_sušilnik", "merilnik",
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
    "kontrolaprimernostitelesainpokrova", "prenosrepro",
    "kontrolarazlika", "aliisto", "kontrolaistizapis",
    "kontrolaustreznostimonomerne", "kontrolaveljavnostimonomerne", "odpispraznemm",
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
    r"merilnik"
]

EQUIPMENT_REGEX = re.compile("|".join(EQUIPMENT_KEYWORDS), flags=re.IGNORECASE)

EQUIPMENT_TIP_PODATKA: FrozenSet[str] = frozenset({
    "tehtnica", "termometer", "kopel", "pipeta", "pipette",
    "ph meter", "ph_meter", "phmeter", "fe", "manometer",
    "sušilnik", "susilnik",
    "vak_sušilnik", "vak_susilnik",
    "merilnik"
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
    "MANJKA_STOLPEC": "Manjka obvezen stolpec",
    "KORAK_NI_CELO": "Številka koraka ni celo število",
    "KORAK_PODVOJEN": "Podvojena številka koraka",
    "KORAK_PRESLEDKI": "Manjkajo vmesni koraki",
    "KORAKI_ZAVIH_NE_1": "Koraki v zavihku se ne začnejo s 1",
    "KORAK_MANJKA": "Manjka številka koraka v vrstici",
    "TIP_OBJEKTA_PRAZEN": "Tip objekta ni določen",
    "TIP_OBJEKTA_NEZNAN": "Neznan tip objekta",
    "TIP_NE_USREZA": "Tip objekta ne ustreza tipu podatka",
    "LABELA_MORA_KODA": "Labela mora biti 'koda'",
    "LABELA_CHECKBOX_OBLIKA": "Pri tipu objekta checkbox mora biti Labela 'DA (kljukica)' ali 'DA (kljukica)/NE (prazno)'",
    "KLJUC_NAPAKEN_FORMAT": "Nepravilen zapis ključa",
    "KLJUC_ZAHTEVAN": "Manjka ključ preverjanja za kemikalijo/raztopino/maso/tehtnico",
    "FORMULA_SINTAKSA": "Nepravilen zapis formule",
    "FORMULA_BREZ_SKLICA": "Formula nima sklica na korake",
    "FORMULA_NAPACEN_SKLICE": "Formula se sklicuje na neobstoječi korak",
    "VEJICA_NEDOVOLJENA": "Vrednost vsebuje nedovoljeno vejico v številu",
    "PAR_KEM_BREZ_MASE": "Za kemikalijo manjka ustrezna masa",
    "PAR_RAZT_BREZ_MASE": "Za raztopino manjka ustrezna masa",
    "PAR_MASA_BREZ_LASTNIKA": "Masa nima pripadajoče kemikalije ali raztopine",
    "PAR_MASA_NAPACEN_RAZD": "Ključ preverjanja za 'masa' se ne ujema z raztopino/kemikalijo",
    "PAR_CAS_BREZ_KONCA": "Manjka končni čas",
    "PAR_CAS_BREZ_ZACETKA": "Manjka začetni čas",
    "KLJUC_NUM_NE_1": "Oštevilčenje ključev se ne začne z 1",
    "KLJUC_NUM_PRESLEDEK": "Manjkajoči ključ v zaporedju",
    "KLJUC_NUM_PODVOJEN_BASE": "Podvojen stil ključa ('base' in 'base1')",
    "KLJUC_PODVOJEN_KEM": "Podvojen ključ za kemikalijo",
    "KLJUC_PODVOJEN_RAZT": "Podvojen ključ za raztopino",
    "KLJUC_PODVOJEN_MASA": "Podvojen ključ za maso",
    "KLJUC_PODVOJEN_MASA_RAZD": "Isti ključ mase v več razdelkih (dovoljeno samo znotraj istega razdelka)",
    "KLJUC_PODVOJEN_CAS_ZAC": "Podvojen ključ za datum_čas začetka",
    "KLJUC_PODVOJEN_CAS_KONEC": "Podvojen ključ za datum_čas konca",
    "KLJUC_PODVOJEN_CAS_PAR": "Podvojen ključ za par datumcaszacetek/datumcaskonec",
    "TEHTNICA_VREDNOST_PREVISOKA": "Nepravilna vrednost pri tehtnici (masa >= 10)",
    "TEHTNICA_VREDNOST_PRENIZKA": "Nepravilna vrednost pri tehtnici (masa < 10)",
    "KONTROLA_ZAHTEVANO_PRAZNO": "Manjka kontrola za prazno polje",
    "KONTROLA_CHECKBOX_PRAZNO": "Checkbox ne sme imeti kontrole prazno polje",
    "KONTROLA_PRICAKOVANO_MANJKA": "Manjka pričakovana kontrola",
    "KONTROLA_NEZNAN": "Neznano ime kontrole",
    "KONTROLA_NAPACEN_KONTEKST": "Kontrola je v napačnem kontekstu",
    "KONTROLA_INTERVAL_PARAMETRI": "Kontrola interval brez mej",
    "KONTROLA_INTERVAL_NI_STEVILO": "Meja intervala ni številčna",
    "KONTROLA_INTERVAL_VRSTA": "Maksimalna meja je manjša ali enaka minimalni",
    "KONTROLA_INTERVAL_NAVODILO": "Parametra intervala ne sledita mejam iz navodila",
    "ENOTA_NE_USREZA": "Enota v 'Labela' se ne ujema z 'Navodilo'",
    "KONTROLA_CAS_MIN": "Kontrola časa brez minimalne vrednosti",
    "KONTROLA_CAS_MIN_NI_STEVILO": "Minimalna vrednost časa ni številčna",
    "KONTROLA_CAS_VRSTA": "Maksimalni čas je manjši od minimalnega",
    "KONTROLA_CAS_MAX_NI_STEVILO": "Maksimalna vrednost časa ni številčna",
    "KONTROLA_CAS_P1_NAVODILO": "Param1 časa ne sledi navodilu (sekunde)",
    "KONTROLA_CAS_P2_NAVODILO": "Param2 časa ne sledi navodilu (sekunde)",
    "KONTROLA_CAS_ZAHTEVANA": "Manjka kontrola 'kontrolaCasa' pri tipu podatka 'datumcasKonec'",
    "KONTROLA_ALIOBKLJUKAN_ZAHTEVANA": "Manjka kontrola 'aliObkljukan' pri tipu podatka 'checkbox'",
    "KONTROLA_ALIPRAVAVLOGAKODA_ZAHTEVANA": "Manjka kontrola 'aliPravavlogaKoda' pri tipu podatka 'zaposleni'",
    "KONTROLA_MONOLIT_VELJAVNOST_ZAHTEVANA": "Manjka kontrola 'kontrolaVeljavnostiMonolita' pri tipu podatka 'monolit'",
    "KONTROLA_MONOLIT_USTREZNOST_ZAHTEVANA": "Manjka kontrola 'kontrolaUstreznostiMonolita' pri tipu podatka 'monolit'",
    "KONTROLA_VLOGA_PARAM": "Manjka parameter vloge",
    "KONTROLA_POGOJ_P1": "Pogoj brez referenčnega ključa (Param1)",
    "KONTROLA_POGOJ_P1_FORMAT": "Pogoj – neveljavni ključi v Param1",
    "KONTROLA_POGOJ_KLJUC": "Pogoj vsebuje neobstoječe ključe",
    "KONTROLA_POGOJ_P2": "Pogoj brez vrednosti 0/1 (Param2)",
    "KONTROLA_POGOJ_VREDNOST": "Param2 pri pogoju mora biti 0 ali 1",
    "KONTROLA_ZAKLENI_BREZ_ALIOB": "Pri 'zaklenipolja' ni dovoljena kontrola 'aliObkljukan'",
    "KONTROLA_CHECKBOX_DA_NE_BREZ_ALIOB": "Pri checkboxu z 'DA (kljukica)/NE (prazno)' ni dovoljena kontrola 'aliObkljukan'",
    "KONTROLA_ZAKLENI_BREZ_PRAZNO": "Pri 'zaklenipolja' na checkbox ne sme biti kontrola 'kontrolaPraznoPolje'",
    "KONTROLA_ZAKLENI_ZAHTEVA_PRAZNO": "Pri 'zaklenipolja' in checkbox tipu objekta mora biti kontrola 'kontrolaPraznoPolje'",
    "ALIOB_PARAM_DA_NE": "aliObkljukan zahteva Param1 'DA' ali 'NE'",
    "CHECKBOX_STANJE": "Stanje checkboxa se ne ujema s pričakovanim",
    "KONTROLA_POGOJ_VREDNOST_ZAHTEVANA": "Vrednost polja je zahtevana zaradi pogoja (aliObstajaPogoj)",
    "RAZTOPINA_KLJUC_MANJKA": "Kontrola raztopine brez ključa v vrstici",
    "RAZTOPINA_P1_MANJKA": "Kontrola raztopine brez baze ključa (Param1)",
    "RAZTOPINA_P1_BAZA": "Param1 ne ustreza bazi ključa",
    "RAZTOPINA_P2_BAZA": "Param2 ne ustreza bazi ključa",
    "OPREMA_MONOMERNA": "Oprema 'monomerna' brez definicije mešanice",
    "OPREMA_BREZ_POVEZAVE": "Oprema ni povezana z nobenim materialom/meritvijo",
    "KONTROLA_INTERVAL_P1_MEJA": "Param1 ne sledi spodnji meji iz navodila",
    "KONTROLA_INTERVAL_P2_MEJA": "Param2 ne sledi zgornji meji iz navodila",
    "KONTROLA_INTERVAL_PM_P1": "Param1 ne sledi spodnji meji iz ±",
    "KONTROLA_INTERVAL_PM_P2": "Param2 ne sledi zgornji meji iz ±",
    "KONTROLA_INTERVAL_CILJ_P1": "Param1 ne sledi spodnji meji iz navodila",
    "KONTROLA_INTERVAL_CILJ_P1_STRICT": "Param1 ne sledi strogi spodnji meji iz navodila",
    "KONTROLA_INTERVAL_CILJ_P2_STRICT": "Param2 ne sledi strogi zgornji meji iz navodila",
    "KONTROLA_INTERVAL_CILJ_P2": "Param2 ne sledi zgornji meji iz navodila",
    "KONTROLA_INTERVAL_CILJ_P1_MAX": "Param1 je nad dovoljeno spodnjo mejo",
    "KONTROLA_INTERVAL_CILJ_P2_MIN": "Param2 je pod zahtevano zgornjo mejo",
    "KONTROLA_INTERVAL_ZAHTEVANA": "Manjka kontrola 'kontrolaInterval'",
    "RAZD_KORAKI_NE_USREZAJO": "Razdelek ima različno število korakov med listi",
    "RAZD_NAVODILO_NE_USREZA": "Razdelek ima različno besedilo navodil med listi",
    "ZAKLENI_P1_BREZ_POGOJA": "Korak iz Param1 nima kontrole 'aliObstajaPogoj'",
    "ZAKLENI_P1_KORAK_MANJKA": "Korak iz Param1 ne obstaja",
    "ZAKLENI_P1_MANJKA_ZA_POGOJ": "Korak z 'aliObstajaPogoj' ni naveden v Param1 pri 'zaklenipolja'",
    "ZAKLENI_POGOJ_P1P2": "Korak iz Param1 nima zahtevane kombinacije Param1/Param2 za 'aliObstajaPogoj'",
    "ZAKLENI_P1_ODVECNI_KORAKI": "Pri zaklenipolja v Param1 so odvečni koraki",
    "ZAKLENI_PAR1_EXCEL_NAPAKA": "Param1 pri 'zaklenipolja' vsebuje Excel napako",
    "ZAKLENI_PAR1_FORMAT": "Param1 pri 'zaklenipolja' ni v pravilnem formatu",
    "ZAKLENI_KLJUC_PODVOJEN": "Kontrola 'zaklenipolja' ima podvojen ključ preverjanja",
    "KONTROLA_ALIOB_NE_DOVOLJENA": "Pri 'aliObstajaPogoj' na checkboxu ni dovoljena kontrola 'aliObkljukan'",
    "KONTROLA_TEHTNICA_BREZ_MASE": "Tehtnica nima pripadajoče mase",
    "FORMULA_KORAK_EDIT_LABELA": "Korak, na katerega se formula sklicuje, nima dovoljenega Tip objekta ('edit', 'formula', 'formula0' ali 'formula1')",
    "SOP_IPO_NE_USREZA": "Ključ preverjanja se ne ujema z IPO šifro iz SOP-a",
    "SOP_IPO_NEDOVOLJEN": "Ključ preverjanja ni dovoljen v SOP-u (ni v seznamu IPO šifer)",
    "SOP_IPO_MANJKA": "Manjka zahtevana IPO šifra iz SOP-a v recepturi",
    "SOP_VRSTA_NEDOVOLJENA": "Vrsta raztopine ni dovoljena v SOP-u",
    "SOP_VOLUMEN_PRENIZEK": "Volumen je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_VOLUMEN_PREVISOK": "Volumen presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_PRETOK_PRENIZEK": "Pretok je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_PRETOK_PREVISOK": "Pretok presega maksimalno dovoljeno vrednost iz SOP-a",
    "PODATKI_PRETOK_MIN_NE_USREZA": "Min. pretok se ne ujema z obsegom Pretok spiranje (pričakuje se spodnja meja − 1)",
    "PODATKI_PRETOK_MAX_NE_USREZA": "Max. pretok se ne ujema z obsegom Pretok spiranje (pričakuje se zgornja meja + 1)",
    "SOP_VZOREC_NEDOVOLJEN": "Vzorec ni dovoljen v SOP-u",
    "SOP_TSST_PRENIZEK": "tSST je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_TSST_PREVISOK": "tSST presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_VR_PRENIZEK": "Vr je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_VR_PREVISOK": "Vr presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_N_PRENIZEK": "N > je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_TLAK_PRENIZEK": "Tlak je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_TLAK_PREVISOK": "Tlak presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_D_PRENIZEK": "Distribucijski koeficient D je pod minimalno zahtevano vrednostjo iz SOP-a",
    "SOP_D_PREVISOK": "Distribucijski koeficient D presega maksimalno dovoljeno vrednost iz SOP-a",
    "SOP_MEDIJ_NE_USREZA": "Medij za določeno fazo se ne ujema z medijem iz SOP-a",
    "SOP_ZAHTEVA_MANJKA": "Manjka zahteva iz SOP-a",
    "SOP_NAPAKA_NALAGANJA": "Napaka pri nalaganju SOP dokumenta",
}


def translate_code(code: str) -> str:
    """Translate an error code to Slovenian description.

    Args:
        code: Koda napake (npr. 'MANJKA_STOLPEC').

    Returns:
        Slovenian translation or the original code if not found.
    """
    return CODE_TRANSLATIONS.get(code, code)

