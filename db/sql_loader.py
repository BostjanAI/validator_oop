"""MySQL recipe loader returning the same structure as :class:`ExcelLoader`.

``MySQLLoader.load_recipe()`` builds a :class:`LoadedWorkbook`, so the whole
validation pipeline (``ValidatorEngine.validate_loaded`` -> ``RuleEngine`` ->
rules) runs unchanged regardless of the data source.

Row numbering: ``row_offset`` is 2, i.e. the first recipe step is reported as
"row 2" – identical to an Excel sheet with the header in row 1. This keeps
error locations consistent between the Excel and SQL sources.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validator_oop.excel.excel_loader import LoadedWorkbook

from .config import DBConfig
from .connection import ConnectionFactory
from .errors import RecipeNotFoundError
from .mapping import ColumnMapping, load_mapping

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RecipeMeta:
    """Recipe metadata for listing/selection in CLI and web UI."""

    recipe_id: int
    name: str = ""
    version: str = ""
    date: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "name": self.name,
            "version": self.version,
            "date": self.date,
        }


class MySQLLoader:
    """Loads MES recipes from MySQL as :class:`LoadedWorkbook` objects."""

    def __init__(
        self,
        config: DBConfig,
        mapping: ColumnMapping | None = None,
        *,
        connection_factory: ConnectionFactory | None = None,
        logger_: logging.Logger | None = None,
    ) -> None:
        """Initialize the loader.

        Args:
            config: Database connection configuration.
            mapping: Column mapping (default profile when omitted; the
                config's ``mapping_file`` is honoured in that case).
            connection_factory: Injectable factory (mockable in tests).
            logger_: Logger instance.
        """
        self._config = config
        self._mapping = mapping or load_mapping(config.mapping_file)
        self._factory = connection_factory or ConnectionFactory(config)
        self._logger = logger_ or logger

    @property
    def mapping(self) -> ColumnMapping:
        return self._mapping

    # ------------------------------------------------------------------ load

    def load_recipe(self, recipe_id: int) -> LoadedWorkbook:
        """Load one recipe and return it as a :class:`LoadedWorkbook`.

        Args:
            recipe_id: Recipe id in the MES database (validated as integer).

        Returns:
            LoadedWorkbook with mapped values/headers, ready for
            ``ValidatorEngine.validate_loaded``.

        Raises:
            RecipeNotFoundError: When the recipe id has no steps.
        """
        recipe_id = _require_int(recipe_id)
        src = self._mapping.source

        select_cols = "*"
        query = (
            f"SELECT {select_cols} FROM {src.steps_table} "  # identifiers validated in mapping
            f"WHERE {src.recipe_id_column} = %s "
            f"ORDER BY {src.order_by_column}"
        )
        with self._factory.cursor() as cur:
            cur.execute(query, (recipe_id,))
            rows = cur.fetchall()

        if not rows:
            raise RecipeNotFoundError(recipe_id)

        values: dict[str, list[dict[str, Any]]] = {}
        if src.sheet_column:
            # MES splits recipe variants into multiple sheets.
            for row in rows:
                sheet = str(row.get(src.sheet_column) or src.default_sheet_name)
                values.setdefault(sheet, []).append(self._mapping.map_row(row))
        else:
            values[src.default_sheet_name] = [self._mapping.map_row(row) for row in rows]

        sheet_names = list(values.keys())
        headers = {sheet: list(self._mapping.headers) for sheet in sheet_names}

        self._logger.info(
            "Naložena receptura id=%s iz MES baze (%d vrstic, listi: %s)",
            recipe_id,
            len(rows),
            ", ".join(sheet_names),
        )

        return LoadedWorkbook(
            values=values,
            headers=headers,
            source_path=Path(f"mysql_receptura_{recipe_id}"),
            row_offset=2,
            sheet_names=sheet_names,
        )

    # ------------------------------------------------------------------ meta

    def recipe_exists(self, recipe_id: int) -> bool:
        """Return True when the recipe id exists in the steps table."""
        recipe_id = _require_int(recipe_id)
        src = self._mapping.source
        query = (
            f"SELECT 1 FROM {src.steps_table} "
            f"WHERE {src.recipe_id_column} = %s LIMIT 1"
        )
        with self._factory.cursor() as cur:
            cur.execute(query, (recipe_id,))
            return cur.fetchone() is not None

    def list_recipes(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        name_filter: str | None = None,
    ) -> list[RecipeMeta]:
        """List recipes from the metadata table (for CLI/web selection).

        Args:
            limit: Maximum number of records (1–500).
            offset: Pagination offset.
            name_filter: Optional case-insensitive substring filter on the name.

        Returns:
            List of RecipeMeta (id, name, version, date).
        """
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
        src = self._mapping.source

        query = (
            f"SELECT {src.recipes_id_column} AS recipe_id, "
            f"{src.recipes_name_column} AS name, "
            f"{src.recipes_version_column} AS version, "
            f"{src.recipes_date_column} AS date "
            f"FROM {src.recipes_table}"
        )
        params: list[Any] = []
        if name_filter:
            query += f" WHERE {src.recipes_name_column} LIKE %s"
            params.append(f"%{name_filter}%")
        query += f" ORDER BY {src.recipes_id_column} DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with self._factory.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()

        return [
            RecipeMeta(
                recipe_id=int(row["recipe_id"]),
                name=str(row.get("name") or ""),
                version=str(row.get("version") or ""),
                date=str(row.get("date") or ""),
            )
            for row in rows
        ]


def _require_int(recipe_id: Any) -> int:
    """Validate recipe_id as an integer (security: no arbitrary values in SQL)."""
    try:
        return int(recipe_id)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"recipe_id mora biti celo stevilo, prejeto: {recipe_id!r}") from exc
