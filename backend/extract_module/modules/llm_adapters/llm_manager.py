import logging
from extract_module.config.settings import config
from extract_module.modules.llm_adapters.gemini_adapter import GeminiAdapter
from extract_module.modules.llm_adapters.qwen_adapter import QwenAdapter

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

    async def get_extraction_text_from_text(self, text_content: str, prompt: str) -> str:
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Đang gọi [Gemini text] lần {attempt}/{self.max_retries}")
                return await self.gemini.extract_text_data(text_content, prompt)
            except Exception as e:
                logger.warning(f"Gemini text lỗi lần {attempt}: {str(e)}")
                if attempt == self.max_retries:
                    logger.error("Gemini text thất bại")
        if self.qwen:
            try:
                logger.warning("Fallback, switch Qwen text")
                return await self.qwen.extract_text_data(text_content, prompt)
            except Exception as e:
                logger.error(f"Qwen text thất bại: {str(e)}")

        raise Exception("Các API AI đều không khả dụng")
            