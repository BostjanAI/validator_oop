"""Read-only evaluation of two committed trees, including transitive Python helpers."""

import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from .cases import BOOK, SHEET, TARGETS

ROOT = Path(__file__).resolve().parent.parent


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def measure(ref, cases, *, repository=ROOT):
    snapshot = {"requested": ref, "commit": None, "app_version": None, "build": None}
    try:
        sha = git("rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}",
                  cwd=repository).stdout.decode().strip()
        snapshot["commit"] = sha
        archive = git("archive", "--format=tar", sha, "*.py", cwd=repository).stdout
        with tempfile.TemporaryDirectory() as tmp:
            # The canonical package name also works for differently named checkout folders.
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(Path(tmp) / "validator_oop", filter="data")
            requests = [{"function": TARGETS[c.target].function, "rows": c.rows(),
                         "sheet": SHEET, "book": BOOK} for c in cases]
            result = subprocess.run(
                [sys.executable, "-I", str(ROOT / "verification/worker.py"), tmp],
                cwd=tmp, input=json.dumps(requests), text=True, capture_output=True,
                check=True, timeout=90,
                env={"PATH": os.defpath, "TZ": "UTC", "LC_ALL": "C"},
            )
        payload = json.loads(result.stdout)
        observations = payload["observations"]
        if len(observations) != len(cases):
            raise ValueError("Incomplete worker output")
        snapshot.update(app_version=payload["app_version"], build=payload["build"])
        return snapshot, observations
    except subprocess.TimeoutExpired:
        snapshot.update(status="INCONCLUSIVE", reason="Python worker exceeded 90 seconds")
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
        snapshot.update(status="NOT VERIFIED", reason=(detail or str(exc))[-1500:])
    except (OSError, ValueError, KeyError, tarfile.TarError) as exc:
        snapshot.update(status="NOT VERIFIED", reason=str(exc))
    return snapshot, None
