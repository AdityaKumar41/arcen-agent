---
name: xlsx
description: "Create, read, edit Excel .xlsx spreadsheets and CSVs."
version: 1.0.0
author: Arcen Agent (ported from Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [Excel, XLSX, Spreadsheets, Office, Productivity]
    category: productivity
    related_skills: [docx, pdf, powerpoint]
---

# XLSX Skill

Create, read, and edit Excel workbooks — formulas, formatting, charts, data
cleaning, and format conversion. Every formula-bearing output must be
recalculated and error-free before delivery.

## When to Use

Use this skill any time a spreadsheet file is the primary input or output:

- Opening, reading, editing, or fixing an existing `.xlsx`, `.xlsm`, `.xltx`,
  `.csv`, or `.tsv` file
- Creating a new spreadsheet from scratch or from other data
- Converting between tabular formats
- Cleaning messy tabular data into a proper spreadsheet

Trigger whenever the user references a spreadsheet file by name or path —
even casually.

Do NOT trigger when the deliverable is a Word document (`docx` skill), HTML
report, standalone script, or Google Sheets API integration. For finance-grade
modeling conventions (DCF, LBO, three-statement), use stricter standards on
top of this skill.

## Prerequisites

```bash
pip install openpyxl pandas "markitdown[xlsx]"

# LibreOffice for formula recalculation (mandatory when file has formulas)
which soffice || brew install libreoffice     # macOS
# Linux: sudo apt install -y libreoffice
```

## Quick Reference

| Task | Approach |
|---|---|
| **Create** or **edit** with formulas/formatting | `openpyxl` — see gotchas below |
| **Bulk data** in or out | `pandas` (`read_excel`, `to_excel`) |
| **Quick look** at a sheet | `markitdown file.xlsx` — `## SheetName` per sheet; reads `.xlsm` too |
| **Read** a model (formulas *and* values) | two `load_workbook` passes — see gotchas |

## Requirements for Every Output

- **Professional font** (Arial, Times New Roman) throughout, unless the user
  says otherwise.
- **Zero formula errors.** Never deliver while any formula cell shows an error.
  If you think an error predates you, prove it: load the *original* with
  `data_only=True` and inspect that cell. An error you introduced looks
  exactly like one you inherited.
- **Use formulas, never hardcoded results.** Write
  `sheet['B10'] = '=SUM(B2:B9)'`, not the Python-computed total. The sheet
  must recalculate when its inputs change.
- **Follow the user's spec literally.** Exact tab names, exact column headers,
  and the formula they spelled out. A redesign that computes something else
  fails, however elegant.
- **Document every assumption and hardcoded number** where the reader will see
  it — a cell comment, or an adjacent cell at a table's end. Cite a real
  source when one exists; when the number came from the user, say so plainly.
- **A workbook *you create* for someone to fill in** needs a short legend
  naming which cells to edit, and one example row of realistic values showing
  the expected format. Never add such a row to a file you were asked to edit.
- **Editing an existing file: match its conventions exactly.** They override
  every guideline here. Find its designated input cells first — a distinct
  font color, fill, or shading marks them — write only there, and leave every
  existing formula untouched.

## Recalculate (Mandatory When the File Contains Formulas)

`openpyxl` writes formulas as strings with **no cached values**. Until you
recalculate, every formula cell reads back as `None` to anything reading
cached values — `pandas`, `load_workbook(data_only=True)`, and most
previewers.

```bash
# Recalculate using LibreOffice (rewrites file in place)
soffice --headless --calc --infilter="Calc MS Excel 2007 XML" \
        --convert-to xlsx output.xlsx
```

Or use this Python helper script:

```python
#!/usr/bin/env python3
"""recalc.py — Recalculate all formulas in an xlsx file via LibreOffice."""
import subprocess, sys, json, pathlib

def recalc(path: str, timeout: int = 30) -> dict:
    p = pathlib.Path(path).resolve()
    result = subprocess.run(
        ["soffice", "--headless", "--calc", "--infilter=Calc MS Excel 2007 XML",
         "--convert-to", "xlsx", "--outdir", str(p.parent), str(p)],
        capture_output=True, text=True, timeout=timeout
    )
    return {"status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout, "stderr": result.stderr}

if __name__ == "__main__":
    print(json.dumps(recalc(sys.argv[1])))
```

## Common Operations

### Create a Workbook with Formulas and Formatting

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "Budget"

# Headers
headers = ["Month", "Revenue", "Expenses", "Profit"]
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.font = Font(bold=True, name="Arial", size=11)
    cell.fill = PatternFill(fill_type="solid", fgColor="4472C4")
    cell.font = Font(bold=True, name="Arial", size=11, color="FFFFFF")
    cell.alignment = Alignment(horizontal="center")

# Data rows
data = [
    ("January", 50000, 35000),
    ("February", 55000, 38000),
    ("March", 60000, 40000),
]
for row_idx, (month, rev, exp) in enumerate(data, 2):
    ws.cell(row=row_idx, column=1, value=month)
    ws.cell(row=row_idx, column=2, value=rev)
    ws.cell(row=row_idx, column=3, value=exp)
    # Formula in column D
    ws.cell(row=row_idx, column=4, value=f"=B{row_idx}-C{row_idx}")

# Totals row
last_row = len(data) + 1
total_row = last_row + 1
ws.cell(row=total_row, column=1, value="TOTAL")
ws.cell(row=total_row, column=2, value=f"=SUM(B2:B{last_row})")
ws.cell(row=total_row, column=3, value=f"=SUM(C2:C{last_row})")
ws.cell(row=total_row, column=4, value=f"=SUM(D2:D{last_row})")

# Column widths
for col in range(1, 5):
    ws.column_dimensions[get_column_letter(col)].width = 15

wb.save("budget.xlsx")
print("Saved budget.xlsx — remember to recalculate formulas!")
```

### Read a Workbook (Formulas AND Cached Values)

```python
from openpyxl import load_workbook

# Read formulas (strings) — use this to inspect/edit formulas
wb_formulas = load_workbook("input.xlsx")
ws = wb_formulas.active
print(ws["B10"].value)   # "=SUM(B2:B9)"

# Read cached values — what was computed last time Excel/LibreOffice saved
wb_values = load_workbook("input.xlsx", data_only=True)
ws_v = wb_values.active
print(ws_v["B10"].value)   # 12345.67  (or None if never recalculated)
```

### Bulk Data with Pandas

```python
import pandas as pd

# Read all sheets
dfs = pd.read_excel("data.xlsx", sheet_name=None)  # dict of DataFrames
for name, df in dfs.items():
    print(f"Sheet: {name}")
    print(df.head())

# Write DataFrame to xlsx
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
df.to_excel("output.xlsx", index=False, sheet_name="Data")
```

### Clean Messy CSV → Formatted XLSX

```python
import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook

df = pd.read_csv("messy.csv")
# Clean: strip whitespace, drop empty rows
df.columns = df.columns.str.strip()
df = df.dropna(how="all").reset_index(drop=True)

wb = Workbook()
ws = wb.active
ws.title = "Cleaned"

header_fill = PatternFill(fill_type="solid", fgColor="2F75B6")
header_font = Font(bold=True, color="FFFFFF", name="Arial")

for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
    for c_idx, value in enumerate(row, 1):
        cell = ws.cell(row=r_idx, column=c_idx, value=value)
        if r_idx == 1:
            cell.fill = header_fill
            cell.font = header_font

wb.save("cleaned.xlsx")
```

## Gotchas

- **openpyxl cannot read `.xlsb` files.** Convert to `.xlsx` first:
  `soffice --headless --calc --convert-to xlsx file.xlsb`
- **`data_only=True` returns `None` for formula cells** if the file was never
  opened in Excel/LibreOffice after last edit. Always recalculate first.
- **Date cells:** openpyxl returns Python `datetime` objects. Format with
  `cell.number_format = "YYYY-MM-DD"` for display.
- **Merged cells:** avoid merging when the data needs to be machine-readable.
  If you must merge: `ws.merge_cells("A1:D1")` — only the top-left cell
  retains the value.
- **Charts:** use `openpyxl.chart` module; charts are embedded XML and
  recalculated by Excel/LibreOffice, not openpyxl.
- **`.xlsm` (macro-enabled):** openpyxl can read/write `.xlsm` but cannot
  run or modify VBA macros. Macros will be preserved if you don't touch them.
