"""Pytest configuration and shared fixtures.

This module provides common test fixtures used across all test modules.
"""

from __future__ import annotations

from typing import Any

import pytest

from validator_oop.core.config import ValidatorConfig
from validator_oop.core.shared_context import SharedContext, SharedContextBuilder
from validator_oop.rules.base_rule import RuleContext
from validator_oop.rules.rule_registry import RuleRegistry


# =============================================================================
# Sample Row Data Fixtures
# =============================================================================


@pytest.fixture
def sample_columns() -> list[str]:
    """Standard column names for MES validation."""
    return [
        "št. Koraka",
        "Tip objekta",
        "Tip podatka",
        "Ključ preverjanja",
        "Vrednost",
        "Navodilo",
        "Zavihek",
        "Kontrola-1",
        "Kontrola-1: Par 1",
        "Kontrola-1: Par 2",
        "Kontrola-2",
        "Kontrola-2: Par 1",
        "Kontrola-2: Par 2",
    ]


@pytest.fixture
def empty_row() -> dict[str, Any]:
    """An empty row with all standard columns."""
    return {
        "št. Koraka": "",
        "Tip objekta": "",
        "Tip podatka": "",
        "Ključ preverjanja": "",
        "Vrednost": "",
        "Navodilo": "",
        "Zavihek": "",
        "Kontrola-1": "",
        "Kontrola-1: Par 1": "",
        "Kontrola-1: Par 2": "",
        "Kontrola-2": "",
        "Kontrola-2: Par 1": "",
        "Kontrola-2: Par 2": "",
    }


@pytest.fixture
def valid_row() -> dict[str, Any]:
    """A valid row with typical values."""
    return {
        "št. Koraka": "1",
        "Tip objekta": "edit",
        "Tip podatka": "kemijski",
        "Ključ preverjanja": "TEST_KEY_1",
        "Vrednost": "100",
        "Navodilo": "Enter value",
        "Zavihek": "Tab1",
        "Kontrola-1": "",
        "Kontrola-1: Par 1": "",
        "Kontrola-1: Par 2": "",
        "Kontrola-2": "",
        "Kontrola-2: Par 1": "",
        "Kontrola-2: Par 2": "",
    }


@pytest.fixture
def checkbox_row() -> dict[str, Any]:
    """A checkbox row."""
    return {
        "št. Koraka": "2",
        "Tip objekta": "checkbox",
        "Tip podatka": "",
        "Ključ preverjanja": "CHECKBOX_KEY",
        "Vrednost": "1",
        "Navodilo": "",
        "Zavihek": "Tab1",
        "Kontrola-1": "",
        "Kontrola-1: Par 1": "",
        "Kontrola-1: Par 2": "",
        "Kontrola-2": "",
        "Kontrola-2: Par 1": "",
        "Kontrola-2: Par 2": "",
    }


@pytest.fixture
def equipment_row() -> dict[str, Any]:
    """An equipment row."""
    return {
        "št. Koraka": "3",
        "Tip objekta": "edit",
        "Tip podatka": "oprema",
        "Ključ preverjanja": "EQUIP_KEY_1",
        "Vrednost": "",
        "Navodilo": "Select equipment",
        "Zavihek": "Tab1",
        "Kontrola-1": "",
        "Kontrola-1: Par 1": "",
        "Kontrola-1: Par 2": "",
        "Kontrola-2": "",
        "Kontrola-2: Par 1": "",
        "Kontrola-2: Par 2": "",
    }


@pytest.fixture
def control_row() -> dict[str, Any]:
    """A row with control configuration."""
    return {
        "št. Koraka": "4",
        "Tip objekta": "edit",
        "Tip podatka": "kemijski",
        "Ključ preverjanja": "CTRL_KEY_1",
        "Vrednost": "50",
        "Navodilo": "Check value",
        "Zavihek": "Tab1",
        "Kontrola-1": "kontrolaIntervala",
        "Kontrola-1: Par 1": "10",
        "Kontrola-1: Par 2": "100",
        "Kontrola-2": "",
        "Kontrola-2: Par 1": "",
        "Kontrola-2: Par 2": "",
    }


@pytest.fixture
def zakleni_row() -> dict[str, Any]:
    """A row with zaklenipolja control."""
    return {
        "št. Koraka": "5",
        "Tip objekta": "edit",
        "Tip podatka": "kemijski",
        "Ključ preverjanja": "ZAKLENI_KEY",
        "Vrednost": "",
        "Navodilo": "",
        "Zavihek": "Tab1",
        "Kontrola-1": "zaklenipolja",
        "Kontrola-1: Par 1": "1,2,3",
        "Kontrola-1: Par 2": "",
        "Kontrola-2": "",
        "Kontrola-2: Par 1": "",
        "Kontrola-2: Par 2": "",
    }


# =============================================================================
# Multi-Row Fixtures
# =============================================================================


@pytest.fixture
def sample_rows(
    valid_row: dict[str, Any],
    checkbox_row: dict[str, Any],
    equipment_row: dict[str, Any],
) -> list[dict[str, Any]]:
    """A list of sample rows for testing."""
    return [valid_row, checkbox_row, equipment_row]


@pytest.fixture
def rows_with_duplicates() -> list[dict[str, Any]]:
    """Rows with duplicate keys for testing duplicate detection."""
    return [
        {
            "št. Koraka": "1",
            "Tip objekta": "edit",
            "Tip podatka": "kemijski",
            "Ključ preverjanja": "KEY_1",
            "Vrednost": "100",
        },
        {
            "št. Koraka": "2",
            "Tip objekta": "edit",
            "Tip podatka": "kemijski",
            "Ključ preverjanja": "KEY_2",
            "Vrednost": "200",
        },
        {
            "št. Koraka": "3",
            "Tip objekta": "edit",
            "Tip podatka": "kemijski",
            "Ključ preverjanja": "KEY_1",  # Duplicate!
            "Vrednost": "300",
        },
    ]


