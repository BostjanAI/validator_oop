"""Shared context for pre-computed data across rules.

This module provides a container for data that is expensive to compute
and needs to be shared across multiple validation rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from validator_oop.core.constants import (
    FORMULA_REF_ALLOWED_OBJECT_TYPES,
    VALIDATION_EXCLUDED_COLUMNS,
)
from validator_oop.utils.helpers import (
    coerce_str,
    has_only_comma_separated_ints,
    is_equipment_tip,
    norm_control_name,
    norm_text,
    parse_checkbox_state,
)


@dataclass(slots=True)
class SharedContext:
    """Pre-computed data shared across all rules during validation.

    This context is built once before rule execution and injected into
    every rule. Rules can read from it but should not modify it.

    Attributes:
        checkbox_states: Mapping of key -> checkbox state (1=checked, 0=unchecked, None=unknown).
        step_to_controls: Mapping of step number -> set of normalized control names.
        step_to_row_indices: Mapping of step number -> list of Excel row indices.
        keys_by_type: Mapping of data type -> key -> list of Excel row indices.
        section_by_row: Mapping of Excel row index -> section ID (based on 'naslov' rows).
        tab_by_row: Mapping of Excel row index -> tab name (from 'Zavihek' column).
        control_columns: Ordered list of control column names.
        param1_columns: Mapping of control number -> Param1 column name.
        param2_columns: Mapping of control number -> Param2 column name.
        existing_steps: Set of all valid step numbers in the sheet.
        step_allowed_for_formula_ref: Set of steps that have at least one row with
            Tip objekta in FORMULA_REF_ALLOWED_OBJECT_TYPES (edit, formula, formula0,
            formula1, klictehtnice1).
        zakleni_param1_steps: Set of steps referenced by 'zaklenipolja' Param1.
        zakleni_param1_steps_by_tab: Mapping of tab -> set of steps referenced by 'zaklenipolja' Param1.
        ali_pogoj_step_locations: Mapping of step -> (row, column) for 'aliObstajaPogoj'.
        ali_pogoj_step_locations_by_tab: Mapping of tab -> step -> list[(row, column)] for 'aliObstajaPogoj'.
        extra: Additional arbitrary pre-computed data.
    """

    # Columns present in the sheet
    columns: list[str] = field(default_factory=list)

    # Checkbox states by key
    checkbox_states: dict[str, int | None] = field(default_factory=dict)

    # Step -> controls mapping
    step_to_controls: dict[int, set[str]] = field(default_factory=dict)
    step_to_row_indices: dict[int, list[int]] = field(default_factory=dict)

    # Keys grouped by data type
    keys_by_type: dict[str, dict[str, list[int]]] = field(default_factory=dict)
    keys_with_value_by_type: dict[str, set[str]] = field(default_factory=dict)

    # Section and tab tracking
    section_by_row: dict[int, int] = field(default_factory=dict)
    tab_by_row: dict[int, str] = field(default_factory=dict)

    # Control column metadata
    control_columns: list[str] = field(default_factory=list)
    control_numbers: dict[str, int | None] = field(default_factory=dict)
    param1_columns: dict[int, str] = field(default_factory=dict)
    param2_columns: dict[int, str] = field(default_factory=dict)

    # Step validation
    existing_steps: set[int] = field(default_factory=set)
    # Steps that can be referenced from formula fields.
    step_allowed_for_formula_ref: set[int] = field(default_factory=set)

    # zaklenipolja specific
    zakleni_param1_steps: set[int] = field(default_factory=set)
    zakleni_param1_steps_by_tab: dict[str, set[int]] = field(default_factory=dict)
    ali_pogoj_step_locations: dict[int, tuple[int, str]] = field(default_factory=dict)
    ali_pogoj_step_locations_by_tab: dict[str, dict[int, list[tuple[int, str]]]] = field(default_factory=dict)
    keys_by_zakleni_step: dict[int, set[str]] = field(default_factory=dict)
    all_zakleni_keys: set[str] = field(default_factory=set)
    # (step, key) -> Param2 value (0 or 1) for aliObstajaPogoj on that step; used to detect odvečni koraki in zaklenipolja Param1
    step_key_param2: dict[tuple[int, str], int] = field(default_factory=dict)
    equipment_keys: set[str] = field(default_factory=set)

    # Extension point
    extra: dict[str, Any] = field(default_factory=dict)

    def get_keys_for_type(self, data_type: str) -> dict[str, list[int]]:
        """Get all keys and their row indices for a specific data type."""
        return self.keys_by_type.get(data_type, {})

    def get_keys_with_value_for_type(self, data_type: str) -> set[str]:
        """Get keys for a specific type where column 'Vrednost' is non-empty."""
        return self.keys_with_value_by_type.get(data_type, set())

    def has_step(self, step: int) -> bool:
        """Check if a step number exists."""
        return step in self.existing_steps

    def get_controls_at_step(self, step: int) -> set[str]:
        """Get normalized control names at a specific step."""
        return self.step_to_controls.get(step, set())


class SharedContextBuilder:
    """Builds SharedContext from workbook data.

    This class encapsulates the pre-processing logic that was previously
    scattered throughout the monolithic validate_dataframe function.
    """

    def __init__(self, *, row_offset: int = 2) -> None:
        self._row_offset = row_offset

    def build(
        self,
        rows: Sequence[Mapping[str, Any]],
        columns: Sequence[str],
    ) -> SharedContext:
        """Build a SharedContext from sheet data.

        Args:
            rows: Sequence of row dictionaries.
            columns: List of column names in the sheet.

        Returns:
            Populated SharedContext instance.
        """
        ctx = SharedContext()
        effective_columns = [c for c in columns if c not in VALIDATION_EXCLUDED_COLUMNS]
        ctx.columns = list(effective_columns)

        # Build column metadata
        self._build_control_columns(ctx, effective_columns)
        self._build_param_columns(ctx, effective_columns)

        # Build row-level data
        self._build_row_level_data(ctx, rows)

        return ctx

    def _build_control_columns(self, ctx: SharedContext, columns: Sequence[str]) -> None:
        """Extract control column names."""
        for col in columns:
            if not isinstance(col, str):
                continue
            head = col.lower().strip()
            if re.fullmatch(r"kontrola\s*[-–:]?\s*\d+\s*", head, flags=re.I):
                ctx.control_columns.append(col)

        # Sort by control number
        def extract_num(c: str) -> int:
            m = re.findall(r"\d+", c.lower())
            return int(m[0]) if m else 0

        ctx.control_columns.sort(key=extract_num)
        ctx.control_numbers = {col: extract_num(col) for col in ctx.control_columns}

    def _build_param_columns(self, ctx: SharedContext, columns: Sequence[str]) -> None:
        """Extract Param1 and Param2 column mappings."""
        # Patterns for Param1 columns like "Kontrola-1: Par 1" or "Kontrola 1: Param 1"
        par1_patterns = [
            re.compile(r"^kontrola[-\s]*(?P<n>\d+)\s*[:]\s*par(?:am)?\s*1\s*$", re.I),
            re.compile(r"^kontrola\s*(?P<n>\d+)\s*(?:[-–:])?\s*par(?:am)?\s*1\s*$", re.I),
            re.compile(r"^p(?:ar|aram|m)\s*1\s*[,._-]?\s*(?P<n>\d+)\s*$", re.I),
        ]
        # Patterns for Param2 columns like "Kontrola-1: Par 2" or "Kontrola 1: Param 2"
        par2_patterns = [
            re.compile(r"^kontrola[-\s]*(?P<n>\d+)\s*[:]\s*par(?:am)?\s*2\s*$", re.I),
            re.compile(r"^kontrola\s*(?P<n>\d+)\s*(?:[-–:])?\s*par(?:am)?\s*2\s*$", re.I),
            re.compile(r"^p(?:ar|aram|m)\s*2\s*[,._-]?\s*(?P<n>\d+)\s*$", re.I),
        ]

        for col in columns:
            if not isinstance(col, str):
                continue
            head = col.strip()

            for pat in par1_patterns:
                m = pat.match(head)
                if m:
                    try:
                        ctx.param1_columns[int(m.group("n"))] = col
                    except (ValueError, IndexError):
                        pass
                    break

            for pat in par2_patterns:
                m = pat.match(head)
                if m:
                    try:
                        ctx.param2_columns[int(m.group("n"))] = col
                    except (ValueError, IndexError):
                        pass
                    break

    def _build_row_level_data(self, ctx: SharedContext, rows: Sequence[Mapping[str, Any]]) -> None:
        """Build all row-derived indexes in a single pass."""
        current_section = 0
        current_tab = ""

        for idx, row in enumerate(rows):
            excel_row = idx + self._row_offset
            tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
            tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
            key = coerce_str(row.get("Ključ preverjanja", ""))
            value = coerce_str(row.get("Vrednost", ""))

            step_num = self._parse_step_number(row)
            if step_num is not None:
                ctx.existing_steps.add(step_num)
                ctx.step_to_row_indices.setdefault(step_num, []).append(excel_row)
                if tip_obj in FORMULA_REF_ALLOWED_OBJECT_TYPES:
                    ctx.step_allowed_for_formula_ref.add(step_num)

            if tip_obj == "checkbox" and key:
                ctx.checkbox_states[key] = parse_checkbox_state(value)

            if tip_data and key:
                ctx.keys_by_type.setdefault(tip_data, {}).setdefault(key, []).append(excel_row)
                if value.strip():
                    ctx.keys_with_value_by_type.setdefault(tip_data, set()).add(key)
                if is_equipment_tip(row.get("Tip podatka", "")):
                    ctx.equipment_keys.add(key)

            # New section on 'naslov'
            if tip_obj == "naslov" or tip_data == "naslov":
                current_section += 1

            ctx.section_by_row[excel_row] = current_section

            # Update tab
            tab_val = coerce_str(row.get("Zavihek", "")).strip()
            if tab_val:
                current_tab = tab_val
            ctx.tab_by_row[excel_row] = current_tab
            self._scan_row_controls(ctx, row, excel_row, current_tab, step_num, key)

    def _scan_row_controls(
        self,
        ctx: SharedContext,
        row: Mapping[str, Any],
        excel_row: int,
        tab: str,
        step_num: int | None,
        key_here: str,
    ) -> None:
        for ctrl_col in ctx.control_columns:
            ctrl_name_raw = coerce_str(row.get(ctrl_col, ""))
            if not ctrl_name_raw:
                continue

            ctrl_name_ns = norm_control_name(ctrl_name_raw)
            if step_num is not None:
                ctx.step_to_controls.setdefault(step_num, set()).add(ctrl_name_ns)

            ctrl_num = ctx.control_numbers.get(ctrl_col, 0) or 0

            if ctrl_name_ns == "zaklenipolja":
                self._scan_zakleni_control(ctx, row, tab, ctrl_num, key_here)
            elif ctrl_name_ns == "aliobstajapogoj" and step_num is not None:
                self._scan_aliobstajapogoj_control(ctx, row, excel_row, tab, step_num, ctrl_col, ctrl_num)

    def _scan_zakleni_control(
        self,
        ctx: SharedContext,
        row: Mapping[str, Any],
        tab: str,
        ctrl_num: int,
        key_here: str,
    ) -> None:
        p1_col = ctx.param1_columns.get(ctrl_num)
        if not p1_col:
            return

        p1_val = coerce_str(row.get(p1_col, ""))
        if key_here:
            ctx.all_zakleni_keys.add(key_here)

        if not p1_val or not has_only_comma_separated_ints(p1_val):
            return

        for tok in p1_val.split(","):
            tok = tok.strip()
            if not tok:
                continue
            try:
                ref_step = int(tok)
            except ValueError:
                continue
            ctx.zakleni_param1_steps.add(ref_step)
            ctx.zakleni_param1_steps_by_tab.setdefault(tab, set()).add(ref_step)
            if key_here:
                ctx.keys_by_zakleni_step.setdefault(ref_step, set()).add(key_here)

    def _scan_aliobstajapogoj_control(
        self,
        ctx: SharedContext,
        row: Mapping[str, Any],
        excel_row: int,
        tab: str,
        step_num: int,
        ctrl_col: str,
        ctrl_num: int,
    ) -> None:
        if step_num not in ctx.ali_pogoj_step_locations:
            ctx.ali_pogoj_step_locations[step_num] = (excel_row, ctrl_col)

        ctx.ali_pogoj_step_locations_by_tab.setdefault(tab, {}).setdefault(step_num, []).append(
            (excel_row, ctrl_col)
        )

        p1_col = ctx.param1_columns.get(ctrl_num)
        p2_col = ctx.param2_columns.get(ctrl_num)
        if not p1_col or not p2_col:
            return

        p1_val = coerce_str(row.get(p1_col, ""))
        p2_val = coerce_str(row.get(p2_col, ""))
        try:
            parsed_p2 = int(float(p2_val.replace(",", ".")))
        except Exception:
            parsed_p2 = None
        if p1_val and parsed_p2 is not None:
            for key in [k.strip() for k in p1_val.split(",") if k.strip()]:
                ctx.step_key_param2[(step_num, key)] = parsed_p2

    def _parse_step_number(self, row: Mapping[str, Any]) -> int | None:
        step_val = coerce_str(row.get("št. Koraka", ""))
        if not step_val:
            return None
        try:
            return int(step_val)
        except ValueError:
            return None

