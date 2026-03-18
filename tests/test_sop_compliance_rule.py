"""Tests for SOPComplianceRule.

This rule depends on optional SOP data. We at least ensure the rule safely
skips when no SOP data is provided.
"""

from __future__ import annotations

import pytest

from validator_oop.rules.builtin.sop_compliance_rule import SOPComplianceRule


class TestSOPComplianceRule:
    """Tests for SOPComplianceRule."""

    @pytest.fixture
    def rule(self) -> SOPComplianceRule:
        """Create an SOPComplianceRule instance with no SOP data (skip mode)."""
        return SOPComplianceRule(sop_data=None)

    def test_skips_when_no_sop_data(self, rule: SOPComplianceRule) -> None:
        """Rule should not error and should return no errors when SOP data is missing."""
        workbook_data = {
            "Sheet1": [
                {"št. Koraka": "1", "Tip podatka": "kemikalija", "Ključ preverjanja": "K1"},
            ]
        }

        errors = rule.run_workbook(workbook_data, workbook_name="test.xlsx", row_offset=2)
        assert errors == []

