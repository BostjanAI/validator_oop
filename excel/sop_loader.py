"""Loader for SOP (Standard Operating Procedure) data from Word documents.

This module provides functionality to parse Word documents containing SOP
specifications and extract structured data for recipe validation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from docx import Document as DocxDocument
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ImportError:
    DocxDocument = None
    Table = None
    Paragraph = None


@dataclass
class SOPRequirement:
    """Single requirement from SOP.
    
    Attributes:
        step_number: Step number in the process (optional).
        ipo_code: IPO šifra (solution key) - used for matching with recipe keys.
        solution_key: Alias for ipo_code (backward compatibility).
        solution_type: Type of solution (e.g., "vodna", "organska", "bazna").
        volume_min: Minimum volume requirement.
        volume_max: Maximum volume requirement.
        volume_unit: Unit for volume (e.g., "mL", "L").
        flow_min: Minimum flow requirement.
        flow_max: Maximum flow requirement.
        flow_unit: Unit for flow (e.g., "mL/min", "L/min").
        required_chemicals: List of required chemical keys.
        description: Description of the requirement.
        raw_text: Original text from Word for debugging.
        # Specific parameters
        column_volume: Optional[float] = None  # Kolona volumen (4, 8, 40, 80, 400, 800 mL)
        sample_pm1: Optional[str] = None  # Vzorec za 1. PM (e.g., "ACV16.7", "ACV50")
        sample_pm23: Optional[str] = None  # Vzorec za 2. in 3. PM (e.g., "URMF1-0.05")
        sample_tk: Optional[str] = None  # Vzorec za testni kromatogram (e.g., "TR0.60")
        tsst_min: Optional[float] = None  # tSST minimum (min)
        tsst_max: Optional[float] = None  # tSST maximum (min)
        vr_min: Optional[float] = None  # Vr minimum (mL)
        vr_max: Optional[float] = None  # Vr maximum (mL)
        n_min: Optional[int] = None  # N > (število teoretičnih plošč)
        pressure_min: Optional[float] = None  # Tlak minimum (bar)
        pressure_max: Optional[float] = None  # Tlak maximum (bar)
        d_min: Optional[float] = None  # Distribucijski koeficient minimum
        d_max: Optional[float] = None  # Distribucijski koeficient maximum
    """
    
    step_number: Optional[int] = None
    ipo_code: Optional[str] = None
    solution_type: Optional[str] = None
    volume_min: Optional[float] = None
    volume_max: Optional[float] = None
    volume_unit: Optional[str] = None
    flow_min: Optional[float] = None
    flow_max: Optional[float] = None
    flow_unit: Optional[str] = None
    required_chemicals: List[str] = field(default_factory=list)
    description: str = ""
    raw_text: str = ""
    # Specific parameters
    column_volume: Optional[float] = None
    sample_pm1: Optional[str] = None
    sample_pm23: Optional[str] = None
    sample_tk: Optional[str] = None
    tsst_min: Optional[float] = None
    tsst_max: Optional[float] = None
    vr_min: Optional[float] = None
    vr_max: Optional[float] = None
    n_min: Optional[int] = None
    pressure_min: Optional[float] = None
    pressure_max: Optional[float] = None
    d_min: Optional[float] = None
    d_max: Optional[float] = None
    # Medium/mobile phase information
    medium_pm1: Optional[str] = None  # Medij/mobilna faza za 1. PM (npr. "dH2O", "voda")
    medium_pm23: Optional[str] = None  # Medij/mobilna faza za 2./3. PM
    medium_tk: Optional[str] = None  # Medij/mobilna faza za testni kromatogram
    medium_endotoxin: Optional[str] = None  # Medij za vzorčenje endotoksinov
    phase_name: Optional[str] = None  # Ime faze (npr. "1. PM", "endotoksini")
    
    @property
    def solution_key(self) -> Optional[str]:
        """Alias for ipo_code for backward compatibility."""
        return self.ipo_code
    
    @solution_key.setter
    def solution_key(self, value: Optional[str]) -> None:
        """Set ipo_code when solution_key is set."""
        self.ipo_code = value


@dataclass
class SOPData:
    """Complete SOP specification.
    
    Attributes:
        sop_id: SOP identifier.
        version: SOP version.
        requirements: List of requirements from the SOP.
        ipo_codes: List of all IPO šifre (solution keys) from the SOP.
        allowed_solution_keys: Alias for ipo_codes (backward compatibility).
        allowed_solution_types: List of allowed solution types.
        source_path: Path to the source Word document.
    """
    
    sop_id: str = ""
    version: str = ""
    requirements: List[SOPRequirement] = field(default_factory=list)
    ipo_codes: List[str] = field(default_factory=list)
    allowed_solution_types: List[str] = field(default_factory=list)
    source_path: Optional[Path] = None
    
    @property
    def allowed_solution_keys(self) -> List[str]:
        """Alias for ipo_codes for backward compatibility."""
        return self.ipo_codes
    
    @classmethod
    def from_word(cls, path: Path, *, logger: Optional[logging.Logger] = None) -> 'SOPData':
        """Load SOP from Word document.
        
        Supports multiple formats:
        - Tables with structured data
        - Structured text with patterns
        - Mixed format
        
        Args:
            path: Path to .docx file.
            logger: Optional logger for debugging.
            
        Returns:
            SOPData instance.
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            RuntimeError: If python-docx is not installed.
        """
        if DocxDocument is None:
            raise RuntimeError(
                "python-docx is required to load Word documents. "
                "Install with: pip install python-docx"
            )
        
        resolved_path = Path(path).expanduser().resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(f"SOP document not found: {resolved_path}")
        
        log = logger or logging.getLogger(cls.__name__)
        log.info(f"Loading SOP from Word document: {resolved_path}")
        
        doc = DocxDocument(str(resolved_path))
        sop_data = cls(source_path=resolved_path)
        
        # Extract SOP metadata (ID, version) from document properties or first paragraphs
        sop_data.sop_id, sop_data.version = cls._extract_metadata(doc, log)
        
        # Try to extract from tables first (most structured format)
        if doc.tables:
            log.debug(f"Found {len(doc.tables)} tables in document")
            for table_idx, table in enumerate(doc.tables):
                # Try parsing as specific parameter table first
                specific_reqs = cls._parse_specific_parameter_table(table, log)
                if specific_reqs:
                    sop_data.requirements.extend(specific_reqs)
                    log.debug(f"Extracted {len(specific_reqs)} specific requirements from table {table_idx + 1}")
                else:
                    # Try standard table parsing
                    requirements = cls._parse_table(table, log)
                    if requirements:
                        sop_data.requirements.extend(requirements)
                        log.debug(f"Extracted {len(requirements)} requirements from table {table_idx + 1}")
        
        # If no requirements from tables, try parsing paragraphs
        if not sop_data.requirements:
            log.debug("No requirements from tables, trying paragraph parsing")
            requirements = cls._parse_paragraphs(doc.paragraphs, log)
            sop_data.requirements.extend(requirements)
        
        # Extract allowed solution keys and types from requirements or dedicated sections
        sop_data.ipo_codes = cls._extract_ipo_codes(sop_data.requirements, doc, log)
        sop_data.allowed_solution_types = cls._extract_allowed_types(sop_data.requirements, doc, log)
        
        # Extract medium information from text
        medium_map = cls._extract_medium_from_text(doc.paragraphs, log)
        # Apply mediums to requirements
        for req in sop_data.requirements:
            if 'pm1' in medium_map and not req.medium_pm1:
                req.medium_pm1 = medium_map['pm1']
            if 'pm23' in medium_map and not req.medium_pm23:
                req.medium_pm23 = medium_map['pm23']
            if 'tk' in medium_map and not req.medium_tk:
                req.medium_tk = medium_map['tk']
            if 'endotoxin' in medium_map and not req.medium_endotoxin:
                req.medium_endotoxin = medium_map['endotoxin']
        
        log.info(f"Loaded SOP: {sop_data.sop_id} v{sop_data.version}, "
                f"{len(sop_data.requirements)} requirements, "
                f"{len(sop_data.ipo_codes)} IPO šifre")
        
        return sop_data
    
    @staticmethod
    def _extract_metadata(doc: DocxDocument, log: logging.Logger) -> tuple[str, str]:
        """Extract SOP ID and version from document."""
        sop_id = ""
        version = ""
        
        # Try document properties first
        try:
            if doc.core_properties.title:
                sop_id = doc.core_properties.title
            if doc.core_properties.revision:
                version = doc.core_properties.revision
        except Exception:
            pass
        
        # Try first few paragraphs for patterns like "SOP-001" or "Version 1.0"
        for para in doc.paragraphs[:10]:
            text = para.text.strip()
            if not text:
                continue
            
            # Look for SOP ID pattern
            if not sop_id:
                match = re.search(r'SOP[:\s-]?([A-Z0-9\-]+)', text, re.IGNORECASE)
                if match:
                    sop_id = match.group(1)
            
            # Look for version pattern
            if not version:
                match = re.search(r'verzija|version|v\.?\s*(\d+[.\d]*)', text, re.IGNORECASE)
                if match:
                    version = match.group(1)
            
            if sop_id and version:
                break
        
        return sop_id or "UNKNOWN", version or "1.0"
    
    @staticmethod
    def _parse_table(table: Table, log: logging.Logger) -> List[SOPRequirement]:
        """Parse requirements from a Word table.
        
        Expected table structure (flexible):
        - First row may be headers
        - Columns may contain: step, IPO šifra, type, volume, flow, etc.
        """
        requirements = []
        
        if not table.rows:
            return requirements
        
        # Try to identify header row
        header_row = None
        headers = []
        
        # Check first row for headers
        first_row = table.rows[0]
        first_row_text = [cell.text.strip().lower() for cell in first_row.cells]
        
        # Common header keywords
        header_keywords = ['korak', 'step', 'ipo', 'ipo šifra', 'ključ', 'key', 'raztopina', 'solution', 
                          'volumen', 'volume', 'pretok', 'flow', 'tip', 'type']
        
        if any(keyword in ' '.join(first_row_text) for keyword in header_keywords):
            header_row = 0
            headers = first_row_text
            log.debug(f"Found header row: {headers}")
        else:
            # No clear headers, use positional columns
            headers = [f"col_{i}" for i in range(len(first_row.cells))]
            log.debug("No clear headers found, using positional columns")
        
        # Parse data rows
        start_row = 1 if header_row is not None else 0
        for row_idx, row in enumerate(table.rows[start_row:], start=start_row):
            if not row.cells:
                continue
            
            req = SOPRequirement()
            cells = [cell.text.strip() for cell in row.cells]
            
            # Map cells to requirement fields based on headers or position
            for col_idx, cell_text in enumerate(cells):
                if not cell_text:
                    continue
                
                header = headers[col_idx] if col_idx < len(headers) else f"col_{col_idx}"
                header_lower = header.lower()
                
                # IPO šifra / Solution key (highest priority for matching)
                if any(kw in header_lower for kw in ['ipo', 'ipo šifra', 'ipo šifra', 'ključ raztopine', 'solution key', 'solution_key']):
                    req.ipo_code = cell_text.strip()
                
                # Step number
                elif any(kw in header_lower for kw in ['korak', 'step', 'št']):
                    try:
                        req.step_number = int(re.search(r'\d+', cell_text).group())
                    except (ValueError, AttributeError):
                        pass
                
                # Solution key (fallback if IPO not found)
                elif any(kw in header_lower for kw in ['ključ', 'key', 'raztopina', 'solution']) and not req.ipo_code:
                    req.ipo_code = cell_text.strip()
                
                # Solution type
                elif any(kw in header_lower for kw in ['tip', 'type', 'vrsta']):
                    req.solution_type = cell_text
                
                # Volume
                elif any(kw in header_lower for kw in ['volumen', 'volume']):
                    volume_data = SOPData._parse_volume_flow(cell_text, is_flow=False)
                    if volume_data:
                        req.volume_min = volume_data.get('min')
                        req.volume_max = volume_data.get('max')
                        req.volume_unit = volume_data.get('unit')
                
                # Flow
                elif any(kw in header_lower for kw in ['pretok', 'flow']):
                    flow_data = SOPData._parse_volume_flow(cell_text, is_flow=True)
                    if flow_data:
                        req.flow_min = flow_data.get('min')
                        req.flow_max = flow_data.get('max')
                        req.flow_unit = flow_data.get('unit')
                
                # Description or other text
                else:
                    if not req.description:
                        req.description = cell_text
                    req.raw_text += f" {cell_text}"
            
            # Only add if we have meaningful data
            if req.ipo_code or req.step_number or req.volume_min or req.flow_min:
                req.raw_text = req.raw_text.strip()
                requirements.append(req)
        
        return requirements
    
    @staticmethod
    def _parse_specific_parameter_table(table: Table, log: logging.Logger) -> List[SOPRequirement]:
        """Parse specific parameter tables from SOP (e.g., PM samples, tSST, Vr, pressure, etc.).
        
        These tables typically have column volumes (4, 8, 40, 80, 400, 800 mL) as headers.
        """
        requirements = []
        
        if not table.rows or len(table.rows) < 2:
            return requirements
        
        first_row = [cell.text.strip() for cell in table.rows[0].cells]
        first_row_lower = [h.lower() for h in first_row]
        
        # Check if this is a column-based table (has volume indicators like "4 mL", "8 mL", etc.)
        has_column_volumes = any(
            re.search(r'\b(4|8|40|80|400|800)\s*(ml|l)\b', h, re.IGNORECASE) 
            for h in first_row
        )
        
        if not has_column_volumes:
            return requirements  # Not a specific parameter table
        
        log.debug(f"Found column-based parameter table with headers: {first_row}")
        
        # Extract column volumes from headers
        column_volumes = []
        for header in first_row:
            vol_match = re.search(r'\b(4|8|40|80|400|800)\s*(ml|l)\b', header, re.IGNORECASE)
            if vol_match:
                column_volumes.append(float(vol_match.group(1)))
        
        # Parse data rows
        for row_idx, row in enumerate(table.rows[1:], start=1):
            if not row.cells:
                continue
            
            row_data = [cell.text.strip() for cell in row.cells]
            if not any(row_data):  # Skip empty rows
                continue
            
            # Check row header (first cell) for parameter type
            row_header = row_data[0].lower() if row_data else ""
            
            # Create requirements for each column volume
            for col_idx, col_vol in enumerate(column_volumes):
                if col_idx + 1 >= len(row_data):
                    continue
                
                cell_value = row_data[col_idx + 1].strip()
                if not cell_value:
                    continue
                
                req = SOPRequirement(column_volume=col_vol)
                
                # Identify parameter type from row header
                if '1. pm' in row_header and 'vzorec' in row_header:
                    req.sample_pm1 = cell_value
                elif ('2.' in row_header or '3.' in row_header) and 'pm' in row_header and 'vzorec' in row_header:
                    req.sample_pm23 = cell_value
                elif 'tk' in row_header and 'vzorec' in row_header:
                    req.sample_tk = cell_value
                elif 'pretok' in row_header:
                    # Parse flow range
                    flow_data = SOPData._parse_volume_flow(cell_value, is_flow=True)
                    if flow_data:
                        req.flow_min = flow_data.get('min')
                        req.flow_max = flow_data.get('max')
                        req.flow_unit = flow_data.get('unit')
                elif 'tlak' in row_header or 'tlaka' in row_header or 'Δp' in row_header.lower():
                    # Parse pressure range
                    pressure_data = SOPData._parse_volume_flow(cell_value.replace('bar', '').replace('≤', '').strip(), is_flow=False)
                    if pressure_data:
                        req.pressure_min = pressure_data.get('min')
                        req.pressure_max = pressure_data.get('max')
                    else:
                        # Try single value
                        try:
                            val = float(re.search(r'[\d.]+', cell_value).group())
                            if '≤' in cell_value or 'max' in row_header:
                                req.pressure_max = val
                            else:
                                req.pressure_min = val
                                req.pressure_max = val
                        except (ValueError, AttributeError):
                            pass
                elif 'tsst' in row_header or 't0' in row_header or 't1' in row_header:
                    # Parse tSST range
                    tsst_data = SOPData._parse_volume_flow(cell_value, is_flow=False)
                    if tsst_data:
                        req.tsst_min = tsst_data.get('min')
                        req.tsst_max = tsst_data.get('max')
                elif 'vr' in row_header and ('min' in row_header or 'max' in row_header):
                    # Parse Vr range
                    vr_data = SOPData._parse_volume_flow(cell_value, is_flow=False)
                    if vr_data:
                        if 'min' in row_header:
                            req.vr_min = vr_data.get('min')
                        if 'max' in row_header:
                            req.vr_max = vr_data.get('max')
                elif 'n' in row_header and ('>' in row_header or 'min' in row_header):
                    # Parse N > value
                    try:
                        n_match = re.search(r'(\d+)', cell_value)
                        if n_match:
                            req.n_min = int(n_match.group(1))
                    except (ValueError, AttributeError):
                        pass
                elif 'd' in row_header and ('[/]' in row_header or 'distribucijski' in row_header):
                    # Parse D (distribution coefficient) range
                    d_data = SOPData._parse_volume_flow(cell_value, is_flow=False)
                    if d_data:
                        req.d_min = d_data.get('min')
                        req.d_max = d_data.get('max')
                
                req.raw_text = f"{row_header}: {cell_value}"
                requirements.append(req)
        
        return requirements
    
    @staticmethod
    def _parse_paragraphs(paragraphs: List[Paragraph], log: logging.Logger) -> List[SOPRequirement]:
        """Parse requirements from document paragraphs.
        
        Looks for structured text patterns like:
        - "Korak 5: Raztopina RAZT_1, volumen 100-500 mL"
        - "RAZT_1: 100-500 mL, pretok 10-50 mL/min"
        - "IPO šifra: RAZT_1"
        """
        requirements = []
        current_req = None
        
        for para in paragraphs:
            text = para.text.strip()
            if not text or len(text) < 5:
                continue
            
            # Try to match structured patterns
            # Pattern 1: "Korak X: ..."
            step_match = re.search(r'korak\s*(\d+)', text, re.IGNORECASE)
            if step_match:
                if current_req:
                    requirements.append(current_req)
                current_req = SOPRequirement(step_number=int(step_match.group(1)))
            
            # Pattern 2: IPO šifra (e.g., "IPO šifra: RAZT_1", "IPO: BASE_1")
            if not current_req:
                current_req = SOPRequirement()
            
            # Look for IPO šifra patterns
            ipo_match = re.search(r'ipo\s*[šifra:]*\s*[:]?\s*([A-Z][A-Z0-9_]+)', text, re.IGNORECASE)
            if ipo_match:
                current_req.ipo_code = ipo_match.group(1)
            
            # Pattern 3: Solution key (e.g., "RAZT_1", "BASE_1") - if no IPO found
            if not current_req.ipo_code:
                key_match = re.search(r'\b([A-Z][A-Z0-9_]+)\b', text)
                if key_match:
                    potential_key = key_match.group(1)
                    if len(potential_key) >= 3:  # Reasonable key length
                        current_req.ipo_code = potential_key
            
            # Extract volumes and flows
            volume_data = SOPData._parse_volume_flow(text, is_flow=False)
            if volume_data:
                current_req.volume_min = volume_data.get('min')
                current_req.volume_max = volume_data.get('max')
                current_req.volume_unit = volume_data.get('unit')
            
            flow_data = SOPData._parse_volume_flow(text, is_flow=True)
            if flow_data:
                current_req.flow_min = flow_data.get('min')
                current_req.flow_max = flow_data.get('max')
                current_req.flow_unit = flow_data.get('unit')
            
            current_req.raw_text += f" {text}"
        
        if current_req and (current_req.step_number or current_req.ipo_code):
            requirements.append(current_req)
        
        return requirements
    
    @staticmethod
    def _parse_volume_flow(text: str, is_flow: bool = False) -> Optional[Dict[str, Any]]:
        """Parse volume or flow from text.
        
        Supports formats:
        - "100-500 mL"
        - "100 ± 50 mL"
        - ">= 100 mL"
        - "100 mL/min"
        """
        # Unit patterns
        if is_flow:
            unit_pattern = r'(ml/min|l/min|ml/мин|l/мин)'
        else:
            unit_pattern = r'(ml|l|ml|L)'
        
        # Range pattern: "100-500 mL"
        range_pattern = rf'(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)\s*{unit_pattern}'
        match = re.search(range_pattern, text, re.IGNORECASE)
        if match:
            return {
                'min': float(match.group(1).replace(',', '.')),
                'max': float(match.group(2).replace(',', '.')),
                'unit': match.group(3).lower()
            }
        
        # ± pattern: "100 ± 50 mL"
        pm_pattern = rf'(\d+(?:[.,]\d+)?)\s*[±+/-]+\s*(\d+(?:[.,]\d+)?)\s*{unit_pattern}'
        match = re.search(pm_pattern, text, re.IGNORECASE)
        if match:
            center = float(match.group(1).replace(',', '.'))
            tolerance = float(match.group(2).replace(',', '.'))
            return {
                'min': center - tolerance,
                'max': center + tolerance,
                'unit': match.group(3).lower()
            }
        
        # Single value: "100 mL"
        single_pattern = rf'(\d+(?:[.,]\d+)?)\s*{unit_pattern}'
        match = re.search(single_pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(',', '.'))
            return {
                'min': value,
                'max': value,
                'unit': match.group(2).lower()
            }
        
        return None
    
    @staticmethod
    def _extract_ipo_codes(requirements: List[SOPRequirement], 
                          doc: DocxDocument, 
                          log: logging.Logger) -> List[str]:
        """Extract IPO šifre from requirements or dedicated sections."""
        codes = set()
        
        log.info(f"Ekstrakcija IPO šifer iz {len(requirements)} zahtev...")
        
        # From requirements - check ipo_code field
        for idx, req in enumerate(requirements):
            if req.ipo_code:
                codes.add(req.ipo_code)
                log.debug(f"  Zahteva {idx+1}: najdena IPO šifra '{req.ipo_code}'")
            else:
                log.debug(f"  Zahteva {idx+1}: ni IPO šifre v req.ipo_code")
                log.debug(f"    - raw_text: {req.raw_text[:100] if req.raw_text else '(prazno)'}")
                log.debug(f"    - description: {req.description[:100] if req.description else '(prazno)'}")
        
        # Also search in raw_text and description of requirements
        # IPO šifre might be in text even if not parsed correctly
        for idx, req in enumerate(requirements):
            if not req.ipo_code:  # Only if not already found
                # Search in raw_text
                text_to_search = f"{req.raw_text} {req.description}".strip()
                if text_to_search:
                    # Pattern: "IPO šifra: GK10" or "IPO: GK" or "GK10" (standalone)
                    ipo_patterns = [
                        r'ipo\s*[šifra:]*\s*[:]?\s*([A-Z][A-Z0-9]+)',  # "IPO šifra: GK10"
                        r'\b([A-Z]{2,}[0-9]*)\b',  # Standalone codes like "GK10", "RAZT1", "BASE2"
                    ]
                    for pattern in ipo_patterns:
                        matches = re.findall(pattern, text_to_search, re.IGNORECASE)
                        for match in matches:
                            if len(match) >= 2:  # At least 2 characters
                                codes.add(match.upper())
                                log.debug(f"  Zahteva {idx+1}: najdena IPO šifra '{match.upper()}' v besedilu")
        
        # Look for dedicated section in document
        log.debug("Iskanje IPO šifer v odstavkih dokumenta...")
        for para_idx, para in enumerate(doc.paragraphs):
            text = para.text.strip().lower()
            if 'dovoljeni ključi' in text or 'allowed keys' in text or 'ipo šifre' in text:
                log.debug(f"  Najden odsek z IPO šiframi v odstavku {para_idx+1}")
                # Next paragraphs might contain keys
                # Try to extract IPO codes from following paragraphs
                para_index = doc.paragraphs.index(para)
                for next_para in doc.paragraphs[para_index + 1:para_index + 5]:
                    para_text = next_para.text.strip()
                    # Look for patterns like "RAZT_1, RAZT_2" or "RAZT_1; RAZT_2"
                    matches = re.findall(r'\b([A-Z][A-Z0-9_]+)\b', para_text)
                    for match in matches:
                        if len(match) >= 3:
                            codes.add(match)
                            log.debug(f"    Najdena IPO šifra '{match}' v odstavku")
        
        # Also search all tables for IPO codes in any cell
        log.debug("Iskanje IPO šifer v tabelah...")
        for table_idx, table in enumerate(doc.tables):
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row.cells):
                    cell_text = cell.text.strip()
                    if cell_text:
                        # Look for IPO patterns
                        ipo_patterns = [
                            r'ipo\s*[šifra:]*\s*[:]?\s*([A-Z][A-Z0-9]+)',
                            r'\b([A-Z]{2,}[0-9]*)\b',
                        ]
                        for pattern in ipo_patterns:
                            matches = re.findall(pattern, cell_text, re.IGNORECASE)
                            for match in matches:
                                if len(match) >= 2:
                                    codes.add(match.upper())
                                    log.debug(f"  Tabela {table_idx+1}, vrstica {row_idx+1}, celica {cell_idx+1}: najdena IPO šifra '{match.upper()}'")
        
        result = sorted(list(codes))
        log.info(f"Skupaj najdenih IPO šifer: {len(result)}")
        if result:
            log.info(f"  IPO šifre: {', '.join(result)}")
        else:
            log.warning("  NISO najdene IPO šifre! Preverite strukturo SOP dokumenta.")
        
        return result
    
    @staticmethod
    def _extract_allowed_types(requirements: List[SOPRequirement],
                              doc: DocxDocument,
                              log: logging.Logger) -> List[str]:
        """Extract allowed solution types from requirements."""
        types = set()
        
        for req in requirements:
            if req.solution_type:
                types.add(req.solution_type)
        
        return sorted(list(types))
    
    @staticmethod
    def _extract_medium_from_text(paragraphs: List[Paragraph], log: logging.Logger) -> Dict[str, str]:
        """Extract medium information from paragraph text.
        
        Looks for patterns like:
        - "endotoksini se izvajajo v vodi" → medium_endotoxin = "voda"
        - "1. PM - MF: dH2O" → medium_pm1 = "dH2O"
        - "v mediju MF1" → medium = "MF1"
        
        Returns:
            Dictionary mapping phase keys to medium names
        """
        medium_map = {}
        
        # Keywords for different phases
        phase_keywords = {
            'endotoxin': ['endotoksini', 'endotoxin', 'vzorec za endotoksine', 'vzorec za meritve endotoksinov'],
            'pm1': ['1. pm', 'prva pm', 'prva pulzna motnja', '1\. pm'],
            'pm23': ['2. pm', '3. pm', 'druga pm', 'tretja pm', 'druga in tretja pm', '2\. pm', '3\. pm'],
            'tk': ['testni kromatogram', 'tk', 'kromatogram'],
        }
        
        # Medium patterns - order matters (more specific first)
        medium_patterns = [
            (r'\b(MF\s*[123]|MF[123])\b', lambda m: m.group(1).upper().replace(' ', '')),  # MF1, MF2, MF3
            (r'\b(dH\s*2O|dH2O|destilirana\s+voda)\b', lambda m: 'voda'),  # dH2O, destilirana voda
            (r'\b(H\s*2O|H2O)\b', lambda m: 'voda'),  # H2O
            (r'v\s+mediju\s+([A-Z0-9]+)', lambda m: m.group(1)),  # "v mediju MF1"
            (r'izvajajo\s+v\s+([a-z]+)', lambda m: m.group(1)),  # "izvajajo v vodi"
            (r'uporablja\s+se\s+([A-Za-z0-9]+)', lambda m: m.group(1)),  # "uporablja se MF1"
        ]
        
        for para in paragraphs:
            text = para.text.strip()
            if not text or len(text) < 10:
                continue
            
            text_lower = text.lower()
            
            # Check for phase mentions
            for phase_key, keywords in phase_keywords.items():
                if any(re.search(rf'\b{re.escape(kw)}\b', text_lower, re.IGNORECASE) for kw in keywords):
                    # Extract medium from text
                    for pattern, extractor in medium_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            try:
                                medium = extractor(match)
                                if medium and medium not in medium_map.get(phase_key, ''):
                                    medium_map[phase_key] = medium
                                    log.debug(f"Found medium for {phase_key}: {medium} in text: {text[:100]}")
                                    break
                            except (IndexError, AttributeError):
                                continue
        
        # Also check tables for medium information (e.g., "1. PM - MF: dH2O")
        # This would be done in _parse_specific_parameter_table, but we can also check here
        # by looking at table cell text
        
        return medium_map

