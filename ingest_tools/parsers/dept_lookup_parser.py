"""Parser for department lookup data (Phụ lục 6)."""

import json
import logging
import re
from typing import Any

from parsers.base_parser import BaseParser
from parsers.table_parser import TableParser

logger = logging.getLogger(__name__)


class DeptLookupParser(BaseParser):
    """Parse organizational unit data from Phụ lục 6 into department JSON.

    Output format matches existing ump_departments.json structure.
    """

    def __init__(self):
        self.table_parser = TableParser()

    def parse(self, raw_data: Any) -> list[dict]:
        if isinstance(raw_data, str):
            return self.parse_text(raw_data)
        if isinstance(raw_data, list):
            return self.parse_rows(raw_data)
        return []

    def parse_text(self, text: str) -> list[dict]:
        records = self.table_parser.parse_phu_luc_6(text)
        return self._normalize(records)

    def parse_rows(self, rows: list[list[str]]) -> list[dict]:
        records = self.table_parser.parse_from_tables([rows])
        return self._normalize(records)

    def parse_tables(self, tables: list[list[list[str]]]) -> list[dict]:
        """Parse from pdfplumber table output directly.

        Handles the specific 4-column structure: [STT, _, Cap1, Cap2]
        Skips header rows and empty rows.
        """
        all_records = []
        for table in tables:
            for row in table:
                if not row or len(row) < 3:
                    continue
                stt = (row[0] or "").strip()
                if not stt or not stt.isdigit():
                    continue
                cap1 = (row[2] or "").strip() if len(row) > 2 else ""
                cap2 = (row[3] or "").strip() if len(row) > 3 else ""
                if not cap1 and not cap2:
                    continue
                all_records.append({
                    "stt": int(stt),
                    "tenDonViCap1": cap1,
                    "tenDonViCap2": cap2 if cap2 else None,
                })
        all_records.sort(key=lambda x: x["stt"])
        return all_records

    def _normalize(self, records: list[dict]) -> list[dict]:
        normalized = []
        seen_stt = set()

        for rec in records:
            stt = rec.get("STT", "").strip()
            if not stt or not stt.isdigit():
                continue
            if stt in seen_stt:
                continue
            seen_stt.add(stt)

            cap1 = rec.get("tenDonViCap1", "").strip()
            cap2 = rec.get("tenDonViCap2", "").strip()

            if not cap1 and not cap2:
                continue

            if cap1 and not cap2:
                cap2 = None

            normalized.append({
                "stt": int(stt),
                "tenDonViCap1": cap1,
                "tenDonViCap2": cap2,
            })

        normalized.sort(key=lambda x: x["stt"])
        return normalized

    def to_json(self, records: list[dict]) -> str:
        return json.dumps(records, ensure_ascii=False, indent=2)

    def validate_against_existing(
        self, new_data: list[dict], existing_path: str
    ) -> dict:
        """Compare new data against existing departments.json.

        Returns:
            Dict with keys: added, removed, modified
        """
        try:
            with open(existing_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"added": new_data, "removed": [], "modified": []}

        existing_map = {str(r["stt"]): r for r in existing}
        new_map = {str(r["stt"]): r for r in new_data}

        added = [r for stt, r in new_map.items() if stt not in existing_map]
        removed = [r for stt, r in existing_map.items() if stt not in new_map]
        modified = []
        for stt, new_r in new_map.items():
            if stt in existing_map:
                old_r = existing_map[stt]
                if (new_r.get("tenDonViCap1") != old_r.get("tenDonViCap1")
                        or new_r.get("tenDonViCap2") != old_r.get("tenDonViCap2")):
                    modified.append({
                        "stt": int(stt),
                        "old": old_r,
                        "new": new_r,
                    })

        return {"added": added, "removed": removed, "modified": modified}
