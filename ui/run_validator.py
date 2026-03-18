"""UI runner utilities.

This module provides utilities for running the validator with a GUI or CLI.
"""

from __future__ import annotations

import sys


def run_gui(gui_style: str = "classic") -> int:
    """Launch the GUI application.

    Args:
        gui_style: "classic" (default), "themed" (black/yellow), or "qt" (PyQt6).
            On failure of specific style, falls back to "classic".

    Returns:
        Exit code (0 = success).
    """
    # 1. Try PyQt6 if requested
    if gui_style == "qt":
        try:
            from validator_oop.ui.main_window_qt import run_app_qt

            run_app_qt()
            return 0
        except ImportError:
            print("Error: PyQt6 is not installed. Falling back to classic GUI.", file=sys.stderr)
        except Exception as e:
            print(f"QT GUI failed, using classic: {e}", file=sys.stderr)
        # Fall through to classic

    # 2. Check for Tkinter (required for classic and themed)
    try:
        import tkinter as tk  # noqa: F401
    except ImportError:
        print("Error: tkinter is required for the GUI.", file=sys.stderr)
        print("Use the CLI instead: python -m validator_oop <workbook>")
        return 1

    # 3. Try Themed Tkinter if requested
    if gui_style == "themed":
        try:
            from validator_oop.ui.main_window_themed import run_app_themed

            run_app_themed()
            return 0
        except Exception as e:
            print(f"Themed GUI failed, using classic: {e}", file=sys.stderr)
            # Fall through to classic

    # 4. Launch Classic Tkinter (default fallback)
    try:
        from validator_oop.ui.main_window import run_app

        run_app()
        return 0
    except Exception as e:
        print(f"Error launching GUI: {e}", file=sys.stderr)
        return 1


def run_cli(args: list[str] | None = None) -> int:
    """Run the CLI validator.

    Args:
        args: Command-line arguments.

    Returns:
        Exit code.
    """
    from validator_oop.main import main

    return main(args)


if __name__ == "__main__":
    sys.exit(run_gui())
