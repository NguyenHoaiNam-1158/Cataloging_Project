from typing import Any, Dict, List

from dublin_core_module.converters import DublinCoreConverter
from dublin_core_module.pipeline.dc_pipeline import DublinCorePipeline
from dublin_core_module.core.dc_record import DublinCoreRecord
from dublin_core_module.core.base_mapper import BaseDCElementMapper
from dublin_core_module.validator import DublinCoreValidator
from dublin_core_module.config.settings import settings


def raw_to_dublin_core(raw: Dict[str, Any], drop_empty: bool = False) -> Dict[str, List[str]]:
    return DublinCoreConverter().convert(raw, drop_empty=drop_empty)


__all__ = [
    "DublinCoreConverter",
    "DublinCorePipeline",
    "DublinCoreRecord",
    "BaseDCElementMapper",
    "DublinCoreValidator",
    "raw_to_dublin_core",
    "settings",
]
