from abc import ABC, abstractmethod

class BaseLLMAdapter(ABC):
    @abstractmethod
    async def extract_data(self, image_paths, prompt: str) -> str:
        pass

    @abstractmethod
    async def extract_text_data(self, text_content: str, prompt: str) -> str:
        pass