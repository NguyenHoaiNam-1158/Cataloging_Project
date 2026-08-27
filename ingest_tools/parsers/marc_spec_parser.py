"""Parser for MARC21 specification documents (Phụ lục 1)."""

import json
import logging
import re
from typing import Any

from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class MarcSpecParser(BaseParser):
    """Parse MARC21 cataloging specification from raw text into validation rules.

    Input: Raw text from Phụ lục 1 (Google Doc export).
    Output: Structured JSON with MARC field rules per document type.
    """

    FIELD_PATTERN = re.compile(
        r"^(\d{3})\s*"  # Tag number
    )

    def parse(self, raw_data: Any) -> list[dict]:
        if isinstance(raw_data, str):
            return self.parse_text(raw_data)
        return []

    def parse_text(self, text: str) -> list[dict]:
        rules = []
        current_field = None
        current_rule = {}

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            match = self.FIELD_PATTERN.match(line)
            if match:
                if current_rule:
                    rules.append(current_rule)
                tag = match.group(1)
                current_rule = {
                    "tag": tag,
                    "ind1": "",
                    "ind2": "",
                    "subfields": "",
                    "field_name": "",
                    "repeatable": "",
                    "description": "",
                    "reference_url": "",
                    "notes": "",
                    "mandatory": "",
                }
                self._parse_tab_fields(line, current_rule)
            elif current_rule:
                current_rule["description"] += " " + line

        if current_rule:
            rules.append(current_rule)

        for rule in rules:
            rule["description"] = rule["description"].strip()

        return rules

    def parse_json_rules(self, raw_data: Any) -> dict:
        """Parse a pre-structured JSON of MARC rules.

        Used when we already have structured data from Google Docs/Sheets.
        """
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        rules_by_type = {
            "luan_van": {"required": [], "optional": [], "fields": {}},
            "luan_an": {"required": [], "optional": [], "fields": {}},
            "khoa_luan": {"required": [], "optional": [], "fields": {}},
            "sach": {"required": [], "optional": [], "fields": {}},
            "tap_chi": {"required": [], "optional": [], "fields": {}},
        }

        for rule in raw_data:
            tag = rule.get("tag", "")
            mandatory = rule.get("mandatory", "").lower()
            for doc_type in rules_by_type:
                if mandatory.startswith("bắt buộc") or mandatory == "required":
                    rules_by_type[doc_type]["required"].append(tag)
                else:
                    rules_by_type[doc_type]["optional"].append(tag)
                rules_by_type[doc_type]["fields"][tag] = rule

        return rules_by_type

    def _parse_tab_fields(self, line: str, rule: dict) -> None:
        parts = re.split(r"\t+", line)
        if len(parts) >= 2:
            rule["tag"] = parts[0].strip()
        if len(parts) >= 3:
            rule["ind1"] = parts[1].strip()
        if len(parts) >= 4:
            rule["ind2"] = parts[2].strip()
        if len(parts) >= 5:
            rule["subfields"] = parts[3].strip()
        if len(parts) >= 6:
            rule["field_name"] = parts[4].strip()
        if len(parts) >= 7:
            rule["repeatable"] = parts[5].strip()
        if len(parts) >= 8:
            rule["description"] = parts[6].strip()
        if len(parts) >= 9:
            rule["reference_url"] = parts[7].strip()
        if len(parts) >= 10:
            rule["notes"] = parts[8].strip()
        if len(parts) >= 11:
            rule["mandatory"] = parts[9].strip()
