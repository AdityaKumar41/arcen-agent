---
name: pdf
description: "Create, merge, split, fill, and secure PDF files."
version: 1.0.0
author: Arcen Agent (ported from Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [PDF, Documents, Forms, Office, Productivity]
    category: productivity
    related_skills: [ocr-and-documents, nano-pdf, docx, xlsx]
---

# PDF Skill

Create, combine, split, transform, and secure PDF files — merging, page
manipulation, form filling, watermarks, encryption, and text/table extraction.

For heavy text extraction from scanned documents prefer the `ocr-and-documents`
skill; for natural-language edits to existing PDF text prefer `nano-pdf`.

## When to Use

Use this skill whenever the user wants to do anything with PDF files:

- Reading or extracting text/tables from PDFs
- Combining or merging multiple PDFs
- Splitting PDFs apart
- Rotating, cropping, or reordering pages
- Adding watermarks or headers/footers
- Creating new PDFs from scratch
- Filling PDF forms
- Encrypting / decrypting PDFs
- Extracting images from PDFs
- OCR on scanned PDFs

If the user mentions a `.pdf` file or asks to produce one, use this skill.

## Prerequisites

```bash
pip install pypdf pdfplumber reportlab

# poppler CLI tools (pdftotext, pdftoppm, pdfimages)
which pdftotext || brew install poppler          # macOS
# Linux: sudo apt install -y poppler-utils

# qpdf for CLI merge/split/decrypt
which qpdf || brew install qpdf                  # macOS
# Linux: sudo apt install -y qpdf

# OCR extras (optional)
pip install pytesseract pdf2image
which tesseract || brew install tesseract        # macOS
# Linux: sudo apt install -y tesseract-ocr
```

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| Merge PDFs | pypdf | `writer.add_page(page)` per page |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs | reportlab | Canvas or Platypus |
| Command-line merge/split | qpdf | `qpdf --empty --pages ...` |
| OCR scanned PDFs | pytesseract | Convert to images first (or use `ocr-and-documents`) |
| Edit existing text | `nano-pdf` skill | natural-language edit via nano-pdf |

## Common Operations

### Merge / Split / Rotate (pypdf)

```python
from pypdf import PdfReader, PdfWriter

# ── Merge ──────────────────────────────────────────────
writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf"]:
    for page in PdfReader(pdf_file).pages:
        writer.add_page(page)
with open("merged.pdf", "wb") as f:
    writer.write(f)

# ── Split: one file per page ──────────────────────────
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    w = PdfWriter()
    w.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as f:
        w.write(f)

# ── Rotate ────────────────────────────────────────────
reader = PdfReader("input.pdf")
writer = PdfWriter()
for page in reader.pages:
    page.rotate(90)   # clockwise 90°
    writer.add_page(page)
with open("rotated.pdf", "wb") as f:
    writer.write(f)
```

### Extract Text (pdfplumber)

```python
import pdfplumber

with pdfplumber.open("input.pdf") as pdf:
    for page in pdf.pages:
        print(page.extract_text())
```

### Extract Tables (pdfplumber)

```python
import pdfplumber

with pdfplumber.open("input.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Page {i+1}, Table {j+1}:")
            for row in table:
                print(row)
```

### Create a PDF from Scratch (reportlab)

```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas("output.pdf", pagesize=letter)
width, height = letter

c.setFont("Helvetica-Bold", 24)
c.drawString(72, height - 100, "My Document Title")

c.setFont("Helvetica", 12)
c.drawString(72, height - 140, "Body text goes here.")

c.save()
```

### Add a Watermark

```python
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# Create watermark page
packet = io.BytesIO()
c = canvas.Canvas(packet, pagesize=letter)
c.setFont("Helvetica", 60)
c.setFillAlpha(0.1)
c.rotate(45)
c.drawString(100, 0, "CONFIDENTIAL")
c.save()
packet.seek(0)
watermark = PdfReader(packet).pages[0]

# Apply to every page
reader = PdfReader("input.pdf")
writer = PdfWriter()
for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)
with open("watermarked.pdf", "wb") as f:
    writer.write(f)
```

### Encrypt / Decrypt

```python
from pypdf import PdfReader, PdfWriter

# Encrypt
reader = PdfReader("input.pdf")
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)
writer.encrypt("my_password")
with open("encrypted.pdf", "wb") as f:
    writer.write(f)

# Decrypt
reader = PdfReader("encrypted.pdf")
if reader.is_encrypted:
    reader.decrypt("my_password")
# now reader.pages is accessible
```

### CLI Merge with qpdf

```bash
# Merge page ranges from two PDFs
qpdf --empty --pages doc1.pdf 1-3 doc2.pdf 4-6 -- merged.pdf

# Linearize (optimize for web / fast first-page)
qpdf --linearize input.pdf output.pdf
```

### OCR a Scanned PDF

```python
from pdf2image import convert_from_path
import pytesseract

pages = convert_from_path("scanned.pdf", dpi=300)
text = ""
for page in pages:
    text += pytesseract.image_to_string(page)
print(text)
```

## Verify the Output

After creating or modifying a PDF, inspect it:

```bash
# Quick text check
pdftotext output.pdf -

# Page count
pdfinfo output.pdf | grep Pages

# Visual check — render pages as images
pdftoppm -jpeg -r 100 output.pdf page
ls page-*.jpg   # inspect each with vision_analyze or open manually
```

## Gotchas

- **`pypdf` vs `PyPDF2`:** `pypdf` is the maintained successor; avoid `PyPDF2`.
- **Form filling:** Use `pypdf`'s `update_page_form_field_values()` for
  fillable AcroForms; for flat PDFs without form fields you'll need to overlay
  new content with reportlab.
- **Font embedding:** reportlab embeds fonts by default for standard fonts;
  for custom fonts use `pdfmetrics.registerFont()`.
- **pdfplumber vs pdftotext:** pdfplumber gives richer layout info (bounding
  boxes, tables); pdftotext is faster for plain text extraction.
- **Large files:** process page-by-page with a generator to avoid loading the
  entire PDF into memory.
