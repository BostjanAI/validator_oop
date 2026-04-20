"""Structural validation rules.

This module contains rules that operate on required columns and
step-numbering logic (obvezni stolpci, številčenje korakov).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, Sequence

from validator_oop.core.constants import REQUIRED_COLUMNS
from validator_oop.core.error import Severity
from validator_oop.rules import RuleContext, SheetRule, register
from validator_oop.utils import coerce_str


@register
class RequiredColumnsRule(SheetRule):
    """Ensure required columns are present on every sheet."""

    name = "required_columns"
    code = "MISSING_COLUMN"
    description = "Preveri prisotnost vseh obveznih stolpcev."

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        columns: set[str] = set()
        if context.shared and context.shared.columns:
            columns = set(context.shared.columns)
        elif rows:
            columns = set(rows[0].keys())

        for column in REQUIRED_COLUMNS:
            if column not in columns:
                yield self.build_error(
                    message=f"Manjka obvezen stolpec: '{column}'",
                    context=context,
                    column=column,
                )


@register
class StepNumberingRule(SheetRule):
    """Validate numbering in 'št. Koraka' column."""

    name = "step_numbering"
    description = "Preveri pravilno številčenje korakov (manjkajoči, podvojeni, vrstni red)."
    tags = ("steps", "structure")

    def evaluate_sheet(
        self,
        rows: Sequence[Mapping[str, object]],
        context: RuleContext,
        *,
        row_offset: int = 2,
    ) -> Iterable:
        columns = set(context.shared.columns if context.shared else [])
        if "št. Koraka" not in columns:
            return []

        errors = []
        step_entries: list[tuple[int, int]] = []

        for index, row in enumerate(rows):
            excel_row = row_offset + index
            raw_value = coerce_str(row.get("št. Koraka", ""))

            if raw_value:
                try:
                    step_num = int(raw_value)
                    step_entries.append((excel_row, step_num))
                except ValueError:
                    errors.append(
                        self.build_error(
                            message=f"'št. Koraka' mora biti celo število, najdeno: {raw_value!r}",
                            context=context.with_row(excel_row),
                            column="št. Koraka",
                            code="STEP_NOT_INTEGER",
                        )
                    )
            else:
                if self._row_contains_data(row):
                    errors.append(
                        self.build_error(
                            message="Manjka 'št. Koraka' v vrstici z vsebino.",
                            context=context.with_row(excel_row),
                            column="št. Koraka",
                            code="STEP_MISSING",
                        )
                    )

        errors.extend(self._check_duplicate_steps(step_entries, context))
        errors.extend(self._check_tab_start(step_entries, context))
        errors.extend(self._check_missing_steps(step_entries, context))
        return errors

    def _row_contains_data(self, row: Mapping[str, object]) -> bool:
        for column in REQUIRED_COLUMNS:
            if column == "št. Koraka":
                continue
            if coerce_str(row.get(column, "")):
                return True
        return False

    def _check_duplicate_steps(
        self,
        step_entries: Sequence[tuple[int, int]],
        context: RuleContext,
    ) -> list:
        if not step_entries:
            return []

        tab_by_row = context.shared.tab_by_row if context.shared else {}
        duplicates: dict[tuple[str, int], list[int]] = defaultdict(list)

        for row_index, step in step_entries:
            tab = tab_by_row.get(row_index, "")
            duplicates[(tab, step)].append(row_index)

        errors = []
        for (tab, step), rows in duplicates.items():
            if len(rows) <= 1:
                continue

            tab_text = f" v zavihku '{tab}'" if tab else ""
            message = f"Podvojena številka koraka: {step}{tab_text}."
            errors.append(
                self.build_error(
                    message=message,
                    context=context,
                    code="STEP_DUPLICATE",
                    severity=Severity.ERROR,
                    payload={"rows": rows},
                )
            )

        return errors

    def _check_tab_start(
        self,
        step_entries: Sequence[tuple[int, int]],
        context: RuleContext,
    ) -> list:
        if not step_entries:
            return []

        tab_by_row = context.shared.tab_by_row if context.shared else {}
        tab_to_steps: dict[str, list[tuple[int, int]]] = defaultdict(list)

        for row_index, step in step_entries:
            tab = tab_by_row.get(row_index, "")
            tab_to_steps[tab].append((row_index, step))

        errors = []
        for tab, entries in tab_to_steps.items():
            steps = [step for _, step in entries]
            min_step = min(steps)
            if min_step == 1:
                continue

            rows = [row for row, step in entries if step == min_step]
            if tab:
                message = f"V zavihku '{tab}' se koraki ne začnejo s 1 (najmanjši korak je {min_step})."
            else:
                message = f"Koraki se ne začnejo s 1 (najmanjši korak je {min_step})."

            errors.append(
                self.build_error(
                    message=message,
                    context=context,
                    code="STEP_TAB_NOT_FROM_ONE",
                    payload={"rows": rows},
                )
            )

        return errors

    def _check_missing_steps(
        self,
        step_entries: Sequence[tuple[int, int]],
        context: RuleContext,
    ) -> list:
        if not step_entries:
            return []

        steps = [step for _, step in step_entries]
        unique_steps = sorted(set(steps))
        if not unique_steps or unique_steps[0] != 1:
            return []

        expected = set(range(1, unique_steps[-1] + 1))
        missing = sorted(expected.difference(set(steps)))
        if not missing:
            return []

        return [
            self.build_error(
                message=f"Manjkajo koraki: {missing}",
                context=context,
                code="STEP_GAPS",
            )
        ]

