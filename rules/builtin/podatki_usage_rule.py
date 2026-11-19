"""Podatki column usage rule.

Javi stolpce iz zavihka ``Podatki``, ki se ne uporabljajo v nobeni formuli
(npr. ``=INDEX(Podatki!$A:$BY,MATCH($D$2,Podatki!$A:$A,0),60)``) v nobenem
drugem zavihku in jih ne potrebuje formula nobenega tako uporabljenega
stolpca (npr. ``Min`` z ``=AP3*0.95-0.1``, ko je ``Min`` v INDEX/MATCH,
``Pretok 1`` pa ne).

Pravilo potrebuje besedilo formul (``parsed_formulas``). Če formule niso
naložene (``include_formulas=False``), se tiho preskoči, ker bi sicer vsi
stolpci izpadli kot neuporabljeni.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from validator_oop.core.error import Severity
from validator_oop.rules import RuleContext, WorkbookRule, register
from validator_oop.rules.builtin.catalog_code_rule import _is_podatki_label_row
from validator_oop.utils import coerce_str

_PODATKI_NAME = "podatki"

# Funkcije, pri katerih je prvi argument razpon, številka stolpca pa tretji argument.
_LOOKUP_FUNCTIONS_RE = re.compile(r"\b(INDEX|VLOOKUP)\s*\(", re.IGNORECASE)

# Sklic na zavihek Podatki: Podatki!$A:$BY, 'Podatki'!A2, Podatki!$1:$1 ...
_PODATKI_REF_RE = re.compile(
    r"(?:'Podatki'|(?<![\w.])Podatki)\s*!\s*"
    r"(?P<ref>\$?[A-Z]{1,3}\$?\d*(?::\$?[A-Z]{1,3}\$?\d*)?|\$?\d+:\$?\d+)",
    re.IGNORECASE,
)
_FIRST_ARG_REF_RE = re.compile(r"^\s*'?Podatki'?\s*!\s*(?P<ref>[^\s]+)\s*$", re.IGNORECASE)
# Razpon v formuli na zavihku Podatki: $A:$BY, Podatki!$A:$BY, 'Podatki'!$AP:$AR.
# Razpon z drugim zavihkom (npr. Other!$A:$B) se ne ujema.
_LOCAL_RANGE_ARG_RE = re.compile(
    r"^\s*(?:'?Podatki'?\s*!\s*)?"
    r"(?P<ref>\$?[A-Z]{1,3}(?:\$?\d+)?(?::\$?[A-Z]{1,3}(?:\$?\d+)?)?)\s*$",
    re.IGNORECASE,
)
# Sklic na celico ali razpon v formuli istega zavihka. Ime lista, ki ni Podatki, se preskoči.
_LOCAL_CELL_REF_RE = re.compile(
    r"(?<![A-Za-z0-9_$.])"
    r"(?:(?:'(?P<qsheet>[^']+)'|(?P<usheet>[A-Za-z_][\w.]*))\s*!\s*)?"
    r"\$?(?P<c1>[A-Z]{1,3})(?:\$?(?P<r1>\d+))?"
    r"(?:\s*:\s*\$?(?P<c2>[A-Z]{1,3})(?:\$?(?P<r2>\d+))?)?"
    r"(?![A-Za-z0-9_(])",
    re.IGNORECASE,
)
_QUOTED_STRING_RE = re.compile(r'"(?:[^"]|"")*"')
_REF_PARTS_RE = re.compile(
    r"^\$?(?P<c1>[A-Z]{1,3})?\$?(?P<r1>\d+)?(?::\$?(?P<c2>[A-Z]{1,3})?\$?(?P<r2>\d+)?)?$",
    re.IGNORECASE,
)
_LITERAL_INT_RE = re.compile(r"^\s*(\d+)\s*$")

# Razpon, širši od tega, štejemo kot "vsi stolpci".
_MAX_SPAN = 2000


def _letters_to_number(letters: str) -> int:
    result = 0
    for char in letters.upper():
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result


def number_to_letters(number: int) -> str:
    """1 -> A, 26 -> Z, 27 -> AA ..."""
    result = ""
    while number > 0:
        number, rem = divmod(number - 1, 26)
        result = chr(ord("A") + rem) + result
    return result


@dataclass
class PodatkiUsage:
    """Zbirka uporabljenih stolpcev zavihka Podatki (1-based)."""

    columns: set[int] = field(default_factory=set)
    all_columns: bool = False
    formula_count: int = 0

    @property
    def found(self) -> bool:
        return self.all_columns or bool(self.columns)

    def is_used(self, column: int) -> bool:
        return self.all_columns or column in self.columns


def _ref_columns(ref: str) -> tuple[int, int] | None:
    """Stolpci, ki jih zajame sklic. None = vsi stolpci (npr. cela vrstica)."""
    match = _REF_PARTS_RE.match(ref.strip())
    if not match:
        return None
    c1, c2 = match.group("c1"), match.group("c2")
    if not c1:
        return None
    low = _letters_to_number(c1)
    high = _letters_to_number(c2) if c2 else low
    if ":" in ref and not c2:
        return None
    if high < low:
        low, high = high, low
    if high - low > _MAX_SPAN:
        return None
    return low, high


def _call_args(text: str, start: int) -> list[tuple[int, int]] | None:
    """Pozicije argumentov klica; ``start`` je indeks takoj za odpiralnim oklepajem."""
    depth = 0
    quote: str | None = None
    args: list[tuple[int, int]] = []
    arg_start = start
    for i in range(start, len(text)):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                args.append((arg_start, i))
                return args
            depth -= 1
        elif ch in ",;" and depth == 0:
            args.append((arg_start, i))
            arg_start = i + 1
    return None


def _span_from_groups(c1: str | None, c2: str | None, r1: str | None) -> tuple[int, int] | None:
    """Stolpci iz skupin sklica. Brez vrstice in brez drugega stolpca ni sklic."""
    if not c1 or (r1 is None and not c2):
        return None
    low = _letters_to_number(c1)
    high = _letters_to_number(c2) if c2 else low
    if high < low:
        low, high = high, low
    if high - low > _MAX_SPAN:
        return None
    return low, high


def _blank_spans(text: str, spans: Sequence[tuple[int, int]]) -> str:
    if not spans:
        return text
    chars = list(text)
    for start, end in spans:
        for index in range(max(start, 0), min(end, len(chars))):
            chars[index] = " "
    return "".join(chars)


def referenced_columns_in_podatki_formula(formula: object) -> tuple[set[int], bool]:
    """Stolpci zavihka Podatki, na katere kaže formula v celici tega zavihka.

    Sklici na druge zavihke (``=Other!AP3``) se ne štejejo. Pri ``INDEX``/``VLOOKUP``
    z dobesedno številko stolpca se šteje samo ta stolpec, ne cel razpon.
    Vrne ``(stolpci, vsi_stolpci)``.
    """
    if not isinstance(formula, str) or not formula.lstrip().startswith("="):
        return set(), False

    text = _QUOTED_STRING_RE.sub(lambda match: " " * len(match.group(0)), formula)
    columns: set[int] = set()
    all_columns = False
    masked: list[tuple[int, int]] = []

    for call in _LOOKUP_FUNCTIONS_RE.finditer(text):
        args = _call_args(text, call.end())
        if not args:
            continue
        is_index = call.group(1).upper() == "INDEX"
        range_arg = args[0] if is_index else (args[1] if len(args) > 1 else None)
        col_arg = args[2] if len(args) > 2 else None
        if range_arg is None or col_arg is None:
            continue
        ref_match = _LOCAL_RANGE_ARG_RE.match(text[range_arg[0]:range_arg[1]])
        if not ref_match:
            continue
        literal = _LITERAL_INT_RE.match(text[col_arg[0]:col_arg[1]])
        span = _ref_columns(ref_match.group("ref"))
        if not literal or span is None:
            continue
        columns.add(span[0] + int(literal.group(1)) - 1)
        masked.append(range_arg)

    scan = _blank_spans(text, masked)
    for ref in _LOCAL_CELL_REF_RE.finditer(scan):
        sheet = ref.group("qsheet") or ref.group("usheet")
        if sheet and sheet.casefold().strip() != _PODATKI_NAME:
            continue
        span = _span_from_groups(ref.group("c1"), ref.group("c2"), ref.group("r1"))
        if span is None:
            if ref.group("c1") and ref.group("c2"):
                all_columns = True
            continue
        columns.update(range(span[0], span[1] + 1))

    return columns, all_columns


def expand_usage_with_podatki_formulas(
    usage: PodatkiUsage,
    formula_rows: Sequence[Mapping[str, Any]] | None,
    headers: Sequence[str],
) -> None:
    """Doda stolpce, ki jih formule uporabljenih stolpcev preberejo (tudi veriga)."""
    if usage.all_columns or not formula_rows:
        return

    header_list = [str(header) for header in headers]
    deps: dict[int, set[int]] = {}
    reads_everything: set[int] = set()
    for row in formula_rows:
        if not isinstance(row, Mapping):
            continue
        for column_num, header in enumerate(header_list, start=1):
            referenced, all_columns = referenced_columns_in_podatki_formula(row.get(header))
            if all_columns:
                reads_everything.add(column_num)
            if referenced:
                deps.setdefault(column_num, set()).update(referenced)

    pending = list(usage.columns)
    seen = set(usage.columns)
    while pending:
        column_num = pending.pop()
        if column_num in reads_everything:
            usage.all_columns = True
            return
        for dependency in deps.get(column_num, ()):
            if dependency in seen:
                continue
            seen.add(dependency)
            usage.columns.add(dependency)
            pending.append(dependency)


def collect_podatki_columns(formula: str, usage: PodatkiUsage) -> bool:
    """Doda stolpce zavihka Podatki, uporabljene v formuli. Vrne True, če formula sega v Podatki."""
    if not formula or not formula.lstrip().startswith("="):
        return False
    if "podatki" not in formula.casefold():
        return False

    masked: list[tuple[int, int]] = []
    touched = False

    # INDEX(Podatki!$A:$BY, ..., N) / VLOOKUP(x, Podatki!$A:$BY, N, ...): uporabljen je samo stolpec N.
    for call in _LOOKUP_FUNCTIONS_RE.finditer(formula):
        args = _call_args(formula, call.end())
        if not args:
            continue
        is_index = call.group(1).upper() == "INDEX"
        range_arg = args[0] if is_index else (args[1] if len(args) > 1 else None)
        col_arg = (args[2] if len(args) > 2 else None)
        if range_arg is None or col_arg is None:
            continue
        ref_match = _FIRST_ARG_REF_RE.match(formula[range_arg[0]:range_arg[1]])
        if not ref_match:
            continue
        touched = True
        literal = _LITERAL_INT_RE.match(formula[col_arg[0]:col_arg[1]])
        span = _ref_columns(ref_match.group("ref"))
        if not literal or span is None:
            # Dinamičen stolpec (npr. MATCH po naslovu) - razpon štejemo konservativno kot uporabljen.
            continue
        usage.columns.add(span[0] + int(literal.group(1)) - 1)
        masked.append(range_arg)

    # Vsi ostali sklici na Podatki (MATCH(..., Podatki!$A:$A, 0), =Podatki!E5, ...).
    for ref_match in _PODATKI_REF_RE.finditer(formula):
        touched = True
        pos = ref_match.start()
        if any(start <= pos < end for start, end in masked):
            continue
        span = _ref_columns(ref_match.group("ref"))
        if span is None:
            usage.all_columns = True
        else:
            usage.columns.update(range(span[0], span[1] + 1))

    return touched


def collect_workbook_usage(
    parsed_formulas: Mapping[str, Sequence[Mapping[str, Any]]],
    podatki_sheet: str,
) -> PodatkiUsage:
    """Preglej formule vseh zavihkov (razen Podatki) in zberi uporabljene stolpce."""
    usage = PodatkiUsage()
    skip = podatki_sheet.casefold().strip()
    for sheet_name, rows in parsed_formulas.items():
        if str(sheet_name).casefold().strip() == skip:
            continue
        for row in rows or ():
            for value in row.values():
                if isinstance(value, str) and collect_podatki_columns(value, usage):
                    usage.formula_count += 1
    return usage


def _find_sheet(names: Iterable[str], wanted: str) -> str | None:
    for name in names:
        if str(name).casefold().strip() == wanted:
            return name
    return None


def _is_meaningful_label(text: str) -> bool:
    return bool(text) and not text.isdigit() and not text.startswith("column_")


@register
class PodatkiColumnUsageRule(WorkbookRule):
    """Javi zapolnjene stolpce zavihka Podatki, ki jih ne uporablja nobena formula."""

    name = "podatki_column_usage_rule"
    description = (
        "Zapolnjen stolpec zavihka Podatki mora biti uporabljen v vsaj eni formuli drugega zavihka "
        "(INDEX/MATCH, VLOOKUP, neposreden sklic) ali v formuli takega uporabljenega stolpca "
        "(prazen neuporabljen stolpec je v redu)."
    )
    code = "PODATKI_COLUMN_UNUSED"
    priority = 170
    severity = Severity.ERROR

    def evaluate_workbook(
        self,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        extra: dict[str, Any] = {}
        if context.shared is not None:
            extra.update(getattr(context.shared, "extra", None) or {})
        extra.update(context.extra or {})

        parsed_formulas = extra.get("parsed_formulas")
        if not parsed_formulas:
            self._logger.debug("Formule niso naložene - preverjanje stolpcev Podatki preskočeno")
            return []

        all_data = extra.get("all_workbook_data") or workbook_data
        all_headers = extra.get("all_workbook_headers") or {}

        podatki_name = _find_sheet(all_data.keys(), _PODATKI_NAME)
        if not podatki_name:
            return []

        usage = collect_workbook_usage(parsed_formulas, podatki_name)
        if not usage.found:
            # Nobena formula ne sega v Podatki - ni kaj primerjati.
            return []

        rows = list(all_data[podatki_name] or ())
        headers = [str(h) for h in (all_headers.get(podatki_name) or ())]
        if not headers and rows:
            headers = [str(key) for key in rows[0].keys()]

        # Formule znotraj Podatki (npr. Min = Pretok*0.95-0.1) štejejo, če je
        # stolpec z formulo sam uporabljen v recepturi. Veriga se sledi do konca.
        formula_sheet = _find_sheet(parsed_formulas.keys(), _PODATKI_NAME)
        expand_usage_with_podatki_formulas(
            usage,
            parsed_formulas.get(formula_sheet) if formula_sheet else None,
            headers,
        )

        sheet_ctx = context.with_sheet(podatki_name)
        errors = []
        for column_num, header in enumerate(headers, start=1):
            if usage.is_used(column_num):
                continue

            labels: list[str] = []
            if _is_meaningful_label(header.strip()):
                labels.append(header.strip())
            if rows:
                first = coerce_str(rows[0].get(header, "")).strip()
                if _is_meaningful_label(first) and first not in labels:
                    labels.append(first)
            first_key = headers[0]
            has_data = any(
                coerce_str(row.get(header, "")).strip()
                and not _is_podatki_label_row(row, first_key, header)
                for row in rows
            )
            if not has_data:
                continue  # prazen stolpec (samo naslov/oznaka) - ni težava

            letters = number_to_letters(column_num)
            label_text = f", '{' / '.join(labels)}'" if labels else ""
            errors.append(
                self.build_error(
                    f"Stolpec {letters} (št. {column_num}{label_text}) v zavihku '{podatki_name}' "
                    "ni uporabljen v nobeni INDEX/MATCH formuli in nanj ne kaže formula "
                    "nobenega uporabljenega stolpca.",
                    context=sheet_ctx,
                    column=letters,
                    payload={"column_number": column_num, "labels": labels},
                )
            )
        return errors
