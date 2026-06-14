from abc import ABC, abstractmethod

class BaseOCRAdapter(ABC):
    @abstractmethod
    def process_pdf(self, pdf_path: str, **kwargs) -> str:
        pass
