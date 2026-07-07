import asyncio
import json
import logging
from utils.logger import setup_logging
from core.orchestrator import CentralOrchestrator

async def main():
    # 1. Khởi tạo cấu hình logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # 2. Khởi tạo Pipeline
    orchestrator = CentralOrchestrator()
    
    # 3. Giả lập thao tác người dùng trên UI, User chọn doc_type từ dropdown và nhập thêm thông tin
    sample_pdf_path = r"data\Mau luan van Thac si_Nguyen Hoang Tung.pdf"
    ui_doc_type = "luan_van"
    ui_additional_info = ""
    
    logger.info(f"Bắt đầu chương trình trích xuất cho file: {sample_pdf_path}")
    
    # Gọi hàm xử lý luồng chính với dữ liệu giả lập từ frontend
    status_code, response_data = await orchestrator.handle_request(
        file_path=sample_pdf_path,
        doc_type=ui_doc_type,
        additional_info=ui_additional_info,
    )
    
    # 4. Hiển thị và lưu kết quả
    print("\n" + "="*50)
    print("KẾT QUẢ TRẢ VỀ TỪ HỆ THỐNG:")
    print(f"Status Code: {status_code}")
    
    if status_code == 200:
        # In ra Terminal dạng JSON
        print(json.dumps(response_data, indent=4, ensure_ascii=False))
        
        # Lưu kết quả ra file JSON
        output_filename = "ket_qua_trich_xuat(kltn).json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Đã lưu dữ liệu thành công vào: {output_filename}")
    else:
        logger.error(f"Trích xuất thất bại. Chi tiết: {response_data}")
        
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())