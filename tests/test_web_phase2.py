"""Testi za fazo 2 spletne aplikacije.

Pokriva:
- modul primerjave razdelkov (``excel/section_compare.py``),
- modul diff dveh verzij (``excel/recipe_diff.py``),
- avtentikacijo (prijava/odjava, role, zaščita endpointov),
- trajno zgodovino validacij,
- audit trail,
- API za primerjavo razdelkov in diff,
- WebSocket napredek.
"""

from __future__ import annotations

import io
import time
from pathlib import Path

import pytest

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover
    pytest.skip("openpyxl ni nameščen", allow_module_level=True)

try:
    from fastapi.testclient import TestClient

    from validator_oop.web.backend.app import create_app
    from validator_oop.web.backend.settings import Settings
except ImportError:
    pytest.skip("web odvisnosti (fastapi/httpx) niso nameščene", allow_module_level=True)

from validator_oop.core.constants import REQUIRED_COLUMNS
from validator_oop.excel.recipe_diff import diff_recipes
from validator_oop.excel.section_compare import compare_sections, parse_sections


# ============================================================================
# Pomožno: generiranje majhnih testnih receptur
# ============================================================================


def _make_rows(*rows: dict) -> list[list]:
    """Pretvori vrstice-slovarje v Excel vrstice po REQUIRED_COLUMNS."""
    out = []
    for row in rows:
        out.append([row.get(col, None) for col in REQUIRED_COLUMNS])
    return out


def _section(title: str, steps: list[tuple[str, str]]) -> list[dict]:
    """Razdelek: naslovna vrstica + koraki (št., navodilo)."""
    rows = [{"Tip objekta": "naslov", "Navodilo": title}]
    for step, instr in steps:
        rows.append({
            "št. Koraka": step,
            "Navodilo": instr,
            "Tip podatka": "opomba",
            "Tip objekta": "edit",
        })
    return rows


def _write_workbook(path: Path, sheets: dict[str, list[dict]]) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    for sheet_name, row_dicts in sheets.items():
        ws = wb.create_sheet(sheet_name)
        ws.append(REQUIRED_COLUMNS)
        for row in _make_rows(*row_dicts):
            ws.append(row)
    wb.save(path)
    return path


def _sample_sections() -> list[dict]:
    return [
        *_section("Priprava", [("1", "Pripravi posodo"), ("2", "Dodaj vodo")]),
        *_section("Doziranje", [("3", "Doziraj kemikalijo"), ("4", "Premešaj")]),
    ]


@pytest.fixture()
def matching_workbook(tmp_path: Path) -> Path:
    """Receptura z dvema listoma z enakimi razdelki."""
    return _write_workbook(
        tmp_path / "enaka.xlsx",
        {"Receptura": _sample_sections(), "Receptura_2": _sample_sections()},
    )


@pytest.fixture()
def mismatched_workbook(tmp_path: Path) -> Path:
    """Receptura z razlikami med listoma (dodaten korak + drugačno navodilo)."""
    sheet2 = [
        *_section("Priprava", [("1", "Pripravi posodo"), ("2", "Dodaj vodo"), ("3", "Dodatni korak")]),
        *_section("Doziranje", [("4", "Doziraj kemikalijo"), ("5", "Premešaj drugače")]),
    ]
    return _write_workbook(
        tmp_path / "razlicna.xlsx",
        {"Receptura": _sample_sections(), "Receptura_2": sheet2},
    )


# ============================================================================
# Modul: primerjava razdelkov
# ============================================================================


class TestSectionCompareModule:
    def test_parse_sections(self) -> None:
        rows = [
            {"Tip objekta": "naslov", "Navodilo": "Prvi"},
            {"št. Koraka": "1", "Navodilo": "Korak 1", "Tip objekta": "edit"},
            {"št. Koraka": "2", "Navodilo": "Korak 2", "Tip objekta": "edit"},
            {"Tip objekta": "naslov", "Navodilo": "Drugi"},
            {"št. Koraka": "3", "Navodilo": "Korak 3", "Tip objekta": "edit"},
        ]
        sections = parse_sections(rows, row_offset=2)
        assert len(sections) == 2
        assert sections[0].title == "Prvi"
        assert sections[0].step_count == 2
        assert sections[0].start_row == 2
        assert sections[1].title == "Drugi"
        assert sections[1].steps == ["3"]

    def test_rows_before_first_naslov_form_section_zero(self) -> None:
        rows = [
            {"št. Koraka": "1", "Navodilo": "Pred naslovom", "Tip objekta": "edit"},
            {"Tip objekta": "naslov", "Navodilo": "Prvi"},
        ]
        sections = parse_sections(rows)
        assert sections[0].index == 0
        assert sections[1].index == 1

    def test_matching_sheets_have_no_issues(self, matching_workbook: Path) -> None:
        result = compare_sections(matching_workbook)
        assert result.is_match
        assert result.issues == []
        assert result.base_sheet == "Receptura"
        assert set(result.sheets) == {"Receptura", "Receptura_2"}

    def test_mismatched_sheets_report_issues(self, mismatched_workbook: Path) -> None:
        result = compare_sections(mismatched_workbook)
        assert not result.is_match
        codes = {i["code"] for i in result.issues}
        assert "SECTION_STEP_COUNT_MISMATCH" in codes
        assert "SECTION_INSTRUCTION_MISMATCH" in codes

    def test_single_sheet_raises(self, tmp_path: Path) -> None:
        path = _write_workbook(tmp_path / "en_list.xlsx", {"Receptura": _sample_sections()})
        with pytest.raises(ValueError):
            compare_sections(path)


