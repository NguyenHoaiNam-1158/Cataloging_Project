from abc import ABC, abstractmethod
from typing import Union

from modules.dublincore.models import DublinCoreRecord


class BaseDublinCoreConverter(ABC):
    @abstractmethod
    def convert(self, source: Union[dict, list]) -> DublinCoreRecord:
        ...
