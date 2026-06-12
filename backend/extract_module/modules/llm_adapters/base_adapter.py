from abc import ABC, abstractmethod

class BaseLLMAdapter(ABC):
    @abstractmethod
    def extract_data(self, prompt: str) -> str:
        pass