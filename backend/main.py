import os
import sys
import glob
import json
import argparse
import asyncio
import logging
import uvicorn
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extract_module.core.orchestrator import CentralOrchestrator
from mapping_module.core.converters import DocumentConverter
from dublin_core_module import DublinCoreConverter          

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("BACKEND_MAIN")

app = FastAPI(title="Hệ thống Biên mục Tự động")

orchestrator = CentralOrchestrator(use_ocr=False)
converter = DocumentConverter()
dc_converter = DublinCoreConverter()     

@app.post("/api/v1/process-document")
async def process_document(
    file: UploadFile = File(...),
    doc_type: str = Form(None),
    additional_info: str = Form(None)
):
    temp_pdf_path = f"temp_{file.filename}"
    with open(temp_pdf_path, "wb") as f:
        f.write(await file.read())

    try:
        status_code, extracted_json = await orchestrator.handle_request(
            file_path=temp_pdf_path,
            doc_type=doc_type,
            additional_info=additional_info
        )

        if status_code != 200:
            return JSONResponse(status_code=400, content={"error": "Lỗi trích xuất", "details": extracted_json})

        os.makedirs("output_final", exist_ok=True)
        output_mrc_path = f"output_final/{file.filename}.mrc"
        output_json_path = f"output_final/{file.filename}_marc.json"
        output_dc_path = f"output_final/{file.filename}_dc.json"     

        final_marc_dict = converter.process_raw_dict(
            raw_data=extracted_json,
            output_mrc=output_mrc_path,
            output_json=output_json_path
        )

        dublin_core_dict = None
        try:
            dublin_core_dict = dc_converter.process_raw_dict(
                raw_data=extracted_json,
                output_json=output_dc_path,
            )
        except Exception as dc_err:
            logger.error(f"[DC] Lỗi ánh xạ Dublin Core: {dc_err}")

        return {
            "status": "success",
            "extracted_raw_data": extracted_json,
            "marc21_record": final_marc_dict,
            "dublin_core_record": dublin_core_dict,  
            "file_paths": {
                "mrc_file": output_mrc_path,
                "json_file": output_json_path,
                "dc_file": output_dc_path,                          
            }
        }

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

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
            converter.process_raw_dict(
                raw_data=response_data,
                output_mrc=out_mrc,
                output_json=out_json
            )

            try:
                dc_converter.process_raw_dict(
                    raw_data=response_data,
                    output_json=out_dc,
                )
            except Exception as dc_err:
                logger.error(f"[DC] Lỗi ánh xạ Dublin Core cho {name}: {dc_err}")

            logger.info(f" Biên mục thành công file {name} -> Lưu tại {output_base_dir}")
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