"""Parser for grading rubric data from Google Sheets (CSV export)."""

import csv
import io
import json
import logging
from typing import Any

from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class RubricParser(BaseParser):
    """Parse grading rubric from CSV data.

    Supports the rubric structure from the Google Sheet:
        TC01-TC06 groups with detailed evaluation criteria.
    """

    def parse(self, raw_data: Any) -> list[dict]:
        if isinstance(raw_data, str):
            if raw_data.strip().startswith("{") or raw_data.strip().startswith("["):
                return json.loads(raw_data)
            return self.parse_csv(raw_data)
        if isinstance(raw_data, list):
            return raw_data
        return []

    def parse_csv(self, csv_text: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(csv_text))
        records = []
        for row in reader:
            cleaned = {}
            for key, value in row.items():
                if key is None:
                    continue
                cleaned_key = key.strip()
                cleaned[cleaned_key] = (value or "").strip()
            if any(cleaned.values()):
                records.append(cleaned)
        return records

    def build_rubric_structure(self, records: list[dict]) -> dict:
        """Convert flat CSV records into hierarchical rubric structure.

        Returns:
            Dict with keys TC01-TC06, each containing criteria details.
        """
        rubric = {}
        current_group = None

        for rec in records:
            group_code = rec.get("Mã nhóm tiêu chí", "").strip()
            if not group_code:
                group_code = rec.get("Mã nhóm", "").strip()

            if group_code and group_code.startswith("TC"):
                if group_code not in rubric:
                    rubric[group_code] = {
                        "code": group_code,
                        "name": rec.get("Tên nhóm", "").strip()
                            or rec.get("Tên tiêu chí đánh giá", "").strip(),
                        "scale": rec.get("Thang điểm", "").strip(),
                        "criteria": [],
                    }
                current_group = group_code

            if current_group:
                criterion_code = rec.get("Mã tiêu chí đánh giá cụ thể", "").strip()
                if criterion_code:
                    rubric[current_group]["criteria"].append({
                        "code": criterion_code,
                        "name": rec.get("Tên tiêu chí đánh giá", "").strip(),
                        "type": rec.get("Loại tiêu chí", "").strip(),
                        "description": rec.get("Mô tả tiêu chí đánh giá", "").strip(),
                        "check_type": rec.get("Kiểu kiểm", "").strip(),
                        "reference": rec.get("Tài liệu căn cứ", "").strip(),
                        "method": rec.get("Phương pháp đánh giá", "").strip(),
                        "formula": rec.get("Công thức tính", "").strip(),
                    })

        return rubric
