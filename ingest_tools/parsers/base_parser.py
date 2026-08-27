"""Base parser interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    """Abstract base class for all parsers."""

    @abstractmethod
    def parse(self, raw_data: Any) -> list[dict]:
        """Parse raw extracted data into structured records.

        Returns:
            List of dicts, each dict is one record with standardized keys.
        """
        ...
