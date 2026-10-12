"""Tests for validation progress timestamps."""

from __future__ import annotations

import json
from datetime import datetime

from validator_oop.utils.validation_progress import record_run


def test_record_run_stores_local_time(tmp_path) -> None:
    progress = tmp_path / "validation_progress.json"
    before = datetime.now().astimezone().replace(microsecond=0)

    record_run(tmp_path / "receptura.xlsm", 1, 0, progress_path=progress)

    after = datetime.now().astimezone()
    stored = datetime.fromisoformat(
        json.loads(progress.read_text(encoding="utf-8"))["runs"][0]["date"]
    )

    assert stored.tzinfo is not None
    assert stored.utcoffset() == before.utcoffset()
    assert before <= stored <= after
