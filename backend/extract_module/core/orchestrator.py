import logging
from typing import Dict, Any, Tuple
from config.settings import config
from modules.preprocessing.image_processor import ImageProcessor
from modules.preprocessing.prompt_manager import PromptManager
from modules.llm_adapters.llm_manager import LLMManager
from modules.postprocessing.data_parser import DataParser

logger = logging.getLogger(__name__)

class CentralOrchestrator:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.prompt_manager = PromptManager()
        self.llm_manager = LLMManager()
        self.parser = DataParser()
    
    async def handle_request(
        self,
        file_path: str,
        doc_type: str = None,
        additional_info: str = None,
    ) -> Tuple[int, Any]:
        logger.info("          ")
        logger.info("Thực hiện quy tình trích xuất")
        
        image_path = None
        try:
            logger.info("Tiền xử lý ảnh và reditect prompt")
            image_path = self.image_processor.pdf_pages_to_images(
                file_path,
                page_count=config.DEFAULT_EXTRACT_PAGES,
                output_prefix="first_page_temp",
            )
            if not image_path:
                return 400, {"error": "không xử lý được file pdf đầu vào vì không tìm thấy"}
            
            prompt, _ = self.prompt_manager.get_prompt_and_schema(
                doc_type=doc_type,
                additional_info=additional_info,
            )
            
            logger.info("Gọi API AI")
            raw_text = await self.llm_manager.get_extraction_text(image_path, prompt)
            
            logger.info("Hậu xử lý và parse dữ liệu")
            json_data = self.parser.parse_text_to_json(raw_text)
            
            logger.info("Done")
            return 200, json_data
        
        except Exception as e:
            logger.exception("Lỗi hệ thống")
            return 500, {"error": str(e)}
        
        finally:
            if image_path:
                self.image_processor.cleanup_image(image_path)
        