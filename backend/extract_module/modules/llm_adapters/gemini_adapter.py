import time
import logging
from google import genai
from google.genai import types
from config.settings import config
from config.model_config import AIConfig
from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)

class GeminiAdapter(BaseLLMAdapter):
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        
    async def extract_data(self, image_paths, prompt: str) -> str:
        if isinstance(image_paths, list):
            logger.info(f"Đang tải {len(image_paths)} ảnh lên máy chủ [Gemini]")
            uploaded_files = [self.client.files.upload(file=path) for path in image_paths]
        else:
            logger.info(f"Đang tải ảnh lên máy chủ [Gemini]")
            uploaded_files = [self.client.files.upload(file=image_paths)]
        
        try:
            for idx, uploaded_file in enumerate(uploaded_files, start=1):
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(2)
                    uploaded_file = self.client.files.get(name=uploaded_file.name)
                    uploaded_files[idx - 1] = uploaded_file
            logger.info(f"Đang trích xuất dữ liệu [Gemini]")
            start_time = time.perf_counter()
            contents = [*uploaded_files, prompt]
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=AIConfig.TEMPERATURE
                )
            )
            
            execute_time = time.perf_counter() - start_time
            logger.info(f"Thời gian trích xuất: {execute_time:.2f} giây")
            
            usage = getattr(response, "usage_metadata", None)
            if usage:
                input_tokens = getattr(usage, "input_tokens", None)
                output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "response_tokens", None)
                hidden_tokens = getattr(usage, "hidden_tokens", None)
                total_tokens = getattr(usage, "total_token_count", None) or getattr(usage, "total_tokens", None)

                logger.info("Token usage [Gemini]:"
                            f" input={input_tokens}"
                            f" hidden={hidden_tokens}"
                            f" output={output_tokens}"
                            f" total={total_tokens}")

                # Show all available usage metadata fields when detailed token counts are missing
                if input_tokens is None and output_tokens is None and hidden_tokens is None:
                    extra = {}
                    if hasattr(usage, "__dict__"):
                        extra = {k: v for k, v in usage.__dict__.items() if v is not None}
                    else:
                        for attr in dir(usage):
                            if attr.startswith("_"):
                                continue
                            value = getattr(usage, attr)
                            if value is not None:
                                extra[attr] = value
                    logger.info(f"Gemini usage metadata fields: {extra}")
            return response.text
        finally:
            try:
                logger.info(f"Đang xóa file đã tải lên [Gemini]")
                for uploaded_file in uploaded_files:
                    self.client.files.delete(name=uploaded_file.name)
            except Exception:
                pass

    async def extract_text_data(self, text_content: str, prompt: str) -> str:
        logger.info(f"Đang trích xuất dữ liệu từ text [Gemini]")
        start_time = time.perf_counter()
        full_prompt = f"{prompt}\n\n===== NỘI DUNG OCR =====\n{text_content}\n===== HẾT ====="
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=AIConfig.TEMPERATURE
            )
        )

        execute_time = time.perf_counter() - start_time
        logger.info(f"Thời gian trích xuất text: {execute_time:.2f} giây")

        usage = getattr(response, "usage_metadata", None)
        if usage:
            input_tokens = getattr(usage, "input_tokens", None)
            output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "response_tokens", None)
            hidden_tokens = getattr(usage, "hidden_tokens", None)
            total_tokens = getattr(usage, "total_token_count", None) or getattr(usage, "total_tokens", None)

            logger.info("Token usage [Gemini text]:"
                        f" input={input_tokens}"
                        f" hidden={hidden_tokens}"
                        f" output={output_tokens}"
                        f" total={total_tokens}")

        return response.text