@pytest.fixture
def rows_with_step_gaps() -> list[dict[str, Any]]:
    """Rows with gaps in step numbering."""
    return [
        {"št. Koraka": "1", "Tip objekta": "edit", "Tip podatka": "kemijski"},
        {"št. Koraka": "2", "Tip objekta": "edit", "Tip podatka": "kemijski"},
        {"št. Koraka": "5", "Tip objekta": "edit", "Tip podatka": "kemijski"},  # Gap!
        {"št. Koraka": "6", "Tip objekta": "edit", "Tip podatka": "kemijski"},
    ]


@pytest.fixture
def rows_with_controls() -> list[dict[str, Any]]:
    """Rows with various control configurations."""
    return [
        {
            "št. Koraka": "1",
            "Tip objekta": "edit",
            "Tip podatka": "kemijski",
            "Ključ preverjanja": "KEY_1",
            "Kontrola-1": "kontrolaIntervala",
            "Kontrola-1: Par 1": "10",
            "Kontrola-1: Par 2": "100",
        },
        {
            "št. Koraka": "2",
            "Tip objekta": "edit",
            "Tip podatka": "kemijski",
            "Ključ preverjanja": "KEY_2",
            "Kontrola-1": "zaklenipolja",
            "Kontrola-1: Par 1": "1",
            "Kontrola-1: Par 2": "",
        },
        {
            "št. Koraka": "3",
            "Tip objekta": "edit",
            "Tip podatka": "kemijski",
            "Ključ preverjanja": "KEY_3",
            "Kontrola-1": "aliObstajaPogoj",
            "Kontrola-1: Par 1": "KEY_1",
            "Kontrola-1: Par 2": "1",
        },
    ]


# =============================================================================
# Context and Configuration Fixtures
# =============================================================================


@pytest.fixture
def rule_context() -> RuleContext:
    """A basic rule context."""
    return RuleContext(sheet="TestSheet", workbook="test.xlsx")


@pytest.fixture
def default_config() -> ValidatorConfig:
    """Default validator configuration."""
    return ValidatorConfig()


@pytest.fixture
def strict_config() -> ValidatorConfig:
    """Strict mode configuration."""
    return ValidatorConfig(strict_mode=True)


@pytest.fixture
def bypass_config() -> ValidatorConfig:
    """Configuration with some rules bypassed."""
    return ValidatorConfig(
        bypass_rules=frozenset(["RequiredColumnsRule", "StepNumberingRule"]),
        bypass_codes=frozenset(["MANJKA_STOLPEC", "KORAK_PRESLEDKI"]),
    )


# =============================================================================
# SharedContext Fixtures
# =============================================================================


@pytest.fixture
def empty_shared_context() -> SharedContext:
    """An empty shared context."""
    return SharedContext()


@pytest.fixture
def shared_context_builder() -> SharedContextBuilder:
    """A shared context builder with default settings."""
    return SharedContextBuilder(row_offset=2)


@pytest.fixture
def populated_shared_context(
    sample_rows: list[dict[str, Any]],
    sample_columns: list[str],
    shared_context_builder: SharedContextBuilder,
) -> SharedContext:
    """A shared context populated with sample data."""
    return shared_context_builder.build(sample_rows, sample_columns)


# =============================================================================
# Registry Fixtures
# =============================================================================


@pytest.fixture
def empty_registry() -> RuleRegistry:
    """An empty rule registry."""
    return RuleRegistry()


@pytest.fixture
def populated_registry() -> RuleRegistry:
    """A registry with built-in rules registered."""
    from validator_oop.rules.builtin import register_all
    from validator_oop.rules.rule_registry import default_registry

    # Ensure built-in rules are registered
    register_all()
    return default_registry


# =============================================================================
# Workbook Data Fixtures
# =============================================================================


@pytest.fixture
def single_sheet_workbook(sample_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """A workbook with a single sheet."""
    return {"Sheet1": sample_rows}


@pytest.fixture
def multi_sheet_workbook(
    sample_rows: list[dict[str, Any]],
    rows_with_controls: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """A workbook with multiple sheets."""
    return {
        "Sheet1": sample_rows,
        "Sheet2": rows_with_controls,
    }


# =============================================================================
# Helper Functions
# =============================================================================


def make_row(**kwargs: Any) -> dict[str, Any]:
    """Create a row dictionary with specified values.

    Args:
        **kwargs: Column name -> value mappings.

    Returns:
        Row dictionary with empty strings for missing columns.
    """
    base = {
        "št. Koraka": "",
        "Tip objekta": "",
        "Tip podatka": "",
        "Ključ preverjanja": "",
        "Vrednost": "",
        "Navodilo": "",
        "Zavihek": "",
        "Kontrola-1": "",
        "Kontrola-1: Par 1": "",
        "Kontrola-1: Par 2": "",
        "Kontrola-2": "",
        "Kontrola-2: Par 1": "",
        "Kontrola-2: Par 2": "",
    }
    base.update(kwargs)
    return base


def make_rows(*row_dicts: dict[str, Any]) -> list[dict[str, Any]]:
    """Create multiple rows from dictionaries.

    Args:
        *row_dicts: Dictionaries with column values.

    Returns:
        List of row dictionaries.
    """
    return [make_row(**rd) for rd in row_dicts]

