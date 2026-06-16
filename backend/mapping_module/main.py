import os
import sys
from pathlib import Path
from typing import List
import logging

from mapping_module.core.converters import DocumentConverter
from mapping_module.config.settings import Settings

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('processing.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BatchProcessor:

    def __init__(self, data_dir: str = "data", output_dir: str = "output"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.converter = DocumentConverter()
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Thư mục input: {self.data_dir.absolute()}")
        logger.info(f"Thư mục output: {self.output_dir.absolute()}")

    def get_json_files(self) -> List[Path]:
        if not self.data_dir.exists():
            logger.error(f"Thư mục {self.data_dir} không tồn tại!")
            return []
        
        json_files = list(self.data_dir.glob("*.json"))
        
        if not json_files:
            logger.warning(f"Không tìm thấy file .json trong {self.data_dir}")
            return []
        
        logger.info(f"Tìm thấy {len(json_files)} file JSON")
        for f in json_files:
            logger.info(f"   - {f.name}")
        
        return sorted(json_files)

    def process_file(self, input_path: Path, index: int, total: int) -> bool:
        try:
            file_stem = input_path.stem
            
            output_mrc = self.output_dir / f"{file_stem}.mrc"
            output_json = self.output_dir / f"{file_stem}.json"
            output_xml = self.output_dir / f"{file_stem}.xml"
            
            # Hiển thị tiến độ
            logger.info(f"\n{'='*70}")
            logger.info(f"[{index}/{total}] Đang xử lý: {input_path.name}")
            logger.info(f"{'='*70}")
            
            # Gọi converter
            self.converter.json_to_marc(
                input_path=str(input_path),
                output_mrc=str(output_mrc),
                output_json=str(output_json),
                output_xml=str(output_xml)
            )
            
            logger.info(f"Thành công: {input_path.name}")
            logger.info(f"   📄 MARC21: {output_mrc.name}")
            logger.info(f"   📄 JSON: {output_json.name}")
            logger.info(f"   📄 XML: {output_xml.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Lỗi xử lý {input_path.name}: {e}", exc_info=True)
            return False

    def run(self) -> None:
        """Chạy xử lý hàng loạt."""
        logger.info("Bắt đầu xử lý hàng loạt...\n")
        
        json_files = self.get_json_files()
        
        if not json_files:
            logger.error("Không có file nào để xử lý. Thoát chương trình.")
            return
        
        # Xử lý từng file
        success_count = 0
        error_count = 0
        
        for index, file_path in enumerate(json_files, 1):
            if self.process_file(file_path, index, len(json_files)):
                success_count += 1
            else:
                error_count += 1
        
        # Báo cáo kết quả
        logger.info(f"\n{'='*70}")
        logger.info(f"ẾT QUẢ CUỐI CÙNG")
        logger.info(f"{'='*70}")
        logger.info(f"Thành công: {success_count}/{len(json_files)} file")
        logger.info(f" Lỗi: {error_count}/{len(json_files)} file")
        logger.info(f"Kết quả lưu tại: {self.output_dir.absolute()}")
        logger.info(f"{'='*70}\n")


def main():
    """Entry point chính."""
    try:
        # Cấu hình thư mục (có thể thay đổi ở đây)
        processor = BatchProcessor(
            data_dir="data", 
            output_dir="output" 
        )
        
        # Chạy xử lý
        processor.run()
        
    except KeyboardInterrupt:
        logger.warning("\nNgười dùng dừng chương trình (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Lỗi không mong đợi: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()