# ============================================================================
# Modul: diff dveh verzij
# ============================================================================


class TestRecipeDiffModule:
    def test_identical_files_have_no_changes(self, tmp_path: Path) -> None:
        a = _write_workbook(tmp_path / "a.xlsx", {"Receptura": _sample_sections()})
        b = _write_workbook(tmp_path / "b.xlsx", {"Receptura": _sample_sections()})
        diff = diff_recipes(a, b)
        assert not diff.has_changes

    def test_added_and_changed_rows(self, tmp_path: Path) -> None:
        rows_a = _sample_sections()
        rows_b = [dict(r) for r in rows_a]
        rows_b[1]["Navodilo"] = "Pripravi DRUGO posodo"          # spremenjena vrstica
        rows_b.append({"št. Koraka": "9", "Navodilo": "Nov korak", "Tip objekta": "edit"})

        a = _write_workbook(tmp_path / "a.xlsx", {"Receptura": rows_a})
        b = _write_workbook(tmp_path / "b.xlsx", {"Receptura": rows_b})
        diff = diff_recipes(a, b)

        assert diff.has_changes
        assert diff.summary["rows_added"] == 1
        assert diff.summary["rows_changed"] == 1
        sheet = next(s for s in diff.sheets if s.sheet == "Receptura")
        change = sheet.rows_changed[0]
        assert any(c.column == "Navodilo" and "DRUGO" in c.new for c in change.changes)

    def test_added_sheet_detected(self, tmp_path: Path) -> None:
        a = _write_workbook(tmp_path / "a.xlsx", {"Receptura": _sample_sections()})
        b = _write_workbook(
            tmp_path / "b.xlsx",
            {"Receptura": _sample_sections(), "Receptura_2": _sample_sections()},
        )
        diff = diff_recipes(a, b)
        added = [s for s in diff.sheets if s.status == "added"]
        assert [s.sheet for s in added] == ["Receptura_2"]


# ============================================================================
# API: pomožno
# ============================================================================


def _client(tmp_path: Path, **settings_overrides) -> TestClient:
    settings = Settings(workdir=tmp_path / "web_workdir", **settings_overrides)
    return TestClient(create_app(settings))


def _wait_for_job(client: TestClient, job_id: str, timeout_s: float = 120.0) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        res = client.get(f"/api/jobs/{job_id}")
        assert res.status_code == 200
        status = res.json()
        if status["state"] in {"done", "error"}:
            return status
        time.sleep(0.2)
    pytest.fail(f"Job {job_id} se ni zaključil v {timeout_s}s")


def _upload_and_wait(client: TestClient, workbook: Path) -> str:
    res = client.post(
        "/api/validate",
        files=[("recipes", (workbook.name, workbook.read_bytes(), "application/vnd.ms-excel"))],
    )
    assert res.status_code == 202
    job_id = res.json()["job_id"]
    _wait_for_job(client, job_id)
    return job_id


DEV_USERS = "tine:geslo1:tehnolog,quality:geslo2:qa,root:geslo3:admin"


# ============================================================================
# API: avtentikacija
# ============================================================================


