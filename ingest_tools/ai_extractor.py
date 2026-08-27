"""AI-powered fallback extractor using Gemini for image-based PDFs."""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


class AIExtractor:
    """Extract structured data from PDF using Gemini AI.

    Used as fallback when pdfplumber/pymupdf cannot extract text
    (image-based PDFs or complex table layouts).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in .env or environment."
            )

        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def extract_from_pdf(
        self,
        pdf_path: str,
        prompt_name: str = "phu_luc_6_extract",
        pages: Optional[list[int]] = None,
    ) -> list[dict]:
        """Extract data from PDF pages using Gemini vision.

        Args:
            pdf_path: Path to PDF file.
            prompt_name: Name of prompt file (without .txt extension).
            pages: Specific pages to process (1-based). If None, process first 5.

        Returns:
            List of structured records.
        """
        prompt = self._load_prompt(prompt_name)
        images = self._pdf_to_images(pdf_path, pages)

        if not images:
            logger.error("Failed to convert PDF to images")
            return []

        logger.info(f"Sending {len(images)} page(s) to Gemini for extraction")
        raw_response = self._call_gemini(images, prompt)
        return self._parse_response(raw_response)

    def extract_from_text(
        self,
        text: str,
        prompt_name: str = "marc_spec_extract",
    ) -> list[dict]:
        """Extract structured data from raw text using Gemini.

        Args:
            text: Raw text content.
            prompt_name: Name of prompt file.

        Returns:
            List of structured records.
        """
        prompt = self._load_prompt(prompt_name)
        full_prompt = f"{prompt}\n\n===== NỘI DUNG =====\n{text}\n===== HẾT ====="

        logger.info("Sending text to Gemini for extraction")
        from google.genai import types
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        return self._parse_response(response.text)

    def _load_prompt(self, name: str) -> str:
        prompt_file = PROMPTS_DIR / f"{name}.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Prompt not found: {prompt_file}")

    def _pdf_to_images(
        self, pdf_path: str, pages: Optional[list[int]] = None
    ) -> list[str]:
        """Convert PDF pages to temporary image files."""
        import fitz

        doc = fitz.open(pdf_path)
        total = len(doc)
        target = pages or list(range(1, min(total + 1, 6)))

        temp_dir = Path(os.getenv("TEMP", "/tmp")) / "ingest_ai"
        temp_dir.mkdir(exist_ok=True)

        image_paths = []
        for page_num in target:
            if page_num < 1 or page_num > total:
                continue
            page = doc[page_num - 1]
            pix = page.get_pixmap(dpi=200)
            img_path = str(temp_dir / f"page_{page_num}.png")
            pix.save(img_path)
            image_paths.append(img_path)

        doc.close()
        return image_paths

    def _call_gemini(self, image_paths: list[str], prompt: str) -> str:
        """Send images + prompt to Gemini."""
        from google.genai import types

        uploaded_files = []
        for path in image_paths:
            uf = self.client.files.upload(file=path)
            uploaded_files.append(uf)

        try:
            for uf in uploaded_files:
                while uf.state.name == "PROCESSING":
                    time.sleep(2)
                    uf = self.client.files.get(name=uf.name)

            contents = [*uploaded_files, prompt]
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            return response.text or ""
        finally:
            for uf in uploaded_files:
                try:
                    self.client.files.delete(name=uf.name)
                except Exception:
                    pass

    def _parse_response(self, response_text: str) -> list[dict]:
        """Parse JSON from Gemini response."""
        text = response_text.strip()

        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            text = text[start:end].strip()

        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return [data]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.debug(f"Raw response: {text[:500]}")
            return []
