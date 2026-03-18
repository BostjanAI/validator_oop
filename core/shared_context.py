"""Shared context for pre-computed data across rules.

This module provides a container for data that is expensive to compute
and needs to be shared across multiple validation rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

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
            Tip objekta 'edit', 'formula', 'formula0' or 'formula1'.
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

    # Section and tab tracking
    section_by_row: dict[int, int] = field(default_factory=dict)
    tab_by_row: dict[int, str] = field(default_factory=dict)

    # Control column metadata
    control_columns: list[str] = field(default_factory=list)
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
        ctx.columns = list(columns)

        # Build column metadata
        self._build_control_columns(ctx, columns)
        self._build_param_columns(ctx, columns)

        # Build row-level data
        self._build_step_data(ctx, rows)
        self._build_checkbox_states(ctx, rows)
        self._build_keys_by_type(ctx, rows)
        self._build_section_and_tab(ctx, rows)
        self._build_zakleni_data(ctx, rows)

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

    def _build_step_data(self, ctx: SharedContext, rows: Sequence[Mapping[str, Any]]) -> None:
        """Build step number mappings and allowed formula reference targets."""
        for idx, row in enumerate(rows):
            excel_row = idx + self._row_offset
            step_val = coerce_str(row.get("št. Koraka", ""))
            if not step_val:
                continue
            try:
                step_num = int(step_val)
                ctx.existing_steps.add(step_num)
                ctx.step_to_row_indices.setdefault(step_num, []).append(excel_row)
                # Formula fields may reference edit and other formula-type objects.
                tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
                if tip_obj in {"edit", "formula", "formula0", "formula1"}:
                    ctx.step_allowed_for_formula_ref.add(step_num)
            except ValueError:
                pass

    def _build_checkbox_states(self, ctx: SharedContext, rows: Sequence[Mapping[str, Any]]) -> None:
        """Build checkbox state mapping."""
        for row in rows:
            tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
            if tip_obj != "checkbox":
                continue
            key = coerce_str(row.get("Ključ preverjanja", ""))
            if not key:
                continue
            value = coerce_str(row.get("Vrednost", ""))
            ctx.checkbox_states[key] = parse_checkbox_state(value)

    def _build_keys_by_type(self, ctx: SharedContext, rows: Sequence[Mapping[str, Any]]) -> None:
        """Build keys grouped by data type."""
        for idx, row in enumerate(rows):
            excel_row = idx + self._row_offset
            tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))
            key = coerce_str(row.get("Ključ preverjanja", ""))
            if not tip_data or not key:
                continue
            ctx.keys_by_type.setdefault(tip_data, {}).setdefault(key, []).append(excel_row)
            if is_equipment_tip(row.get("Tip podatka", "")):
                ctx.equipment_keys.add(key)

    def _build_section_and_tab(self, ctx: SharedContext, rows: Sequence[Mapping[str, Any]]) -> None:
        """Build section and tab mappings."""
        current_section = 0
        current_tab = ""

        for idx, row in enumerate(rows):
            excel_row = idx + self._row_offset
            tip_obj = norm_text(coerce_str(row.get("Tip objekta", "")))
            tip_data = norm_text(coerce_str(row.get("Tip podatka", "")))

            # New section on 'naslov'
            if tip_obj == "naslov" or tip_data == "naslov":
                current_section += 1

            ctx.section_by_row[excel_row] = current_section

            # Update tab
            tab_val = coerce_str(row.get("Zavihek", "")).strip()
            if tab_val:
                current_tab = tab_val
            ctx.tab_by_row[excel_row] = current_tab

    def _build_zakleni_data(self, ctx: SharedContext, rows: Sequence[Mapping[str, Any]]) -> None:
        """Build zaklenipolja-specific data."""
        for idx, row in enumerate(rows):
            excel_row = idx + self._row_offset
            tab = ctx.tab_by_row.get(excel_row, "")

            # Get step number for this row
            step_val = coerce_str(row.get("št. Koraka", ""))
            try:
                step_num = int(step_val) if step_val else None
            except ValueError:
                step_num = None

            # Scan control columns
            for ctrl_col in ctx.control_columns:
                ctrl_name_raw = coerce_str(row.get(ctrl_col, ""))
                if not ctrl_name_raw:
                    continue

                ctrl_name_ns = norm_control_name(ctrl_name_raw)

                # Track controls at each step
                if step_num is not None:
                    ctx.step_to_controls.setdefault(step_num, set()).add(ctrl_name_ns)

                # Extract control number
                ctrl_num_match = re.findall(r"\d+", ctrl_col.lower())
                ctrl_num = int(ctrl_num_match[0]) if ctrl_num_match else 0

                if ctrl_name_ns == "zaklenipolja":
                    p1_col = ctx.param1_columns.get(ctrl_num)
                    if p1_col:
                        p1_val = coerce_str(row.get(p1_col, ""))
                        key_here = coerce_str(row.get("Ključ preverjanja", ""))
                        if key_here:
                            ctx.all_zakleni_keys.add(key_here)

                        # Parse Param1 as comma-separated integers
                        if p1_val and has_only_comma_separated_ints(p1_val):
                            for tok in p1_val.split(","):
                                tok = tok.strip()
                                if tok:
                                    try:
                                        ref_step = int(tok)
                                        ctx.zakleni_param1_steps.add(ref_step)
                                        ctx.zakleni_param1_steps_by_tab.setdefault(tab, set()).add(ref_step)
                                        if key_here:
                                            ctx.keys_by_zakleni_step.setdefault(ref_step, set()).add(key_here)
                                    except ValueError:
                                        pass

                elif ctrl_name_ns == "aliobstajapogoj":
                    if step_num is None:
                        continue

                    # Backward compatible: keep the first location globally
                    if step_num not in ctx.ali_pogoj_step_locations:
                        ctx.ali_pogoj_step_locations[step_num] = (excel_row, ctrl_col)

                    # Tab-aware: keep all occurrences per tab
                    ctx.ali_pogoj_step_locations_by_tab.setdefault(tab, {}).setdefault(step_num, []).append(
                        (excel_row, ctrl_col)
                    )

                    # Store (step, key) -> Param2 for odvečni koraki check
                    p1_col = ctx.param1_columns.get(ctrl_num)
                    p2_col = ctx.param2_columns.get(ctrl_num)
                    if p1_col and p2_col:
                        p1_val = coerce_str(row.get(p1_col, ""))
                        p2_val = coerce_str(row.get(p2_col, ""))
                        try:
                            parsed_p2 = int(float(p2_val.replace(",", ".")))
                        except Exception:
                            parsed_p2 = None
                        if p1_val and parsed_p2 is not None:
                            for key in [k.strip() for k in p1_val.split(",") if k.strip()]:
                                ctx.step_key_param2[(step_num, key)] = parsed_p2

