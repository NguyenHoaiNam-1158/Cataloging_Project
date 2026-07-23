# Extract Module

Pipeline trích xuất thư mục từ PDF bằng OCR (PaddleOCR) + AI (Gemini / Qwen), xuất ra JSON và MARC21.

## Kiến trúc

```
                    ┌─────────────────────────────┐
                    │     CentralOrchestrator      │
                    │  (core/orchestrator.py)      │
                    └──────────┬──────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
   ┌─────────────────────┐       ┌─────────────────────┐
   │  Image Mode (mặc định) │       │    OCR Mode          │
   │  PDF → Ảnh → LLM    │       │  PDF → OCR → LLM     │
   └─────────────────────┘       └─────────────────────┘
         │                              │
         ▼                              ▼
   ┌──────────┐                 ┌──────────────┐
   │ImageProc │                 │PaddleOCRAdapt│
   │  essor   │                 │   er         │
   └──────────┘                 └──────────────┘
         │                              │
         ▼                              ▼
   ┌──────────────────────────────────────────┐
   │           LLMManager                     │
   │  ┌──────────┐  ┌──────────┐             │
   │  │  Gemini  │  │   Qwen   │  (fallback) │
   │  └──────────┘  └──────────┘             │
   └──────────────────────────────────────────┘
                      │
                      ▼
   ┌──────────────────────────────────────────┐
   │           DataParser                     │
   │       (postprocessing/data_parser.py)    │
   └──────────────────────────────────────────┘
                      │
                      ▼
   ┌──────────────────────────────────────────┐
   │           Marc21Mapper                   │
   │       (postprocessing/marc21_mapper.py)  │
   └──────────────────────────────────────────┘
```

## Tính năng

- **2 chế độ trích xuất**: gửi ảnh trực tiếp (mặc định) hoặc OCR qua PaddleOCR
- **Adapter pattern** cho cả OCR (`BaseOCRAdapter`) và LLM (`BaseLLMAdapter`)
- **Fallback** Gemini → Qwen nếu API lỗi
- **Retry** tự động khi API quá tải (429, 503, 500)
- **Output**: Extraction JSON + MARC21 JSON + MARC21 binary (.mrc)
- **Batch processing**: tự động xử lý tất cả PDF trong `data/`
- **Metadata per-file** qua `data/batch_metadata.json`

## Cấu trúc thư mục

```
extract_module/
├── main.py                          # Entrypoint CLI
├── requirements.txt                 # Dependencies
├── Dockerfile                       # Docker image
├── config/
│   ├── settings.py                  # Biến môi trường
│   └── model_config.py              # Cấu hình model
├── core/
│   └── orchestrator.py              # CentralOrchestrator
├── modules/
│   ├── ocr_adapters/                # OCR Adapter (mới)
│   │   ├── __init__.py
│   │   ├── base_ocr_adapter.py      # Abstract base
│   │   └── paddle_ocr_adapter.py    # PaddleOCR implementation
│   ├── llm_adapters/                # LLM Adapter
│   │   ├── base_adapter.py          # Abstract base
│   │   ├── gemini_adapter.py        # Gemini
│   │   ├── qwen_adapter.py          # Qwen/OpenRouter
│   │   └── llm_manager.py           # Quản lý retry + fallback
│   ├── preprocessing/
│   │   ├── image_processor.py       # PDF → Ảnh
│   │   └── prompt_manager.py        # Xây prompt + schema
│   └── postprocessing/
│       ├── data_parser.py           # Parse text → JSON
│       └── marc21_mapper.py         # JSON → MARC21 (mới)
├── resources/
│   ├── prompts/
│   │   ├── extraction_prompt_v3.md
│   │   ├── lv_la_promtp.md
│   │   └── nckh_prompt.md
│   └── schema/
│       └── extraction_schema.json
├── utils/
│   ├── logger.py
│   └── exceptions.py
├── data/                            # PDF đầu vào
├── output/                          # Kết quả đầu ra
└── tests/                           # Unit tests (mới)
    ├── test_adapters.py
    ├── test_data_parser.py
    ├── test_ocr_adapter.py
    └── test_orchestrator.py
```

