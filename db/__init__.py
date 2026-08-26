"""MySQL/MES integration layer for Validator OOP.

This package provides an optional SQL data source and results sink for the
validation engine:

- ``DBConfig``           – environment-driven connection configuration
- ``ConnectionFactory``  – lazy-import connection handling (mysql-connector)
- ``ColumnMapping``      – config-driven MES column -> validator header mapping
- ``MySQLLoader``        – loads a recipe from MySQL as a ``LoadedWorkbook``
- ``MySQLReportWriter``  – persists a ``ValidationReport`` back to MySQL

The MySQL driver is an *optional* dependency: importing this package works
without it, and a clear error is raised only when a connection is attempted.
"""

from __future__ import annotations

from .config import DBConfig
from .errors import (
    DBConnectionError,
    DBDriverMissingError,
    DBError,
    MappingError,
    RecipeNotFoundError,
)
from .mapping import ColumnMapping, load_mapping
from .sql_loader import MySQLLoader, RecipeMeta
from .sql_report_writer import MySQLReportWriter

__all__ = [
    "DBConfig",
    "DBError",
    "DBConnectionError",
    "DBDriverMissingError",
    "MappingError",
    "RecipeNotFoundError",
    "ColumnMapping",
    "load_mapping",
    "MySQLLoader",
    "RecipeMeta",
    "MySQLReportWriter",
]
