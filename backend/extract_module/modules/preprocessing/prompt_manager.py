import os
import json
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self, resource_dir: str = "None"):
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        self.prompt_dir = os.path.join(base_path, "extract_module", "resources", "prompts")
        self.schema_path = os.path.join(base_path, "extract_module", "resources", "schema", "extraction_schema.json")
        self.schema_dict = self._load_schema()
    
    def _load_schema(self) -> dict:
        if not os.path.exists(self.schema_path):
            logger.error(f"Không tìm thấy schema tại: {self.schema_path}")
            return {}
        with open(self.schema_path, 'r', encoding = 'utf-8') as f:
            return json.load(f)
    
    def get_prompt_and_schema(self, doc_type: str = None, additional_info: str = None) -> Tuple[str, dict]:
        if doc_type in ["luan_van", "luan_an", "khoa_luan"]:
            file_name = "lv_la_prompt.md"
        elif doc_type == "bao_cao_nckh":
            file_name = "nckh_prompt.md"
        else:
            file_name = "extraction_prompt_v3.md"
        
        prompt_path = os.path.join(self.prompt_dir, file_name)
        logger.info(f"Loại tài liệu: {doc_type}")
        
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Không tìm thấy file prompt: {prompt_path}")
        
        with open(prompt_path, "r", encoding = 'utf-8') as f:
            base_prompt = f.read()

        base_prompt = (
            "Lưu ý: bạn đang xem ảnh trang đầu tiên của tài liệu.\n\n"
            + base_prompt
        )
        
        if additional_info and additional_info.strip():
            logger.info("Thông tin bổ sung")
            base_prompt += (
                "\n\n## ADDITIONAL INFO FROM USER (USER INPUT):\n"
                f"{additional_info}\n"
                "(NOTE: Cross-reference this information with the images. "
                "If plausible, prioritize using it to fill in any blurred or missing fields)."
            )
        
        return base_prompt, self.schema_dict