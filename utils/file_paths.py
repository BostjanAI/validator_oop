"""File path utilities.

This module provides utilities for working with file paths in the validator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator


def find_excel_files(
    directory: str | Path,
    *,
    recursive: bool = True,
    extensions: tuple[str, ...] = (".xlsx", ".xlsm", ".xls"),
) -> Iterator[Path]:
    """Find all Excel files in a directory.

    Args:
        directory: Directory to search.
        recursive: If True, search subdirectories recursively.
        extensions: File extensions to match.

    Yields:
        Path objects for each Excel file found.

    Example:
        for excel_file in find_excel_files("./data"):
            print(excel_file)
    """
    root = Path(directory).expanduser().resolve()

    if not root.exists():
        return

    if not root.is_dir():
        if root.suffix.lower() in extensions:
            yield root
        return

    pattern = "**/*" if recursive else "*"

    for ext in extensions:
        for path in root.glob(f"{pattern}{ext}"):
            if path.is_file():
                yield path


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        Resolved Path object.
    """
    resolved = Path(path).expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def get_output_path(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    suffix: str = "_validated",
    extension: str = ".json",
) -> Path:
    """Generate an output path based on input file.

    Args:
        input_path: Input file path.
        output_dir: Output directory (default: same as input).
        suffix: Suffix to add before extension.
        extension: Output file extension.

    Returns:
        Output file path.

    Example:
        get_output_path("data/test.xlsx")
        # Returns: data/test_validated.json
    """
    input_path = Path(input_path).expanduser().resolve()

    if output_dir:
        out_dir = ensure_directory(output_dir)
    else:
        out_dir = input_path.parent

    stem = input_path.stem
    return out_dir / f"{stem}{suffix}{extension}"

