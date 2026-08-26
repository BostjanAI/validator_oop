"""Tests for the MySQL/MES integration layer (db/ package).

No live MySQL server is required: the loader and report writer are tested
against mocked connections. An optional real round-trip test runs only when
``MES_DB_HOST`` is configured (marker ``mysql``, skipped by default).
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pytest

from validator_oop.core import RuleEngine, ValidatorConfig, ValidatorEngine
from validator_oop.core.constants import REQUIRED_COLUMNS
from validator_oop.core.error import Severity, ValidationError
from validator_oop.core.report import ValidationReport
from validator_oop.db.config import DBConfig
from validator_oop.db.errors import MappingError, RecipeNotFoundError
from validator_oop.db.mapping import DEFAULT_COLUMN_MAP, ColumnMapping, load_mapping
from validator_oop.db.sql_loader import MySQLLoader
from validator_oop.db.sql_report_writer import MySQLReportWriter
from validator_oop.excel import ExcelLoader
from validator_oop.excel.excel_loader import LoadedWorkbook
from validator_oop.rules import default_registry
from validator_oop.rules.builtin import register_all


# =============================================================================
# Fakes (mocked DB connection layer)
# =============================================================================


class FakeCursor:
    """Records executed queries and returns pre-configured rows."""

    def __init__(self, rows: list[dict[str, Any]], lastrowid: int = 42) -> None:
        self.rows = rows
        self.executed: list[tuple[str, tuple | None]] = []
        self.lastrowid = lastrowid
        self.fail_on: str | None = None

    def execute(self, query: str, params: tuple | None = None) -> None:
        if self.fail_on and self.fail_on in query:
            raise RuntimeError(f"simulated failure on: {self.fail_on}")
        self.executed.append((query, params))

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows

    def fetchone(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self, dictionary: bool = True) -> FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        pass


class FakeConnectionFactory:
    """Drop-in replacement for ConnectionFactory in tests."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.fake_cursor = FakeCursor(rows or [])
        self.fake_connection = FakeConnection(self.fake_cursor)

    @contextmanager
    def cursor(self, *, dictionary: bool = True, for_results: bool = False) -> Iterator[FakeCursor]:
        yield self.fake_cursor

    @contextmanager
    def connection(self, *, for_results: bool = False) -> Iterator[FakeConnection]:
        yield self.fake_connection


def _db_config() -> DBConfig:
    return DBConfig(host="testhost", database="testdb", user="testuser", password="x")


def _mes_row(step: int, **overrides: Any) -> dict[str, Any]:
    """A MES database row using the default column profile."""
    row: dict[str, Any] = {mes_col: "" for mes_col in DEFAULT_COLUMN_MAP.values()}
    row.update(
        {
            "step_number": step,
            "instruction": f"Navodilo {step}",
            "data_type": "naslov",
            "object_type": "naslov",
            "check_key": "",
            "value": "",
            "label": "",
        }
    )
    row.update(overrides)
    return row


# =============================================================================
# Unit: mapping
# =============================================================================


