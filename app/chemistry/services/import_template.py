"""An empty results-table template whose headers the import recognises, for authors and their AI assistants."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

PROFILE_HEADERS = ["No.", "Compound", "RT", "RI exp", "RI lit", "Identification", "Level", "CAS", "m/z", "Adduct",
                   "S1", "S2", "Source"]
ISOLATION_HEADERS = ["Compound", "SMILES", "S1", "Purity (%)", "NMR experiments", "Solvent", "New or known",
                     "Literature DOI", "Optical rotation", "ECD", "CCDC", "Configuration type", "Configuration",
                     "Identification", "Level", "m/z", "Adduct", "Δ ppm", "Source"]
DETAILS = [
    ("Sample code", "As in the sample columns, e.g. S1"), ("Plant name", ""), ("Voucher and herbarium", ""),
    ("Plant part", ""), ("Fresh or dried", ""), ("Collection date", ""), ("Locality", ""), ("Phenological stage", ""),
    ("Preparation", "Essential oil or extract"), ("Method and parameters", ""), ("Plant material (g)", ""),
    ("Yield (% w/w)", ""), ("Technique", "GC-MS, GC-FID, LC-MS, LC-MS/MS, HPLC-DAD or isolation"), ("Column", ""),
    ("Stationary phase", ""), ("Temperature programme", ""), ("Carrier gas", ""), ("Alkane series", ""),
    ("RI type", "Temperature-programmed or isothermal"), ("Isolation procedure", ""), ("NMR spectrometer and frequency", ""),
    ("HRMS instrument and ionisation", ""),
]
README = [
    "How to use this template",
    "",
    "Fill one sheet: GC-MS profile (or another chromatographic technique) or Isolated compounds.",
    "Keep the headers. Rename S1, S2 to your sample codes and add one column per sample.",
    "Leave out columns you do not need. Write tr for trace and nd for not detected.",
    "Leave summary rows out, or the import will set them aside for you to check.",
    "The Source column is ignored by the import: use it for where each value comes from.",
    "Details is not imported: enter those values when you create the samples and preparations and in the run settings.",
    "",
    "To extract a published paper with your own AI assistant, use the prompt on the study page.",
]


def _sheet(book, title, headers, width=14):
    sheet = book.create_sheet(title)
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for index in range(1, len(headers) + 1):
        sheet.column_dimensions[sheet.cell(1, index).column_letter].width = width
    sheet.freeze_panes = "A2"
    return sheet


def template_workbook() -> bytes:
    book = Workbook()
    book.remove(book.active)
    _sheet(book, "GC-MS profile", PROFILE_HEADERS).column_dimensions["B"].width = 28
    isolated = _sheet(book, "Isolated compounds", ISOLATION_HEADERS)
    isolated.column_dimensions["A"].width = 24
    isolated.column_dimensions["B"].width = 40
    details = _sheet(book, "Details", ["Field", "Value", "Note"], width=30)
    for field, note in DETAILS:
        details.append([field, None, note or None])
    readme = book.create_sheet("Read me")
    for line in README:
        readme.append([line])
    readme["A1"].font = Font(bold=True)
    readme.column_dimensions["A"].width = 110
    for row in readme.iter_rows():
        row[0].alignment = Alignment(wrap_text=True)
    output = BytesIO()
    book.save(output)
    return output.getvalue()
