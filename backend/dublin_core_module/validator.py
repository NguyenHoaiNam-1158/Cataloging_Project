from typing import List, Optional

from dublin_core_module.config.settings import settings
from dublin_core_module.core.dc_record import DublinCoreRecord


class DublinCoreValidator:
    
    def __init__(self, required: Optional[List[str]] = None):
        self.required = required or settings.REQUIRED_ELEMENTS

    def validate(self, record: DublinCoreRecord) -> List[str]:
        problems: List[str] = []
        data = record.to_dict()
        if list(data.keys()) != settings.ELEMENTS:
            problems.append("Sai/thiếu bộ 15 trường hoặc sai thứ tự")
        for element in self.required:
            if not data.get(element):
                problems.append(f"Thiếu phần tử bắt buộc '{element}'")
        return problems

    def is_valid(self, record: DublinCoreRecord) -> bool:
        return not self.validate(record)
