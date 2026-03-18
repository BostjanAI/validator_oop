"""Core validation components.

This module exports the main classes for validation:
- ValidationError: Represents a single validation failure
- ValidationReport: Aggregates validation errors
- RuleEngine: Coordinates rule execution
- ValidatorEngine: High-level orchestrator
- ValidatorConfig: Runtime configuration
- SharedContext: Pre-computed data shared across rules
- Severity: Error severity levels
- constants: Static constants and regex patterns
"""

from validator_oop.core import constants
from validator_oop.core.config import DEFAULT_CONFIG, ValidatorConfig
from validator_oop.core.error import Severity, ValidationError
from validator_oop.core.report import ValidationReport
from validator_oop.core.rule_engine import RuleEngine
from validator_oop.core.shared_context import SharedContext, SharedContextBuilder
from validator_oop.core.validator_engine import ValidatorEngine

__all__ = [
    "constants",
    "DEFAULT_CONFIG",
    "RuleEngine",
    "Severity",
    "SharedContext",
    "SharedContextBuilder",
    "ValidationError",
    "ValidationReport",
    "ValidatorConfig",
    "ValidatorEngine",
]

