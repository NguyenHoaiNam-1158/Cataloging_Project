import sys
import os
import json
from typing import List, Optional

from mapping_module.config.settings import Settings
from mapping_module.utils import pdf_extractor

try:
    from mapping_module.LCC_and_NLM.rag_engine import CatalogingRAG
    from mapping_module.LCC_and_NLM import scraper
    RAG_AVAILABLE = True
except ImportError as e:
    Settings.log.error(f"Không thể nạp RAG Engine! Lỗi: {e}")
    RAG_AVAILABLE = False
    CatalogingRAG = None


class RAGIntegration:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        if not RAG_AVAILABLE or CatalogingRAG is None:
            raise RuntimeError("RAG Engine không khả dụng cục bộ")

        # [VÁ A03] KHÔNG nạp embedder/FAISS ở đây nữa. Chỉ đặt cờ; việc nạp nặng
        # được dời sang _ensure_ready(), chạy ở LẦN QUERY ĐẦU TIÊN. Nhờ vậy khởi
        # động backend tức thì, không nạp 2 lần dưới uvicorn --reload, và không
        # crash lúc startup nếu thiếu index/model.
        self.rag = None
        self.lcc_index, self.lcc_metadata = None, None
        self.nlm_index, self.nlm_metadata = None, None
        self._ready = False
        self._load_failed = False
        self._initialized = True

    def _ensure_ready(self) -> bool:
        """Nạp engine + chỉ mục ở lần gọi đầu tiên (lazy). True nếu sẵn sàng dùng."""
        if self._ready:
            return True
        if self._load_failed:
            return False
        try:
            Settings.log.info("Lazy-load RAG: nạp embedding model + chỉ mục FAISS (lần đầu)...")
            self.rag = CatalogingRAG()
            self._load_indices()
            self._ready = True
            Settings.log.info("RAG sẵn sàng.")
            return True
        except Exception as e:
            self._load_failed = True
            Settings.log.error(f"Lazy-load RAG thất bại -> bỏ qua phân loại RAG cho phiên này: {e}")
            return False

    def _load_indices(self) -> None:
        os.makedirs(Settings.RAG_INDEX_DIR, exist_ok=True)

        if os.path.exists(Settings.LCC_OUTPUT_FILE):
            with open(Settings.LCC_OUTPUT_FILE, "r", encoding="utf-8") as f:
                lcc_data = json.load(f)
        else:
            lcc_data = pdf_extractor.extract_all_lcc(Settings.PDF_FOLDER, Settings.LCC_OUTPUT_FILE)

        self.lcc_index, self.lcc_metadata = self.rag.load_or_build_index(
            data_dict=lcc_data,
            index_path=os.path.join(Settings.RAG_INDEX_DIR, "lcc_index.faiss"),
            meta_path=os.path.join(Settings.RAG_INDEX_DIR, "lcc_meta.json"),
            is_nlm=False,
        )

        if os.path.exists(Settings.NLM_OUTPUT_FILE):
            with open(Settings.NLM_OUTPUT_FILE, "r", encoding="utf-8") as f:
                nlm_data = json.load(f)
        else:
            nlm_data = scraper.scrape_all_nlm(Settings.NLM_OUTPUT_FILE)

        self.nlm_index, self.nlm_metadata = self.rag.load_or_build_index(
            data_dict=nlm_data,
            index_path=os.path.join(Settings.RAG_INDEX_DIR, "nlm_index.faiss"),
            meta_path=os.path.join(Settings.RAG_INDEX_DIR, "nlm_meta.json"),
            is_nlm=True,
        )

    def query_lcc(self, title: str, subject_terms: Optional[List[str]] = None, top_k: int = 3) -> List[dict]:
        if not self._ensure_ready() or not self.lcc_index:
            return []
        query = " ".join([title] + (subject_terms or []))
        results = self.rag.search_top_k(query, self.lcc_index, self.lcc_metadata, k=top_k)
        best_code, confidence = self.rag.ask_llm_for_best_match(title, results)
        return [{"code": best_code, "description": results[0].get("description", "") if results else "", "confidence": confidence}] if best_code else []

    def query_nlm(self, title: str, subject_terms: Optional[List[str]] = None, top_k: int = 3) -> List[dict]:
        if not self._ensure_ready() or not self.nlm_index:
            return []
        query = " ".join([title] + (subject_terms or []))
        results = self.rag.search_top_k(query, self.nlm_index, self.nlm_metadata, k=top_k)
        best_code, confidence = self.rag.ask_llm_for_best_match(title, results)
        return [{"code": best_code, "description": results[0].get("description", "") if results else "", "confidence": confidence}] if best_code else []

    def generate_summary(self, title: str, subject_terms: Optional[List[str]] = None) -> str:
        """Sử dụng Gemini để tự động sinh đoạn tóm tắt nội dung trơn dưới dạng chữ thuần."""
        if not self._ensure_ready() or not self.rag or not self.rag.llm:
            return "Tóm tắt nội dung đang được cập nhật."

        subjects_str = ", ".join(subject_terms) if subject_terms else "Chưa xác định"

        prompt = f"""Bạn là một chuyên gia biên mục thư viện. Hãy viết duy nhất 1 đoạn văn tóm tắt nội dung khoa học ngắn gọn (từ 2 đến 3 câu) bằng tiếng Việt cho tài liệu sau:
Nhan đề: "{title}"
Chủ đề liên quan: {subjects_str}

Yêu cầu nghiêm ngặt: Viết trực tiếp vào nội dung tóm tắt, KHÔNG chào hỏi, KHÔNG giải thích, KHÔNG sử dụng cấu trúc JSON. Hãy viết thẳng vào vấn đề."""

        try:
            response = self.rag.llm.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "text/plain",
                    "max_output_tokens": 250,
                    "temperature": 0.2
                }
            )

            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                self.rag.total_prompt_tokens += response.usage_metadata.prompt_token_count
                self.rag.total_completion_tokens += response.usage_metadata.candidates_token_count

            text = getattr(response, 'text', None)
            if not text or not text.strip():
                return "Tóm tắt nội dung đang được cập nhật."

            return text.strip()

        except Exception as e:
            Settings.log.error(f"Lỗi sinh trường 520: {e}")
            return f"Nghiên cứu khoa học về chủ đề {title}."


def get_rag_integration() -> Optional[RAGIntegration]:
    try:
        return RAGIntegration()
    except RuntimeError as e:
        Settings.log.error(f"Không thể nạp RAG Engine: {e}")
        return None