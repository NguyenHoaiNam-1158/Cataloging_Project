"""Base extractor interface for all document extractors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ExtractionResult:
    """Result from a document extraction."""
    raw_text: str = ""
    tables: list[list[list[str]]] = field(default_factory=list)
    pages: int = 0
    is_image_only: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseExtractor(ABC):
    """Abstract base class for document extractors."""

    @abstractmethod
    def extract(
        self,
        file_path: str,
        pages: Optional[list[int]] = None,
    ) -> ExtractionResult:
        """Extract content from a document.

        Args:
            file_path: Path to the document file.
            pages: Optional list of 1-based page numbers to extract.
                   If None, extract all pages.

        Returns:
            ExtractionResult with raw_text, tables, and metadata.
        """
        ...

    def _validate_file(self, file_path: str) -> None:
        """Validate that the file exists and is readable."""
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        if not os.path.isfile(file_path):
            raise ValueError(f"Not a file: {file_path}")
