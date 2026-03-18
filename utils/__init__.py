"""Utility modules.

This package provides utility functions and helpers:
- logger: Logging configuration
- file_paths: File path utilities
- helpers: String normalization, parsing, and validation utilities
"""

from validator_oop.utils.helpers import (
    base_key_no_trailing_number,
    coerce_str,
    decimal_places_of_first_number,
    decimals_from_eps,
    derive_decimal_step_from_text,
    eq_with_decimals,
    extract_suffix_number,
    extract_unit_token,
    extract_unit_token_near_number,
    has_only_comma_separated_ints,
    is_equipment_row,
    is_equipment_tip,
    is_excel_error_token,
    is_water_key,
    looks_like_number_with_commas,
    max_decimals,
    norm_control_name,
    norm_text,
    normalize_column_names,
    parse_checkbox_state,
    column_letter_to_number,
    find_row_by_match,
    get_cell_value_from_workbook,
    parse_index_match_formula,
    parse_navodilo_inequality,
    parse_navodilo_interval,
    parse_navodilo_pm,
    parse_navodilo_single,
    parse_numeric_value,
    parse_time_lower_bound_from_navodilo,
    parse_time_phrase_to_seconds,
    parse_time_range_from_navodilo,
    split_key_number,
)
from validator_oop.utils.logger import get_logger, LoggerMixin, setup_logger

__all__ = [
    # Logger
    "get_logger",
    "LoggerMixin",
    "setup_logger",
    # String normalization
    "coerce_str",
    "norm_text",
    "norm_control_name",
    "normalize_column_names",
    # Checkbox
    "parse_checkbox_state",
    "has_only_comma_separated_ints",
    # Key manipulation
    "base_key_no_trailing_number",
    "extract_suffix_number",
    "split_key_number",
    "is_water_key",
    # Equipment detection
    "is_equipment_tip",
    "is_equipment_row",
    # Excel errors
    "is_excel_error_token",
    "looks_like_number_with_commas",
    # Time parsing
    "parse_time_phrase_to_seconds",
    "parse_time_range_from_navodilo",
    "parse_time_lower_bound_from_navodilo",
    # Numeric parsing
    "parse_numeric_value",
    "decimal_places_of_first_number",
    "derive_decimal_step_from_text",
    "decimals_from_eps",
    "eq_with_decimals",
    "max_decimals",
    # Unit extraction
    "extract_unit_token",
    "extract_unit_token_near_number",
    # Navodilo parsing
    "parse_navodilo_interval",
    "parse_navodilo_pm",
    "parse_navodilo_inequality",
    "parse_navodilo_single",
    # Excel formula parsing
    "parse_index_match_formula",
    "column_letter_to_number",
    "find_row_by_match",
    "get_cell_value_from_workbook",
]

