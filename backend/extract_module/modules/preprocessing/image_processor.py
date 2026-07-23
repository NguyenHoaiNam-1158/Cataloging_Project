import os
import logging
import fitz # PyMuPDF
from PIL import Image
from extract_module.config.model_config import AIConfig

logger = logging.getLogger(__name__)

class ImageProcessor:
    def pdf_pages_to_images(
        self,
        pdf_path: str,
        page_count: int = 1,
        output_prefix: str = "page",
    ) -> list[str]:
        logger.info(f"Đọc {page_count} trang đầu tiên từ PDF: {pdf_path}...")
        doc = fitz.open(pdf_path)

        if len(doc) == 0:
            logger.error("Lỗi: File PDF trống")
            return []

        image_paths = []
        page_count = min(page_count, len(doc))
        for page_index in range(page_count):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(dpi=AIConfig.IMAGE_DPI)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            output_path = f"{output_prefix}_{page_index + 1}.jpg"
            img.save(output_path, "JPEG", quality=AIConfig.JPEG_QUALITY)
            logger.info(f"Đã lưu trang {page_index + 1} tại: {output_path}")
            image_paths.append(output_path)

        return image_paths

    def pdf_first_page_to_image(self, pdf_path: str, output_path: str = "first_page_temp.jpg") -> str:
        image_paths = self.pdf_pages_to_images(pdf_path, page_count=1, output_prefix="first_page_temp")
        return image_paths[0] if image_paths else None

    def cleanup_image(self, image_path):
        if not image_path:
            return

        paths = image_path if isinstance(image_path, list) else [image_path]
        for path in paths:
            if path and os.path.exists(path):
                os.remove(path)
                logger.info(f"Dọn dẹp xong file tạm: {path}")