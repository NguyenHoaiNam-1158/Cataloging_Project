# Extractor Module

Một pipeline Python để trích xuất metadata từ trang bìa PDF bằng AI (Gemini / Qwen).

## Mục tiêu
- Chuyển đổi trang bìa PDF thành ảnh
- Xây dựng prompt cho model dựa trên `doc_type` và `additional_info`
- Gọi API Gemini trước, fallback sang Qwen nếu cần
- Parse kết quả text trả về thành JSON theo schema
- Lưu output vào thư mục `output/YYYY-MM-DD`

## Cấu trúc chính
- `main.py` → entrypoint, chạy batch PDF trong `data/`
- `core/orchestrator.py` → điều phối luồng dữ liệu
- `modules/preprocessing/prompt_manager.py` → xây prompt + load schema
- `modules/preprocessing/image_processor.py` → chuyển PDF thành ảnh
- `modules/llm_adapters/` → adapter Gemini/Qwen
- `modules/postprocessing/data_parser.py` → parse text thành JSON
- `config/settings.py` → cấu hình môi trường
- `config/model_config.py` → cấu hình model/ảnh

## Cài đặt
1. Tạo và kích hoạt virtualenv:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # PowerShell
# hoặc
.venv\Scripts\activate.bat  # cmd
```

2. Cài dependencies:

```bash
pip install -r requirements.txt
```

## Cấu hình môi trường
Tạo file `.env` ở gốc dự án với các biến sau:

```env
GEMINI_API_KEY=your_gemini_api_key
QWEN_API_KEY=your_qwen_api_key
MAX_RETRIES=4
DEFAULT_EXTRACT_PAGES=1
```

### Giải thích các biến
- `GEMINI_API_KEY`: API key cho Gemini
- `QWEN_API_KEY`: API key cho Qwen/OpenRouter
- `MAX_RETRIES`: số lần thử gọi Gemini trước khi fallback sang Qwen
- `DEFAULT_EXTRACT_PAGES`: số trang PDF đầu tiên sẽ chuyển sang ảnh
  - giá trị mặc định là `1` (chỉ trang bìa)

## Cách dùng
1. Đặt PDF vào thư mục `data/`
2. Nếu cần metadata per-file, tạo `data/batch_metadata.json`

Ví dụ `data/batch_metadata.json`:

```json
[
  {
    "path": "data/Mau Bao cao KHCN_Tran Thi Trung Chien.pdf",
    "doc_type": "bao_cao_nckh",
    "additional_info": "Nguồn: Thư viện ĐHYD TP.HCM - Cơ sở 2."
  },
  {
    "path": "data/Another_Thesis.pdf",
    "doc_type": "",
    "additional_info": ""
  }
]
```

3. Chạy pipeline:

```bash
python main.py
```

## Output
- Kết quả JSON được lưu vào thư mục:
  - `output/YYYY-MM-DD/ket_qua_trich_xuat(<tên file>).json`

## Luồng hoạt động dữ liệu
1. `main.py` quét tất cả PDF trong `data/`
2. Nếu `data/batch_metadata.json` tồn tại, mỗi file PDF được gán `doc_type` và `additional_info`
3. `CentralOrchestrator.handle_request(...)` xử lý từng file:
   - chuyển trang PDF thành ảnh
   - tạo prompt
   - gọi LLM
   - parse kết quả thành JSON
4. JSON output được lưu vào thư mục theo ngày

## Prompt và schema
- `resources/prompts/nckh_prompt.md`: prompt cho báo cáo khoa học
- `resources/prompts/lv_la_prompt.md`: prompt cho luận văn/luận án
- `resources/prompts/extraction_prompt_v3.md`: prompt mặc định khi `doc_type` không xác định
- `resources/schema/extraction_schema.json`: schema đầu ra

## Cấu hình có thể chỉnh sửa
### `config/settings.py`
- `GEMINI_API_KEY`
- `QWEN_API_KEY`
- `MAX_RETRIES`
- `DEFAULT_EXTRACT_PAGES`

### `config/model_config.py`
- `TEMPERATURE`: độ sáng tạo của model
- `JPEG_QUALITY`: chất lượng ảnh JPEG đầu vào
- `IMAGE_DPI`: độ phân giải ảnh từ PDF

## Ghi chú
- Nếu `DEFAULT_EXTRACT_PAGES > 1`, pipeline sẽ lấy nhiều trang đầu tiên của PDF.
- `PromptManager` đang dùng `doc_type` để chọn prompt và thêm `additional_info` nếu có.
- `LLMManager` ưu tiên Gemini, fallback sang Qwen.

## Lỗi thường gặp
- `FileNotFoundError: Không tìm thấy file prompt` → kiểm tra `doc_type` và tên file prompt trong `resources/prompts/`
- `ValueError` khi thiếu API key → kiểm tra `.env`

## Mở rộng
Khả năng mở rộng:
- thêm prompt mới vào `resources/prompts/`
- parse các kiểu trả về LLM khác nhau
- xử lý nhiều trang PDF bằng cách chỉnh thông số trong `DEFAULT_EXTRACT_PAGES`
