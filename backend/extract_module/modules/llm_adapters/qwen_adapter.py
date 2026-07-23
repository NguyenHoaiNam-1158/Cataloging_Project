import base64
import logging
from openai import OpenAI
from extract_module.config.settings import config
from extract_module.config.model_config import AIConfig
from extract_module.modules.llm_adapters.base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)

class QwenAdapter(BaseLLMAdapter):
    def __init__(self):
        self.client = OpenAI(api_key = config.QWEN_API_KEY, base_url = "https://openrouter.ai/api/v1")
    
    def _encode_image(self, image_path : str) -> str:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded}"
    
    async def extract_data(self, image_paths, prompt: str) -> str:
        logger.info("Mã hóa ảnh sang base64 [Qwen]")
        images = image_paths if isinstance(image_paths, list) else [image_paths]
        encoded_images = [self._encode_image(path) for path in images]
        
        strict_prompt = prompt + "\n\nCRITICAL: You MUST output ONLY the bullet point list (*Key: Value). Do not include any explanations or conversational text"

        logger.info("Đang trích xuất dữ liệu [Qwen]")
        response = self.client.chat.completions.create(
            model = "qwen/qwen-2-vl-72b-instruct",
            messages = [
                {
                    "role" : "user",
                    "content" : [
                        {"type": "text", "text": strict_prompt},
                        *[
                            {"type": "image_url", "image_url": {"url": image_url}}
                            for image_url in encoded_images
                        ]
                    ]
                }
            ],
            temperature = AIConfig.TEMPERATURE
        )
        
        usage = getattr(response, "usage", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", None)
            completion_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            logger.info("Token usage [Qwen]:"
                        f" input={prompt_tokens}"
                        f" output={completion_tokens}"
                        f" total={total_tokens}")

        logger.info("Trích xuất dữ liệu hoàn tất [Qwen]")
        return response.choices[0].message.content

    async def extract_text_data(self, text_content: str, prompt: str) -> str:
        logger.info("Đang trích xuất dữ liệu từ text [Qwen]")
        strict_prompt = f"{prompt}\n\n===== NỘI DUNG OCR =====\n{text_content}\n===== HẾT =====\n\nCRITICAL: You MUST output ONLY the bullet point list (*Key: Value). Do not include any explanations or conversational text"

        response = self.client.chat.completions.create(
            model="qwen/qwen-2-vl-72b-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": strict_prompt}],
                }
            ],
            temperature=AIConfig.TEMPERATURE,
        )

        usage = getattr(response, "usage", None)
        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", None)
            completion_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            logger.info("Token usage [Qwen text]:"
                        f" input={prompt_tokens}"
                        f" output={completion_tokens}"
                        f" total={total_tokens}")

        logger.info("Trích xuất dữ liệu text hoàn tất [Qwen]")
        return response.choices[0].message.content