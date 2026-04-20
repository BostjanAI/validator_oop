"""Fail fast when generated artifacts are present in the repository tree."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IGNORED_DIRS = {".git", ".venv", "venv", ".idea", ".cursor"}
GENERATED_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    "analytics_out",
    "analytics_out_test",
    "build",
    "dist",
    "htmlcov",
}
GENERATED_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
}
GENERATED_FILE_NAMES = {
    ".coverage",
}


def iter_generated_paths(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)

        if any(part in IGNORED_DIRS for part in relative.parts):
            continue

        if path.is_dir() and path.name in GENERATED_DIR_NAMES:
            found.append(relative)
            continue

        if not path.is_file():
            continue

        if path.name in GENERATED_FILE_NAMES or any(path.name.startswith(f"{name}.") for name in GENERATED_FILE_NAMES):
            found.append(relative)
            continue

        if path.suffix in GENERATED_FILE_SUFFIXES:
            found.append(relative)

    return sorted(set(found))


def main() -> int:
    generated_paths = iter_generated_paths(ROOT)
    if not generated_paths:
        print("Workspace je cist: generated artefakti niso prisotni.")
        return 0

    print("Najdeni generated artefakti, ki ne sodijo v clean workspace:")
    for path in generated_paths:
        print(f" - {path.as_posix()}")
    print("\nPo potrebi jih odstrani ali razsiri .gitignore pred merge.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
