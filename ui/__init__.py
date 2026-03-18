"""UI module (optional).

This package provides optional graphical user interface components:
- ValidatorApp: Tkinter-based main window (classic)
- ValidatorAppThemed: Black/yellow themed main window
- run_app: Function to launch the classic GUI
- run_app_themed: Function to launch the themed GUI
- run_gui: Function to launch the GUI (choice via gui_style=)
- run_cli: Function to run the CLI validator
"""

from validator_oop.ui.main_window import ValidatorApp, run_app
from validator_oop.ui.main_window_themed import ValidatorAppThemed, run_app_themed
from validator_oop.ui.run_validator import run_cli, run_gui

__all__ = [
    "ValidatorApp",
    "ValidatorAppThemed",
    "run_app",
    "run_app_themed",
    "run_cli",
    "run_gui",
]
