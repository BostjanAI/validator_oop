"""Testi za web endpointe MES/MySQL integracije (/api/db/*).

Brez žive baze: MySQLLoader je zamenjan s fake razredom prek monkeypatcha.
Endpointi so registrirani samo pri MES_WEB_ENABLE_DB=1 (settings.enable_db).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

try:
    from fastapi.testclient import TestClient

    from validator_oop.web.backend.app import create_app
    from validator_oop.web.backend.settings import Settings
except ImportError:  # spletne odvisnosti niso nameščene
    pytest.skip("web odvisnosti (fastapi/httpx) niso nameščene", allow_module_level=True)

from validator_oop.db.mapping import ColumnMapping
from validator_oop.db.sql_loader import RecipeMeta
from validator_oop.excel.excel_loader import LoadedWorkbook


# =============================================================================
# Fake loader (brez baze)
# =============================================================================

_RECIPE_ROWS = [
    {
        "št. Koraka": 1,
        "Navodilo": "Naslov",
        "Tip podatka": "naslov",
        "Tip objekta": "naslov",
        "Ključ preverjanja": "",
        "Vrednost": "",
        "Labela": "",
    },
]


class FakeMySQLLoader:
    """Nadomešča MySQLLoader v testih (isti javni vmesnik)."""

    def __init__(self, config: Any, mapping: Any = None, **kwargs: Any) -> None:
        self.mapping = mapping or ColumnMapping()

    def load_recipe(self, recipe_id: int) -> LoadedWorkbook:
        from validator_oop.db.errors import RecipeNotFoundError

        if int(recipe_id) == 999:
            raise RecipeNotFoundError(999)
        return LoadedWorkbook(
            values={"Receptura": list(_RECIPE_ROWS)},
            headers={"Receptura": list(_RECIPE_ROWS[0].keys())},
            source_path=Path(f"mysql_receptura_{recipe_id}"),
            row_offset=2,
            sheet_names=["Receptura"],
        )

    def recipe_exists(self, recipe_id: int) -> bool:
        return int(recipe_id) != 999

    def list_recipes(self, *, limit: int = 50, offset: int = 0, name_filter: str | None = None):
        recipes = [
            RecipeMeta(recipe_id=2, name="MOD-QA", version="3", date="2026-07-01"),
            RecipeMeta(recipe_id=1, name="MOD-SO3", version="1", date="2026-06-15"),
        ]
        if name_filter:
            recipes = [r for r in recipes if name_filter.lower() in r.name.lower()]
        return recipes[offset : offset + limit]


@pytest.fixture()
def db_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Client z vklopljenimi /api/db/* endpointi in fake loaderjem."""
    monkeypatch.setenv("MES_DB_HOST", "testhost")
    monkeypatch.setenv("MES_DB_NAME", "testdb")
    monkeypatch.setenv("MES_DB_USER", "reader")
    monkeypatch.setattr("validator_oop.db.MySQLLoader", FakeMySQLLoader)

    settings = Settings(workdir=tmp_path / "web_workdir", enable_db=True)
    app = create_app(settings)
    return TestClient(app)


@pytest.fixture()
def plain_client(tmp_path: Path) -> TestClient:
    """Client brez MES_WEB_ENABLE_DB (privzeto stanje)."""
    settings = Settings(workdir=tmp_path / "web_workdir")
    app = create_app(settings)
    return TestClient(app)


def _wait_for_job(client: TestClient, job_id: str, timeout_s: float = 60.0) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        res = client.get(f"/api/jobs/{job_id}")
        assert res.status_code == 200
        status = res.json()
        if status["state"] in {"done", "error"}:
            return status
        time.sleep(0.2)
    pytest.fail(f"Job {job_id} se ni zaključil v {timeout_s}s")


class TestDBEndpointsHidden:
    def test_db_endpoints_are_hidden_by_default(self, plain_client: TestClient) -> None:
        assert plain_client.get("/api/db/health").status_code == 404
        assert plain_client.get("/api/db/recipes").status_code == 404
        assert plain_client.post("/api/db/validate", json={"recipe_id": 1}).status_code == 404


class TestDBEndpoints:
    def test_recipes_list(self, db_client: TestClient) -> None:
        res = db_client.get("/api/db/recipes")
        assert res.status_code == 200
        data = res.json()
        assert [r["recipe_id"] for r in data["recipes"]] == [2, 1]

    def test_recipes_filter(self, db_client: TestClient) -> None:
        res = db_client.get("/api/db/recipes", params={"q": "so3"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["recipes"]) == 1
        assert data["recipes"][0]["name"] == "MOD-SO3"

    def test_validate_unknown_recipe_returns_404(self, db_client: TestClient) -> None:
        res = db_client.post("/api/db/validate", json={"recipe_id": 999})
        assert res.status_code == 404

    def test_validate_runs_through_job_infrastructure(self, db_client: TestClient) -> None:
        res = db_client.post("/api/db/validate", json={"recipe_id": 5})
        assert res.status_code == 202
        job_id = res.json()["job_id"]

        status = _wait_for_job(db_client, job_id)
        assert status["state"] == "done"
        assert status["files"][0]["state"] == "done"

        res = db_client.get(f"/api/jobs/{job_id}/results")
        assert res.status_code == 200
        results = res.json()
        assert len(results["files"]) == 1
        file_result = results["files"][0]
        assert file_result["filename"] == "MES_receptura_5"
        # Poročila se generirajo skozi obstoječo infrastrukturo
        kinds = {r["kind"] for r in file_result["reports"]}
        assert "excel" in kinds and "json" in kinds

    def test_health_unconfigured(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        for name in ("MES_DB_HOST", "MES_DB_NAME", "MES_DB_USER", "MES_DB_PASSWORD"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.chdir(tmp_path)  # brez .env
        settings = Settings(workdir=tmp_path / "web_workdir", enable_db=True)
        client = TestClient(create_app(settings))

        res = client.get("/api/db/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "unconfigured"
        # Nobenih poverilnic v odgovoru
        assert "password" not in str(data).lower()
