from typing import Any, Dict, List, Optional

from dublin_core_module.config.settings import settings
from dublin_core_module.core.base_mapper import BaseDCElementMapper
from dublin_core_module.core.dc_record import DublinCoreRecord
from dublin_core_module.mappers import default_mappers


class DublinCorePipeline:
    
    def __init__(self, mappers: Optional[List[BaseDCElementMapper]] = None):
        self.mappers = mappers if mappers is not None else default_mappers()
        self._verify_coverage()

    def _verify_coverage(self) -> None:
        covered = {m.element for m in self.mappers}
        missing = [e for e in settings.ELEMENTS if e not in covered]
        if missing:
            raise ValueError(f"Thiếu mapper cho phần tử DC: {missing}")

    def build(self, raw: Dict[str, Any]) -> DublinCoreRecord:
        if not isinstance(raw, dict):
            raise TypeError("raw phải là dict (một biểu ghi trích xuất).")
        record = DublinCoreRecord()
        for mapper in self.mappers:
            record.add(mapper.element, mapper.map(raw))
        return record
