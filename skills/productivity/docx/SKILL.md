---
name: docx
description: "Create, read, edit Word .docx documents and templates."
version: 1.0.0
author: Arcen Agent (ported from Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [Word, DOCX, Documents, Office, Productivity]
    category: productivity
    related_skills: [pdf, xlsx, powerpoint, ocr-and-documents]
---

# DOCX Skill

Create, read, and edit Word documents — reports, memos, letters, letterheads,
tables of contents, tracked changes (redlining), and comments. A `.docx` is a
ZIP archive of XML files; this skill covers both the high-level creation path
and surgical XML editing.

## When to Use

Use this skill whenever the user wants to create, read, edit, or manipulate
Word documents (.docx) or Word templates (.dotx). Triggers include:

- Any mention of "Word doc", ".docx", ".dotx"
- Requests for a "report", "memo", "letter", or similar deliverable as a Word file
- Extracting or reorganizing content from .docx files
- Find-and-replace in Word files
- Inserting images into Word documents
- Tracked changes or comments in a Word doc

Do NOT use for PDFs (see the `pdf` skill), spreadsheets (`xlsx`), or
presentations (`powerpoint`).

## Prerequisites

```bash
# Creation (docx-js / Node)
npm ls docx --depth=0 2>/dev/null | grep -q docx || npm install docx

# Reading / conversion
which pandoc || brew install pandoc        # macOS
# Linux: sudo apt install -y pandoc

# Rendering / verification
which soffice || brew install libreoffice  # macOS
# Linux: sudo apt install -y libreoffice

# PDF → images (for verification)
which pdftoppm || brew install poppler     # macOS
# Linux: sudo apt install -y poppler-utils

# XML validation
pip install defusedxml lxml
```

## Quick Reference

| Task | Approach |
|---|---|
| **Create** a new document | Write a `docx` (npm) script — see gotchas below |
| **Edit** an existing document | `unzip` → edit `word/document.xml` → `zip` (docx-js cannot open existing files) |
| **Read** content | `pandoc -t markdown file.docx` (or `read_file`, which auto-extracts .docx text) |

## Creating with docx-js — Gotchas

Write the script and `require('docx')`. The model knows the API; these are the
footguns:

- **Page size defaults to A4.** For US Letter set
  `page: { size: { width: 12240, height: 15840 } }` (DXA; 1440 = 1″).
- **Landscape:** pass portrait dimensions and
  `orientation: PageOrientation.LANDSCAPE` — docx-js swaps width/height
  internally.
- **Tables need dual widths:** set `columnWidths` on the table AND `width` on
  every cell, both in `WidthType.DXA` (PERCENTAGE breaks in Google Docs).
  Column widths must sum to the table width.
- **Table shading:** use `ShadingType.CLEAR`, never `SOLID` (renders black).
- **Lists:** never insert `•` literally; use a `numbering` config with
  `LevelFormat.BULLET`.
- **`ImageRun` requires `type:`** (`"png"`, `"jpg"`, …).
- **`PageBreak` must be inside a `Paragraph`.**
- **Never use `\n`** — use separate `Paragraph` elements.
- **TOC:** headings must use built-in `HeadingLevel.*`; custom heading styles
  need `outlineLevel` set or they won't appear.
- **Don't use a table as a horizontal rule** — use a paragraph bottom border
  instead.
- **Dot-leader / right-aligned-on-same-line:** use `PositionalTab`
  (`alignment: PositionalTabAlignment.RIGHT`,
  `leader: PositionalTabLeader.DOT`) inside a `TextRun`, not literal `.` or
  space padding.

## Verify the Output

After writing a `.docx`, render it and look at it:

```bash
# Convert to PDF with LibreOffice (headless)
soffice --headless --convert-to pdf output.docx

# Convert PDF pages to images
pdftoppm -jpeg -r 100 output.pdf page

# Inspect each page image
ls page-*.jpg
```

`pdftoppm` zero-pads page numbers to the width of the page count
(`page-01.jpg`…`page-12.jpg`). Inspect each image visually (or with
`vision_analyze` if available) to confirm formatting looks right.

## Editing Existing Documents

docx-js **cannot open existing .docx files**. For surgical edits:

```bash
# 1. Unzip to inspect structure
mkdir docx_tmp && cd docx_tmp
unzip ../input.docx

# 2. Edit the XML (main content is in word/document.xml)
# Use your text editor or sed/awk for targeted find-replace

# 3. Repack
zip -r ../output.docx .
cd .. && rm -rf docx_tmp
```

For more complex edits (e.g., tracked changes, comments, styles), use
`python-docx`:

```bash
pip install python-docx
```

```python
from docx import Document

doc = Document("input.docx")
for para in doc.paragraphs:
    if "OLD TEXT" in para.text:
        para.runs[0].text = para.runs[0].text.replace("OLD TEXT", "NEW TEXT")
doc.save("output.docx")
```

## Common Patterns

### Create a report with heading, table, and image

```javascript
const { Document, Packer, Paragraph, Table, TableRow, TableCell,
        HeadingLevel, ImageRun, WidthType, ShadingType } = require('docx');
const fs = require('fs');

const doc = new Document({
  sections: [{
    children: [
      new Paragraph({ text: "My Report", heading: HeadingLevel.HEADING_1 }),
      new Paragraph({ text: "Introduction goes here." }),
      // Table example
      new Table({
        columnWidths: [4500, 4500],
        rows: [
          new TableRow({
            children: [
              new TableCell({ children: [new Paragraph("Col A")], width: { size: 4500, type: WidthType.DXA } }),
              new TableCell({ children: [new Paragraph("Col B")], width: { size: 4500, type: WidthType.DXA } }),
            ]
          }),
        ]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("report.docx", buffer);
  console.log("Done!");
});
```

### Read .docx content as Markdown

```bash
pandoc -t markdown input.docx -o output.md
cat output.md
```
