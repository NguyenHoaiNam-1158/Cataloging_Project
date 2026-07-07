import json
from typing import Dict, List

from dublin_core_module.config.settings import settings


class DublinCoreRecord:
    
    def __init__(self):
        self._data: Dict[str, List[str]] = {e: [] for e in settings.ELEMENTS}

    def add(self, element: str, values: List[str]) -> None:
        if element not in self._data:
            raise KeyError(f"Phần tử Dublin Core không hợp lệ: {element}")
        for value in values:
            if value:
                self._data[element].append(value)

    def get(self, element: str) -> List[str]:
        return self._data.get(element, [])

    def to_dict(self, drop_empty: bool = False) -> Dict[str, List[str]]:
        if drop_empty:
            return {k: list(v) for k, v in self._data.items() if v}
        return {k: list(self._data[k]) for k in settings.ELEMENTS}

    def to_json(self, drop_empty: bool = False, indent: int = 2) -> str:
        return json.dumps(self.to_dict(drop_empty), ensure_ascii=False, indent=indent)

    def filled_count(self) -> int:
        return sum(1 for v in self._data.values() if v)

    def __repr__(self) -> str:
        return f"<DublinCoreRecord filled={self.filled_count()}/{len(settings.ELEMENTS)}>"
