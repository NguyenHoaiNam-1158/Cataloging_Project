import os
import json
from mapping_module.config import settings as config

# [VÁ A03] Các thư viện NẶNG (faiss, numpy, google.generativeai, sentence-transformers)
# KHÔNG còn import ở cấp module. Chúng được import bên trong phương thức, chỉ khi
# CatalogingRAG thực sự được khởi tạo/sử dụng -> 'import rag_engine' trở nên rất rẻ,
# và toàn bộ chi phí nạp model/thư viện dời sang lần phân loại đầu tiên.


class CatalogingRAG:
    def __init__(self):
        # import tại chỗ: chỉ chạy khi engine thật sự được tạo (lazy)
        from sentence_transformers import SentenceTransformer
        import google.generativeai as genai

        config.log.info("Khởi tạo RAG Engine...")
        config.log.info("Đang tải Embedding Model (Chạy Local/Offline)...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        if hasattr(self.embedder, 'get_embedding_dimension'):
            self.dimension = self.embedder.get_embedding_dimension()
        else:
            self.dimension = self.embedder.get_sentence_embedding_dimension()

        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.llm = genai.GenerativeModel('gemini-2.5-flash')
            config.log.info("Đã kết nối thành công với Gemini API.")
        else:
            self.llm = None
            config.log.error("Không tìm thấy cấu hình Gemini API Key.")

    def build_faiss_index(self, data_dict, index_path, meta_path, is_nlm=False, is_subject=False):
        import faiss
        import numpy as np

        config.log.info(f"Đang xây dựng Vector Database cho {index_path}...")
        index = faiss.IndexFlatL2(self.dimension)
        metadata = []
        texts_to_embed = []

        if is_subject:
            for term, desc in data_dict.items():
                texts_to_embed.append(f"Chủ đề 650: {term}. Mô tả: {desc}")
                metadata.append({"code": term, "description": desc})
        elif is_nlm:
            for schedule, content in data_dict.items():
                for entry in content.get("entries", []):
                    if not entry.get("unused"):
                        name = entry.get("name", "")
                        notes = entry.get("notes", "")
                        texts_to_embed.append(f"Chủ đề NLM: {name}. Ghi chú: {notes}")
                        metadata.append({"code": entry.get("code"), "description": name})
        else:
            for code, desc in data_dict.items():
                texts_to_embed.append(f"Mã LCC: {code}. Mô tả: {desc}")
                metadata.append({"code": code, "description": desc})

        vectors = self.embedder.encode(texts_to_embed, show_progress_bar=True)
        index.add(np.array(vectors).astype('float32'))

        faiss.write_index(index, index_path)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False)

        return index, metadata

    def load_or_build_index(self, data_dict, index_path, meta_path, is_nlm=False, is_subject=False):
        import faiss

        if os.path.exists(index_path) and os.path.exists(meta_path):
            index = faiss.read_index(index_path)
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return index, metadata
        return self.build_faiss_index(data_dict, index_path, meta_path, is_nlm, is_subject)

    def search_top_k(self, query: str, index, metadata, k=3):
        query_vector = self.embedder.encode([query]).astype('float32')
        distances, indices = index.search(query_vector, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(metadata):
                item = metadata[idx].copy()
                item["distance"] = float(distances[0][i])
                results.append(item)
        return results

    def ask_llm_for_best_match(self, book_title, top_k_results):
        """Cơ chế RAG tự động sửa lỗi chuỗi JSON dông dài bằng Regex."""
        if not self.llm or not top_k_results:
            return (top_k_results[0]['code'], "Lỗi/Mặc định") if top_k_results else (None, "Không có dữ liệu")

        top_1 = top_k_results[0]
        best_distance = top_1['distance']

        if best_distance < 0.6:
            confidence_metric = f"Tin cậy tuyệt đối (Bỏ qua LLM) - L2 Distance: {best_distance:.3f}"
            return top_1['code'], confidence_metric

        context_str = "\n".join([f"- Mã: {item['code']} | Mô tả: {item['description']}" for item in top_k_results])
        prompt = f"""Chọn 1 mã phân loại MARC 21 đúng nhất cho sách: "{book_title}"
Tùy chọn:
{context_str}
Trả về định dạng JSON bắt buộc sau: {{"best_code": "<mã>"}}"""

        try:
            response = self.llm.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "max_output_tokens": 100,
                    "temperature": 0.0
                }
            )

            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                self.total_prompt_tokens += response.usage_metadata.prompt_token_count
                self.total_completion_tokens += response.usage_metadata.candidates_token_count

            text = getattr(response, 'text', None)
            if not text or not text.strip():
                return top_1['code'], "Lỗi API (Response rỗng)"

            best_code = None
            try:
                result_dict = json.loads(text.strip())
                best_code = result_dict.get("best_code")
            except json.JSONDecodeError:
                import re
                match = re.search(r'"best_code"\s*:\s*"([^"]+)"', text)
                if match:
                    best_code = match.group(1)

            confidence_metric = f"LLM phân xử (Khó phân định) - L2 Distance Top 1: {best_distance:.3f}"
            if best_code:
                return best_code, confidence_metric
            return top_1['code'], f"LLM phản hồi sai format - Tự động lấy Top 1 FAISS (L2: {best_distance:.3f})"

        except Exception as e:
            config.log.error(f"Lỗi gọi Gemini: {e}")
            return top_1['code'], "Lỗi API (Lấy Top 1 FAISS)"