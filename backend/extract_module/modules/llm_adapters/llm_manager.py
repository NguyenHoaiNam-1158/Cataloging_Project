import logging
from config.settings import config
from .gemini_adapter import GeminiAdapter
from .qwen_adapter import QwenAdapter

logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self):
        self.gemini = GeminiAdapter()
        self.qwen = QwenAdapter()
        self.max_retries = config.MAX_RETRIES
    
    async def get_extraction_text(self, image_paths, prompt: str) -> str:
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Đang gọi [Gemini] lần {attempt}/{self.max_retries}")
                return await self.gemini.extract_data(image_paths, prompt)
            except Exception as e:
                logger.warning(f"Gemini lỗi lần {attempt}: {str(e)}")
                if attempt == self.max_retries:
                    logger.error("Gemini thất bại")
        if self.qwen:
            try:
                logger.warning("Fallback, switch Qwen")
                return await self.qwen.extract_data(image_paths, prompt)
            except Exception as e:
                logger.error(f"Qwen thất bại: {str(e)}")
        
        raise Exception("Các API AI đều không khả dụng")
            