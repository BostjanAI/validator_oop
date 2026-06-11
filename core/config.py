"""Validator configuration.

This module provides runtime configuration for the validation framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ValidatorConfig:
    """Runtime configuration for validation behavior.

    Attributes:
        bypass_rules: Set of rule names or codes to skip during validation.
        bypass_codes: Set of error codes to suppress in output.
        strict_mode: If True, treat warnings as errors.
        locale: Locale for error messages (default 'sl' for Slovenian).
        row_offset: Excel row number of the first data row (default 2).
        include_formulas: If True, load cell formulas for validation.
        max_errors_per_rule: Maximum errors to collect per rule (0 = unlimited).
        stop_on_first_error: If True, stop validation after first error.
        bypass_zakleni_require_empty_for_checkbox: Skip 'kontrolaPraznoPolje' requirement
            for checkbox with 'zaklenipolja'.
        bypass_zakleni_require_pogoj_for_param1_steps: Skip 'aliObstajaPogoj' requirement
            for steps referenced in zaklenipolja Param1.
        bypass_zakleni_inverse_pogoj_requirement: Skip inverse check (every step with
            aliObstajaPogoj must be in zaklenipolja Param1).
        sop_data_path: Path to SOP Word document (optional).
        enable_sop_validation: Enable SOP validation (default True, but validator works without SOP).
        extra: Additional configuration options.
    """

    bypass_rules: frozenset[str] = field(default_factory=frozenset)
    bypass_codes: frozenset[str] = field(default_factory=frozenset)
    strict_mode: bool = False
    locale: str = "sl"
    row_offset: int = 2
    include_formulas: bool = False
    max_errors_per_rule: int = 0
    stop_on_first_error: bool = False
    # Zaklenipolja-specific bypass flags (matching original MES_validator.py behavior)
    bypass_zakleni_require_empty_for_checkbox: bool = True
    bypass_zakleni_require_pogoj_for_param1_steps: bool = True
    bypass_zakleni_inverse_pogoj_requirement: bool = False
    # SOP validation settings
    sop_data_path: Path | None = None
    enable_sop_validation: bool = True
    # Catalog validation settings (solution/chemical code matching)
    catalog_raztopine_path: Path | None = None
    catalog_kemikalije_path: Path | None = None
    enable_catalog_validation: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def should_skip_rule(self, rule_name: str, rule_code: str = "") -> bool:
        """Check if a rule should be skipped based on configuration.

        Args:
            rule_name: Name of the rule.
            rule_code: Error code of the rule.

        Returns:
            True if the rule should be skipped.
        """
        if rule_name in self.bypass_rules:
            return True
        if rule_code and rule_code in self.bypass_rules:
            return True
        return False

    def should_suppress_error(self, error_code: str) -> bool:
        """Check if an error code should be suppressed.

        Args:
            error_code: The error code to check.

        Returns:
            True if the error should be suppressed.
        """
        return error_code in self.bypass_codes

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidatorConfig:
        """Create a config from a dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            ValidatorConfig instance.
        """
        bypass_rules = data.get("bypass_rules", [])
        if isinstance(bypass_rules, (list, tuple, set)):
            bypass_rules = frozenset(bypass_rules)

        bypass_codes = data.get("bypass_codes", [])
        if isinstance(bypass_codes, (list, tuple, set)):
            bypass_codes = frozenset(bypass_codes)

        return cls(
            bypass_rules=bypass_rules,
            bypass_codes=bypass_codes,
            strict_mode=data.get("strict_mode", False),
            locale=data.get("locale", "sl"),
            row_offset=data.get("row_offset", 2),
            include_formulas=data.get("include_formulas", False),
            max_errors_per_rule=data.get("max_errors_per_rule", 0),
            stop_on_first_error=data.get("stop_on_first_error", False),
            bypass_zakleni_require_empty_for_checkbox=data.get(
                "bypass_zakleni_require_empty_for_checkbox", True
            ),
            bypass_zakleni_require_pogoj_for_param1_steps=data.get(
                "bypass_zakleni_require_pogoj_for_param1_steps", True
            ),
            bypass_zakleni_inverse_pogoj_requirement=data.get(
                "bypass_zakleni_inverse_pogoj_requirement", False
            ),
            sop_data_path=Path(data["sop_data_path"]) if data.get("sop_data_path") else None,
            enable_sop_validation=data.get("enable_sop_validation", True),
            catalog_raztopine_path=Path(data["catalog_raztopine_path"]) if data.get("catalog_raztopine_path") else None,
            catalog_kemikalije_path=Path(data["catalog_kemikalije_path"]) if data.get("catalog_kemikalije_path") else None,
            enable_catalog_validation=data.get("enable_catalog_validation", True),
            extra=data.get("extra", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to a dictionary.

        Returns:
            Configuration dictionary.
        """
        return {
            "bypass_rules": list(self.bypass_rules),
            "bypass_codes": list(self.bypass_codes),
            "strict_mode": self.strict_mode,
            "locale": self.locale,
            "row_offset": self.row_offset,
            "include_formulas": self.include_formulas,
            "max_errors_per_rule": self.max_errors_per_rule,
            "stop_on_first_error": self.stop_on_first_error,
            "bypass_zakleni_require_empty_for_checkbox": self.bypass_zakleni_require_empty_for_checkbox,
            "bypass_zakleni_require_pogoj_for_param1_steps": self.bypass_zakleni_require_pogoj_for_param1_steps,
            "bypass_zakleni_inverse_pogoj_requirement": self.bypass_zakleni_inverse_pogoj_requirement,
            "sop_data_path": str(self.sop_data_path) if self.sop_data_path else None,
            "enable_sop_validation": self.enable_sop_validation,
            "catalog_raztopine_path": str(self.catalog_raztopine_path) if self.catalog_raztopine_path else None,
            "catalog_kemikalije_path": str(self.catalog_kemikalije_path) if self.catalog_kemikalije_path else None,
            "enable_catalog_validation": self.enable_catalog_validation,
            "extra": self.extra,
        }


# Default configuration
DEFAULT_CONFIG = ValidatorConfig()

