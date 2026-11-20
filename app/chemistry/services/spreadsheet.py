"""Read an author's results table (.xlsx or .csv) and parse its cells."""

import csv
import math
import re
from datetime import date, datetime
from io import BytesIO, StringIO
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 1000
MAX_SAMPLES = 100
MAX_COLUMNS = 300
PREVIEW_ROWS = 20
NOT_DETECTED = {"", "-", "–", "—", "nd", "n.d.", "n.d", "n/d"}
MARKS = r"[*†‡§#]+|[a-zA-Z]{1,2}|[ªº¹²³ᵃ-ᵡⁱⁿ⁰-⁹]+"
NUMBER = re.compile(rf"^(?P<number>\d+(?:[.,]\d+)?|[.,]\d+)\s*(?P<marks>{MARKS})?$")
TRACE = re.compile(rf"^(tr|t|trace)\.?\s*(?P<marks>{MARKS})?$", re.IGNORECASE)
LOQ = re.compile(r"^<\s*loq$", re.IGNORECASE)
SUMMARY = [re.compile(pattern, re.IGNORECASE) for pattern in (
    r"^(grand\s+)?(total|sum|σ|∑)\b", r"\btotal\b.*\b(identified|compounds|components)\b",
    r"^(total\s+)?(identified|unidentified)(\s+(compounds|components))?\s*(\(%\))?$",
    r"^(mono|sesqui|di|tri)terpene\s+hydrocarbons$", r"^oxygenated\s+(mono|sesqui|di|tri)terpenes$",
    r"^(non-terpenic|other|others)(\s+compounds)?$", r"^yield\b", r"^number\s+of\s+(compounds|components)\b",
)]


def cell_ref(column: int, row: int) -> str:
    return f"{get_column_letter(column + 1)}{row}"


def _cell(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _trim(rows):
    rows = [list(row) for row in rows]
    while rows and all(cell is None for cell in rows[-1]):
        rows.pop()
    width = max((index + 1 for row in rows for index, cell in enumerate(row) if cell is not None), default=0)
    return [row[:width] + [None] * (width - len(row)) for row in rows]


def read_table(content: bytes, kind: str) -> dict[str, list[list]]:
    """Sheet name → rows of cells (text, number or None). A CSV has one sheet, named CSV."""
    if len(content) > MAX_BYTES:
        raise ValueError("The file exceeds the 5 MB limit.")
    if kind == "xlsx":
        try:
            workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        except (BadZipFile, InvalidFileException, KeyError, ValueError, OSError) as error:
            raise ValueError("The file is not a readable .xlsx workbook.") from error
        try:
            return {sheet.title: _trim([_cell(value) for value in row] for row in sheet.iter_rows(
                max_row=MAX_ROWS + 60, max_col=MAX_COLUMNS, values_only=True)) for sheet in workbook.worksheets}
        finally:
            workbook.close()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialect = csv.Sniffer().sniff(text[:20000], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = []
    for row in csv.reader(StringIO(text, newline=""), dialect):
        if len(rows) > MAX_ROWS + 60:
            break
        rows.append([_cell(value) for value in row[:MAX_COLUMNS]])
    return {"CSV": _trim(rows)}


def parse_number(cell):
    """A number from a cell, accepting a decimal comma. Returns (value, footnote marks or None)."""
    if isinstance(cell, float):
        return cell, None
    match = NUMBER.match(cell)
    if not match:
        raise ValueError
    return float(match["number"].replace(",", ".")), match["marks"]


def parse_value(cell) -> dict:
    """A sample cell: a number, trace, <LOQ or not detected. Footnote marks are stripped and reported."""
    if cell is None or (isinstance(cell, str) and cell.casefold() in NOT_DETECTED):
        return {"status": "not_detected", "value": None, "qualifier": None, "marks": None}
    if isinstance(cell, str):
        trace = TRACE.match(cell)
        if trace:
            return {"status": "measured", "value": None, "qualifier": "trace", "marks": trace["marks"]}
        if LOQ.match(cell):
            return {"status": "measured", "value": None, "qualifier": "<LOQ", "marks": None}
    value, marks = parse_number(cell)
    return {"status": "measured", "value": value, "qualifier": None, "marks": marks}


def evidence_text(cell) -> str:
    """Evidence cells as text, so 6654.0 from a spreadsheet reads as 6654."""
    if cell is None:
        return ""
    if isinstance(cell, float):
        return str(int(cell)) if cell.is_integer() else repr(cell)
    return cell


def is_summary(name: str) -> bool:
    return any(pattern.search(name.strip()) for pattern in SUMMARY)
