"""SOP compliance validation rule.

This module provides validation to ensure recipe data complies with
Standard Operating Procedure (SOP) specifications.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Optional, Sequence

from validator_oop.core.error import Severity
from validator_oop.rules import RuleContext, WorkbookRule, register
from validator_oop.utils import base_key_no_trailing_number, coerce_str, norm_text

try:
    from validator_oop.excel.sop_loader import SOPData
except ImportError:
    SOPData = None  # type: ignore


@register
class SOPComplianceRule(WorkbookRule):
    """Validate recipe compliance with SOP requirements.
    
    This rule checks that:
    - Solution keys (IPO šifre) from recipe match IPO codes from SOP
    - Solution types are allowed according to SOP
    - Volumes and flows comply with SOP limits
    - Required elements from SOP are present in recipe
    """
    
    name = "sop_compliance_rule"
    description = "Preverjanje skladnosti recepture s SOP-om"
    code = "SOP_COMPLIANCE"
    priority = 200  # Run after basic structural/field rules
    
    def __init__(self, sop_data: Optional[SOPData] = None, *, logger=None):
        """Initialize SOP compliance rule.
        
        Args:
            sop_data: SOP data to validate against. If None, rule is skipped.
            logger: Optional logger instance.
        """
        super().__init__(logger=logger)
        self._sop_data = sop_data
    
    def evaluate_workbook(
        self,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        """Check all sheets against SOP requirements.
        
        Validates all data from "Podatki" sheet against SOP specifications.
        
        Args:
            workbook_data: Mapping of sheet names to row sequences (filtered).
            context: Rule context.
            row_offset: Excel row number of the first data row.
            
        Yields:
            ValidationError objects for any non-compliance issues.
        """
        # Skip validation if no SOP data is available
        if not self._sop_data:
            self._logger.info("SOPComplianceRule: Ni SOP podatkov - preskakujem validacijo")
            return
        
        self._logger.info("SOPComplianceRule: Začenjam validacijo proti SOP-u")
        self._logger.info(f"  - SOP ID: {self._sop_data.sop_id}, Verzija: {self._sop_data.version}")
        self._logger.info(f"  - Število IPO šifer v SOP-u: {len(self._sop_data.ipo_codes)}")
        if self._sop_data.ipo_codes:
            self._logger.info(f"  - IPO šifre v SOP-u: {', '.join(self._sop_data.ipo_codes)}")
        self._logger.info(f"  - Število zahtev v SOP-u: {len(self._sop_data.requirements)}")
        
        # Get access to all sheets (including "Podatki") from extra context
        all_workbook_data = context.extra.get("all_workbook_data", workbook_data)
        all_headers = context.extra.get("all_workbook_headers", {})
        
        self._logger.info(f"  - Razpoložljivi zavihki: {', '.join(all_workbook_data.keys())}")
        
        errors = []
        
        # Extract and validate all data from "Podatki" sheet
        podatki_data = self._extract_all_podatki_data(
            all_workbook_data, all_headers, context, row_offset
        )
        
        # Log extracted data
        self._logger.info(f"  - Ekstrahirane IPO šifre iz 'Podatki': {len(podatki_data.get('ipo_codes', {}))}")
        if podatki_data.get('ipo_codes'):
            for (sheet, row, col), ipo in podatki_data['ipo_codes'].items():
                self._logger.info(f"    - Vrstica {row}, stolpec '{col}': {ipo}")
        
        self._logger.info(f"  - Ekstrahirani volumni iz 'Podatki': {len(podatki_data.get('volumes', {}))}")
        if podatki_data.get('volumes'):
            for (sheet, row, col), vol in podatki_data['volumes'].items():
                self._logger.info(f"    - Vrstica {row}, stolpec '{col}': {vol.get('min')}-{vol.get('max')} {vol.get('unit')}")
        
        self._logger.info(f"  - Ekstrahirani pretoki iz 'Podatki': {len(podatki_data.get('flows', {}))}")
        if podatki_data.get('flows'):
            for (sheet, row, col), flow in podatki_data['flows'].items():
                self._logger.info(f"    - Vrstica {row}, stolpec '{col}': {flow.get('min')}-{flow.get('max')} {flow.get('unit')}")
        
        self._logger.info(f"  - Ekstrahirane vrste raztopin iz 'Podatki': {len(podatki_data.get('solution_types', {}))}")
        if podatki_data.get('solution_types'):
            for (sheet, row, col), sol_type in podatki_data['solution_types'].items():
                self._logger.info(f"    - Vrstica {row}, stolpec '{col}': {sol_type}")
        
        # Log column volumes
        self._logger.info(f"  - Ekstrahirani volumni kolon iz 'Podatki': {len(podatki_data.get('column_volumes', {}))}")
        if podatki_data.get('column_volumes'):
            for (sheet, row), col_vol in podatki_data['column_volumes'].items():
                self._logger.info(f"    - Vrstica {row}: volumen kolone {col_vol} mL")
        
        # Log SOP requirements with column volumes
        if self._sop_data:
            reqs_with_col_vol = [req for req in self._sop_data.requirements if req.column_volume is not None]
            reqs_with_flow = [req for req in self._sop_data.requirements if req.flow_min is not None or req.flow_max is not None]
            self._logger.info(f"  - Zahteve iz SOP-a z volumenom kolone: {len(reqs_with_col_vol)}")
            self._logger.info(f"  - Zahteve iz SOP-a s pretoki: {len(reqs_with_flow)}")
            for req in reqs_with_col_vol[:10]:  # Show first 10
                self._logger.info(f"    - Volumen kolone: {req.column_volume} mL, pretok: {req.flow_min}-{req.flow_max} {req.flow_unit}")
            if len(reqs_with_flow) > len(reqs_with_col_vol):
                self._logger.warning(f"  - OPOZORILO: {len(reqs_with_flow) - len(reqs_with_col_vol)} zahtev s pretoki nima volumna kolone - te se ne bodo validirale!")
        
        # Validate all extracted data against SOP
        errors.extend(self._validate_podatki_against_sop(podatki_data, context, workbook_data, row_offset))
        # Konsistentnost Min./Max. pretok z obsegom Pretok spiranje (velja za vse vrstice, neodvisno od SOP)
        errors.extend(self._validate_podatki_flow_range_consistency(
            podatki_data.get("flows", {}), context
        ))
        
        self._logger.info(f"  - Najdenih napak pri validaciji 'Podatki': {len(errors)}")
        
        # Also validate recipe sheets (for solution types, volumes, flows)
        solution_types_data = self._extract_solution_types(workbook_data, context, row_offset)
        volumes_flows_data = self._extract_volumes_flows(workbook_data, context, row_offset)
        
        errors.extend(self._validate_solution_types(solution_types_data, context))
        errors.extend(self._validate_volumes(volumes_flows_data, context))
        errors.extend(self._validate_flows(volumes_flows_data, context))
        errors.extend(self._validate_requirements(workbook_data, context, row_offset))
        
        self._logger.info(f"SOPComplianceRule: Skupaj najdenih napak: {len(errors)}")
        
        for error in errors:
            yield error
    
    def _extract_all_podatki_data(
        self,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        headers: Mapping[str, Sequence[str]],
        context: RuleContext,
        row_offset: int,
    ) -> dict:
        """Extract all data from "Podatki" sheet.
        
        Returns:
            Dictionary with structure:
            {
                'ipo_codes': {(sheet, row, col): ipo_base},
                'volumes': {(sheet, row, col): {'min': ..., 'max': ..., 'unit': ...}},
                'flows': {(sheet, row, col): {'min': ..., 'max': ..., 'unit': ...}},
                'solution_types': {(sheet, row, col): type},
                'other_data': {(sheet, row, col): value}
            }
        """
        result = {
            'ipo_codes': {},
            'volumes': {},
            'flows': {},
            'solution_types': {},
            'sample_pm1': {},  # Vzorec prva PM
            'sample_pm23': {},  # Vzorec 2. in 3. PM
            'sample_tk': {},  # Vzorec testni kromatogram
            'tsst': {},  # tSST (min)
            'vr': {},  # Vr min/max
            'n': {},  # N >
            'pressure': {},  # Tlak
            'd': {},  # Distribucijski koeficient
            'column_volumes': {},  # Volumen kolone (V monolita) - ključno za validacijo pretokov
            'other_data': {},
        }
        
        # Find "Podatki" sheet (case-insensitive)
        podatki_sheet = None
        for sheet_name in workbook_data.keys():
            if sheet_name.lower().strip() == "podatki":
                podatki_sheet = sheet_name
                break
        
        if not podatki_sheet:
            self._logger.warning("SOPComplianceRule: Zavihek 'Podatki' ni najden!")
            self._logger.info(f"  - Razpoložljivi zavihki: {', '.join(workbook_data.keys())}")
            return result
        
        self._logger.info(f"SOPComplianceRule: Najden zavihek 'Podatki'")
        
        rows = workbook_data[podatki_sheet]
        sheet_headers = headers.get(podatki_sheet, [])
        
        self._logger.info(f"  - Število vrstic v 'Podatki': {len(rows)}")
        self._logger.info(f"  - Stolpci v 'Podatki': {', '.join(sheet_headers)}")
        
        # Find Ključ columns (supports "Ključ", "Ključ1", "Ključ 1", "Ključ2", "Ključ 2", etc.)
        kljuc_columns = [col for col in sheet_headers if re.match(r'^ključ\s*\d*$', col.lower().strip())]
        if kljuc_columns:
            self._logger.info(f"  - Najdeni stolpci za IPO šifre: {', '.join(kljuc_columns)}")
        else:
            self._logger.warning(f"  - Ni najdenih stolpcev 'Ključ', 'Ključ1', 'Ključ 1', 'Ključ2' v 'Podatki'")
        
        # First pass: extract column volumes for each row
        for row_idx, row in enumerate(rows, start=row_offset):
            for col_name in sheet_headers:
                col_lower = col_name.lower().strip()
                # Volumen kolone (V monolita) - ključno za validacijo pretokov
                if 'monolita' in col_lower or ('v' in col_lower and 'monolita' in col_lower):
                    value = coerce_str(row.get(col_name, "")).strip()
                    if value:
                        # Extract column volume (e.g., 4, 8, 40, 80, 400, 800)
                        try:
                            col_vol = float(re.search(r'(\d+(?:[.,]\d+)?)', value).group(1).replace(',', '.'))
                            result['column_volumes'][(podatki_sheet, row_idx)] = col_vol
                            self._logger.debug(f"    - Vrstica {row_idx}, stolpec '{col_name}': volumen kolone {col_vol} mL")
                        except (ValueError, AttributeError):
                            pass
        
        # Second pass: extract other data (now we have column volumes)
        for row_idx, row in enumerate(rows, start=row_offset):
            # Process each column
            for col_name in sheet_headers:
                value = coerce_str(row.get(col_name, "")).strip()
                if not value:
                    continue
                
                col_lower = col_name.lower().strip()
                
                # Identify column type and extract data
                # IPO šifre (Ključ, Ključ1, Ključ 1, Ključ2, Ključ 2, etc.)
                if re.match(r'^ključ\s*\d*$', col_lower):
                    ipo_base = base_key_no_trailing_number(value)
                    if ipo_base and len(ipo_base) >= 2:
                        result['ipo_codes'][(podatki_sheet, row_idx, col_name)] = ipo_base
                        self._logger.debug(f"    - Vrstica {row_idx}, stolpec '{col_name}': ekstrahirana IPO šifra '{value}' -> baza '{ipo_base}'")
                
                # Skip "V monolita" column in second pass (already processed)
                elif 'monolita' in col_lower or ('v' in col_lower and 'monolita' in col_lower):
                    pass  # Already processed in first pass
                
                # Volumni
                elif any(keyword in col_lower for keyword in ['volumen', 'volume']):
                    volume_data = self._extract_volume(value, "")
                    if volume_data:
                        result['volumes'][(podatki_sheet, row_idx, col_name)] = volume_data
                    else:
                        # Store as other data if not parseable as volume
                        result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # Pretoki
                elif any(keyword in col_lower for keyword in ['pretok', 'flow']):
                    flow_data = self._extract_flow(value, "")
                    if flow_data:
                        result['flows'][(podatki_sheet, row_idx, col_name)] = flow_data
                    else:
                        result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # Vrste raztopin
                elif any(keyword in col_lower for keyword in ['tip', 'vrsta', 'type']):
                    sol_type = self._parse_solution_type(value)
                    if sol_type:
                        result['solution_types'][(podatki_sheet, row_idx, col_name)] = sol_type
                    else:
                        result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # Vzorec prva PM
                elif 'vzorec' in col_lower and ('prva' in col_lower or '1.' in col_lower) and 'pm' in col_lower:
                    result['sample_pm1'][(podatki_sheet, row_idx, col_name)] = value
                
                # Vzorec 2. in 3. PM
                elif 'vzorec' in col_lower and ('2.' in col_lower or '3.' in col_lower) and 'pm' in col_lower:
                    result['sample_pm23'][(podatki_sheet, row_idx, col_name)] = value
                
                # Vzorec testni kromatogram
                elif 'vzorec' in col_lower and ('tk' in col_lower or 'testni' in col_lower or 'kromatogram' in col_lower):
                    result['sample_tk'][(podatki_sheet, row_idx, col_name)] = value
                
                # tSST (min)
                elif 'tsst' in col_lower or ('t0' in col_lower and 'min' in col_lower):
                    tsst_data = self._extract_volume(value, "")
                    if tsst_data:
                        result['tsst'][(podatki_sheet, row_idx, col_name)] = tsst_data
                    else:
                        result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # Vr min/max
                elif 'vr' in col_lower and ('min' in col_lower or 'max' in col_lower):
                    vr_data = self._extract_volume(value, "")
                    if vr_data:
                        result['vr'][(podatki_sheet, row_idx, col_name)] = vr_data
                    else:
                        result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # N > (število teoretičnih plošč)
                elif col_lower == 'n >' or (col_lower.startswith('n') and '>' in col_lower):
                    try:
                        n_value = int(re.search(r'\d+', value).group())
                        result['n'][(podatki_sheet, row_idx, col_name)] = n_value
                    except (ValueError, AttributeError):
                        result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # Tlak
                elif 'tlak' in col_lower or 'Δp' in col_lower.lower():
                    pressure_data = self._extract_volume(value, "")
                    if pressure_data:
                        result['pressure'][(podatki_sheet, row_idx, col_name)] = pressure_data
                    else:
                        result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # Distribucijski koeficient D
                elif col_lower == 'd' or 'distribucijski' in col_lower:
                    d_data = self._extract_volume(value, "")
                    if d_data:
                        result['d'][(podatki_sheet, row_idx, col_name)] = d_data
                    else:
                        result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # Kemikalije/Zahteve
                elif any(keyword in col_lower for keyword in ['kemikalija', 'chemical', 'zahteva', 'requirement']):
                    result['other_data'][(podatki_sheet, row_idx, col_name)] = value
                
                # All other columns - store as other data
                else:
                    result['other_data'][(podatki_sheet, row_idx, col_name)] = value
        
        return result
    
    def _extract_solution_types(
        self,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        context: RuleContext,
        row_offset: int,
    ) -> dict[tuple[str, int], str]:
        """Extract solution types from recipe.
        
        Returns:
            Dictionary mapping (sheet_name, row_index) -> solution_type
        """
        types = {}
        for sheet_name, rows in workbook_data.items():
            for row_idx, row in enumerate(rows, start=row_offset):
                tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
                if tip_data == "raztopina":
                    navodilo = coerce_str(row.get("Navodilo", ""))
                    # Try to extract solution type from Navodilo
                    sol_type = self._parse_solution_type(navodilo)
                    if sol_type:
                        types[(sheet_name, row_idx)] = sol_type
        return types
    
    def _extract_volumes_flows(
        self,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        context: RuleContext,
        row_offset: int,
    ) -> dict[tuple[str, int], dict[str, dict[str, float | str]]]:
        """Extract volumes and flows from recipe.
        
        Returns:
            Dictionary mapping (sheet_name, row_index) -> {'volume': {...}, 'flow': {...}}
        """
        data = {}
        for sheet_name, rows in workbook_data.items():
            for row_idx, row in enumerate(rows, start=row_offset):
                navodilo = coerce_str(row.get("Navodilo", ""))
                labela = coerce_str(row.get("Labela", ""))
                
                row_data = {}
                
                # Extract volume
                volume = self._extract_volume(navodilo, labela)
                if volume:
                    row_data['volume'] = volume
                
                # Extract flow
                flow = self._extract_flow(navodilo, labela)
                if flow:
                    row_data['flow'] = flow
                
                if row_data:
                    data[(sheet_name, row_idx)] = row_data
        
        return data
    
    def _extract_volume(self, navodilo: str, labela: str) -> Optional[dict[str, float | str]]:
        """Extract volume from Navodilo or Labela."""
        from validator_oop.utils.helpers import (
            extract_unit_token_near_number,
            parse_navodilo_interval,
            parse_navodilo_pm,
            parse_navodilo_single,
        )
        
        # Try parsing interval from navodilo
        interval = parse_navodilo_interval(navodilo)
        if interval[0] is not None and interval[2] and interval[2] in ('ml', 'l'):
            return {
                'min': interval[0],
                'max': interval[1] if interval[1] is not None else interval[0],
                'unit': interval[2],
            }
        
        # Try parsing ± from navodilo
        pm = parse_navodilo_pm(navodilo)
        if pm[0] is not None and pm[2] and pm[2] in ('ml', 'l'):
            tolerance = pm[1] if pm[1] is not None else 0.0
            return {
                'min': pm[0] - tolerance,
                'max': pm[0] + tolerance,
                'unit': pm[2],
            }
        
        # Try parsing single value from navodilo
        single = parse_navodilo_single(navodilo)
        if single[0] is not None and single[1] and single[1] in ('ml', 'l'):
            return {
                'min': single[0],
                'max': single[0],
                'unit': single[1],
            }
        
        # Try labela
        unit = extract_unit_token_near_number(labela)
        if unit in ('ml', 'l'):
            # Try to extract number from labela
            import re
            match = re.search(r'(\d+(?:[.,]\d+)?)', labela)
            if match:
                value = float(match.group(1).replace(',', '.'))
                return {
                    'min': value,
                    'max': value,
                    'unit': unit,
                }
        
        return None
    
    def _extract_flow(self, navodilo: str, labela: str) -> Optional[dict[str, float | str]]:
        """Extract flow from Navodilo or Labela."""
        from validator_oop.utils.helpers import (
            parse_navodilo_interval,
            parse_navodilo_pm,
            parse_navodilo_single,
        )
        
        # Try parsing interval from navodilo
        interval = parse_navodilo_interval(navodilo)
        if interval[0] is not None and interval[2] and interval[2] in ('ml/min', 'l/min'):
            return {
                'min': interval[0],
                'max': interval[1] if interval[1] is not None else interval[0],
                'unit': interval[2],
            }
        
        # Try parsing ± from navodilo
        pm = parse_navodilo_pm(navodilo)
        if pm[0] is not None and pm[2] and pm[2] in ('ml/min', 'l/min'):
            tolerance = pm[1] if pm[1] is not None else 0.0
            return {
                'min': pm[0] - tolerance,
                'max': pm[0] + tolerance,
                'unit': pm[2],
            }
        
        # Try parsing single value from navodilo
        single = parse_navodilo_single(navodilo)
        if single[0] is not None and single[1] and single[1] in ('ml/min', 'l/min'):
            return {
                'min': single[0],
                'max': single[0],
                'unit': single[1],
            }
        
        return None
    
    def _validate_podatki_against_sop(
        self,
        podatki_data: dict,
        context: RuleContext,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        row_offset: int,
    ) -> list:
        """Validate all data from "Podatki" sheet against SOP requirements.
        
        Validates:
        - IPO codes against SOP IPO codes
        - Volumes against SOP volume limits
        - Flows against SOP flow limits
        - Solution types against allowed types
        - Other data (if applicable)
        """
        if not self._sop_data:
            return []
        
        errors = []
        
        # Validate IPO codes
        errors.extend(self._validate_podatki_ipo_codes(
            podatki_data.get('ipo_codes', {}), context
        ))
        
        # Validate volumes (with column volume matching)
        errors.extend(self._validate_podatki_volumes(
            podatki_data.get('volumes', {}),
            podatki_data.get('column_volumes', {}),
            context
        ))
        
        # Validate flows (with column volume matching)
        errors.extend(self._validate_podatki_flows(
            podatki_data.get('flows', {}),
            podatki_data.get('column_volumes', {}),
            context
        ))
        
        # Validate solution types
        errors.extend(self._validate_podatki_solution_types(
            podatki_data.get('solution_types', {}), context
        ))
        
        # Validate specific parameters
        errors.extend(self._validate_podatki_samples(
            podatki_data.get('sample_pm1', {}),
            podatki_data.get('sample_pm23', {}),
            podatki_data.get('sample_tk', {}),
            context
        ))
        errors.extend(self._validate_podatki_tsst(
            podatki_data.get('tsst', {}), context
        ))
        errors.extend(self._validate_podatki_vr(
            podatki_data.get('vr', {}), context
        ))
        errors.extend(self._validate_podatki_n(
            podatki_data.get('n', {}), context
        ))
        errors.extend(self._validate_podatki_pressure(
            podatki_data.get('pressure', {}), context
        ))
        errors.extend(self._validate_podatki_d(
            podatki_data.get('d', {}), context
        ))
        
        # Validate medium compliance from recipe
        recipe_mediums = self._extract_medium_from_recipe(workbook_data, context, row_offset)
        errors.extend(self._validate_medium_compliance(recipe_mediums, context))
        
        return errors
    
    def _validate_podatki_ipo_codes(
        self,
        ipo_codes: dict[tuple[str, int, str], str],
        context: RuleContext,
    ) -> list:
        """Validate IPO codes from "Podatki" against SOP IPO codes.
        
        Comparison ignores trailing numbers (e.g., "GK10" matches "GK").
        """
        if not self._sop_data:
            return []
        
        errors = []
        
        # Normalize SOP IPO codes
        sop_ipo_bases = {}
        for ipo_code in self._sop_data.ipo_codes:
            base = base_key_no_trailing_number(ipo_code)
            sop_ipo_bases[base] = ipo_code  # Store original for error messages
        
        self._logger.info(f"  - Validacija IPO šifer:")
        self._logger.info(f"    - IPO šifre iz SOP-a (baze): {', '.join(sop_ipo_bases.keys())}")
        podatki_bases_set = set(ipo_codes.values())
        self._logger.info(f"    - IPO šifre iz 'Podatki' (baze): {', '.join(podatki_bases_set) if podatki_bases_set else '(ni podatkov)'}")
        
        # Check each IPO code from "Podatki"
        for (sheet_name, row_idx, col_name), podatki_ipo in ipo_codes.items():
            self._logger.debug(f"    - Preverjam IPO šifro '{podatki_ipo}' iz vrstice {row_idx}, stolpec '{col_name}'")
            # podatki_ipo is already normalized (base without trailing numbers)
            if podatki_ipo not in sop_ipo_bases:
                self._logger.warning(f"    - NAPAKA: IPO šifra '{podatki_ipo}' se ne ujema z SOP-om")
                errors.append(
                    self.build_error(
                        f"IPO šifra '{podatki_ipo}' iz stolpca '{col_name}' v zavihku 'Podatki' se ne ujema z IPO šifro iz SOP-a.",
                        context=context.with_sheet(sheet_name).with_row(row_idx),
                        column=col_name,
                        code="SOP_IPO_MISMATCH",
                    )
                )
            else:
                self._logger.debug(f"    - OK: IPO šifra '{podatki_ipo}' se ujema z SOP-om")
        
        # Check for required IPO codes missing in "Podatki" sheet
        podatki_bases = set(ipo_codes.values())
        missing_codes = []
        for req in self._sop_data.requirements:
            if req.ipo_code:
                req_base = base_key_no_trailing_number(req.ipo_code)
                if req_base not in podatki_bases:
                    missing_codes.append(req.ipo_code)
        
        if missing_codes:
            self._logger.warning(f"    - Manjkajoče IPO šifre iz SOP-a: {', '.join(missing_codes)}")
            for req in self._sop_data.requirements:
                if req.ipo_code:
                    req_base = base_key_no_trailing_number(req.ipo_code)
                    if req_base not in podatki_bases:
                        errors.append(
                            self.build_error(
                                f"Manjka zahtevana IPO šifra '{req.ipo_code}' (baza: '{req_base}') iz SOP-a v zavihku 'Podatki'.",
                                context=context.with_sheet("Podatki"),
                                code="SOP_IPO_MISSING",
                            )
                        )
        else:
            if podatki_bases:
                self._logger.info(f"    - Vse IPO šifre iz SOP-a so prisotne v 'Podatki'")
        
        return errors
    
    def _validate_podatki_volumes(
        self,
        volumes: dict[tuple[str, int, str], dict[str, float | str]],
        column_volumes: dict[tuple[str, int], float],
        context: RuleContext,
    ) -> list:
        """Validate volumes from "Podatki" against SOP volume limits.
        
        Only validates volumes against SOP requirements that match the column volume.
        """
        if not self._sop_data:
            return []
        
        errors = []
        
        if volumes:
            self._logger.info(f"  - Validacija volumnov: preverjam {len(volumes)} volumnov")
        
        for (sheet_name, row_idx, col_name), volume_data in volumes.items():
            vol_min = volume_data.get('min')
            vol_max = volume_data.get('max')
            vol_unit = volume_data.get('unit', '')
            
            # Get column volume for this row
            col_vol = column_volumes.get((sheet_name, row_idx))
            
            # Find matching SOP requirement (by column volume)
            matching_reqs = []
            for req in self._sop_data.requirements:
                # Only check requirements that have volume limits
                if req.volume_min is None and req.volume_max is None:
                    continue
                
                # If we have column volume, only match requirements with matching column volume
                if col_vol is not None:
                    if req.column_volume is not None:
                        # Allow small tolerance for floating point comparison
                        if abs(req.column_volume - col_vol) < 0.1:
                            matching_reqs.append(req)
                    # If requirement doesn't have column_volume, skip it (don't validate against it)
                    # This prevents matching wrong requirements
                else:
                    # If we don't have column volume info, we can't safely validate
                    # Skip validation for this volume
                    self._logger.debug(f"    - Vrstica {row_idx}: ni volumna kolone, preskakujem validacijo volumna")
                    break
            
            # If we have column volume but no matching requirements, skip validation
            if col_vol is not None and not matching_reqs:
                self._logger.debug(f"    - Vrstica {row_idx}: ni ustreznih zahtev za volumen kolone {col_vol} mL")
                continue
            
            # If we don't have column volume, skip validation entirely
            if col_vol is None:
                continue
            
            # Validate against matching requirements only
            for req in matching_reqs:
                if req.volume_min is not None or req.volume_max is not None:
                    # Check unit compatibility
                    req_unit = (req.volume_unit or '').lower()
                    vol_unit_lower = str(vol_unit).lower()
                    
                    # Convert units if needed (mL <-> L)
                    if req_unit and vol_unit_lower:
                        # Simple unit check - could be enhanced
                        if req_unit in ('ml', 'l') and vol_unit_lower in ('ml', 'l'):
                            if vol_min is not None and req.volume_min is not None and vol_min < req.volume_min:
                                errors.append(
                                    self.build_error(
                                        f"Volumen {vol_min} {vol_unit} iz stolpca '{col_name}' je pod minimalno zahtevano vrednostjo {req.volume_min} {req.volume_unit or ''} iz SOP-a (za volumen kolone {col_vol or '?'} mL).",
                                        context=context.with_sheet(sheet_name).with_row(row_idx),
                                        column=col_name,
                                        code="SOP_VOLUME_TOO_LOW",
                                    )
                                )
                            
                            if req.volume_max is not None and vol_max is not None and vol_max > req.volume_max:
                                errors.append(
                                    self.build_error(
                                        f"Volumen {vol_max} {vol_unit} iz stolpca '{col_name}' presega maksimalno dovoljeno vrednost {req.volume_max} {req.volume_unit or ''} iz SOP-a (za volumen kolone {col_vol or '?'} mL).",
                                        context=context.with_sheet(sheet_name).with_row(row_idx),
                                        column=col_name,
                                        code="SOP_VOLUME_TOO_HIGH",
                                    )
                                )
        
        return errors
    
    def _validate_podatki_flows(
        self,
        flows: dict[tuple[str, int, str], dict[str, float | str]],
        column_volumes: dict[tuple[str, int], float],
        context: RuleContext,
    ) -> list:
        """Validate flows from "Podatki" against SOP flow limits.
        
        Only validates flows against SOP requirements that match the column volume.
        """
        if not self._sop_data:
            return []
        
        errors = []
        
        if flows:
            self._logger.info(f"  - Validacija pretokov: preverjam {len(flows)} pretokov")
            self._logger.info(f"  - Razpoložljivi volumni kolon: {len(column_volumes)}")
            if column_volumes:
                for (sheet, row), vol in list(column_volumes.items())[:5]:  # Show first 5
                    self._logger.info(f"    - Vrstica {row}: {vol} mL")
        
        for (sheet_name, row_idx, col_name), flow_data in flows.items():
            flow_min = flow_data.get('min')
            flow_max = flow_data.get('max')
            flow_unit = flow_data.get('unit', '')
            
            # Get column volume for this row
            col_vol = column_volumes.get((sheet_name, row_idx))
            
            # Log for debugging
            if col_vol is None:
                # Try to find any column volume for debugging
                available_vols = [f"vrstica {r}: {v} mL" for (s, r), v in list(column_volumes.items())[:3]]
                self._logger.warning(f"    - Vrstica {row_idx}, stolpec '{col_name}': ni volumna kolone za pretok {flow_min}-{flow_max} {flow_unit}. Razpoložljivi volumni: {', '.join(available_vols) if available_vols else 'ni'}")
                continue
            
            self._logger.debug(f"    - Vrstica {row_idx}, stolpec '{col_name}': pretok {flow_min}-{flow_max} {flow_unit}, volumen kolone: {col_vol} mL")
            
            # Find matching SOP requirement (by column volume)
            matching_reqs = []
            all_flow_reqs = [req for req in self._sop_data.requirements if req.flow_min is not None or req.flow_max is not None]
            self._logger.debug(f"    - Vrstica {row_idx}: preverjam {len(all_flow_reqs)} zahtev s pretoki")
            
            for req in self._sop_data.requirements:
                # Only check requirements that have flow limits
                if req.flow_min is None and req.flow_max is None:
                    continue
                
                # Only match requirements with matching column volume
                if req.column_volume is not None:
                    # Allow small tolerance for floating point comparison
                    if abs(req.column_volume - col_vol) < 0.1:
                        matching_reqs.append(req)
                        self._logger.debug(f"    - Vrstica {row_idx}: najdena ustreznost za volumen kolone {col_vol} mL (pretok: {req.flow_min}-{req.flow_max} {req.flow_unit})")
                # If requirement doesn't have column_volume, skip it (don't validate against it)
                # This prevents matching wrong requirements
            
            # If we have column volume but no matching requirements, skip validation
            if col_vol is not None and not matching_reqs:
                reqs_without_col_vol = [req for req in all_flow_reqs if req.column_volume is None]
                self._logger.warning(f"    - Vrstica {row_idx}: ni ustreznih zahtev za volumen kolone {col_vol} mL. Zahteve brez volumna kolone: {len(reqs_without_col_vol)}")
                continue
            
            # If we don't have column volume, skip validation entirely
            if col_vol is None:
                continue
            
            # Validate against matching requirements only
            # CRITICAL: Only validate against requirements that have column_volume
            # This prevents validating against requirements from _parse_table that don't have column_volume
            for req in matching_reqs:
                # Double-check: skip if requirement doesn't have column_volume
                if req.column_volume is None:
                    self._logger.warning(f"    - Vrstica {row_idx}: preskakujem zahtevo brez volumna kolone (pretok: {req.flow_min}-{req.flow_max} {req.flow_unit})")
                    continue
                
                if req.flow_min is not None or req.flow_max is not None:
                    req_unit = (req.flow_unit or '').lower()
                    flow_unit_lower = str(flow_unit).lower()
                    
                    # Log validation attempt
                    self._logger.debug(f"    - Vrstica {row_idx}: validiram pretok {flow_min}-{flow_max} {flow_unit} proti zahtevi {req.flow_min}-{req.flow_max} {req.flow_unit} (volumen kolone: {req.column_volume} mL)")
                    
                    if req_unit and flow_unit_lower:
                        if req_unit in ('ml/min', 'l/min') and flow_unit_lower in ('ml/min', 'l/min'):
                            # Convert units if needed for comparison
                            req_flow_min = req.flow_min
                            req_flow_max = req.flow_max
                            recipe_flow_min = flow_min
                            recipe_flow_max = flow_max
                            
                            if req_unit == 'l/min' and flow_unit_lower == 'ml/min':
                                req_flow_min = req.flow_min * 1000 if req.flow_min else None
                                req_flow_max = req.flow_max * 1000 if req.flow_max else None
                            elif req_unit == 'ml/min' and flow_unit_lower == 'l/min':
                                recipe_flow_min = flow_min * 1000 if flow_min else None
                                recipe_flow_max = flow_max * 1000 if flow_max else None
                            
                            if recipe_flow_min is not None and req_flow_min is not None and recipe_flow_min < req_flow_min:
                                errors.append(
                                    self.build_error(
                                        f"Pretok {flow_min} {flow_unit} iz stolpca '{col_name}' je pod minimalno zahtevano vrednostjo {req.flow_min} {req.flow_unit or ''} iz SOP-a (za volumen kolone {col_vol or '?'} mL).",
                                        context=context.with_sheet(sheet_name).with_row(row_idx),
                                        column=col_name,
                                        code="SOP_FLOW_TOO_LOW",
                                    )
                                )
                            
                            if req.flow_max is not None and flow_max is not None and flow_max > req.flow_max:
                                errors.append(
                                    self.build_error(
                                        f"Pretok {flow_max} {flow_unit} iz stolpca '{col_name}' presega maksimalno dovoljeno vrednost {req.flow_max} {req.flow_unit or ''} iz SOP-a (za volumen kolone {col_vol or '?'} mL).",
                                        context=context.with_sheet(sheet_name).with_row(row_idx),
                                        column=col_name,
                                        code="SOP_FLOW_TOO_HIGH",
                                    )
                                )
        
        return errors
    
    def _validate_podatki_flow_range_consistency(
        self,
        flows: dict[tuple[str, int, str], dict[str, float | str]],
        context: RuleContext,
    ) -> list:
        """Validate that Min. pretok and Max. pretok are consistent with Pretok spiranje range in each row.
        
        Rule: Min. pretok must equal (lower bound of Pretok spiranje) - 1,
              Max. pretok must equal (upper bound of Pretok spiranje) + 1.
        This applies to every row in Podatki that has all three columns, regardless of recipe.
        """
        errors = []
        tolerance = 0.01  # za primerjavo float vrednosti
        
        # Group flow entries by (sheet, row)
        by_row: dict[tuple[str, int], list[tuple[str, dict[str, float | str]]]] = {}
        for (sheet_name, row_idx, col_name), flow_data in flows.items():
            key = (sheet_name, row_idx)
            if key not in by_row:
                by_row[key] = []
            by_row[key].append((col_name, flow_data))
        
        for (sheet_name, row_idx), row_flows in by_row.items():
            col_lower_map = {col_name: col_name.lower().strip() for col_name, _ in row_flows}
            range_low = range_high = None
            range_col = None
            min_pretok_val = None
            min_pretok_col = None
            max_pretok_val = None
            max_pretok_col = None
            
            for col_name, flow_data in row_flows:
                cl = col_lower_map[col_name]
                # Stolpec obsega "Pretok spiranje (mL/min)"
                if "spiranje" in cl and ("pretok" in cl or "flow" in cl):
                    lo, hi = flow_data.get("min"), flow_data.get("max")
                    if lo is not None and hi is not None:
                        try:
                            range_low = float(lo)
                            range_high = float(hi)
                            range_col = col_name
                        except (TypeError, ValueError):
                            pass
                # Min. pretok (izključimo stolpec obsega "Pretok spiranje")
                elif "min" in cl and ("pretok" in cl or "flow" in cl) and "spiranje" not in cl:
                    val = flow_data.get("min") or flow_data.get("max")
                    if val is not None:
                        try:
                            min_pretok_val = float(val)
                            min_pretok_col = col_name
                        except (TypeError, ValueError):
                            pass
                # Max. pretok (izključimo stolpec obsega "Pretok spiranje")
                elif "max" in cl and ("pretok" in cl or "flow" in cl) and "spiranje" not in cl:
                    val = flow_data.get("max") or flow_data.get("min")
                    if val is not None:
                        try:
                            max_pretok_val = float(val)
                            max_pretok_col = col_name
                        except (TypeError, ValueError):
                            pass
            
            if range_low is None or range_high is None or min_pretok_val is None or max_pretok_val is None:
                continue
            
            expected_min = range_low - 1
            expected_max = range_high + 1
            
            if abs(min_pretok_val - expected_min) > tolerance:
                errors.append(
                    self.build_error(
                        f"Min. pretok ({min_pretok_val}) se ne ujema z obsegom Pretok spiranje ({range_low}–{range_high}): pričakovana vrednost je {expected_min} (spodnja meja − 1).",
                        context=context.with_sheet(sheet_name).with_row(row_idx),
                        column=min_pretok_col or "Min. pretok",
                        code="DATA_FLOW_MIN_MISMATCH",
                    )
                )
            if abs(max_pretok_val - expected_max) > tolerance:
                errors.append(
                    self.build_error(
                        f"Max. pretok ({max_pretok_val}) se ne ujema z obsegom Pretok spiranje ({range_low}–{range_high}): pričakovana vrednost je {expected_max} (zgornja meja + 1).",
                        context=context.with_sheet(sheet_name).with_row(row_idx),
                        column=max_pretok_col or "Max. pretok",
                        code="DATA_FLOW_MAX_MISMATCH",
                    )
                )
        
        return errors
    
    def _validate_podatki_solution_types(
        self,
        solution_types: dict[tuple[str, int, str], str],
        context: RuleContext,
    ) -> list:
        """Validate solution types from "Podatki" against SOP allowed types."""
        if not self._sop_data:
            return []
        
        errors = []
        allowed_types = set(self._sop_data.allowed_solution_types)
        
        for (sheet_name, row_idx, col_name), sol_type in solution_types.items():
            if sol_type and sol_type not in allowed_types and allowed_types:
                errors.append(
                    self.build_error(
                        f"Vrsta raztopine '{sol_type}' iz stolpca '{col_name}' ni dovoljena v SOP-u.",
                        context=context.with_sheet(sheet_name).with_row(row_idx),
                        column=col_name,
                        code="SOP_TYPE_NOT_ALLOWED",
                    )
                )
        
        return errors
    
    def _validate_solution_types(
        self,
        solution_types_data: dict[tuple[str, int], str],
        context: RuleContext,
    ) -> list:
        """Validate solution types against SOP."""
        if not self._sop_data:
            return []
        
        errors = []
        allowed_types = set(self._sop_data.allowed_solution_types)
        
        for (sheet_name, row_idx), sol_type in solution_types_data.items():
            if sol_type and sol_type not in allowed_types and allowed_types:
                errors.append(
                    self.build_error(
                        f"Vrsta raztopine '{sol_type}' ni dovoljena v SOP-u.",
                        context=context.with_sheet(sheet_name).with_row(row_idx),
                        column="Navodilo",
                        code="SOP_TYPE_NOT_ALLOWED",
                    )
                )
        
        return errors
    
    def _validate_volumes(
        self,
        volumes_flows_data: dict[tuple[str, int], dict[str, dict[str, float | str]]],
        context: RuleContext,
    ) -> list:
        """Validate volumes against SOP requirements."""
        if not self._sop_data:
            return []
        
        errors = []
        
        for (sheet_name, row_idx), row_data in volumes_flows_data.items():
            if 'volume' not in row_data:
                continue
            
            volume = row_data['volume']
            
            # Find matching SOP requirement by sheet/row context
            # For now, we'll check against all requirements
            for req in self._sop_data.requirements:
                if req.volume_min is not None:
                    vol_min = volume.get('min')
                    vol_max = volume.get('max')
                    
                    if vol_min is not None and vol_min < req.volume_min:
                        errors.append(
                            self.build_error(
                                f"Volumen {vol_min} {volume.get('unit', '')} je pod minimalno zahtevano vrednostjo {req.volume_min} {req.volume_unit or ''} iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column="Navodilo",
                                code="SOP_VOLUME_TOO_LOW",
                            )
                        )
                    
                    if req.volume_max is not None and vol_max is not None and vol_max > req.volume_max:
                        errors.append(
                            self.build_error(
                                f"Volumen {vol_max} {volume.get('unit', '')} presega maksimalno dovoljeno vrednost {req.volume_max} {req.volume_unit or ''} iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column="Navodilo",
                                code="SOP_VOLUME_TOO_HIGH",
                            )
                        )
        
        return errors
    
    def _validate_flows(
        self,
        volumes_flows_data: dict[tuple[str, int], dict[str, dict[str, float | str]]],
        context: RuleContext,
    ) -> list:
        """Validate flows against SOP requirements."""
        if not self._sop_data:
            return []
        
        errors = []
        
        for (sheet_name, row_idx), row_data in volumes_flows_data.items():
            if 'flow' not in row_data:
                continue
            
            flow = row_data['flow']
            
            # Find matching SOP requirement
            for req in self._sop_data.requirements:
                if req.flow_min is not None:
                    flow_min = flow.get('min')
                    flow_max = flow.get('max')
                    
                    if flow_min is not None and flow_min < req.flow_min:
                        errors.append(
                            self.build_error(
                                f"Pretok {flow_min} {flow.get('unit', '')} je pod minimalno zahtevano vrednostjo {req.flow_min} {req.flow_unit or ''} iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column="Navodilo",
                                code="SOP_FLOW_TOO_LOW",
                            )
                        )
                    
                    if req.flow_max is not None and flow_max is not None and flow_max > req.flow_max:
                        errors.append(
                            self.build_error(
                                f"Pretok {flow_max} {flow.get('unit', '')} presega maksimalno dovoljeno vrednost {req.flow_max} {req.flow_unit or ''} iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column="Navodilo",
                                code="SOP_FLOW_TOO_HIGH",
                            )
                        )
        
        return errors
    
    def _validate_podatki_samples(
        self,
        sample_pm1: dict,
        sample_pm23: dict,
        sample_tk: dict,
        context: RuleContext,
    ) -> list:
        """Validate sample specifications (PM1, PM23, TK) against SOP."""
        if not self._sop_data:
            return []
        
        errors = []
        
        # Collect allowed samples from SOP requirements
        allowed_pm1 = set()
        allowed_pm23 = set()
        allowed_tk = set()
        
        for req in self._sop_data.requirements:
            if req.sample_pm1:
                allowed_pm1.add(req.sample_pm1)
            if req.sample_pm23:
                allowed_pm23.add(req.sample_pm23)
            if req.sample_tk:
                allowed_tk.add(req.sample_tk)
        
        # Validate PM1 samples
        for (sheet_name, row_idx, col_name), sample in sample_pm1.items():
            if allowed_pm1 and sample not in allowed_pm1:
                errors.append(
                    self.build_error(
                        f"Vzorec '{sample}' za 1. PM iz stolpca '{col_name}' ni dovoljen v SOP-u. Dovoljeni vzorci: {', '.join(allowed_pm1)}.",
                        context=context.with_sheet(sheet_name).with_row(row_idx),
                        column=col_name,
                        code="SOP_SAMPLE_NOT_ALLOWED",
                    )
                )
        
        # Validate PM23 samples
        for (sheet_name, row_idx, col_name), sample in sample_pm23.items():
            if allowed_pm23 and sample not in allowed_pm23:
                errors.append(
                    self.build_error(
                        f"Vzorec '{sample}' za 2./3. PM iz stolpca '{col_name}' ni dovoljen v SOP-u. Dovoljeni vzorci: {', '.join(allowed_pm23)}.",
                        context=context.with_sheet(sheet_name).with_row(row_idx),
                        column=col_name,
                        code="SOP_SAMPLE_NOT_ALLOWED",
                    )
                )
        
        # Validate TK samples
        for (sheet_name, row_idx, col_name), sample in sample_tk.items():
            if allowed_tk and sample not in allowed_tk:
                errors.append(
                    self.build_error(
                        f"Vzorec '{sample}' za testni kromatogram iz stolpca '{col_name}' ni dovoljen v SOP-u. Dovoljeni vzorci: {', '.join(allowed_tk)}.",
                        context=context.with_sheet(sheet_name).with_row(row_idx),
                        column=col_name,
                        code="SOP_SAMPLE_NOT_ALLOWED",
                    )
                )
        
        return errors
    
    def _validate_podatki_tsst(
        self,
        tsst_data: dict,
        context: RuleContext,
    ) -> list:
        """Validate tSST values against SOP requirements."""
        if not self._sop_data:
            return []
        
        errors = []
        
        for (sheet_name, row_idx, col_name), tsst in tsst_data.items():
            tsst_min = tsst.get('min')
            tsst_max = tsst.get('max')
            
            # Find matching SOP requirement
            for req in self._sop_data.requirements:
                if req.tsst_min is not None or req.tsst_max is not None:
                    if tsst_min is not None and req.tsst_min is not None and tsst_min < req.tsst_min:
                        errors.append(
                            self.build_error(
                                f"tSST {tsst_min} min iz stolpca '{col_name}' je pod minimalno zahtevano vrednostjo {req.tsst_min} min iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column=col_name,
                                code="SOP_TSST_TOO_LOW",
                            )
                        )
                    if tsst_max is not None and req.tsst_max is not None and tsst_max > req.tsst_max:
                        errors.append(
                            self.build_error(
                                f"tSST {tsst_max} min iz stolpca '{col_name}' presega maksimalno dovoljeno vrednost {req.tsst_max} min iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column=col_name,
                                code="SOP_TSST_TOO_HIGH",
                            )
                        )
        
        return errors
    
    def _validate_podatki_vr(
        self,
        vr_data: dict,
        context: RuleContext,
    ) -> list:
        """Validate Vr (retention volume) values against SOP requirements."""
        if not self._sop_data:
            return []
        
        errors = []
        
        for (sheet_name, row_idx, col_name), vr in vr_data.items():
            vr_min = vr.get('min')
            vr_max = vr.get('max')
            
            # Find matching SOP requirement
            for req in self._sop_data.requirements:
                if req.vr_min is not None or req.vr_max is not None:
                    if vr_min is not None and req.vr_min is not None and vr_min < req.vr_min:
                        errors.append(
                            self.build_error(
                                f"Vr {vr_min} mL iz stolpca '{col_name}' je pod minimalno zahtevano vrednostjo {req.vr_min} mL iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column=col_name,
                                code="SOP_VR_TOO_LOW",
                            )
                        )
                    if vr_max is not None and req.vr_max is not None and vr_max > req.vr_max:
                        errors.append(
                            self.build_error(
                                f"Vr {vr_max} mL iz stolpca '{col_name}' presega maksimalno dovoljeno vrednost {req.vr_max} mL iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column=col_name,
                                code="SOP_VR_TOO_HIGH",
                            )
                        )
        
        return errors
    
    def _validate_podatki_n(
        self,
        n_data: dict,
        context: RuleContext,
    ) -> list:
        """Validate N (number of theoretical plates) values against SOP requirements."""
        if not self._sop_data:
            return []
        
        errors = []
        
        for (sheet_name, row_idx, col_name), n_value in n_data.items():
            # Find matching SOP requirement
            for req in self._sop_data.requirements:
                if req.n_min is not None and n_value < req.n_min:
                    errors.append(
                        self.build_error(
                            f"N > {n_value} iz stolpca '{col_name}' je pod minimalno zahtevano vrednostjo {req.n_min} iz SOP-a.",
                            context=context.with_sheet(sheet_name).with_row(row_idx),
                            column=col_name,
                            code="SOP_N_TOO_LOW",
                        )
                    )
        
        return errors
    
    def _validate_podatki_pressure(
        self,
        pressure_data: dict,
        context: RuleContext,
    ) -> list:
        """Validate pressure values against SOP requirements."""
        if not self._sop_data:
            return []
        
        errors = []
        
        for (sheet_name, row_idx, col_name), pressure in pressure_data.items():
            pressure_min = pressure.get('min')
            pressure_max = pressure.get('max')
            
            # Find matching SOP requirement
            for req in self._sop_data.requirements:
                if req.pressure_min is not None or req.pressure_max is not None:
                    if pressure_min is not None and req.pressure_min is not None and pressure_min < req.pressure_min:
                        errors.append(
                            self.build_error(
                                f"Tlak {pressure_min} bar iz stolpca '{col_name}' je pod minimalno zahtevano vrednostjo {req.pressure_min} bar iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column=col_name,
                                code="SOP_PRESSURE_TOO_LOW",
                            )
                        )
                    if pressure_max is not None and req.pressure_max is not None and pressure_max > req.pressure_max:
                        errors.append(
                            self.build_error(
                                f"Tlak {pressure_max} bar iz stolpca '{col_name}' presega maksimalno dovoljeno vrednost {req.pressure_max} bar iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column=col_name,
                                code="SOP_PRESSURE_TOO_HIGH",
                            )
                        )
        
        return errors
    
    def _validate_podatki_d(
        self,
        d_data: dict,
        context: RuleContext,
    ) -> list:
        """Validate D (distribution coefficient) values against SOP requirements."""
        if not self._sop_data:
            return []
        
        errors = []
        
        for (sheet_name, row_idx, col_name), d in d_data.items():
            d_min = d.get('min')
            d_max = d.get('max')
            
            # Find matching SOP requirement
            for req in self._sop_data.requirements:
                if req.d_min is not None or req.d_max is not None:
                    if d_min is not None and req.d_min is not None and d_min < req.d_min:
                        errors.append(
                            self.build_error(
                                f"Distribucijski koeficient D {d_min} iz stolpca '{col_name}' je pod minimalno zahtevano vrednostjo {req.d_min} iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column=col_name,
                                code="SOP_D_TOO_LOW",
                            )
                        )
                    if d_max is not None and req.d_max is not None and d_max > req.d_max:
                        errors.append(
                            self.build_error(
                                f"Distribucijski koeficient D {d_max} iz stolpca '{col_name}' presega maksimalno dovoljeno vrednost {req.d_max} iz SOP-a.",
                                context=context.with_sheet(sheet_name).with_row(row_idx),
                                column=col_name,
                                code="SOP_D_TOO_HIGH",
                            )
                        )
        
        return errors
    
    def _extract_medium_from_recipe(
        self,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        context: RuleContext,
        row_offset: int,
        search_window: int = 5,
    ) -> dict[tuple[str, int], dict[str, str]]:
        """Extract medium information from recipe for different phases.
        
        Args:
            workbook_data: Recipe data
            context: Rule context
            row_offset: Excel row offset
            search_window: Number of rows to search before/after phase mention
            
        Returns:
            Dictionary mapping (sheet_name, row_index) -> {'phase': 'pm1', 'medium': 'MF1', 'medium_ipo': '...'}
        """
        from validator_oop.utils import coerce_str, norm_text, base_key_no_trailing_number
        
        result = {}
        
        # Phase keywords
        phase_keywords = {
            'pm1': ['1. pm', 'prva pm', 'prva pulzna motnja', r'1\.\s*pm'],
            'pm23': ['2. pm', '3. pm', 'druga pm', 'tretja pm', 'druga in tretja pm', r'2\.\s*pm', r'3\.\s*pm'],
            'tk': ['testni kromatogram', 'tk'],
            'endotoxin': ['endotoksini', 'endotoxin', 'vzorec za endotoksine', 'vzorec za meritve endotoksinov'],
        }
        
        # Medium keywords
        medium_keywords = ['MF1', 'MF2', 'MF3', 'dH2O', 'H2O', 'voda', 'destilirana voda', 'dh2o', 'h2o']
        
        for sheet_name, rows in workbook_data.items():
            for row_idx, row in enumerate(rows, start=row_offset):
                navodilo = coerce_str(row.get("Navodilo", "")).strip()
                if not navodilo:
                    continue
                
                navodilo_lower = navodilo.lower()
                
                # Check for phase mentions
                for phase_key, keywords in phase_keywords.items():
                    if any(re.search(rf'\b{re.escape(kw)}\b', navodilo_lower, re.IGNORECASE) for kw in keywords):
                        # Search for medium in nearby rows
                        medium_info = self._find_medium_nearby(
                            rows, row_idx, row_offset, search_window, medium_keywords
                        )
                        if medium_info:
                            result[(sheet_name, row_idx)] = {
                                'phase': phase_key,
                                'medium': medium_info.get('medium'),
                                'medium_ipo': medium_info.get('medium_ipo'),
                                'medium_text': medium_info.get('medium_text'),
                            }
        
        return result
    
    def _find_medium_nearby(
        self,
        rows: Sequence[Mapping[str, object]],
        phase_row_idx: int,
        row_offset: int,
        search_window: int,
        medium_keywords: list[str],
    ) -> Optional[dict[str, str]]:
        """Find medium in nearby rows."""
        from validator_oop.utils import coerce_str, norm_text, base_key_no_trailing_number
        
        # Search in window around phase row
        start_idx = max(0, phase_row_idx - row_offset - search_window)
        end_idx = min(len(rows), phase_row_idx - row_offset + search_window + 1)
        
        for idx in range(start_idx, end_idx):
            row = rows[idx]
            navodilo = coerce_str(row.get("Navodilo", "")).strip()
            tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
            kljuc = coerce_str(row.get("Ključ preverjanja", "")).strip()
            
            # Check Navodilo for medium keywords
            navodilo_lower = navodilo.lower()
            for medium_kw in medium_keywords:
                if medium_kw.lower() in navodilo_lower:
                    return {
                        'medium': medium_kw,
                        'medium_text': navodilo,
                        'medium_ipo': None,
                    }
            
            # Check Ključ preverjanja for IPO šifra (if Tip podatka = raztopina)
            if tip_data == "raztopina" and kljuc:
                # Check if this IPO šifra corresponds to a known medium
                # This would require mapping IPO šifre to medium names
                # For now, return the IPO šifra
                return {
                    'medium': None,
                    'medium_text': navodilo,
                    'medium_ipo': kljuc,
                }
        
        return None
    
    def _validate_medium_compliance(
        self,
        recipe_mediums: dict[tuple[str, int], dict[str, str]],
        context: RuleContext,
    ) -> list:
        """Validate that mediums in recipe match SOP requirements."""
        if not self._sop_data:
            return []
        
        errors = []
        
        # Normalize medium names for comparison
        def normalize_medium(medium: str) -> str:
            if not medium:
                return ""
            medium_lower = medium.lower().strip()
            # Normalize variations
            if 'dh2o' in medium_lower or 'destilirana voda' in medium_lower or medium_lower == 'voda' or 'h2o' in medium_lower:
                return 'voda'
            if 'mf1' in medium_lower:
                return 'mf1'
            if 'mf2' in medium_lower:
                return 'mf2'
            if 'mf3' in medium_lower:
                return 'mf3'
            return medium_lower
        
        # Collect SOP mediums by phase
        sop_mediums = {}
        for req in self._sop_data.requirements:
            if req.medium_pm1:
                sop_mediums['pm1'] = normalize_medium(req.medium_pm1)
            if req.medium_pm23:
                sop_mediums['pm23'] = normalize_medium(req.medium_pm23)
            if req.medium_tk:
                sop_mediums['tk'] = normalize_medium(req.medium_tk)
            if req.medium_endotoxin:
                sop_mediums['endotoxin'] = normalize_medium(req.medium_endotoxin)
        
        # Also check IPO codes for medium mapping
        # If recipe has IPO šifra, check if it matches SOP IPO šifre for known mediums
        ipo_to_medium = {}
        for req in self._sop_data.requirements:
            if req.ipo_code and req.medium_pm1:
                ipo_to_medium[req.ipo_code] = ('pm1', normalize_medium(req.medium_pm1))
            if req.ipo_code and req.medium_pm23:
                ipo_to_medium[req.ipo_code] = ('pm23', normalize_medium(req.medium_pm23))
            if req.ipo_code and req.medium_tk:
                ipo_to_medium[req.ipo_code] = ('tk', normalize_medium(req.medium_tk))
            if req.ipo_code and req.medium_endotoxin:
                ipo_to_medium[req.ipo_code] = ('endotoxin', normalize_medium(req.medium_endotoxin))
        
        # Validate each recipe medium
        for (sheet_name, row_idx), medium_info in recipe_mediums.items():
            phase = medium_info.get('phase')
            recipe_medium = normalize_medium(medium_info.get('medium') or medium_info.get('medium_text', ''))
            recipe_ipo = medium_info.get('medium_ipo')
            
            if phase in sop_mediums:
                sop_medium = sop_mediums[phase]
                
                # Check if recipe medium matches SOP medium
                if recipe_medium and sop_medium and recipe_medium != sop_medium:
                    errors.append(
                        self.build_error(
                            f"Medij '{medium_info.get('medium') or medium_info.get('medium_text')}' za fazo '{phase}' se ne ujema z medijem iz SOP-a (zahtevan: '{sop_medium}').",
                            context=context.with_sheet(sheet_name).with_row(row_idx),
                            column="Navodilo",
                            code="SOP_MEDIUM_MISMATCH",
                        )
                    )
                
                # Check IPO šifra if available
                if recipe_ipo and not recipe_medium:
                    # Try to match IPO šifra to medium
                    ipo_base = base_key_no_trailing_number(recipe_ipo)
                    matched = False
                    for ipo_code, (ipo_phase, ipo_medium) in ipo_to_medium.items():
                        ipo_code_base = base_key_no_trailing_number(ipo_code)
                        if ipo_base == ipo_code_base and ipo_phase == phase:
                            if ipo_medium != sop_medium:
                                errors.append(
                                    self.build_error(
                                        f"Medij z IPO šifro '{recipe_ipo}' za fazo '{phase}' se ne ujema z medijem iz SOP-a (zahtevan: '{sop_medium}').",
                                        context=context.with_sheet(sheet_name).with_row(row_idx),
                                        column="Ključ preverjanja",
                                        code="SOP_MEDIUM_MISMATCH",
                                    )
                                )
                            matched = True
                            break
                    
                    if not matched and sop_medium:
                        # IPO šifra not found in SOP mediums - might be an error
                        self._logger.warning(f"IPO šifra '{recipe_ipo}' za fazo '{phase}' ni najdena v SOP medijih")
        
        return errors
    
    def _validate_requirements(
        self,
        workbook_data: Mapping[str, Sequence[Mapping[str, object]]],
        context: RuleContext,
        row_offset: int,
    ) -> list:
        """Validate that all SOP requirements are met."""
        if not self._sop_data:
            return []
        
        errors = []
        # Additional requirement validation can be added here
        # For now, IPO code validation covers the main requirement
        
        return errors
    
    def _parse_solution_type(self, navodilo: str) -> Optional[str]:
        """Extract solution type from Navodilo text."""
        # Simple pattern matching for common solution types
        text = navodilo.lower()
        
        if 'vodna' in text or 'water' in text:
            return 'vodna'
        elif 'organska' in text or 'organic' in text:
            return 'organska'
        elif 'bazna' in text or 'base' in text:
            return 'bazna'
        elif 'kisla' in text or 'acid' in text:
            return 'kisla'
        
        return None

