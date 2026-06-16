import os
import re
import json
import time
import pdfplumber
from concurrent.futures import ThreadPoolExecutor, as_completed

from mapping_module.config.settings import Settings

def parse_lcc_pdf_accurate_and_fast(pdf_path):
    lcc_dict = {}
    try:
        lcc_pattern = re.compile(r'^([A-Z]{1,3}\s?\d*(?:\.\d+)?)\s*[-–:]?\s*(.+)$')
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        line = line.strip()
                        match = lcc_pattern.match(line)
                        if match:
                            code = match.group(1).strip()
                            description = match.group(2).strip()
                            lcc_dict[code] = description
    except Exception as e:
        Settings.log.error(f"Lỗi khi đọc file {os.path.basename(pdf_path)}: {e}")
    return lcc_dict

def extract_all_lcc(pdf_folder: str = Settings.PDF_FOLDER, output_path: str = Settings.LCC_OUTPUT_FILE):
    master_lcc_index = {}
    if os.path.exists(pdf_folder):
        pdf_files = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    else:
        pdf_files = []
        Settings.log.error(f"Không tìm thấy thư mục: {pdf_folder}")

    if pdf_files:
        Settings.log.info(f"Bắt đầu quét {len(pdf_files)} file PDF bằng pdfplumber (Đa luồng)...")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(parse_lcc_pdf_accurate_and_fast, path): path for path in pdf_files}
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    file_data = future.result()
                    master_lcc_index.update(file_data)
                except Exception as exc:
                    Settings.log.error(f"{os.path.basename(file_path)} gặp sự cố: {exc}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(master_lcc_index, f, indent=4, ensure_ascii=False)

        end_time = time.time()
        Settings.log.info(f"Hoàn thành LCC Index! Tổng thời gian: {round(end_time - start_time, 2)} giây.")
    return master_lcc_index


def parse_subject_650_pdf(pdf_path):
    subject_dict = {}
    try:
        subject_pattern = re.compile(r'^\s*(?:\d+[\.)]?\s*)?(?P<term>[^\-–:]+?)(?:\s*[-–:]\s*(?P<desc>.+))?$')
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        match = subject_pattern.match(line)
                        if match:
                            term = match.group('term').strip()
                            desc = match.group('desc')
                            if term:
                                subject_dict[term] = desc.strip() if desc else term
    except Exception as e:
        Settings.log.error(f"Lỗi khi đọc file subject 650 {os.path.basename(pdf_path)}: {e}")
    return subject_dict


def extract_all_subject_650(pdf_folder: str = Settings.PDF_FOLDER_650, output_path: str = Settings.SUBJECT_650_OUTPUT_FILE):
    subject_index = {}
    if os.path.exists(pdf_folder):
        pdf_files = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    else:
        pdf_files = []
        Settings.log.error(f"Không tìm thấy thư mục subject 650: {pdf_folder}")

    if pdf_files:
        Settings.log.info(f"Bắt đầu trích xuất 650 từ {len(pdf_files)} file PDF bằng pdfplumber...")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(parse_subject_650_pdf, path): path for path in pdf_files}
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    file_data = future.result()
                    subject_index.update(file_data)
                except Exception as exc:
                    Settings.log.error(f"{os.path.basename(file_path)} gặp sự cố: {exc}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(subject_index, f, indent=4, ensure_ascii=False)

        end_time = time.time()
        Settings.log.info(f"Hoàn thành Subject 650 Index! Tổng thời gian: {round(end_time - start_time, 2)} giây.")
    return subject_index


if __name__ == "__main__":
    extract_all_lcc()