import argparse
import asyncio
import json
import logging
import os
import glob
from datetime import datetime
from pathlib import Path
from utils.logger import setup_logging
from core.orchestrator import CentralOrchestrator
from modules.postprocessing.marc21_mapper import Marc21Mapper

async def main():
    parser = argparse.ArgumentParser(description="Extract Module - Trích xuất thư mục")
    parser.add_argument("--use-ocr", action="store_true", help="Sử dụng OCR (PaddleOCR) thay vì gửi ảnh trực tiếp")
    args = parser.parse_args()

    # 1. Khởi tạo cấu hình logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # 2. Khởi tạo Pipeline
    orchestrator = CentralOrchestrator(use_ocr=args.use_ocr)
    
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
            base_name = os.path.splitext(os.path.basename(sample_pdf_path))[0]

            filename = f"ket_qua_trich_xuat({base_name}).json"
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(response_data, f, indent=4, ensure_ascii=False)
            logger.info(f"Đã lưu dữ liệu thành công vào: {output_path}")

            # Convert to MARC21 và lưu
            try:
                mapper = Marc21Mapper(response_data)
                record = mapper.to_record()
                marc_records = [record.as_dict()]

                marc_json_path = os.path.join(output_dir, f"MARC21_{base_name}.json")
                with open(marc_json_path, "w", encoding="utf-8") as f:
                    json.dump(marc_records, f, ensure_ascii=False, indent=2)
                logger.info(f"Đã lưu MARC-in-JSON: {marc_json_path}")

                from pymarc import Record, Field, Subfield, Indicators
                rec = Record()
                if "leader" in marc_records[0]:
                    rec.leader = marc_records[0]["leader"]
                for field_data in marc_records[0].get("fields", []):
                    for tag, content in field_data.items():
                        if tag == "008":
                            rec.add_ordered_field(Field(tag="008", data=content))
                        elif isinstance(content, dict):
                            ind1 = content.get("ind1", " ")
                            ind2 = content.get("ind2", " ")
                            subfields = []
                            for sf in content.get("subfields", []):
                                for c, v in sf.items():
                                    subfields.append(Subfield(c, v))
                            rec.add_ordered_field(Field(tag=tag, indicators=Indicators(ind1, ind2), subfields=subfields))
                marc_bin_path = os.path.join(output_dir, f"MARC21_{base_name}.mrc")
                with open(marc_bin_path, "wb") as f:
                    f.write(rec.as_marc())
                logger.info(f"Đã lưu binary .mrc: {marc_bin_path}")
            except Exception as e:
                logger.error(f"Lỗi chuyển đổi MARC21: {e}")
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