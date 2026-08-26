"""Zagon spletne aplikacije MES Excel Validator.

Uporaba:
    python run_web.py                 # zagon na 127.0.0.1:8000
    python run_web.py --host 0.0.0.0 --port 8080
    python run_web.py --reload        # razvojni način (samodejni reload)

Skripta poskrbi, da je nadrejeni imenik (kjer je paket ``validator_oop``)
na ``sys.path``, tako da deluje tudi ob neposrednem zagonu.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_importable() -> None:
    # run_web.py leži v paketu validator_oop; njegov nadrejeni imenik mora
    # biti na sys.path, da je "import validator_oop" mogoč.
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IPO Excel Validator – spletni strežnik")
    parser.add_argument("--host", default="127.0.0.1", help="Naslov (privzeto 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Vrata (privzeto 8000)")
    parser.add_argument("--reload", action="store_true", help="Razvojni način z auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Število uvicorn workerjev")
    args = parser.parse_args(argv)

    _ensure_importable()

    import uvicorn

    uvicorn.run(
        "validator_oop.web.backend.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
