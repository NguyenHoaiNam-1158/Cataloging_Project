"""JSON exporter for structured data."""

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class JSONExporter:
    """Export structured data to JSON files."""

    def __init__(self, indent: int = 2):
        self.indent = indent

    def export(
        self,
        data: Any,
        output_path: str,
        ensure_ascii: bool = False,
    ) -> str:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=self.indent)

        logger.info(f"Exported JSON to {output_path}")
        return output_path

    def export_with_metadata(
        self,
        data: Any,
        output_path: str,
        source_file: Optional[str] = None,
        parser_used: Optional[str] = None,
    ) -> str:
        wrapper = {
            "metadata": {
                "source_file": source_file or "unknown",
                "parser": parser_used or "unknown",
                "record_count": len(data) if isinstance(data, list) else 1,
            },
            "data": data,
        }
        return self.export(wrapper, output_path)
