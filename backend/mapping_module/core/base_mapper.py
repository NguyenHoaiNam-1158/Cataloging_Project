from abc import ABC, abstractmethod
from typing import List
from pymarc import Field

from mapping_module.core.models import RawExtractionData

class BaseFieldMapper(ABC):
    @abstractmethod
    def can_handle(self, raw_data: RawExtractionData) -> bool:
        pass

    @abstractmethod
    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        pass