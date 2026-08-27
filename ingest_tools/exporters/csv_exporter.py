"""CSV exporter with UTF-8 BOM for Excel compatibility."""

import csv
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export structured data to CSV files.

    Default encoding: UTF-8 with BOM for correct Vietnamese display in Excel.
    """

    def __init__(self, encoding: str = "utf-8-sig"):
        self.encoding = encoding

    def export(
        self,
        records: list[dict],
        output_path: str,
        columns: Optional[list[str]] = None,
    ) -> str:
        if not records:
            logger.warning("No records to export")
            return output_path

        if columns is None:
            columns = list(records[0].keys())

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "w", newline="", encoding=self.encoding) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=columns,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(records)

        logger.info(f"Exported {len(records)} records to {output_path}")
        return output_path

    def export_phu_luc_6(
        self,
        records: list[dict],
        output_path: str,
    ) -> str:
        """Export department lookup data to CSV.

        Columns: STT, Tên đơn vị (cap1), Đơn vị cấp 1, Đơn vị cấp 2
        """
        columns = ["STT", "tenDonViCap1", "tenDonViCap2"]
        renamed = []
        for rec in records:
            renamed.append({
                "STT": rec.get("stt", ""),
                "tenDonViCap1": rec.get("tenDonViCap1", ""),
                "tenDonViCap2": rec.get("tenDonViCap2", ""),
            })
        return self.export(renamed, output_path, columns)
