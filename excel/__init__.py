"""Excel I/O module.

This module provides utilities for reading and writing Excel workbooks:
- ExcelLoader: Main class for loading Excel files
- LoadedWorkbook: Container for loaded workbook data
- WorkbookParser: Converts worksheets to dictionaries
- ReportWriter: Writes validation reports to Excel/text files
- WorkbookFixer: Applies proposed fixes to workbooks
- SOPData, SOPRequirement: Classes for loading SOP data from Word documents
"""

from validator_oop.excel.excel_loader import ExcelLoader, LoadedWorkbook
from validator_oop.excel.report_writer import ReportWriter, WorkbookFixer
from validator_oop.excel.workbook_parser import WorkbookParser

try:
    from validator_oop.excel.sop_loader import SOPData, SOPRequirement
except ImportError:
    SOPData = None  # type: ignore
    SOPRequirement = None  # type: ignore

__all__ = [
    "ExcelLoader",
    "LoadedWorkbook",
    "ReportWriter",
    "WorkbookFixer",
    "WorkbookParser",
    "SOPData",
    "SOPRequirement",
]

