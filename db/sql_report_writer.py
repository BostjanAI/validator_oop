"""Persist :class:`ValidationReport` results into MySQL.

Writes one ``validation_runs`` row (header) plus one ``validation_findings``
row per error, in a single transaction (rollback on failure).

Idempotency: by default every ``save()`` creates a *new* run with a fresh
timestamp, so the full validation history per recipe is preserved. With
``replace_existing=True`` all previous runs for the same ``recipe_id`` are
deleted first (findings cascade via the foreign key), keeping only the
latest result.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from validator_oop.core._version import VERSION_REPORT
from validator_oop.core.config import ValidatorConfig
from validator_oop.core.report import ValidationReport

from .config import DBConfig
from .connection import ConnectionFactory

logger = logging.getLogger(__name__)

_INSERT_RUN = (
    "INSERT INTO validation_runs "
    "(recipe_id, recipe_name, is_valid, error_count, warning_count, info_count, "
    "validator_version, config_json) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
)

_INSERT_FINDING = (
    "INSERT INTO validation_findings "
    "(run_id, sheet, row_index, col, rule_name, code, severity, message, payload_json) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
)

_DELETE_RUNS_FOR_RECIPE = "DELETE FROM validation_runs WHERE recipe_id = %s"


class MySQLReportWriter:
    """Writes validation reports into the MySQL results tables."""

    def __init__(
        self,
        config: DBConfig,
        *,
        connection_factory: ConnectionFactory | None = None,
        logger_: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._factory = connection_factory or ConnectionFactory(config)
        self._logger = logger_ or logger

    def save(
        self,
        report: ValidationReport,
        *,
        recipe_id: int,
        recipe_name: str | None = None,
        config: ValidatorConfig | dict[str, Any] | None = None,
        replace_existing: bool = False,
    ) -> int:
        """Persist a report and return the new ``run_id``.

        Args:
            report: Validation report to store.
            recipe_id: MES recipe id the report belongs to.
            recipe_name: Optional human-readable recipe name.
            config: Validator configuration to archive with the run.
            replace_existing: Delete previous runs for this recipe first.

        Returns:
            The ``validation_runs.id`` of the inserted run.
        """
        recipe_id = int(recipe_id)
        report_dict = report.to_dict()
        counts = report_dict.get("counts", {})

        config_json: str | None = None
        if config is not None:
            config_dict = config.to_dict() if isinstance(config, ValidatorConfig) else config
            config_json = json.dumps(config_dict, ensure_ascii=False, default=str)

        run_params = (
            recipe_id,
            recipe_name,
            1 if report_dict.get("is_valid") else 0,
            int(counts.get("error", 0)),
            int(counts.get("warning", 0)),
            int(counts.get("info", 0)),
            VERSION_REPORT,
            config_json,
        )
        finding_rows = [self._finding_params(e) for e in report_dict.get("errors", [])]

        with self._factory.connection(for_results=True) as conn:
            cur = conn.cursor()
            try:
                if replace_existing:
                    cur.execute(_DELETE_RUNS_FOR_RECIPE, (recipe_id,))
                cur.execute(_INSERT_RUN, run_params)
                run_id = int(cur.lastrowid)
                for params in finding_rows:
                    cur.execute(_INSERT_FINDING, (run_id, *params))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()

        self._logger.info(
            "Rezultati validacije shranjeni v MySQL (run_id=%s, receptura=%s, napak=%s)",
            run_id,
            recipe_id,
            counts.get("error", 0),
        )
        return run_id

    @staticmethod
    def _finding_params(error: dict[str, Any]) -> tuple[Any, ...]:
        """Build finding INSERT params from ``ValidationError.to_dict()`` output."""
        payload = error.get("payload")
        payload_json = (
            json.dumps(payload, ensure_ascii=False, default=str) if payload else None
        )
        row = error.get("row")
        return (
            error.get("sheet"),
            int(row) if isinstance(row, (int, float)) else None,
            error.get("col"),
            error.get("rule"),
            error.get("code"),
            error.get("severity"),
            error.get("message"),
            payload_json,
        )
