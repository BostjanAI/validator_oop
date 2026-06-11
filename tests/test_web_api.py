"""Testi za spletni API (web/backend) – FastAPI TestClient.

Ne testira validacijske logike (to pokrivajo obstoječi testi engine-a),
ampak HTTP plast: endpointe, validacijo uploadov, jobe in prenos poročil.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient

    from validator_oop.web.backend.app import create_app
    from validator_oop.web.backend.settings import Settings
except ImportError:  # spletne odvisnosti niso nameščene
    pytest.skip("web odvisnosti (fastapi/httpx) niso nameščene", allow_module_level=True)


SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "Poročilo" / "MOD-QA.xlsx"


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    settings = Settings(workdir=tmp_path / "web_workdir")
    app = create_app(settings)
    return TestClient(app)


def _wait_for_job(client: TestClient, job_id: str, timeout_s: float = 180.0) -> dict:
    """Polla stanje joba dokler ni 'done'/'error' ali poteče timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        res = client.get(f"/api/jobs/{job_id}")
        assert res.status_code == 200
        status = res.json()
        if status["state"] in {"done", "error"}:
            return status
        time.sleep(0.3)
    pytest.fail(f"Job {job_id} se ni zaključil v {timeout_s}s")


class TestBasicEndpoints:
    def test_health(self, client: TestClient) -> None:
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

    def test_rules_catalog(self, client: TestClient) -> None:
        res = client.get("/api/rules")
        assert res.status_code == 200
        data = res.json()
        assert len(data["rules"]) > 0
        assert len(data["codes"]) > 0
        assert data["version"]
        first = data["rules"][0]
        assert {"name", "code", "severity", "priority", "type", "description"} <= set(first)

    def test_unknown_job_returns_404(self, client: TestClient) -> None:
        assert client.get("/api/jobs/neobstojec").status_code == 404
        assert client.get("/api/jobs/neobstojec/results").status_code == 404
        assert client.get("/api/jobs/neobstojec/files/0/report/x.xlsx").status_code == 404
        assert client.get("/api/jobs/neobstojec/report/x.xlsx").status_code == 404


class TestUploadValidation:
    def test_validate_requires_recipes(self, client: TestClient) -> None:
        res = client.post("/api/validate")
        assert res.status_code == 422

    def test_rejects_wrong_recipe_extension(self, client: TestClient) -> None:
        res = client.post(
            "/api/validate",
            files=[("recipes", ("zlobna.exe", b"MZ...", "application/octet-stream"))],
        )
        assert res.status_code == 415
        assert "končnice" in res.json()["detail"]

    def test_rejects_wrong_sop_extension(self, client: TestClient) -> None:
        res = client.post(
            "/api/validate",
            files=[
                ("recipes", ("receptura.xlsx", b"PK", "application/octet-stream")),
                ("sop", ("sop.txt", b"x", "text/plain")),
            ],
        )
        assert res.status_code == 415

    def test_rejects_invalid_config_json(self, client: TestClient) -> None:
        res = client.post(
            "/api/validate",
            files=[("recipes", ("receptura.xlsx", b"PK", "application/octet-stream"))],
            data={"config": "{to ni json"},
        )
        assert res.status_code == 422


@pytest.mark.smoke
@pytest.mark.skipif(not SAMPLE.is_file(), reason="vzorčna datoteka MOD-QA.xlsx ni na voljo")
class TestEndToEnd:
    def test_single_file_validation_and_reports(self, client: TestClient) -> None:
        with SAMPLE.open("rb") as fh:
            res = client.post(
                "/api/validate",
                files=[("recipes", (SAMPLE.name, fh, "application/vnd.ms-excel"))],
            )
        assert res.status_code == 202
        job_id = res.json()["job_id"]

        status = _wait_for_job(client, job_id)
        assert status["state"] == "done"
        assert status["processed_files"] == 1

        res = client.get(f"/api/jobs/{job_id}/results")
        assert res.status_code == 200
        results = res.json()
        assert len(results["files"]) == 1
        fr = results["files"][0]
        assert fr["error"] is None
        assert isinstance(fr["is_valid"], bool)
        # Poročila so generirana in prenosljiva
        kinds = {r["kind"] for r in fr["reports"]}
        assert {"excel", "json", "txt", "management"} <= kinds
        for rep in fr["reports"]:
            dl = client.get(f"/api/jobs/{job_id}/files/0/report/{rep['filename']}")
            assert dl.status_code == 200, rep["filename"]
            assert len(dl.content) > 0
        # En sam file → brez skupnega poročila
        assert results["combined_reports"] == []

    def test_batch_validation_creates_combined_reports(self, client: TestClient) -> None:
        data = SAMPLE.read_bytes()
        res = client.post(
            "/api/validate",
            files=[
                ("recipes", ("prva.xlsx", data, "application/vnd.ms-excel")),
                ("recipes", ("druga.xlsx", data, "application/vnd.ms-excel")),
            ],
        )
        assert res.status_code == 202
        job_id = res.json()["job_id"]

        status = _wait_for_job(client, job_id, timeout_s=360.0)
        assert status["state"] == "done"
        assert status["total_files"] == 2
        assert status["processed_files"] == 2

        results = client.get(f"/api/jobs/{job_id}/results").json()
        assert len(results["files"]) == 2
        combined = results["combined_reports"]
        assert {"excel", "json", "txt", "management"} <= {r["kind"] for r in combined}
        for rep in combined:
            dl = client.get(f"/api/jobs/{job_id}/report/{rep['filename']}")
            assert dl.status_code == 200, rep["filename"]
            assert len(dl.content) > 0

    def test_report_path_traversal_blocked(self, client: TestClient) -> None:
        with SAMPLE.open("rb") as fh:
            res = client.post(
                "/api/validate",
                files=[("recipes", (SAMPLE.name, fh, "application/vnd.ms-excel"))],
            )
        job_id = res.json()["job_id"]
        _wait_for_job(client, job_id)
        res = client.get(f"/api/jobs/{job_id}/files/0/report/..%2F..%2Finput%2F{SAMPLE.name}")
        assert res.status_code == 404
