import json
import logging
import os
import tempfile
from pathlib import Path

from .base_ocr_adapter import BaseOCRAdapter

logger = logging.getLogger(__name__)


class PaddleOCRAdapter(BaseOCRAdapter):
    def __init__(self, model_size: str = "tiny", model_dir: str = "paddle markdown", lang: str = "vi"):
        self.model_size = model_size
        self.model_dir = model_dir
        self.lang = lang

    def _create_ocr(self):
        from paddleocr import PaddleOCR

        model_dir = self.model_dir
        models = {
            "tiny": {
                "det_name": "PP-OCRv6_tiny_det",
                "rec_name": "PP-OCRv6_tiny_rec",
                "det_dir": f"{model_dir}/PP-OCRv6_tiny_det_safetensors",
                "rec_dir": f"{model_dir}/PP-OCRv6_tiny_rec_safetensors",
            },
            "small": {
                "det_name": "PP-OCRv6_small_det",
                "rec_name": "PP-OCRv6_small_rec",
                "det_dir": f"{model_dir}/PP-OCRv6_small_det_safetensors",
                "rec_dir": f"{model_dir}/PP-OCRv6_small_rec_safetensors",
            },
            "medium": {
                "det_name": "PP-OCRv6_medium_det",
                "rec_name": "PP-OCRv6_medium_rec",
                "det_dir": f"{model_dir}/PP-OCRv6_medium_det_safetensors",
                "rec_dir": f"{model_dir}/PP-OCRv6_medium_rec_safetensors",
            },
        }
        cfg = models.get(self.model_size, models["tiny"])
        return PaddleOCR(
            text_detection_model_name=cfg["det_name"],
            text_recognition_model_name=cfg["rec_name"],
            text_detection_model_dir=cfg["det_dir"],
            text_recognition_model_dir=cfg["rec_dir"],
            engine="transformers",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            lang=self.lang,
        )

    def _text_blocks_from_json(self, json_path: str):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        texts = data.get("rec_texts", [])
        boxes = data.get("rec_boxes", [])
        page_idx = data.get("page_index", 0)

        if not texts or not boxes:
            return [], page_idx

        lines = []
        for text, box in zip(texts, boxes):
            x1, y1, x2, y2 = box
            cy = (y1 + y2) / 2
            height = y2 - y1
            lines.append({"text": text.strip(), "cy": cy, "y1": y1, "y2": y2, "height": height})

        lines.sort(key=lambda l: (l["cy"], l["y1"]))

        paragraphs = []
        current = []
        for line in lines:
            if not current:
                current.append(line)
                continue

            prev = current[-1]
            gap = line["y1"] - prev["y2"]
            threshold = max(prev["height"] * 1.2, 20)

            if gap > threshold:
                paragraphs.append(current)
                current = [line]
            else:
                current.append(line)

        if current:
            paragraphs.append(current)

        blocks = []
        for para in paragraphs:
            text = " ".join(l["text"] for l in para if l["text"])
            if text:
                blocks.append(text)

        return blocks, page_idx

    def _json_to_markdown(self, json_path: str) -> str:
        blocks, page_idx = self._text_blocks_from_json(json_path)
        if not blocks:
            return ""

        lines = [f"# Trang {page_idx + 1}\n"]
        for block in blocks:
            lines.append(block)
            lines.append("")
        lines.append("---\n")
        return "\n".join(lines)

    def process_pdf(self, pdf_path: str, **kwargs) -> str:
        output_dir = kwargs.get("output_dir") or tempfile.mkdtemp(prefix="ocr_")
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Running PaddleOCR on: {pdf_path} (model: {self.model_size})")
        ocr = self._create_ocr()
        result = ocr.predict(pdf_path)

        json_files = []
        for i, res in enumerate(result, start=1):
            json_path = os.path.join(output_dir, f"page_{i}_result.json")
            res.save_to_json(json_path)
            json_files.append(json_path)
            logger.info(f"OCR page {i} -> {json_path}")

        md_parts = []
        for jf in json_files:
            md_text = self._json_to_markdown(jf)
            if md_text:
                md_parts.append(md_text)

        full_markdown = "\n".join(md_parts)
        logger.info(f"OCR complete: {len(json_files)} pages -> {len(full_markdown)} chars of markdown")
        return full_markdown
