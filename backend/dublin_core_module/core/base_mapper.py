from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseDCElementMapper(ABC):
    
    element: str = ""

    @abstractmethod
    def map(self, raw: Dict[str, Any]) -> List[str]:
        """Trả về danh sách giá trị đã chuẩn hóa cho phần tử này."""
        raise NotImplementedError
