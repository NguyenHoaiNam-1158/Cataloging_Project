import os
import sys
import glob
import json
import uuid
import argparse
import asyncio
import logging
import tempfile
import uvicorn
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict

# Thêm đường dẫn hiện tại vào hệ thống để Python nhận diện module chính xác
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# [LÀM GỌN LOG] phải chạy TRƯỚC khi import module nạp faiss/transformers
from quiet_logging import setup_logging
setup_logging()

from extract_module.core.orchestrator import CentralOrchestrator
from mapping_module.core.converters import DocumentConverter
from dublin_core_module import DublinCoreConverter          # [DC] module ánh xạ Dublin Core

# Khởi tạo logger của hệ thống (định dạng do quiet_logging.setup_logging cấu hình)
logger = logging.getLogger("BACKEND_MAIN")

app = FastAPI(title="Hệ thống Biên mục Tự động")

# Khởi tạo các module lõi
orchestrator = CentralOrchestrator(use_ocr=False)
converter = DocumentConverter()
dc_converter = DublinCoreConverter()                        # [DC] khởi tạo 1 lần, dùng lại

# [VÁ A01] Thư mục chứa file PDF tạm (tên ngẫu nhiên, không dùng tên người dùng)
TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_uploads")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


def _safe_stem(filename: str) -> str:
    """Lấy tên file an toàn để đặt tên output (chống path traversal '../')."""
    base = os.path.basename(filename or "document")   # bỏ mọi thành phần thư mục
    stem = os.path.splitext(base)[0] or "document"
    # chỉ giữ ký tự an toàn cho tên file
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in stem)


@app.post("/api/v1/process-document")
async def process_document(
    file: UploadFile = File(...),
    doc_type: str = Form(None),
    additional_info: str = Form(None)
):
    # [VÁ A01] Ghi ra file tạm với tên NGẪU NHIÊN trong thư mục riêng.
    # Tránh path traversal (tên chứa '../') và đụng tên khi nhiều request song song.
    temp_pdf_path = os.path.join(TEMP_UPLOAD_DIR, f"{uuid.uuid4().hex}.pdf")
    with open(temp_pdf_path, "wb") as f:
        f.write(await file.read())

    safe_stem = _safe_stem(file.filename)

    try:
        status_code, extracted_json = await orchestrator.handle_request(
            file_path=temp_pdf_path,
            doc_type=doc_type,
            additional_info=additional_info
        )

        if status_code != 200:
            return JSONResponse(status_code=400, content={"error": "Lỗi trích xuất", "details": extracted_json})

        os.makedirs("output_final", exist_ok=True)
        output_mrc_path = f"output_final/{safe_stem}.mrc"
        output_json_path = f"output_final/{safe_stem}_marc.json"
        output_dc_path = f"output_final/{safe_stem}_dc.json"

        # [VÁ A04] MARC và Dublin Core chạy ĐỘC LẬP: một nhánh lỗi không kéo
        # sập nhánh kia, và không làm hỏng cả request.
        final_marc_dict = None
        marc_error = None
        try:
            final_marc_dict = converter.process_raw_dict(
                raw_data=extracted_json,
                output_mrc=output_mrc_path,
                output_json=output_json_path
            )
        except Exception as marc_err:
            marc_error = str(marc_err)
            logger.exception("[MARC] Lỗi ánh xạ MARC21")

        dublin_core_dict = None
        dc_error = None
        try:
            dublin_core_dict = dc_converter.process_raw_dict(
                raw_data=extracted_json,
                output_json=output_dc_path,
            )
        except Exception as dc_err:
            dc_error = str(dc_err)
            logger.exception("[DC] Lỗi ánh xạ Dublin Core")

        # Nếu cả hai cùng hỏng thì mới coi là thất bại toàn cục
        if final_marc_dict is None and dublin_core_dict is None:
            return JSONResponse(
                status_code=500,
                content={"error": "Ánh xạ thất bại", "marc_error": marc_error, "dc_error": dc_error},
            )

        return {
            "status": "success",
            "extracted_raw_data": extracted_json,
            "marc21_record": final_marc_dict,
            "marc_error": marc_error,                               # None nếu không lỗi
            "dublin_core_record": dublin_core_dict,
            "dc_error": dc_error,
            "file_paths": {
                "mrc_file": output_mrc_path if final_marc_dict is not None else None,
                "json_file": output_json_path if final_marc_dict is not None else None,
                "dc_file": output_dc_path if dublin_core_dict is not None else None,
            }
        }

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

