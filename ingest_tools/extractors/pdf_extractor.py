"""PDF extractor using pdfplumber (tables) + pymupdf (text fallback)."""

import logging
from typing import Optional

from extractors.base_extractor import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """Extract text and tables from PDF documents.

    Strategy:
        1. Try pdfplumber for table detection (structured tables with borders).
        2. Fallback to pymupdf for plain text extraction.
        3. Detect if PDF is image-only (no extractable text).
    """

    def extract(
        self,
        file_path: str,
        pages: Optional[list[int]] = None,
    ) -> ExtractionResult:
        self._validate_file(file_path)
        logger.info(f"Extracting PDF: {file_path}")

        result = ExtractionResult()

        try:
            result = self._extract_with_pdfplumber(file_path, pages)
            if result.tables:
                logger.info(f"Found {len(result.tables)} table(s) via pdfplumber")
                return result
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        try:
            result = self._extract_with_pymupdf(file_path, pages)
            if result.raw_text.strip():
                logger.info(f"Extracted text via pymupdf ({len(result.raw_text)} chars)")
                return result
        except Exception as e:
            logger.warning(f"pymupdf failed: {e}")

        result.is_image_only = True
        result.error = "No extractable text found. PDF may be image-based."
        logger.warning("PDF appears to be image-only")
        return result

    def _extract_with_pdfplumber(
        self, file_path: str, pages: Optional[list[int]]
    ) -> ExtractionResult:
        import pdfplumber

        result = ExtractionResult()
        with pdfplumber.open(file_path) as pdf:
            result.pages = len(pdf.pages)
            target_pages = self._resolve_pages(pages, result.pages)

            all_text_parts = []
            for page_num in target_pages:
                page = pdf.pages[page_num - 1]
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        cleaned = self._clean_table(table)
                        if cleaned:
                            result.tables.append(cleaned)
                text = page.extract_text() or ""
                all_text_parts.append(text)

            result.raw_text = "\n\n".join(all_text_parts)
        return result

    def _extract_with_pymupdf(
        self, file_path: str, pages: Optional[list[int]]
    ) -> ExtractionResult:
        import fitz

        result = ExtractionResult()
        doc = fitz.open(file_path)
        result.pages = len(doc)
        target_pages = self._resolve_pages(pages, result.pages)

        all_text_parts = []
        for page_num in target_pages:
            page = doc[page_num - 1]
            text = page.get_text("text")
            all_text_parts.append(text)

        result.raw_text = "\n\n".join(all_text_parts)
        doc.close()
        return result

    def _resolve_pages(
        self, pages: Optional[list[int]], total: int
    ) -> list[int]:
        if pages is None:
            return list(range(1, total + 1))
        return [p for p in pages if 1 <= p <= total]

    def _clean_table(self, table: list[list]) -> list[list[str]]:
        cleaned = []
        for row in table:
            cleaned_row = []
            for cell in row:
                val = (cell or "").strip()
                cleaned_row.append(val)
            cleaned.append(cleaned_row)
        cleaned = [row for row in cleaned if any(c for c in row)]
        return cleaned if len(cleaned) >= 2 else []
