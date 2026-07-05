import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    QWEN_API_KEY = os.getenv("QWEN_API_KEY")

    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 4))
    DEFAULT_EXTRACT_PAGES: int = int(os.getenv("DEFAULT_EXTRACT_PAGES", "10"))

    USE_OCR: bool = os.getenv("USE_OCR", "false").lower() == "true"
    PADDLE_MODEL_SIZE: str = os.getenv("PADDLE_MODEL_SIZE", "tiny")
    
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("Lỗi không tìm thấy API Key của Gemini.")
        if not cls.QWEN_API_KEY:
            raise ValueError("Lỗi không tìm thấy API Key của Qwen.")
    
config = Settings()