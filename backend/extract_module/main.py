import asyncio
import json
import logging
import os
import glob
from datetime import datetime
from utils.logger import setup_logging
from core.orchestrator import CentralOrchestrator

async def main():
    # 1. Khởi tạo cấu hình logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # 2. Khởi tạo Pipeline
    orchestrator = CentralOrchestrator()
    
    # 3. Giả lập thao tác người dùng trên UI (mặc định) - sẽ được ghi đè bởi metadata per-file nếu có
    ui_doc_type = "bao_cao_nckh"
    #ui_additional_info = "Đây là tài liệu thuộc thư viện ĐHYD TP.HCM, mượn từ cơ sở 2."

    # Hỗ trợ batch metadata: đọc từ data/batch_metadata.json nếu tồn tại.
    # Định dạng file JSON: list các object {"path": "...", "doc_type": "...", "additional_info": "..."}
    metadata_path = os.path.join("data", "batch_metadata.json")
    metadata_items_raw = []
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_items_raw = json.load(f)
                logger.info(f"Đã tải batch metadata từ: {metadata_path}")
        except Exception:
            logger.exception("Không thể đọc batch metadata, sẽ dùng cấu hình mặc định")

    # Build a map by filename for quick lookup
    metadata_map = {}
    for it in metadata_items_raw:
        p = it.get("path")
        if p:
            metadata_map[os.path.basename(p)] = it

    # Find all PDFs under data/ to process; if none found, fallback to metadata paths
    pdf_paths = glob.glob(os.path.join("data", "*.pdf"))
    if not pdf_paths and metadata_items_raw:
        pdf_paths = [it.get("path") for it in metadata_items_raw if it.get("path")]

    # Build batch_items: for files without metadata, doc_type will be None -> uses extraction_prompt_v3
    batch_items = []
    for p in pdf_paths:
        name = os.path.basename(p)
        meta = metadata_map.get(name, {})
        batch_items.append({
            "path": p,
            "doc_type": meta.get("doc_type"),
            "additional_info": meta.get("additional_info"),
        })

    # Xử lý từng file với metadata riêng (doc_type=None sẽ dùng extraction_prompt_v3)
    for item in batch_items:
        sample_pdf_path = item.get("path")
        doc_type = item.get("doc_type")
        additional_info = item.get("additional_info")

        logger.info(f"Bắt đầu chương trình trích xuất cho file: {sample_pdf_path} (doc_type={doc_type})")

        status_code, response_data = await orchestrator.handle_request(
            file_path=sample_pdf_path,
            doc_type=doc_type,
            additional_info=additional_info,
        )

        # 4. Hiển thị và lưu kết quả cho từng file
        print("\n" + "="*50)
        print(f"KẾT QUẢ TRẢ VỀ TỪ HỆ THỐNG CHO: {sample_pdf_path}")
        print(f"Status Code: {status_code}")

        if status_code == 200:
            print(json.dumps(response_data, indent=4, ensure_ascii=False))

            # Create dated output folder and save result there
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_dir = os.path.join("output", date_str)
            os.makedirs(output_dir, exist_ok=True)
            filename = f"ket_qua_trich_xuat({os.path.splitext(os.path.basename(sample_pdf_path))[0]}).json"
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(response_data, f, indent=4, ensure_ascii=False)
            logger.info(f"Đã lưu dữ liệu thành công vào: {output_path}")
        else:
            logger.error(f"Trích xuất thất bại. Chi tiết: {response_data}")

        print("="*50 + "\n")

    # Commented single file processing block for reference
    # sample_pdf_path = r"data\Mau Bao cao KHCN_Tran Thi Trung Chien.pdf"
    # ui_doc_type = "bao_cao_nckh"
    # ui_additional_info = "Đây là tài liệu thuộc thư viện ĐHYD TP.HCM, mượn từ cơ sở 2."
    # status_code, response_data = await orchestrator.handle_request(
    #     file_path=sample_pdf_path,
    #     doc_type=ui_doc_type,
    #     additional_info=ui_additional_info,
    # )

if __name__ == "__main__":
    asyncio.run(main())