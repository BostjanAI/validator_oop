"""Config-driven mapping between MES database columns and validator headers.

The real MES schema is not fixed, so nothing is hardcoded: a default profile
(matching the example in ``docs/SQL_integracija_notes.md``) can be fully
overridden by a JSON file (env ``MES_DB_MAPPING_FILE`` or CLI ``--db-mapping``)
without touching code.

JSON file format (all keys optional – anything omitted keeps the default)::

    {
        "columns": {
            "št. Koraka": "step_number",
            "Navodilo": "instruction",
            ...
        },
        "transforms": {
            "null_default": "",
            "trim": true,
            "casts": {"št. Koraka": "str"}
        },
        "source": {
            "steps_table": "recipe_steps",
            "recipe_id_column": "recipe_id",
            "order_by_column": "step_number",
            "sheet_column": null,
            "default_sheet_name": "Receptura",
            "recipes_table": "recipes",
            "recipes_id_column": "id",
            "recipes_name_column": "name",
            "recipes_version_column": "version",
            "recipes_date_column": "created_at"
        }
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from validator_oop.core.constants import REQUIRED_COLUMNS

from .errors import MappingError

# ---------------------------------------------------------------------------
# Default profile
# TODO(shema): potrditi realna imena tabel/stolpcev z MES adminom.
# Privzeti profil sledi primeru iz docs/SQL_integracija_notes.md.
# ---------------------------------------------------------------------------

DEFAULT_COLUMN_MAP: dict[str, str] = {
    "št. Koraka": "step_number",
    "Navodilo": "instruction",
    "Tip podatka": "data_type",
    "Ključ preverjanja": "check_key",
    "Vrednost": "value",
    "Labela": "label",
    "Tip objekta": "object_type",
    "Kontrola 1": "control1",
    "Kontrola 1 - par 1": "control1_par1",
    "Kontrola 1 - par 2": "control1_par2",
    "Kontrola 2": "control2",
    "Kontrola 2 - par 1": "control2_par1",
    "Kontrola 2 - par 2": "control2_par2",
    "Kontrola 3": "control3",
    "Kontrola 3 - par 1": "control3_par1",
    "Kontrola 3 - par 2": "control3_par2",
    "Kontrola 4": "control4",
    "Kontrola 4 - par 1": "control4_par1",
    "Kontrola 4 - par 2": "control4_par2",
}

_ALLOWED_CASTS = {"str", "int", "float"}


@dataclass(slots=True)
class SourceProfile:
    """Where and how recipe data lives in the MES database.

    All identifiers are validated to be safe SQL identifiers because they are
    interpolated into queries (values are always parametrized separately).
    """

    steps_table: str = "recipe_steps"
    recipe_id_column: str = "recipe_id"
    order_by_column: str = "step_number"
    # Optional column that splits steps into multiple sheets (recipe variants).
    sheet_column: str | None = None
    default_sheet_name: str = "Receptura"
    # Recipe metadata (for list_recipes / recipe_exists).
    recipes_table: str = "recipes"
    recipes_id_column: str = "id"
    recipes_name_column: str = "name"
    recipes_version_column: str = "version"
    recipes_date_column: str = "created_at"

    def validate(self) -> None:
        """Reject unsafe SQL identifiers (defense against injection via config)."""
        names = {
            "steps_table": self.steps_table,
            "recipe_id_column": self.recipe_id_column,
            "order_by_column": self.order_by_column,
            "recipes_table": self.recipes_table,
            "recipes_id_column": self.recipes_id_column,
            "recipes_name_column": self.recipes_name_column,
            "recipes_version_column": self.recipes_version_column,
            "recipes_date_column": self.recipes_date_column,
        }
        if self.sheet_column:
            names["sheet_column"] = self.sheet_column
        bad = [f"{key}={value!r}" for key, value in names.items() if not _is_safe_identifier(value)]
        if bad:
            raise MappingError(
                "Neveljavna imena tabel/stolpcev v mapping konfiguraciji "
                "(dovoljene so samo črke, številke in _): " + ", ".join(bad)
            )


@dataclass(slots=True)
class ColumnMapping:
    """Maps a MES database row to a validator row (``{header: value}``).

    Attributes:
        columns: validator header -> MES column name.
        null_default: Value used when the MES column is NULL (default "").
        trim: Strip leading/trailing whitespace from string values.
        casts: Optional per-header cast ("str", "int" or "float").
        source: Table/column profile for building queries.
    """

    columns: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_COLUMN_MAP))
    null_default: Any = ""
    trim: bool = True
    casts: dict[str, str] = field(default_factory=dict)
    source: SourceProfile = field(default_factory=SourceProfile)

    def validate(self) -> None:
        """Raise :class:`MappingError` when the mapping is incomplete or invalid."""
        missing = [header for header in REQUIRED_COLUMNS if header not in self.columns]
        if missing:
            raise MappingError(
                "Mapping MES stolpcev je nepopoln – manjkajo preslikave za: "
                + ", ".join(missing)
                + ". Dopolni JSON mapping datoteko (MES_DB_MAPPING_FILE).",
                missing=missing,
            )
        bad_casts = {h: c for h, c in self.casts.items() if c not in _ALLOWED_CASTS}
        if bad_casts:
            raise MappingError(
                "Neveljavni cast tipi v mapping konfiguraciji: "
                + ", ".join(f"{h} -> {c}" for h, c in bad_casts.items())
                + f". Dovoljeni: {', '.join(sorted(_ALLOWED_CASTS))}."
            )
        self.source.validate()

    @property
    def headers(self) -> list[str]:
        """Validator headers in the canonical REQUIRED_COLUMNS order."""
        ordered = [h for h in REQUIRED_COLUMNS if h in self.columns]
        extras = [h for h in self.columns if h not in REQUIRED_COLUMNS]
        return ordered + extras

    def map_row(self, mes_row: Mapping[str, Any]) -> dict[str, Any]:
        """Convert one MES database row into a validator row.

        Args:
            mes_row: Dictionary as returned by a dictionary cursor.

        Returns:
            ``{validator_header: value}`` with NULL/trim/cast transformations.
        """
        out: dict[str, Any] = {}
        for header in self.headers:
            value = mes_row.get(self.columns[header])
            out[header] = self._transform(header, value)
        return out

    def _transform(self, header: str, value: Any) -> Any:
        if value is None:
            value = self.null_default
        elif isinstance(value, str) and self.trim:
            value = value.strip()

        cast = self.casts.get(header)
        if cast and value != "" and value is not None:
            try:
                if cast == "str":
                    value = str(value)
                elif cast == "int":
                    value = int(value)
                elif cast == "float":
                    value = float(value)
            except (TypeError, ValueError) as exc:
                raise MappingError(
                    f"Vrednosti '{value}' za stolpec '{header}' ni mogoče "
                    f"pretvoriti v tip '{cast}'."
                ) from exc
        return value


def load_mapping(mapping_file: str | Path | None = None) -> ColumnMapping:
    """Build a :class:`ColumnMapping`, optionally overridden by a JSON file.

    Args:
        mapping_file: Path to the JSON override (or None for the default profile).

    Returns:
        Validated ColumnMapping.

    Raises:
        MappingError: When the file is unreadable/invalid or the mapping is incomplete.
    """
    mapping = ColumnMapping()

    if mapping_file:
        path = Path(mapping_file)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise MappingError(f"Mapping datoteke ni mogoče prebrati: {path} ({exc})") from exc
        except json.JSONDecodeError as exc:
            raise MappingError(f"Mapping datoteka ni veljaven JSON: {path} ({exc})") from exc
        if not isinstance(data, dict):
            raise MappingError(f"Mapping datoteka mora vsebovati JSON objekt: {path}")
        _apply_overrides(mapping, data)

    mapping.validate()
    return mapping


def _apply_overrides(mapping: ColumnMapping, data: dict[str, Any]) -> None:
    columns = data.get("columns")
    if isinstance(columns, dict):
        mapping.columns.update({str(k): str(v) for k, v in columns.items()})

    transforms = data.get("transforms")
    if isinstance(transforms, dict):
        if "null_default" in transforms:
            mapping.null_default = transforms["null_default"]
        if "trim" in transforms:
            mapping.trim = bool(transforms["trim"])
        casts = transforms.get("casts")
        if isinstance(casts, dict):
            mapping.casts.update({str(k): str(v) for k, v in casts.items()})

    source = data.get("source")
    if isinstance(source, dict):
        for key in (
            "steps_table",
            "recipe_id_column",
            "order_by_column",
            "sheet_column",
            "default_sheet_name",
            "recipes_table",
            "recipes_id_column",
            "recipes_name_column",
            "recipes_version_column",
            "recipes_date_column",
        ):
            if key in source and source[key] is not None:
                setattr(mapping.source, key, str(source[key]))
        if "sheet_column" in source and source["sheet_column"] is None:
            mapping.source.sheet_column = None


def _is_safe_identifier(name: str) -> bool:
    """Allow only plain SQL identifiers (letters, digits, underscore)."""
    return bool(name) and all(c.isalnum() or c == "_" for c in name) and not name[0].isdigit()
