"""Generic table parser: rows from PDF -> structured records."""

import logging
import re
from typing import Optional

from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class TableParser(BaseParser):
    """Parse tabular data (from PDF tables or text lines) into structured records.

    Supports two input modes:
        - Table mode: list of rows (list of lists) from pdfplumber.
        - Text mode: raw text block, parsed line-by-line.
    """

    def __init__(self, columns: Optional[list[str]] = None):
        """
        Args:
            columns: Desired output column names.
                     If None, auto-detect from header row.
        """
        self.columns = columns

    def parse_from_tables(self, tables: list[list[list[str]]]) -> list[dict]:
        """Parse tables extracted by pdfplumber.

        Args:
            tables: List of tables, each table is list of rows, each row is list of cells.

        Returns:
            List of record dicts.
        """
        all_records = []
        for table in tables:
            if not table or len(table) < 2:
                continue
            header, data_rows = self._split_header(table)
            cols = self.columns or header
            for row in data_rows:
                record = self._row_to_record(row, cols)
                if record:
                    all_records.append(record)
        return all_records

    def parse(self, raw_data):
        if isinstance(raw_data, str):
            return self.parse_from_text(raw_data)
        if isinstance(raw_data, list):
            return self.parse_from_tables(raw_data)
        return []

    def parse_from_text(
        self, text: str, delimiter: str = "|"
    ) -> list[dict]:
        """Parse raw text line-by-line.

        For structured text (pipe-delimited or tabular),
        split lines into fields and map to columns.

        Args:
            text: Raw extracted text.
            delimiter: Field separator (default: pipe for MARC-style data).

        Returns:
            List of record dicts.
        """
        records = []
        lines = text.split("\n")
        header = None
        header_idx = 0

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            if delimiter in line:
                parts = [p.strip() for p in line.split(delimiter)]
                parts = [p for p in parts if p]
                if header is None and self._looks_like_header(parts):
                    header = parts
                    header_idx = i
                    continue
                if header:
                    cols = self.columns or header
                    record = self._row_to_record(parts, cols)
                    if record:
                        records.append(record)
            else:
                numeric = re.match(r"^(\d+)\s+(.+)$", line)
                if numeric:
                    record = {"STT": numeric.group(1), "raw": numeric.group(2)}
                    records.append(record)

        return records

    def parse_phu_luc_6(self, text: str) -> list[dict]:
        """Specialized parser for Phụ lục 6 (organizational units).

        Handles the specific format:
            STT
            Tên đơn vị cấp 1
            Tên đơn vị cấp 2

        Returns:
            List of dicts with keys: STT, tenDonViCap1, tenDonViCap2
        """
        records = []
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        i = 0
        skip_prefixes = [
            "phụ lục", "tài liệu quy ước", "tên tổ",
            "tên đơn vị", "trực thuộc", "đại học",
        ]

        while i < len(lines):
            line = lines[i]
            if any(line.lower().startswith(p) for p in skip_prefixes):
                i += 1
                continue

            stt_match = re.match(r"^(\d+)$", line)
            if stt_match:
                stt = stt_match.group(1)
                cap1 = ""
                cap2 = ""
                i += 1

                if i < len(lines) and not re.match(r"^\d+$", lines[i]):
                    cap1 = lines[i]
                    i += 1

                if i < len(lines) and not re.match(r"^\d+$", lines[i]):
                    cap2 = lines[i]
                    i += 1

                records.append({
                    "STT": stt,
                    "tenDonViCap1": cap1,
                    "tenDonViCap2": cap2,
                })
            else:
                i += 1

        return records

    def _split_header(
        self, table: list[list[str]]
    ) -> tuple[list[str], list[list[str]]]:
        header = table[0]
        data = table[1:]
        cleaned_header = []
        for h in header:
            val = (h or "").strip()
            cleaned_header.append(val if val else f"col_{len(cleaned_header)}")
        return cleaned_header, data

    def _row_to_record(
        self, row: list[str], columns: list[str]
    ) -> Optional[dict]:
        if not row or not columns:
            return None
        record = {}
        for idx, col in enumerate(columns):
            if idx < len(row):
                record[col] = row[idx].strip()
            else:
                record[col] = ""
        has_value = any(v for v in record.values() if v)
        return record if has_value else None

    def _looks_like_header(self, parts: list[str]) -> bool:
        keywords = ["stt", "tên", "đơn vị", "phòng", "trường", "khoa", "mã"]
        text = " ".join(parts).lower()
        return any(kw in text for kw in keywords)
