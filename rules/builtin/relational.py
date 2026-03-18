"""Relational validation rules (cross-row/cross-key)."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, Sequence

from validator_oop.core.error import Severity
from validator_oop.rules import RuleContext, SheetRule, register
from validator_oop.utils import (
    base_key_no_trailing_number,
    extract_unit_token,
    is_water_key,
    split_key_number,
)


@register
class DuplicateKeyRule(SheetRule):
    """Detect duplicate keys for kemikalija, raztopina, and masa."""

    name = "duplicate_key_rule"
    description = "Ključi morajo biti unikatni v zavihku/razdelku."

    DATA_TYPES = {
        "kemikalija": "KEY_DUP_KEM",
        "raztopina": "KEY_DUP_RAZT",
    }

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        errors = []
        for tip, code in self.DATA_TYPES.items():
            keys = shared.get_keys_for_type(tip)
            for key, row_numbers in keys.items():
                grouped = self._group_by_tab(row_numbers, shared)
                for tab, tab_rows in grouped.items():
                    if len(tab_rows) <= 1:
                        continue
                    tab_suffix = f" v zavihku '{tab}'" if tab else ""
                    errors.append(
                        self.build_error(
                            f"Podvojen ključ '{key}' za tip '{tip}'{tab_suffix}.",
                            context=context,
                            code=code,
                            payload={"rows": tab_rows},
                        )
                    )

        errors.extend(self._check_mass_duplicates(shared, context))
        return errors

    def _group_by_tab(self, rows: Sequence[int], shared) -> dict[str, list[int]]:
        grouped: dict[str, list[int]] = defaultdict(list)
        for row in rows:
            tab = shared.tab_by_row.get(row, "") if shared else ""
            grouped[tab].append(row)
        return grouped

    def _check_mass_duplicates(self, shared, context: RuleContext) -> list:
        keys = shared.get_keys_for_type("masa")
        if not keys:
            return []

        errors = []
        section_by_row = shared.section_by_row
        tab_by_row = shared.tab_by_row

        # Enak ključ (natančno) pri tipu masa ne sme nastopati v več razdelkih – samo znotraj istega razdelka je dovoljeno
        for key, row_numbers in keys.items():
            if len(row_numbers) <= 1:
                continue
            tab_to_sections: dict[str, set[int]] = defaultdict(set)
            tab_to_rows: dict[str, list[int]] = defaultdict(list)
            for row in row_numbers:
                tab = tab_by_row.get(row, "")
                section = section_by_row.get(row, 0)
                tab_to_sections[tab].add(section)
                tab_to_rows[tab].append(row)
            for tab, sections in tab_to_sections.items():
                if len(sections) > 1:
                    tab_suffix = f" v zavihku '{tab}'" if tab else ""
                    errors.append(
                        self.build_error(
                            f"Isti ključ mase '{key}' nastopa v več razdelkih{tab_suffix}.",
                            context=context,
                            code="KLJUC_PODVOJEN_MASA_RAZD",
                            payload={"rows": tab_to_rows[tab]},
                        )
                    )

        kem = shared.get_keys_for_type("kemikalija")
        raz = shared.get_keys_for_type("raztopina")

        # Združimo mase po bazi ključa (brez številke na koncu)
        from validator_oop.utils import base_key_no_trailing_number
        
        masa_by_base: dict[str, list[tuple[str, int]]] = defaultdict(list)  # base -> [(full_key, row), ...]
        for key, row_numbers in keys.items():
            base = base_key_no_trailing_number(key)
            for row in row_numbers:
                masa_by_base[base].append((key, row))

        for base, key_row_pairs in masa_by_base.items():
            # Voda (dH2O, H2O) nima vrstice kemikalija/raztopina – več mas z isto bazo je dovoljeno
            if is_water_key(base):
                continue
            # Združimo po zavihkih
            grouped_tab = defaultdict(list)
            for key, row in key_row_pairs:
                tab = tab_by_row.get(row, "")
                grouped_tab[tab].append((key, row))

            for tab, tab_pairs in grouped_tab.items():
                if len(tab_pairs) <= 1:
                    continue
                
                # Razdeli vrstice z maso po razdelkih
                grouped_section = defaultdict(list)
                for key, row in tab_pairs:
                    section = section_by_row.get(row, 0)
                    grouped_section[section].append((key, row))

                # Preverimo vsak razdelek posebej
                for section, mass_pairs_in_sec in grouped_section.items():
                    # Če je v razdelku samo ena masa, ni podvojitve
                    if len(mass_pairs_in_sec) <= 1:
                        continue

                    # Preveri, ali ima ta razdelek (v tem zavihku) vsaj eno 'kemikalija' ali 'raztopina' z isto bazo ključa
                    # (lastnik je lahko v istem razdelku ali v kateremkoli prejšnjem – kemikalija lahko več razdelkov pred maso)
                    has_owner = False

                    # Preverimo kemikalije z isto bazo ključa (isti ali katerikoli prejšnji razdelek)
                    for kem_key, kem_rows in kem.items():
                        kem_base = base_key_no_trailing_number(kem_key)
                        if kem_base == base:
                            for rkem in kem_rows:
                                kem_tab = tab_by_row.get(rkem, "")
                                kem_section = section_by_row.get(rkem, 0)
                                if kem_tab == tab and kem_section <= section:
                                    has_owner = True
                                    break
                            if has_owner:
                                break

                    # Preverimo raztopine z isto bazo ključa (isti ali katerikoli prejšnji razdelek)
                    if not has_owner:
                        for raz_key, razt_rows in raz.items():
                            raz_base = base_key_no_trailing_number(raz_key)
                            if raz_base == base:
                                for rraz in razt_rows:
                                    raz_tab = tab_by_row.get(rraz, "")
                                    raz_section = section_by_row.get(rraz, 0)
                                    if raz_tab == tab and raz_section <= section:
                                        has_owner = True
                                        break
                                if has_owner:
                                    break

                    # Če ima razdelek lastnika (kemikalija/raztopina), so večkratne mase dovoljene
                    if has_owner:
                        continue

                    # Sicer poročaj podvojen ključ mase znotraj tega razdelka
                    mass_rows = [row for _, row in mass_pairs_in_sec]
                    tab_suffix = f" v zavihku '{tab}'" if tab else ""
                    errors.append(
                        self.build_error(
                            f"Podvojen ključ '{base}' za tip 'masa'{tab_suffix}.",
                            context=context,
                            code="KLJUC_PODVOJEN_MASA",
                            payload={"rows": mass_rows},
                        )
                    )
                
                # Preverimo tudi, ali je ista baza ključa uporabljena v različnih razdelkih
                sections_with_base = list(grouped_section.keys())
                if len(sections_with_base) > 1:
                    # Preverimo, ali ima vsak razdelek svojega lastnika (kemikalija/raztopina v istem ali kateremkoli prejšnjem razdelku)
                    all_sections_have_owner = True
                    for section in sections_with_base:
                        section_has_owner = False

                        # Preverimo kemikalije z isto bazo ključa v tem ali kateremkoli prejšnjem razdelku
                        for kem_key, kem_rows in kem.items():
                            kem_base = base_key_no_trailing_number(kem_key)
                            if kem_base == base:
                                for rkem in kem_rows:
                                    kem_tab = tab_by_row.get(rkem, "")
                                    kem_section = section_by_row.get(rkem, 0)
                                    if kem_tab == tab and kem_section <= section:
                                        section_has_owner = True
                                        break
                                if section_has_owner:
                                    break

                        # Preverimo raztopine z isto bazo ključa v tem ali kateremkoli prejšnjem razdelku
                        if not section_has_owner:
                            for raz_key, razt_rows in raz.items():
                                raz_base = base_key_no_trailing_number(raz_key)
                                if raz_base == base:
                                    for rraz in razt_rows:
                                        raz_tab = tab_by_row.get(rraz, "")
                                        raz_section = section_by_row.get(rraz, 0)
                                        if raz_tab == tab and raz_section <= section:
                                            section_has_owner = True
                                            break
                                    if section_has_owner:
                                        break

                        if not section_has_owner:
                            all_sections_have_owner = False
                            break
                    
                    # Če ima vsak razdelek svojega lastnika, so večkratne mase dovoljene
                    if all_sections_have_owner:
                        continue
                    
                    # Sicer poročaj podvojen ključ
                    all_rows = []
                    for section_rows in grouped_section.values():
                        all_rows.extend([row for _, row in section_rows])
                    
                    tab_suffix = f" v zavihku '{tab}'" if tab else ""
                    errors.append(
                        self.build_error(
                            f"Podvojen ključ '{base}' za tip 'masa'{tab_suffix}.",
                            context=context,
                            code="KLJUC_PODVOJEN_MASA",
                            payload={"rows": all_rows},
                        )
                    )
        return errors

    def _has_owner_in_section(
        self,
        key: str,
        tab: str,
        section: int,
        kem: Mapping[str, Sequence[int]],
        raz: Mapping[str, Sequence[int]],
        tab_by_row: Mapping[int, str],
        section_by_row: Mapping[int, int],
    ) -> bool:
        def rows_match(rows: Sequence[int]) -> bool:
            for row in rows:
                if tab_by_row.get(row, "") == tab and section_by_row.get(row, 0) == section:
                    return True
            return False

        if rows_match(kem.get(key, [])):
            return True
        if rows_match(raz.get(key, [])):
            return True
        return False


@register
class MassOwnerRule(SheetRule):
    """Ensure every mass has a corresponding owner (kemikalija/raztopina)."""

    name = "mass_owner_rule"
    description = "Mase morajo imeti ustrezno kemikalijo ali raztopino."

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        from validator_oop.utils import coerce_str, norm_text
        
        shared = context.shared
        if not shared:
            return []

        errors = []
        kem = shared.get_keys_for_type("kemikalija")
        raz = shared.get_keys_for_type("raztopina")
        section_by_row = shared.section_by_row
        tab_by_row = shared.tab_by_row

        # Iteriramo po vseh vrsticah, da najdemo mase
        for row_idx, row in enumerate(rows, start=row_offset):
            tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
            if tip_data != "masa":
                continue
            
            masa_key = coerce_str(row.get("Ključ preverjanja", "")).strip()
            if not masa_key or is_water_key(masa_key):
                continue
            
            masa_tab = tab_by_row.get(row_idx, "")
            masa_base = base_key_no_trailing_number(masa_key)
            
            # Poiščimo najbližjo (najnovejšo) raztopino ali kemikalijo pred to maso z isto bazo ključa
            first_owner_row = None
            first_owner_key = None
            first_owner_type = None
            
            # Iteriramo nazaj od najbližje vrstice (od row_idx - 1 do row_offset)
            # Pomembno: iščemo najbližjo (najnovejšo) raztopino/kemikalijo z isto bazo ključa
            # Vedno najdemo najbližjo, ne glede na to, ali se ključa ujemata
            # Ne smemo najti starejše raztopine z enakim ključem, če je pred njo najbližja z isto bazo
            for prev_idx in range(row_idx - 1, row_offset - 1, -1):
                prev_row = rows[prev_idx - row_offset]
                prev_tip = norm_text(coerce_str(prev_row.get("Tip podatka", "")))
                prev_key = coerce_str(prev_row.get("Ključ preverjanja", "")).strip()
                prev_tab = tab_by_row.get(prev_idx, "")
                
                # Preverimo, ali je to raztopina ali kemikalija v istem zavihku
                if prev_tip in {"raztopina", "kemikalija"} and prev_key and prev_tab == masa_tab:
                    # Preverimo, ali se bazi ključa ujemata
                    prev_base = base_key_no_trailing_number(prev_key)
                    if prev_base == masa_base:
                        # Shranimo najbližjo raztopino/kemikalijo z isto bazo ključa
                        # (ker iteriramo nazaj, je to prva, ki jo najdemo - najbližja)
                        first_owner_row = prev_idx
                        first_owner_key = prev_key
                        first_owner_type = prev_tip
                        # Prekinemo takoj, ko najdemo najbližjo z isto bazo ključa
                        # (ne glede na to, ali se ključa ujemata)
                        break
            
            # Preverimo, ali se ključa ujemata
            if first_owner_key is None:
                # Ni raztopine/kemikalije z isto bazo ključa pred maso
                errors.append(
                    self.build_error(
                        f"Za maso s ključem '{masa_key}' ne obstaja ustrezna 'kemikalija' ali 'raztopina' pred tem korakom.",
                        context=context.with_row(row_idx),
                        column="Ključ preverjanja",
                        code="PAR_MASA_BREZ_LASTNIKA",
                    )
                )
            elif masa_key != first_owner_key:
                # Ključa se ne ujemata - masa mora imeti enak ključ kot najbližja raztopina/kemikalija
                errors.append(
                    self.build_error(
                        f"Vrstica {row_idx} mora imeti ključ preverjanja '{first_owner_key}' (kot vrstica {first_owner_row}, {first_owner_type}).",
                        context=context.with_row(row_idx),
                        column="Ključ preverjanja",
                        code="PAR_MASA_NAPACEN_RAZD",
                    )
                )
        return errors


@register
class TimePairRule(SheetRule):
    """Ensure datumcaszacetek/datumcaskonec pairs exist and keys are unique."""

    name = "time_pair_rule"
    description = "DatumCas začetka in konca morata nastopati v parih z enakim ključem, isti ključ se ne sme ponoviti znotraj istega zavihka."

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        errors = []
        start_keys = shared.get_keys_for_type("datumcaszacetek")
        end_keys = shared.get_keys_for_type("datumcaskonec")
        
        start_keys_set = set(start_keys.keys())
        end_keys_set = set(end_keys.keys())

        # Preverimo, da obstajajo pari
        for missing in sorted(start_keys_set - end_keys_set):
            rows_missing = start_keys[missing]
            errors.append(
                self.build_error(
                    f"Za 'datumcaszacetek' ključ '{missing}' manjka ustrezen 'datumcaskonec'.",
                    context=context,
                    code="PAR_CAS_BREZ_KONCA",
                    payload={"rows": rows_missing},
                )
            )

        for missing in sorted(end_keys_set - start_keys_set):
            rows_missing = end_keys[missing]
            errors.append(
                self.build_error(
                    f"Za 'datumcaskonec' ključ '{missing}' manjka ustrezen 'datumcaszacetek'.",
                    context=context,
                    code="PAR_CAS_BREZ_ZACETKA",
                    payload={"rows": rows_missing},
                )
            )

        # Exact isti ključ je lahko uporabljen samo enkrat za start in enkrat za end
        # znotraj istega zavihka. Numbered ključi (npr. crpanje in crpanje1) ostanejo ločeni.
        tab_by_row = shared.tab_by_row
        for key in start_keys_set | end_keys_set:
            start_rows = start_keys.get(key, [])
            end_rows = end_keys.get(key, [])

            start_by_tab: dict[str, list[int]] = {}
            for row_idx in start_rows:
                tab = tab_by_row.get(row_idx, "")
                start_by_tab.setdefault(tab, []).append(row_idx)

            end_by_tab: dict[str, list[int]] = {}
            for row_idx in end_rows:
                tab = tab_by_row.get(row_idx, "")
                end_by_tab.setdefault(tab, []).append(row_idx)

            for tab in set(start_by_tab) | set(end_by_tab):
                tab_start_rows = start_by_tab.get(tab, [])
                tab_end_rows = end_by_tab.get(tab, [])
                if len(tab_start_rows) <= 1 and len(tab_end_rows) <= 1:
                    continue

                all_rows = tab_start_rows + tab_end_rows
                tab_info = f" v zavihku '{tab}'" if tab else ""
                errors.append(
                    self.build_error(
                        f"Ključ '{key}' se ponavlja za 'datumcaszacetek'/'datumcaskonec'{tab_info}.",
                        context=context,
                        column="Ključ preverjanja",
                        code="KLJUC_PODVOJEN_CAS_PAR",
                        payload={"rows": all_rows, "tab": tab},
                    )
                )

        return errors


@register
class KeyNumberingRule(SheetRule):
    """Enforce numbering conventions for kemikalija/raztopina/masa keys."""

    name = "key_numbering_rule"
    description = "Oštevilčeni ključi morajo začeti z 1 brez preskokov."

    DATA_TYPES = {"kemikalija", "raztopina", "masa"}

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        shared = context.shared
        if not shared:
            return []

        errors = []
        # Združimo ključe za vse tipe skupaj (kot v MES_validator.py)
        all_keys = []
        for data_type in self.DATA_TYPES:
            keys = shared.get_keys_for_type(data_type)
            all_keys.extend(keys.keys())
        
        bases: dict[str, set[int]] = defaultdict(set)
        bare_present: dict[str, bool] = defaultdict(bool)

        for key in all_keys:
            base, number = split_key_number(key)
            bases[base].add(number if number > 0 else 1)
            if number == 0:
                bare_present[base] = True

        for base, numbers in bases.items():
            ordered = sorted(numbers)
            if ordered and ordered[0] != 1:
                errors.append(
                    self.build_error(
                        f"Ključ '{base}…' začetek oštevilčenja ni 1 (najdeno {ordered[0]}).",
                        context=context,
                        column="Ključ preverjanja",
                        code="KLJUC_NUM_NE_1",
                    )
                )
            for n in range(1, ordered[-1] + 1):
                if n not in numbers:
                    errors.append(
                        self.build_error(
                            f"Ključ '{base}{n}' manjka v zaporedju (preskok).",
                            context=context,
                            column="Ključ preverjanja",
                            code="KLJUC_NUM_PRESLEDEK",
                        )
                    )
            if bare_present.get(base) and len(numbers) > 1:
                errors.append(
                    self.build_error(
                        f"Nekonsistenten stil označevanja ključa '{base}'",
                        context=context,
                        column="Ključ preverjanja",
                        code="KLJUC_NUM_PODVOJEN_BASE",
                        severity=Severity.WARNING,
                    )
                )
        return errors


@register
class TehtnicaMasaPairRule(SheetRule):
    """Ensure tehtnica has corresponding masa, or forbid kontrolaustreznostiopreme."""

    name = "tehtnica_masa_pair_rule"
    description = "Tehtnica brez ustrezne mase ne sme imeti kontrole 'kontrolaustreznostiopreme'."

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        from validator_oop.rules.builtin.control import _get_present_controls, _has_control
        from validator_oop.utils import coerce_str, norm_text

        shared = context.shared
        if not shared:
            return []

        errors = []
        masa_keys = set(shared.get_keys_for_type("masa").keys())

        # Iterate through all rows to find tehtnica rows with kontrolaustreznostiopreme
        for row_idx, row in enumerate(rows, start=row_offset):
            tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
            if tip_data != "tehtnica":
                continue

            key = coerce_str(row.get("Ključ preverjanja", ""))
            if not key:
                continue

            # Check if masa with same key exists
            if key in masa_keys:
                continue  # Pair exists, kontrola is allowed

            # No masa found - check if kontrolaustreznostiopreme is present
            controls = _get_present_controls(row, shared)
            if _has_control(controls, "kontrolaustreznostiopreme"):
                errors.append(
                    self.build_error(
                        f"Tehtnica s ključem '{key}' nima ustrezne mase, zato ne sme imeti kontrole 'kontrolaustreznostiopreme'.",
                        context=context.with_row(row_idx),
                        column="(Kontrole)",
                        code="KONTROLA_TEHTNICA_BREZ_MASE",
                    )
                )

        return errors


@register
class TehtnicaVrednostFromFormulaRule(SheetRule):
    """Validate tehtnica Vrednost based on masa formula that references Podatki sheet."""

    name = "tehtnica_vrednost_from_formula_rule"
    description = "Vrednost pri tehtnici mora biti pravilna glede na maso iz formule INDEX MATCH."

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        from validator_oop.utils import (
            coerce_str,
            find_row_by_match,
            get_cell_value_from_workbook,
            norm_text,
            parse_index_match_formula,
            parse_numeric_value,
        )

        shared = context.shared
        if not shared:
            return []

        # Get workbook objects from extra (optional - needed only for INDEX MATCH formulas)
        workbook_values = shared.extra.get("workbook_values") if shared else None
        parsed_formulas = shared.extra.get("parsed_formulas") if shared else None

        # Note: We can still validate if formulas are not available, as long as masa values are direct numbers
        # This rule should always run, even without workbook access, to validate direct masa values

        errors = []
        masa_by_key = shared.get_keys_for_type("masa")

        # Iterate through all rows to find tehtnica rows
        for row_idx, row in enumerate(rows, start=row_offset):
            tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
            if tip_data != "tehtnica":
                continue

            key = coerce_str(row.get("Ključ preverjanja", ""))
            if not key:
                continue

            # Find masa with same key
            masa_row_numbers = masa_by_key.get(key, [])
            if not masa_row_numbers:
                continue

            # Get masa formula and value
            masa_value = None
            masa_label_unit = None
            for masa_row_idx in masa_row_numbers:
                masa_row = rows[masa_row_idx - row_offset]
                candidate_label_unit = extract_unit_token(coerce_str(masa_row.get("Labela", "")))

                # Try to get formula first (only if formulas and workbook are available)
                masa_formula = None
                if parsed_formulas and workbook_values and context.sheet in parsed_formulas:
                    formulas_sheet = parsed_formulas[context.sheet]
                    row_index_in_sheet = masa_row_idx - row_offset
                    if 0 <= row_index_in_sheet < len(formulas_sheet):
                        masa_formula_row = formulas_sheet[row_index_in_sheet]
                        masa_formula = coerce_str(masa_formula_row.get("Vrednost", ""))

                # Parse formula if present
                if masa_formula and masa_formula.startswith("="):
                    parsed = parse_index_match_formula(masa_formula)
                    if parsed and workbook_values:
                        sheet_name, col_num, lookup_cell = parsed
                        # Find row using MATCH logic
                        match_row = find_row_by_match(
                            workbook_values,
                            sheet_name,
                            lookup_cell,
                            context.sheet,
                            masa_row_idx,
                        )
                        if match_row:
                            masa_value = get_cell_value_from_workbook(
                                workbook_values,
                                sheet_name,
                                match_row,
                                col_num,
                            )

                # Fallback: try to parse numeric value directly (always try this)
                if masa_value is None:
                    masa_vrednost_str = coerce_str(masa_row.get("Vrednost", ""))
                    masa_value = parse_numeric_value(masa_vrednost_str)

                if masa_value is not None:
                    masa_label_unit = candidate_label_unit
                    break

            if masa_value is None:
                continue  # Could not determine masa value

            # Get tehtnica vrednost
            tehtnica_vrednost = coerce_str(row.get("Vrednost", "")).strip()
            # Support single value ("TEH-KLA") and comma-separated variants ("TEH-KLA, TEH-ANA")
            tehtnica_values = [v.strip() for v in tehtnica_vrednost.split(",") if v.strip()]
            tehtnica_set = set(tehtnica_values)

            # Validate based on masa value
            masa_num = parse_numeric_value(str(masa_value)) if masa_value else None
            if masa_num is None:
                continue

            if masa_num >= 10:
                # Must be "TEH-KLA" or "TEH-KLA, TEH-ANA" (in any order)
                allowed_sets = [{"TEH-KLA"}, {"TEH-KLA", "TEH-ANA"}]
                if tehtnica_set not in allowed_sets:
                    errors.append(
                        self.build_error(
                            f"Pri tehtnici s ključem '{key}' mora biti vrednost 'TEH-KLA' ali 'TEH-KLA, TEH-ANA' (masa je {masa_num}, kar je >= 10).",
                            context=context.with_row(row_idx),
                            column="Vrednost",
                            code="TEHTNICA_VREDNOST_PREVISOKA",
                        )
                    )
            else:
                # Pri masi < 10 napako javimo samo, če je masa podana v gramih.
                if masa_label_unit == "kg":
                    continue
                # Must be "TEH-ANA" or "TEH-KLA, TEH-ANA" (in any order)
                allowed_sets = [{"TEH-ANA"}, {"TEH-KLA", "TEH-ANA"}]
                if tehtnica_set not in allowed_sets:
                    errors.append(
                        self.build_error(
                            f"Pri tehtnici s ključem '{key}' mora biti vrednost 'TEH-ANA' ali 'TEH-KLA, TEH-ANA' (masa je {masa_num}, kar je < 10).",
                            context=context.with_row(row_idx),
                            column="Vrednost",
                            code="TEHTNICA_VREDNOST_PRENIZKA",
                        )
                    )

        return errors

