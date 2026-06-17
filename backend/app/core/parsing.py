"""Extract text from uploaded documents, tagged with a page/section label.

The page label is what gets surfaced in source citations:
- PDF: 1-based page number (int)
- XLSX: sheet name (str), one "page" per sheet
- DOCX: None — Word documents have no fixed page boundaries, so the whole
  document is returned as a single block (paragraph breaks are preserved
  so the chunker can still split on them)
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pdfplumber
from docx import Document


@dataclass
class PageContent:
    text: str
    page: int | str | None


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls"}


def parse_document(file_path: str | Path, filename: str) -> list[PageContent]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(file_path)
    if suffix == ".docx":
        return _parse_docx(file_path)
    if suffix in (".xlsx", ".xls"):
        return _parse_xlsx(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")


def _parse_pdf(file_path: str | Path) -> list[PageContent]:
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(PageContent(text=text, page=index))
    return pages


def _parse_docx(file_path: str | Path) -> list[PageContent]:
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs)
    return [PageContent(text=text, page=None)] if text else []


def _parse_xlsx(file_path: str | Path) -> list[PageContent]:
    sheets = pd.read_excel(file_path, sheet_name=None, dtype=str)
    pages = []
    for sheet_name, df in sheets.items():
        text = df.fillna("").to_csv(index=False)
        if text.strip():
            pages.append(PageContent(text=text, page=sheet_name))
    return pages