## Cài đặt

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1    # PowerShell
pip install -r requirements.txt
```

> **Lưu ý**: Cần có model PaddleOCR trong thư mục `paddle markdown/` (xem phần Model OCR).

## Cấu hình môi trường

Tạo file `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key
QWEN_API_KEY=your_qwen_api_key
MAX_RETRIES=4
DEFAULT_EXTRACT_PAGES=1
USE_OCR=false
PADDLE_MODEL_SIZE=tiny
```

| Biến | Mô tả |
|------|-------|
| `GEMINI_API_KEY` | API key cho Gemini |
| `QWEN_API_KEY` | API key cho Qwen/OpenRouter |
| `MAX_RETRIES` | Số lần retry Gemini trước fallback (mặc định: 4) |
| `DEFAULT_EXTRACT_PAGES` | Số trang PDF đầu chuyển ảnh (mặc định: 1) |
| `USE_OCR` | `true` để dùng PaddleOCR, `false` để gửi ảnh trực tiếp |
| `PADDLE_MODEL_SIZE` | Kích thước model OCR: `tiny`, `small`, `medium` |

## Cách dùng

### 1. Chuẩn bị dữ liệu

Đặt PDF vào `data/`. Tạo `data/batch_metadata.json` nếu cần metadata riêng cho từng file:

```json
[
  {
    "path": "data/Mau Bao cao KHCN.pdf",
    "doc_type": "bao_cao_nckh",
    "additional_info": "Nguồn: Thư viện ĐHYD TP.HCM"
  },
  {
    "path": "data/Luan van.pdf",
    "doc_type": "luan_van",
    "additional_info": ""
  }
]
```

### 2. Chạy pipeline

**Chế độ ảnh (mặc định):**
```bash
python main.py
```

**Chế độ OCR:**
```bash
python main.py --use-ocr
```

Hoặc dùng biến môi trường:
```bash
$env:USE_OCR = "true"
python main.py
```

### 3. Output

Kết quả lưu vào `output/YYYY-MM-DD/`:

| File | Định dạng | Mô tả |
|------|-----------|-------|
| `ket_qua_trich_xuat(...).json` | JSON | Dữ liệu trích xuất gốc |
| `MARC21_...json` | MARC-in-JSON | Biểu ghi MARC21 dạng JSON |
| `MARC21_...mrc` | Binary MARC21 | Biểu ghi MARC21 dạng .mrc |

## Chi tiết luồng xử lý

### Image Mode (mặc định)
```
PDF → ImageProcessor (PDF → Ảnh)
    → PromptManager (xây prompt)
        → LLMManager → Gemini/Qwen (gửi ảnh + prompt)
            → DataParser (parse response → JSON)
                → Marc21Mapper (JSON → MARC21)
```

### OCR Mode (`--use-ocr`)
```
PDF → PaddleOCRAdapter (PaddleOCR → Markdown)
    → PromptManager (xây prompt)
        → LLMManager → Gemini/Qwen (gửi text + prompt)
            → DataParser (parse response → JSON)
                → Marc21Mapper (JSON → MARC21)
```

## Model OCR

PaddleOCRAdapter sử dụng model PP-OCRv6 (tiny/small/medium). Các model file được đặt trong thư mục `paddle markdown/`:

```
paddle markdown/
├── PP-OCRv6_tiny_det_safetensors/
├── PP-OCRv6_tiny_rec_safetensors/
├── PP-OCRv6_small_det_safetensors/
├── PP-OCRv6_small_rec_safetensors/
├── PP-OCRv6_medium_det_safetensors/
└── PP-OCRv6_medium_rec_safetensors/
```

## Docker

```bash
# Build và chạy
docker-compose up extract-module

# Hoặc run với OCR
docker-compose run extract-module python main.py --use-ocr
```

Docker mount:
- `./OCR/paddle markdown:/app/paddle markdown` — model OCR
- `./OCR/BC KHCN:/app/data` — PDF đầu vào

## Kiểm thử

```bash
# Chạy toàn bộ test (18 tests, không cần API key)
python -m pytest tests/ -v
```

## API keys

- **Gemini**: lấy free tại https://aistudio.google.com/apikey
- **Qwen/OpenRouter**: đăng ký tại https://openrouter.ai
- Có thể set key qua biến môi trường hoặc file `.env`