class TestMapping:
    def test_default_mapping_covers_required_columns(self) -> None:
        mapping = load_mapping(None)
        for header in REQUIRED_COLUMNS:
            assert header in mapping.columns

    def test_map_row_null_and_trim(self) -> None:
        mapping = load_mapping(None)
        row = mapping.map_row({"step_number": None, "instruction": "  hello  "})
        assert row["št. Koraka"] == ""
        assert row["Navodilo"] == "hello"

    def test_map_row_cast(self) -> None:
        mapping = ColumnMapping(casts={"št. Koraka": "str"})
        mapping.validate()
        row = mapping.map_row({"step_number": 5})
        assert row["št. Koraka"] == "5"

    def test_invalid_cast_value_raises_mapping_error(self) -> None:
        mapping = ColumnMapping(casts={"št. Koraka": "int"})
        with pytest.raises(MappingError):
            mapping.map_row({"step_number": "abc"})

    def test_missing_mapping_raises_with_missing_list(self) -> None:
        mapping = ColumnMapping(columns={"št. Koraka": "step_number"})
        with pytest.raises(MappingError) as exc_info:
            mapping.validate()
        assert "Navodilo" in exc_info.value.missing

    def test_json_override(self, tmp_path: Path) -> None:
        override = {
            "columns": {"Navodilo": "opis_navodila"},
            "transforms": {"trim": False, "casts": {"št. Koraka": "str"}},
            "source": {"steps_table": "mes_koraki", "default_sheet_name": "List1"},
        }
        path = tmp_path / "mapping.json"
        path.write_text(json.dumps(override), encoding="utf-8")

        mapping = load_mapping(path)
        assert mapping.columns["Navodilo"] == "opis_navodila"
        assert mapping.trim is False
        assert mapping.casts["št. Koraka"] == "str"
        assert mapping.source.steps_table == "mes_koraki"
        assert mapping.source.default_sheet_name == "List1"
        # Ostale preslikave ostanejo privzete
        assert mapping.columns["Tip podatka"] == "data_type"

    def test_invalid_json_raises_mapping_error(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{to ni json", encoding="utf-8")
        with pytest.raises(MappingError):
            load_mapping(path)

    def test_unsafe_sql_identifier_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "inj.json"
        path.write_text(
            json.dumps({"source": {"steps_table": "steps; DROP TABLE x"}}),
            encoding="utf-8",
        )
        with pytest.raises(MappingError):
            load_mapping(path)

    def test_headers_are_in_canonical_order(self) -> None:
        mapping = load_mapping(None)
        assert mapping.headers[: len(REQUIRED_COLUMNS)] == REQUIRED_COLUMNS


# =============================================================================
# Unit: DBConfig
# =============================================================================


class TestDBConfig:
    def test_from_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.chdir(tmp_path)  # brez .env v cwd
        monkeypatch.setenv("MES_DB_HOST", "mes.local")
        monkeypatch.setenv("MES_DB_NAME", "mes")
        monkeypatch.setenv("MES_DB_USER", "reader")
        monkeypatch.setenv("MES_DB_PASSWORD", "secret")
        monkeypatch.setenv("MES_DB_PORT", "3307")

        cfg = DBConfig.from_env()
        cfg.validate()
        assert cfg.host == "mes.local"
        assert cfg.port == 3307
        assert cfg.results_user == "reader"  # privzeto = bralni user

    def test_env_file_fallback(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        for name in ("MES_DB_HOST", "MES_DB_NAME", "MES_DB_USER", "MES_DB_PASSWORD"):
            monkeypatch.delenv(name, raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text(
            'MES_DB_HOST=envhost\nMES_DB_NAME="envdb"\n# komentar\nMES_DB_USER=envuser\n',
            encoding="utf-8",
        )
        cfg = DBConfig.from_env(env_file)
        assert cfg.host == "envhost"
        assert cfg.database == "envdb"
        assert cfg.user == "envuser"

    def test_validate_reports_missing(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.chdir(tmp_path)
        for name in ("MES_DB_HOST", "MES_DB_NAME", "MES_DB_USER"):
            monkeypatch.delenv(name, raising=False)
        cfg = DBConfig.from_env()
        with pytest.raises(ValueError) as exc_info:
            cfg.validate()
        assert "MES_DB_HOST" in str(exc_info.value)

    def test_password_not_in_repr(self) -> None:
        cfg = DBConfig(host="h", database="d", user="u", password="super-secret")
        assert "super-secret" not in repr(cfg)


# =============================================================================
# Unit: MySQLLoader (mocked connection)
# =============================================================================


class TestMySQLLoader:
    def test_load_recipe_returns_loaded_workbook(self) -> None:
        rows = [_mes_row(1), _mes_row(2)]
        factory = FakeConnectionFactory(rows)
        loader = MySQLLoader(_db_config(), connection_factory=factory)  # type: ignore[arg-type]

        loaded = loader.load_recipe(123)

        assert isinstance(loaded, LoadedWorkbook)
        assert loaded.sheet_names == ["Receptura"]
        assert loaded.row_offset == 2
        assert loaded.source_path == Path("mysql_receptura_123")
        assert len(loaded.values["Receptura"]) == 2
        assert loaded.values["Receptura"][0]["št. Koraka"] == 1
        assert loaded.values["Receptura"][0]["Navodilo"] == "Navodilo 1"
        assert loaded.headers["Receptura"][: len(REQUIRED_COLUMNS)] == REQUIRED_COLUMNS
        # Poizvedba je parametrizirana (recipe_id ni v SQL nizu)
        query, params = factory.fake_cursor.executed[0]
        assert "%s" in query
        assert params == (123,)

    def test_load_recipe_not_found(self) -> None:
        loader = MySQLLoader(
            _db_config(), connection_factory=FakeConnectionFactory([])  # type: ignore[arg-type]
        )
        with pytest.raises(RecipeNotFoundError):
            loader.load_recipe(999)

    def test_load_recipe_rejects_non_integer_id(self) -> None:
        loader = MySQLLoader(
            _db_config(), connection_factory=FakeConnectionFactory([])  # type: ignore[arg-type]
        )
        with pytest.raises(ValueError):
            loader.load_recipe("1; DROP TABLE recipes")  # type: ignore[arg-type]

    def test_multi_sheet_via_sheet_column(self) -> None:
        mapping = ColumnMapping()
        mapping.source.sheet_column = "variant"
        rows = [
            _mes_row(1, variant="Receptura"),
            _mes_row(1, variant="Receptura_2"),
            _mes_row(2, variant="Receptura"),
        ]
        loader = MySQLLoader(
            _db_config(),
            mapping,
            connection_factory=FakeConnectionFactory(rows),  # type: ignore[arg-type]
        )
        loaded = loader.load_recipe(7)
        assert set(loaded.sheet_names) == {"Receptura", "Receptura_2"}
        assert len(loaded.values["Receptura"]) == 2
        assert len(loaded.values["Receptura_2"]) == 1

    def test_recipe_exists(self) -> None:
        loader = MySQLLoader(
            _db_config(),
            connection_factory=FakeConnectionFactory([{"1": 1}]),  # type: ignore[arg-type]
        )
        assert loader.recipe_exists(1) is True

        loader_empty = MySQLLoader(
            _db_config(), connection_factory=FakeConnectionFactory([])  # type: ignore[arg-type]
        )
        assert loader_empty.recipe_exists(1) is False

    def test_list_recipes(self) -> None:
        rows = [
            {"recipe_id": 2, "name": "MOD-QA", "version": "3", "date": "2026-07-01"},
            {"recipe_id": 1, "name": "MOD-SO3", "version": "1", "date": None},
        ]
        factory = FakeConnectionFactory(rows)
        loader = MySQLLoader(_db_config(), connection_factory=factory)  # type: ignore[arg-type]

        recipes = loader.list_recipes(limit=10, offset=0, name_filter="MOD")
        assert [r.recipe_id for r in recipes] == [2, 1]
        assert recipes[0].name == "MOD-QA"
        assert recipes[1].date == ""  # NULL -> ""
        query, params = factory.fake_cursor.executed[0]
        assert "LIKE %s" in query
        assert params == ("%MOD%", 10, 0)


# =============================================================================
# Unit: MySQLReportWriter (mocked connection)
# =============================================================================


def _sample_report() -> ValidationReport:
    report = ValidationReport(source_path=Path("mysql_receptura_5"))
    report.add_error(
        ValidationError(
            rule_name="test_rule",
            message="Testna napaka",
            code="TEST_CODE",
            severity=Severity.ERROR,
            sheet="Receptura",
            row_index=4,
            column="Vrednost",
            payload={"extra": "info"},
        )
    )
    report.add_error(
        ValidationError(
            rule_name="warn_rule",
            message="Opozorilo",
            code="WARN_CODE",
            severity=Severity.WARNING,
            sheet="Receptura",
        )
    )
    return report


class TestMySQLReportWriter:
    def test_save_inserts_run_and_findings_in_transaction(self) -> None:
        factory = FakeConnectionFactory()
        writer = MySQLReportWriter(_db_config(), connection_factory=factory)  # type: ignore[arg-type]

        run_id = writer.save(
            _sample_report(),
            recipe_id=5,
            recipe_name="MOD-QA",
            config=ValidatorConfig(),
        )

        assert run_id == 42  # lastrowid iz FakeCursor
        executed = factory.fake_cursor.executed
        assert len(executed) == 3  # 1x run + 2x finding
        run_query, run_params = executed[0]
        assert "INSERT INTO validation_runs" in run_query
        assert run_params[0] == 5
        assert run_params[1] == "MOD-QA"
        assert run_params[2] == 0  # is_valid=False (ima ERROR)
        assert run_params[3] == 1  # error_count
        assert run_params[4] == 1  # warning_count

        finding_query, finding_params = executed[1]
        assert "INSERT INTO validation_findings" in finding_query
        assert finding_params[0] == 42  # run_id
        assert finding_params[1] == "Receptura"
        assert finding_params[2] == 4  # row_index
        assert finding_params[3] == "Vrednost"
        assert finding_params[5] == "TEST_CODE"
        assert json.loads(finding_params[8]) == {"extra": "info"}

        assert factory.fake_connection.committed is True
        assert factory.fake_connection.rolled_back is False

    def test_save_rolls_back_on_failure(self) -> None:
        factory = FakeConnectionFactory()
        factory.fake_cursor.fail_on = "validation_findings"
        writer = MySQLReportWriter(_db_config(), connection_factory=factory)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError):
            writer.save(_sample_report(), recipe_id=5)

        assert factory.fake_connection.rolled_back is True
        assert factory.fake_connection.committed is False

    def test_replace_existing_deletes_previous_runs(self) -> None:
        factory = FakeConnectionFactory()
        writer = MySQLReportWriter(_db_config(), connection_factory=factory)  # type: ignore[arg-type]

        writer.save(_sample_report(), recipe_id=5, replace_existing=True)

        first_query, first_params = factory.fake_cursor.executed[0]
        assert "DELETE FROM validation_runs" in first_query
        assert first_params == (5,)


# =============================================================================
# Equivalence: Excel source vs SQL source -> identical errors
# =============================================================================


def _write_excel_recipe(path: Path, rows: list[dict[str, Any]]) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Receptura"
    ws.append(REQUIRED_COLUMNS)
    for row in rows:
        ws.append([row.get(col, "") for col in REQUIRED_COLUMNS])
    wb.save(path)


def _validator_rows_to_mes_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert validator-header rows into MES-column rows (default profile)."""
    out = []
    for row in rows:
        out.append({DEFAULT_COLUMN_MAP[h]: row.get(h, "") for h in REQUIRED_COLUMNS})
    return out


@pytest.mark.smoke
class TestExcelSqlEquivalence:
    def test_same_recipe_produces_identical_errors(self, tmp_path: Path) -> None:
        """The SQL source must not change validation results (source neutrality)."""
        register_all()

        # Receptura z namerno napako (neveljaven Tip objekta) in veljavnimi vrstici
        rows: list[dict[str, Any]] = [
            {
                "št. Koraka": 1,
                "Navodilo": "Naslov postopka",
                "Tip podatka": "naslov",
                "Tip objekta": "naslov",
            },
            {
                "št. Koraka": 2,
                "Navodilo": "Vpiši maso",
                "Tip podatka": "masa",
                "Tip objekta": "neveljaven_tip",  # napaka
                "Ključ preverjanja": "masa1",
            },
        ]

        def _make_engine() -> ValidatorEngine:
            config = ValidatorConfig()
            rule_engine = RuleEngine(default_registry, config=config)
            return ValidatorEngine(rule_engine, ExcelLoader())

        # 1) Excel vir
        excel_path = tmp_path / "receptura.xlsx"
        _write_excel_recipe(excel_path, rows)
        excel_report = _make_engine().validate(excel_path)

        # 2) SQL vir (mockana baza z istimi vrsticami)
        mes_rows = _validator_rows_to_mes_rows(rows)
        loader = MySQLLoader(
            _db_config(),
            connection_factory=FakeConnectionFactory(mes_rows),  # type: ignore[arg-type]
        )
        loaded = loader.load_recipe(1)
        sql_report = _make_engine().validate_loaded(loaded)

        def _normalize(report: ValidationReport) -> list[tuple]:
            return sorted(
                (e.rule_name, e.code, e.severity.value, e.sheet, e.row_index, e.column, e.message)
                for e in report.errors
            )

        assert len(excel_report.errors) > 0, "test mora sprožiti vsaj eno napako"
        assert _normalize(excel_report) == _normalize(sql_report)


# =============================================================================
# Optional: live MySQL round-trip (requires configured test database)
# =============================================================================


@pytest.mark.mysql
@pytest.mark.skipif(
    not os.environ.get("MES_DB_HOST"),
    reason="MES_DB_HOST ni nastavljen – integracijski test z živo bazo preskočen",
)
class TestLiveMySQL:
    def test_round_trip(self) -> None:
        """Real DB round-trip: migrate -> save report -> verify tables exist.

        Requires a test MySQL (see tests/docker-compose.mysql.yml) and
        MES_DB_* env variables pointing to it.
        """
        from validator_oop.db.connection import ConnectionFactory
        from validator_oop.db.migrate import ensure_results_tables, verify_results_tables

        config = DBConfig.from_env()
        factory = ConnectionFactory(config)
        ensure_results_tables(factory)
        assert verify_results_tables(factory) == []

        writer = MySQLReportWriter(config)
        run_id = writer.save(_sample_report(), recipe_id=1, recipe_name="test")
        assert run_id > 0
