"""Tests for SharedContext and SharedContextBuilder.

This module tests the shared context infrastructure that pre-computes
data for validation rules.
"""

from __future__ import annotations

from typing import Any

import pytest

from validator_oop.core.shared_context import SharedContext, SharedContextBuilder


class TestSharedContext:
    """Tests for SharedContext dataclass."""

    def test_empty_context(self) -> None:
        """Test that empty context has default values."""
        ctx = SharedContext()

        assert ctx.columns == []
        assert ctx.checkbox_states == {}
        assert ctx.step_to_controls == {}
        assert ctx.step_to_row_indices == {}
        assert ctx.keys_by_type == {}
        assert ctx.keys_with_value_by_type == {}
        assert ctx.section_by_row == {}
        assert ctx.tab_by_row == {}
        assert ctx.control_columns == []
        assert ctx.control_numbers == {}
        assert ctx.param1_columns == {}
        assert ctx.param2_columns == {}
        assert ctx.existing_steps == set()
        assert ctx.zakleni_param1_steps == set()
        assert ctx.ali_pogoj_step_locations == {}
        assert ctx.keys_by_zakleni_step == {}
        assert ctx.all_zakleni_keys == set()
        assert ctx.extra == {}

    def test_get_keys_for_type(self) -> None:
        """Test get_keys_for_type method."""
        ctx = SharedContext()
        ctx.keys_by_type = {
            "kemijski": {"KEY_1": [2, 3], "KEY_2": [4]},
            "raztopine": {"RAZT_1": [5]},
        }

        assert ctx.get_keys_for_type("kemijski") == {"KEY_1": [2, 3], "KEY_2": [4]}
        assert ctx.get_keys_for_type("raztopine") == {"RAZT_1": [5]}
        assert ctx.get_keys_for_type("nonexistent") == {}

    def test_get_keys_with_value_for_type(self) -> None:
        """Test get_keys_with_value_for_type method."""
        ctx = SharedContext()
        ctx.keys_with_value_by_type = {
            "masa": {"MASA_1", "MASA_3"},
            "kemijski": {"KEM_1"},
        }

        assert ctx.get_keys_with_value_for_type("masa") == {"MASA_1", "MASA_3"}
        assert ctx.get_keys_with_value_for_type("kemijski") == {"KEM_1"}
        assert ctx.get_keys_with_value_for_type("nonexistent") == set()

    def test_has_step(self) -> None:
        """Test has_step method."""
        ctx = SharedContext()
        ctx.existing_steps = {1, 2, 3, 5}

        assert ctx.has_step(1) is True
        assert ctx.has_step(2) is True
        assert ctx.has_step(4) is False
        assert ctx.has_step(5) is True

    def test_get_controls_at_step(self) -> None:
        """Test get_controls_at_step method."""
        ctx = SharedContext()
        ctx.step_to_controls = {
            1: {"kontrolaintervala", "zaklenipolja"},
            2: {"aliobstajapogoj"},
        }

        assert ctx.get_controls_at_step(1) == {"kontrolaintervala", "zaklenipolja"}
        assert ctx.get_controls_at_step(2) == {"aliobstajapogoj"}
        assert ctx.get_controls_at_step(3) == set()


