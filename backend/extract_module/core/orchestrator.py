import logging
from typing import Dict, Any, Tuple
from extract_module.config.settings import config
from extract_module.modules.preprocessing.image_processor import ImageProcessor
from extract_module.modules.preprocessing.prompt_manager import PromptManager
from extract_module.modules.llm_adapters.llm_manager import LLMManager
from extract_module.modules.ocr_adapters.paddle_ocr_adapter import PaddleOCRAdapter
from extract_module.modules.postprocessing.data_parser import DataParser

logger = logging.getLogger(__name__)

class CentralOrchestrator:
    def __init__(self, use_ocr: bool = None):
        self.use_ocr = config.USE_OCR if use_ocr is None else use_ocr
        self.image_processor = ImageProcessor()
        self.prompt_manager = PromptManager()
        self.llm_manager = LLMManager()
        self.parser = DataParser()
        if self.use_ocr:
            self.ocr_adapter = PaddleOCRAdapter(model_size=config.PADDLE_MODEL_SIZE)
    
    async def handle_request(
        self,
        file_path: str,
        doc_type: str = None,
        additional_info: str = None,
        use_ocr: bool = None,
    ) -> Tuple[int, Any]:
        logger.info("          ")
        logger.info("Thực hiện quy trình trích xuất")

        ocr_mode = self.use_ocr if use_ocr is None else use_ocr
        
        if ocr_mode:
            return await self._handle_with_ocr(file_path, doc_type, additional_info)
        else:
            return await self._handle_with_image(file_path, doc_type, additional_info)

    async def _handle_with_image(
        self,
        file_path: str,
        doc_type: str = None,
        additional_info: str = None,
    ) -> Tuple[int, Any]:
        image_path = None
        try:
            logger.info("Tiền xử lý ảnh và redirect prompt")
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
            
            logger.info("Gọi API AI [Image mode]")
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

    async def _handle_with_ocr(
        self,
        file_path: str,
        doc_type: str = None,
        additional_info: str = None,
    ) -> Tuple[int, Any]:
        try:
            logger.info("Chạy OCR trên file PDF")
            markdown_text = self.ocr_adapter.process_pdf(file_path)
            if not markdown_text.strip():
                return 400, {"error": "OCR không trích xuất được nội dung từ file PDF"}

            logger.info("Xây dựng prompt trích xuất")
            prompt, _ = self.prompt_manager.get_prompt_and_schema(
                doc_type=doc_type,
                additional_info=additional_info,
            )

            logger.info("Gọi API AI [OCR text mode]")
            raw_text = await self.llm_manager.get_extraction_text_from_text(markdown_text, prompt)

            logger.info("Hậu xử lý và parse dữ liệu")
            json_data = self.parser.parse_text_to_json(raw_text)

            logger.info("Done")
            return 200, json_data

        except Exception as e:
            logger.exception("Lỗi hệ thống")
            return 500, {"error": str(e)}
        