class TestAuthDisabled:
    def test_me_reports_disabled(self, tmp_path: Path) -> None:
        client = _client(tmp_path)
        res = client.get("/api/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["auth_enabled"] is False
        assert data["user"] is not None  # anonimni uporabnik

    def test_endpoints_open_without_login(self, tmp_path: Path) -> None:
        client = _client(tmp_path)
        assert client.get("/api/history").status_code == 200
        assert client.get("/api/audit").status_code == 200


class TestAuthEnabled:
    @pytest.fixture()
    def client(self, tmp_path: Path) -> TestClient:
        return _client(tmp_path, auth_enabled=True, auth_mode="local", dev_users=DEV_USERS)

    def test_protected_endpoints_require_login(self, client: TestClient) -> None:
        assert client.get("/api/history").status_code == 401
        assert client.get("/api/audit").status_code == 401
        res = client.post(
            "/api/validate",
            files=[("recipes", ("r.xlsx", b"PK", "application/vnd.ms-excel"))],
        )
        assert res.status_code == 401

    def test_health_and_rules_stay_open(self, client: TestClient) -> None:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/rules").status_code == 200

    def test_wrong_password_rejected_and_audited(self, client: TestClient) -> None:
        res = client.post("/api/auth/login", json={"username": "tine", "password": "napacno"})
        assert res.status_code == 401

        # Uspešna prijava kot QA → v auditu mora biti neuspešen poskus
        client.post("/api/auth/login", json={"username": "quality", "password": "geslo2"})
        audit = client.get("/api/audit").json()
        actions = {e["action"] for e in audit["entries"]}
        assert "prijava_neuspesna" in actions
        assert "prijava" in actions

    def test_login_logout_flow(self, client: TestClient) -> None:
        res = client.post("/api/auth/login", json={"username": "tine", "password": "geslo1"})
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["username"] == "tine"
        assert data["user"]["role"] == "tehnolog"
        assert "mes_session" in res.cookies

        me = client.get("/api/auth/me").json()
        assert me["user"]["username"] == "tine"

        client.post("/api/auth/logout")
        me = client.get("/api/auth/me").json()
        assert me["user"] is None

    def test_tehnolog_cannot_view_audit(self, client: TestClient) -> None:
        client.post("/api/auth/login", json={"username": "tine", "password": "geslo1"})
        assert client.get("/api/audit").status_code == 403

    def test_qa_and_admin_can_view_audit(self, client: TestClient) -> None:
        client.post("/api/auth/login", json={"username": "quality", "password": "geslo2"})
        assert client.get("/api/audit").status_code == 200
        client.post("/api/auth/logout")
        client.post("/api/auth/login", json={"username": "root", "password": "geslo3"})
        assert client.get("/api/audit").status_code == 200

    def test_bearer_token_supported(self, tmp_path: Path) -> None:
        client = _client(tmp_path, auth_enabled=True, auth_mode="local", dev_users=DEV_USERS)
        res = client.post("/api/auth/login", json={"username": "root", "password": "geslo3"})
        token = res.cookies.get("mes_session")
        client.cookies.clear()
        res = client.get("/api/history", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200


# ============================================================================
# API: zgodovina + audit + lastništvo jobov
# ============================================================================


class TestHistoryAndAudit:
    def test_completed_job_lands_in_history(self, tmp_path: Path, matching_workbook: Path) -> None:
        client = _client(tmp_path)
        job_id = _upload_and_wait(client, matching_workbook)

        history = client.get("/api/history").json()
        assert history["total"] >= 1
        record = next(r for r in history["records"] if r["job_id"] == job_id)
        assert record["total_files"] == 1
        assert record["state"] == "done"

        detail = client.get(f"/api/history/{job_id}").json()
        assert detail["record"]["job_id"] == job_id
        assert detail["results"] is not None
        assert len(detail["results"]["files"]) == 1

        # Poročila so prenosljiva tudi iz trajne zgodovine
        reports = detail["results"]["files"][0]["reports"]
        assert reports, "poročila morajo obstajati"
        for rep in reports:
            dl = client.get(f"/api/history/{job_id}/files/0/report/{rep['filename']}")
            assert dl.status_code == 200, rep["filename"]
            assert len(dl.content) > 0

    def test_history_survives_job_cleanup(self, tmp_path: Path, matching_workbook: Path) -> None:
        client = _client(tmp_path)
        job_id = _upload_and_wait(client, matching_workbook)

        # Počisti začasne jobe (TTL 0) – zgodovina mora ostati
        client.app.state.job_manager.cleanup_expired(0)
        assert client.get(f"/api/jobs/{job_id}").status_code == 404
        assert client.get(f"/api/history/{job_id}").status_code == 200

    def test_validation_actions_audited(self, tmp_path: Path, matching_workbook: Path) -> None:
        client = _client(tmp_path)
        _upload_and_wait(client, matching_workbook)
        audit = client.get("/api/audit").json()
        actions = {e["action"] for e in audit["entries"]}
        assert "validacija_zagnana" in actions
        assert "validacija_zakljucena" in actions

    def test_tehnolog_sees_only_own_history(self, tmp_path: Path, matching_workbook: Path) -> None:
        client = _client(tmp_path, auth_enabled=True, auth_mode="local", dev_users=DEV_USERS)

        client.post("/api/auth/login", json={"username": "quality", "password": "geslo2"})
        qa_job = _upload_and_wait(client, matching_workbook)
        client.post("/api/auth/logout")

        client.post("/api/auth/login", json={"username": "tine", "password": "geslo1"})
        my_job = _upload_and_wait(client, matching_workbook)

        history = client.get("/api/history").json()
        job_ids = {r["job_id"] for r in history["records"]}
        assert my_job in job_ids
        assert qa_job not in job_ids
        assert client.get(f"/api/history/{qa_job}").status_code == 403

        # QA vidi vse
        client.post("/api/auth/logout")
        client.post("/api/auth/login", json={"username": "quality", "password": "geslo2"})
        history = client.get("/api/history").json()
        job_ids = {r["job_id"] for r in history["records"]}
        assert {my_job, qa_job} <= job_ids


# ============================================================================
# API: primerjava razdelkov + diff
# ============================================================================


class TestSectionCompareApi:
    def test_compare_endpoint(self, tmp_path: Path, mismatched_workbook: Path) -> None:
        client = _client(tmp_path)
        res = client.post(
            "/api/section-compare",
            files=[("recipe", (mismatched_workbook.name, mismatched_workbook.read_bytes(), "application/vnd.ms-excel"))],
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_match"] is False
        assert data["base_sheet"] == "Receptura"
        assert {i["code"] for i in data["issues"]} & {
            "SECTION_STEP_COUNT_MISMATCH",
            "SECTION_INSTRUCTION_MISMATCH",
        }

    def test_compare_rejects_single_sheet(self, tmp_path: Path) -> None:
        client = _client(tmp_path)
        path = _write_workbook(tmp_path / "en.xlsx", {"Receptura": _sample_sections()})
        res = client.post(
            "/api/section-compare",
            files=[("recipe", (path.name, path.read_bytes(), "application/vnd.ms-excel"))],
        )
        assert res.status_code == 422

    def test_compare_rejects_wrong_extension(self, tmp_path: Path) -> None:
        client = _client(tmp_path)
        res = client.post(
            "/api/section-compare",
            files=[("recipe", ("zlobna.exe", b"MZ", "application/octet-stream"))],
        )
        assert res.status_code == 415


class TestDiffApi:
    def test_diff_two_uploads(self, tmp_path: Path) -> None:
        client = _client(tmp_path)
        rows_b = _sample_sections()
        rows_b.append({"št. Koraka": "9", "Navodilo": "Nov korak", "Tip objekta": "edit"})
        a = _write_workbook(tmp_path / "v1.xlsx", {"Receptura": _sample_sections()})
        b = _write_workbook(tmp_path / "v2.xlsx", {"Receptura": rows_b})

        res = client.post(
            "/api/diff",
            files=[
                ("file_a", (a.name, a.read_bytes(), "application/vnd.ms-excel")),
                ("file_b", (b.name, b.read_bytes(), "application/vnd.ms-excel")),
            ],
        )
        assert res.status_code == 200
        data = res.json()
        assert data["has_changes"] is True
        assert data["summary"]["rows_added"] == 1

    def test_diff_requires_both_sides(self, tmp_path: Path, matching_workbook: Path) -> None:
        client = _client(tmp_path)
        res = client.post(
            "/api/diff",
            files=[("file_a", (matching_workbook.name, matching_workbook.read_bytes(), "application/vnd.ms-excel"))],
        )
        assert res.status_code == 422

    def test_diff_from_history(self, tmp_path: Path, matching_workbook: Path) -> None:
        client = _client(tmp_path)
        job_id = _upload_and_wait(client, matching_workbook)

        res = client.post(
            "/api/diff",
            data={
                "history_a": job_id,
                "history_a_file": matching_workbook.name,
                "history_b": job_id,
                "history_b_file": matching_workbook.name,
            },
        )
        assert res.status_code == 200
        assert res.json()["has_changes"] is False


# ============================================================================
# WebSocket napredek
# ============================================================================


class TestWebSocketProgress:
    def test_ws_streams_progress_until_done(self, tmp_path: Path, matching_workbook: Path) -> None:
        client = _client(tmp_path)
        res = client.post(
            "/api/validate",
            files=[("recipes", (matching_workbook.name, matching_workbook.read_bytes(), "application/vnd.ms-excel"))],
        )
        job_id = res.json()["job_id"]

        states = []
        with client.websocket_connect(f"/api/ws/jobs/{job_id}") as ws:
            while True:
                msg = ws.receive_json()
                states.append(msg["state"])
                if msg["state"] in {"done", "error"}:
                    break
        assert states[-1] == "done"

    def test_ws_unknown_job_closes(self, tmp_path: Path) -> None:
        client = _client(tmp_path)
        with pytest.raises(Exception):
            with client.websocket_connect("/api/ws/jobs/neobstojec") as ws:
                ws.receive_json()
