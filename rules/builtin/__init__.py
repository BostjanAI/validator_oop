"""Built-in validation rules.

This package contains all the built-in validation rules for MES Excel workbooks.
Rules are organized into submodules by category:

- structural: Column presence, step numbering
- field: Field format, type validation
- relational: Key pairs, duplicates
- control: Control validation, parameters

To register all built-in rules, import this module:
    from validator_oop.rules import builtin
    builtin.register_all()

Or import specific rule classes:
    from validator_oop.rules.builtin.structural import RequiredColumnsRule
"""

from validator_oop.rules.rule_registry import default_registry

# List of all built-in rule modules to import
_RULE_MODULES: list[str] = [
    "validator_oop.rules.builtin.structural",
    "validator_oop.rules.builtin.field",
    "validator_oop.rules.builtin.relational",
    "validator_oop.rules.builtin.control",
    "validator_oop.rules.builtin.sop_compliance_rule",
    "validator_oop.rules.builtin.catalog_code_rule",
]


def register_all() -> int:
    """Register all built-in rules with the default registry.

    Returns:
        Number of rules registered.
    """
    import importlib

    count_before = default_registry.count()

    for module_name in _RULE_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            import logging
            logging.getLogger(__name__).warning(
                "Failed to import rule module %s: %s", module_name, e
            )

    return default_registry.count() - count_before


__all__ = ["register_all"]