class SaveRecordRequest(BaseModel):
    source_file: str
    marc_record: Dict[str, Any]


@app.post("/api/v1/save-record")
async def save_record(payload: SaveRecordRequest):
    """[VÁ F04] Nhận biểu ghi đã sửa từ giao diện và ghi đè .mrc/_marc.json.

    Dùng cùng _safe_stem như lúc xử lý để trỏ đúng file gốc trong output_final.
    """
    stem = _safe_stem(payload.source_file)
    os.makedirs("output_final", exist_ok=True)
    out_mrc = f"output_final/{stem}.mrc"
    out_json = f"output_final/{stem}_marc.json"

    try:
        saved = converter.save_edited_record(
            marc_dict=payload.marc_record,
            output_mrc=out_mrc,
            output_json=out_json,
        )
        logger.info(f"[SAVE] Đã ghi biểu ghi đã sửa: {out_mrc}")
        return {
            "status": "success",
            "marc21_record": saved,
            "file_paths": {"mrc_file": out_mrc, "json_file": out_json},
        }
    except Exception as e:
        logger.exception("[SAVE] Lỗi ghi biểu ghi đã sửa")
        return JSONResponse(status_code=500, content={"error": f"Không ghi được biểu ghi: {e}"})


async def run_batch_processing(use_ocr: bool):
    logger.info("Kích hoạt chế độ xử lý Batch từ thư mục nội bộ extract_module/data")

    batch_orchestrator = CentralOrchestrator(use_ocr=use_ocr)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "extract_module", "data")

    metadata_path = os.path.join(data_dir, "batch_metadata.json")
    metadata_items_raw = []

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_items_raw = json.load(f)
                logger.info(f"Đã tải batch metadata từ: {metadata_path}")
        except Exception:
            logger.error("Không thể đọc batch metadata, sẽ dùng cấu hình mặc định")

    metadata_map = {os.path.basename(it.get("path", "")): it for it in metadata_items_raw if it.get("path")}

    pdf_paths = glob.glob(os.path.join(data_dir, "*.pdf"))
    if not pdf_paths and metadata_items_raw:
        pdf_paths = [os.path.join(data_dir, os.path.basename(it["path"])) for it in metadata_items_raw if it.get("path")]

    if not pdf_paths:
        logger.warning(f"Không tìm thấy file PDF nào tại thư mục: {data_dir}")
        return

    output_base_dir = os.path.join(base_dir, "output_final", datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(output_base_dir, exist_ok=True)

    for sample_pdf_path in pdf_paths:
        name = os.path.basename(sample_pdf_path)
        meta = metadata_map.get(name, {})
        doc_type = meta.get("doc_type")
        additional_info = meta.get("additional_info")

        logger.info(f"Đang trích xuất: {name} (doc_type={doc_type})")

        status_code, response_data = await batch_orchestrator.handle_request(
            file_path=sample_pdf_path,
            doc_type=doc_type,
            additional_info=additional_info,
        )

        if status_code == 200:
            base_name = os.path.splitext(name)[0]

            out_mrc = os.path.join(output_base_dir, f"{base_name}.mrc")
            out_json = os.path.join(output_base_dir, f"{base_name}_marc.json")
            out_dc = os.path.join(output_base_dir, f"{base_name}_dc.json")

            # [VÁ A04] Mỗi nhánh độc lập trong batch
            try:
                converter.process_raw_dict(
                    raw_data=response_data,
                    output_mrc=out_mrc,
                    output_json=out_json
                )
            except Exception as marc_err:
                logger.error(f"[MARC] Lỗi map MARC cho {name}: {marc_err}")

            try:
                dc_converter.process_raw_dict(
                    raw_data=response_data,
                    output_json=out_dc,
                )
            except Exception as dc_err:
                logger.error(f"[DC] Lỗi map Dublin Core cho {name}: {dc_err}")

            logger.info(f" Biên mục xong file {name} -> Lưu tại {output_base_dir}")
        else:
            logger.error(f" Thất bại khi xử lý file {name}: {response_data}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hệ thống Biên mục Tổng thể Backend")
    parser.add_argument("--batch", action="store_true", help="Chạy chế độ quét file hàng loạt trong thư mục data")
    parser.add_argument("--use-ocr", action="store_true", help="Sử dụng OCR trong chế độ batch")

    args, unknown = parser.parse_known_args()

    if args.batch:
        asyncio.run(run_batch_processing(use_ocr=args.use_ocr))
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)