class TestSharedContextBuilder:
    """Tests for SharedContextBuilder."""

    @pytest.fixture
    def builder(self) -> SharedContextBuilder:
        """Create a SharedContextBuilder with default settings."""
        return SharedContextBuilder(row_offset=2)

    def test_build_empty(self, builder: SharedContextBuilder) -> None:
        """Test building context from empty data."""
        ctx = builder.build([], [])

        assert ctx.columns == []
        assert ctx.existing_steps == set()

    def test_build_columns(self, builder: SharedContextBuilder) -> None:
        """Test that columns are stored correctly."""
        columns = ["št. Koraka", "Tip objekta", "Ključ preverjanja"]
        ctx = builder.build([], columns)

        assert ctx.columns == columns

    def test_build_excludes_column_0_from_validation(self, builder: SharedContextBuilder) -> None:
        """Placeholder column_0 (prazen naslov) ne sme biti v kontekstu validacije."""
        columns = ["column_0", "št. Koraka", "Vrednost"]
        ctx = builder.build([], columns)

        assert ctx.columns == ["št. Koraka", "Vrednost"]
        assert "column_0" not in ctx.columns

    def test_build_control_columns(self, builder: SharedContextBuilder) -> None:
        """Test extraction of control columns."""
        columns = [
            "št. Koraka",
            "Kontrola-1",
            "Kontrola-2",
            "Kontrola-10",
            "Other Column",
        ]
        ctx = builder.build([], columns)

        assert "Kontrola-1" in ctx.control_columns
        assert "Kontrola-2" in ctx.control_columns
        assert "Kontrola-10" in ctx.control_columns
        assert "Other Column" not in ctx.control_columns

    def test_build_control_columns_sorted(self, builder: SharedContextBuilder) -> None:
        """Test that control columns are sorted by number."""
        columns = ["Kontrola-10", "Kontrola-2", "Kontrola-1"]
        ctx = builder.build([], columns)

        assert ctx.control_columns == ["Kontrola-1", "Kontrola-2", "Kontrola-10"]
        assert ctx.control_numbers == {
            "Kontrola-1": 1,
            "Kontrola-2": 2,
            "Kontrola-10": 10,
        }

    def test_build_param_columns(self, builder: SharedContextBuilder) -> None:
        """Test extraction of param columns."""
        columns = [
            "Kontrola-1",
            "Kontrola-1: Par 1",
            "Kontrola-1: Par 2",
            "Kontrola-2",
            "Kontrola-2: Par 1",
        ]
        ctx = builder.build([], columns)

        assert ctx.param1_columns.get(1) == "Kontrola-1: Par 1"
        assert ctx.param2_columns.get(1) == "Kontrola-1: Par 2"
        assert ctx.param1_columns.get(2) == "Kontrola-2: Par 1"

    def test_build_step_data(self, builder: SharedContextBuilder) -> None:
        """Test extraction of step data."""
        rows = [
            {"št. Koraka": "1"},
            {"št. Koraka": "2"},
            {"št. Koraka": "3"},
        ]
        columns = ["št. Koraka"]
        ctx = builder.build(rows, columns)

        assert ctx.existing_steps == {1, 2, 3}
        assert ctx.step_to_row_indices[1] == [2]  # row_offset + 0
        assert ctx.step_to_row_indices[2] == [3]  # row_offset + 1
        assert ctx.step_to_row_indices[3] == [4]  # row_offset + 2

    def test_build_step_data_with_duplicates(self, builder: SharedContextBuilder) -> None:
        """Test step data with duplicate step numbers."""
        rows = [
            {"št. Koraka": "1"},
            {"št. Koraka": "1"},  # Duplicate
            {"št. Koraka": "2"},
        ]
        columns = ["št. Koraka"]
        ctx = builder.build(rows, columns)

        assert ctx.existing_steps == {1, 2}
        assert ctx.step_to_row_indices[1] == [2, 3]  # Both rows

    def test_build_checkbox_states(self, builder: SharedContextBuilder) -> None:
        """Test extraction of checkbox states."""
        rows = [
            {"Tip objekta": "checkbox", "Ključ preverjanja": "CHECK_1", "Vrednost": "1"},
            {"Tip objekta": "checkbox", "Ključ preverjanja": "CHECK_2", "Vrednost": "0"},
            {"Tip objekta": "checkbox", "Ključ preverjanja": "CHECK_3", "Vrednost": ""},
            {"Tip objekta": "edit", "Ključ preverjanja": "NOT_CHECK", "Vrednost": "1"},
        ]
        columns = ["Tip objekta", "Ključ preverjanja", "Vrednost"]
        ctx = builder.build(rows, columns)

        assert ctx.checkbox_states["CHECK_1"] == 1
        assert ctx.checkbox_states["CHECK_2"] == 0
        assert ctx.checkbox_states["CHECK_3"] is None
        assert "NOT_CHECK" not in ctx.checkbox_states

    def test_build_keys_by_type(self, builder: SharedContextBuilder) -> None:
        """Test grouping of keys by data type."""
        rows = [
            {"Tip podatka": "kemijski", "Ključ preverjanja": "KEM_1", "Vrednost": "A"},
            {"Tip podatka": "kemijski", "Ključ preverjanja": "KEM_2", "Vrednost": ""},
            {"Tip podatka": "raztopine", "Ključ preverjanja": "RAZT_1", "Vrednost": "B"},
            {"Tip podatka": "masa", "Ključ preverjanja": "MASA_1", "Vrednost": ""},
            {"Tip podatka": "masa", "Ključ preverjanja": "MASA_2", "Vrednost": "10 g"},
        ]
        columns = ["Tip podatka", "Ključ preverjanja", "Vrednost"]
        ctx = builder.build(rows, columns)

        assert "kemijski" in ctx.keys_by_type
        assert "KEM_1" in ctx.keys_by_type["kemijski"]
        assert "KEM_2" in ctx.keys_by_type["kemijski"]
        assert "RAZT_1" in ctx.keys_by_type["raztopine"]
        assert "MASA_1" in ctx.keys_by_type["masa"]
        assert ctx.keys_with_value_by_type["kemijski"] == {"KEM_1"}
        assert ctx.keys_with_value_by_type["raztopine"] == {"RAZT_1"}
        assert ctx.keys_with_value_by_type["masa"] == {"MASA_2"}

    def test_build_section_and_tab(self, builder: SharedContextBuilder) -> None:
        """Test section and tab tracking."""
        rows = [
            {"Tip objekta": "naslov", "Zavihek": "Tab1"},  # Section 1
            {"Tip objekta": "edit", "Zavihek": ""},
            {"Tip objekta": "naslov", "Zavihek": "Tab2"},  # Section 2
            {"Tip objekta": "edit", "Zavihek": ""},
        ]
        columns = ["Tip objekta", "Zavihek"]
        ctx = builder.build(rows, columns)

        # Sections should increment on 'naslov'
        assert ctx.section_by_row[2] == 1  # First naslov
        assert ctx.section_by_row[3] == 1  # Same section
        assert ctx.section_by_row[4] == 2  # Second naslov
        assert ctx.section_by_row[5] == 2  # Same section

        # Tabs should persist
        assert ctx.tab_by_row[2] == "Tab1"
        assert ctx.tab_by_row[3] == "Tab1"
        assert ctx.tab_by_row[4] == "Tab2"
        assert ctx.tab_by_row[5] == "Tab2"

    def test_build_zakleni_data(self, builder: SharedContextBuilder) -> None:
        """Test zaklenipolja-specific data extraction."""
        rows = [
            {"št. Koraka": "1", "Ključ preverjanja": "KEY_1", "Kontrola-1": ""},
            {"št. Koraka": "2", "Ključ preverjanja": "KEY_2", "Kontrola-1": ""},
            {
                "št. Koraka": "3",
                "Ključ preverjanja": "ZAKLENI_KEY",
                "Kontrola-1": "zaklenipolja",
                "Kontrola-1: Par 1": "1,2",
            },
        ]
        columns = ["št. Koraka", "Ključ preverjanja", "Kontrola-1", "Kontrola-1: Par 1"]
        ctx = builder.build(rows, columns)

        assert ctx.zakleni_param1_steps == {1, 2}
        assert "ZAKLENI_KEY" in ctx.all_zakleni_keys
        assert 1 in ctx.keys_by_zakleni_step
        assert 2 in ctx.keys_by_zakleni_step

    def test_build_step_to_controls(self, builder: SharedContextBuilder) -> None:
        """Test step to controls mapping."""
        rows = [
            {"št. Koraka": "1", "Kontrola-1": "kontrolaIntervala", "Kontrola-2": "zaklenipolja"},
            {"št. Koraka": "2", "Kontrola-1": "aliObstajaPogoj", "Kontrola-2": ""},
        ]
        columns = ["št. Koraka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)

        assert "kontrolaintervala" in ctx.step_to_controls[1]
        assert "zaklenipolja" in ctx.step_to_controls[1]
        assert "aliobstajapogoj" in ctx.step_to_controls[2]

    def test_build_ali_pogoj_locations(self, builder: SharedContextBuilder) -> None:
        """Test aliObstajaPogoj location tracking."""
        rows = [
            {"št. Koraka": "1", "Kontrola-1": "aliObstajaPogoj"},
            {"št. Koraka": "2", "Kontrola-1": ""},
            {"št. Koraka": "3", "Kontrola-2": "aliObstajaPogoj"},
        ]
        columns = ["št. Koraka", "Kontrola-1", "Kontrola-2"]
        ctx = builder.build(rows, columns)

        assert 1 in ctx.ali_pogoj_step_locations
        assert ctx.ali_pogoj_step_locations[1] == (2, "Kontrola-1")
        assert 3 in ctx.ali_pogoj_step_locations

    def test_row_offset_applied(self) -> None:
        """Test that row offset is correctly applied."""
        builder = SharedContextBuilder(row_offset=5)
        rows = [
            {"št. Koraka": "1"},
            {"št. Koraka": "2"},
        ]
        columns = ["št. Koraka"]
        ctx = builder.build(rows, columns)

        assert ctx.step_to_row_indices[1] == [5]  # row_offset + 0
        assert ctx.step_to_row_indices[2] == [6]  # row_offset + 1

