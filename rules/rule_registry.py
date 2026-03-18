"""Rule registration and instantiation."""

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, TypeVar

from .base_rule import BaseRule

RuleType = TypeVar("RuleType", bound=BaseRule)


class RuleRegistry:
    """Keeps track of all available rule classes.

    The registry stores rule classes and handles their instantiation
    with dependency injection. Rules are sorted by priority when
    instantiated (lower priority number = earlier execution).
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._rules: dict[str, type[BaseRule]] = {}

    def register(self, rule_cls: type[RuleType]) -> type[RuleType]:
        """Register a rule class for later instantiation.

        Args:
            rule_cls: The rule class to register.

        Returns:
            The same rule class (for use as a decorator).

        Raises:
            ValueError: If a rule with the same name is already registered.
        """
        key = rule_cls.name or rule_cls.__name__
        if key in self._rules:
            raise ValueError(f"Rule '{key}' already registered.")
        self._rules[key] = rule_cls
        return rule_cls

    def unregister(self, rule_name: str) -> None:
        """Remove a rule from the registry.

        Args:
            rule_name: Name of the rule to remove.
        """
        self._rules.pop(rule_name, None)

    def get(self, rule_name: str) -> type[BaseRule] | None:
        """Fetch a rule class by name.

        Args:
            rule_name: Name of the rule to fetch.

        Returns:
            The rule class, or None if not found.
        """
        return self._rules.get(rule_name)

    def all(self) -> tuple[type[BaseRule], ...]:
        """Return all registered rule classes."""
        return tuple(self._rules.values())

    def count(self) -> int:
        """Return the number of registered rules."""
        return len(self._rules)

    def instantiate(
        self,
        *,
        logger_factory: Callable[[str], logging.Logger] | None = None,
        **dependencies: Any,
    ) -> list[BaseRule]:
        """Instantiate all registered rules, sorted by priority.

        Args:
            logger_factory: Factory function to create loggers for each rule.
            **dependencies: Additional dependencies to inject into rule constructors.

        Returns:
            List of instantiated rules, sorted by priority (lower = earlier).
        """
        instances: list[BaseRule] = []

        for rule_cls in self._rules.values():
            ctor_kwargs = self._filter_dependencies(rule_cls, dependencies)

            # Inject logger if the rule accepts it
            if "logger" in inspect.signature(rule_cls).parameters and "logger" not in ctor_kwargs:
                if logger_factory:
                    ctor_kwargs["logger"] = logger_factory(rule_cls.__name__)
                else:
                    ctor_kwargs["logger"] = None

            instances.append(rule_cls(**ctor_kwargs))

        # Sort by priority (lower = earlier)
        instances.sort(key=lambda r: r.priority)

        return instances

    def decorator(self, rule_cls: type[RuleType]) -> type[RuleType]:
        """Decorator-style registration helper.

        Usage:
            @registry.decorator
            class MyRule(RowRule):
                ...
        """
        return self.register(rule_cls)

    def _filter_dependencies(
        self,
        rule_cls: type[BaseRule],
        dependencies: dict[str, Any],
    ) -> dict[str, Any]:
        """Filter dependencies to only those accepted by the rule constructor."""
        signature = inspect.signature(rule_cls)
        return {
            name: value
            for name, value in dependencies.items()
            if name in signature.parameters
        }


# Global default registry for convenience
default_registry = RuleRegistry()


def register(rule_cls: type[RuleType]) -> type[RuleType]:
    """Register a rule class with the default registry.

    Usage:
        @register
        class MyRule(RowRule):
            ...
    """
    return default_registry.register(rule_cls)
