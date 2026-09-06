# Cataloging_Project — Hệ thống Biên mục Thư viện Tự động

Hệ thống biên mục tự động cho Thư viện Trường Đại học Y Dược TP.HCM (DHYD/UMP).
Đầu vào là file PDF/ảnh trang bìa tài liệu (sách, luận văn, luận án, báo cáo NCKH,
tạp chí); đầu ra là biểu ghi **MARC21** (`.mrc` + JSON) và **Dublin Core** (JSON).

## Luồng xử lý

```
PDF/ảnh
  │  POST /api/v1/process-document  (backend/main.py — FastAPI)
  ▼
extract_module   PDF → (render ảnh trang 1 | OCR PaddleOCR) → LLM (Gemini→Qwen)
                 → DataParser → dict thô (~40 trường, theo extraction_schema.json)
  ▼
  ├─ mapping_module      dict → 9 field-mapper → pymarc.Record → .mrc + _marc.json
  │                      (+ RAG: FAISS + Gemini tự gán mã LCC/NLM, sinh tóm tắt 520)
  └─ dublin_core_module  dict → 15 element-mapper → _dc.json
  ▼
Frontend: thủ thư sửa tay trên bảng MARC → POST /api/v1/save-record → ghi đè .mrc
```

## Cấu trúc thư mục

```text
Cataloging_Project/
├── backend/
│   ├── main.py                  # FastAPI: /process-document, /save-record; có chế độ --batch
│   ├── extract_module/          # PDF → ảnh/OCR → LLM → JSON thô
│   │   ├── extract_main.py      # entrypoint CLI chạy riêng
│   │   ├── core/orchestrator.py
│   │   ├── modules/             # llm_adapters, ocr_adapters, preprocessing, postprocessing
│   │   └── resources/           # prompts/ + schema/extraction_schema.json
│   ├── mapping_module/          # JSON thô → MARC21
│   │   ├── pipeline/marc_pipeline.py
│   │   ├── mappers/             # control/identifier/title/author/pub_phys/note/rag/local
│   │   ├── LCC_and_NLM/         # rag_engine.py (FAISS + embeddings), scraper.py (NLM)
│   │   └── rag_index/           # FAISS index đã build sẵn
│   ├── dublin_core_module/      # JSON thô → Dublin Core 15 phần tử
│   └── output_final/            # kết quả .mrc + _marc.json + _dc.json
├── ai-agent/                    # placeholder (chưa có logic — chỉ giữ container sống)
├── frontend_react/              # UI chính (Vite + React + Tailwind + react-router)
├── frontend_streamlit/          # UI thay thế (Streamlit) — sơ khai
├── docker-compose.yml
└── .env.example
```

## Công nghệ

* **Backend:** Python 3.12, FastAPI, pymarc, pydantic
* **AI trích xuất:** Google Gemini (chính) → Qwen/OpenRouter (fallback); PaddleOCR (tùy chọn)
* **RAG phân loại:** sentence-transformers (`all-MiniLM-L6-v2`, chạy local) + FAISS + Gemini
* **Frontend:** React 18 + Vite (chính); Streamlit (phụ)
* **Hạ tầng:** Docker Compose; PostgreSQL 15 (đã khai báo, **chưa được sử dụng trong code**)

## Chạy nhanh (chỉ backend, môi trường local)

```bash
cp .env.example .env          # điền GEMINI_API_KEY (bắt buộc)

cd backend
uv sync                       # hoặc: pip install -r <mỗi module>/requirements.txt
uv run python main.py         # FastAPI tại http://localhost:8000/docs

# xử lý hàng loạt PDF trong backend/extract_module/data/
uv run python main.py --batch [--use-ocr]
```

Frontend React:

```bash
cd frontend_react
npm install
npm run dev                   # http://localhost:5173, gọi API qua proxy Vite
```

> Trên Windows: chạy `scripts\setup.bat` một lần, rồi `scripts\start-dev.bat`
> (chi tiết trong [`scripts/README.md`](scripts/README.md)).

## Cách sử dụng

1. Mở `http://localhost:5173`, vào trang **Tải lên**.
2. Kéo–thả một hoặc nhiều file PDF/ảnh trang bìa, chọn **loại tài liệu**
   (Sách / Luận văn – Luận án / Nghiên cứu khoa học), điền dữ liệu bổ sung nếu cần.
3. Bấm **Bắt đầu trích xuất** — mỗi file được xử lý lần lượt qua AI rồi tự ánh xạ
   sang MARC21 + Dublin Core.
4. Sang trang **Biên tập MARC21**: rà lại các trường (trường AI đánh dấu độ tin
   cậy thấp được tô màu), sửa trực tiếp trên bảng.
5. **Lưu bản ghi** để ghi `.mrc` + `_marc.json` vào `backend/output_final/`, hoặc
   **Xuất JSON** để tải về.

Xử lý hàng loạt không cần giao diện: đặt PDF vào `backend/extract_module/data/`
(kèm `batch_metadata.json` nếu muốn khai báo loại tài liệu cho từng file) rồi chạy
`uv run python main.py --batch`.

## Biến môi trường chính (`.env`)

| Biến | Bắt buộc | Mô tả |
|------|----------|-------|
| `GEMINI_API_KEY` | ✅ | Key Gemini cho trích xuất + RAG |
| `QWEN_API_KEY` | | Key fallback khi Gemini lỗi |
| `USE_OCR` | | `true` để dùng PaddleOCR thay vì gửi ảnh |
| `PADDLE_MODEL_SIZE` | | `tiny` / `small` / `medium` |
| `POSTGRES_*` | | Cấu hình service `db` trong compose |

## Trạng thái & hạn chế đã biết

* `docker-compose.yml` còn tham chiếu `./frontend` (không tồn tại) và mount `./OCR/...` —
  cần cập nhật context sang `frontend_react` hoặc `frontend_streamlit` trước khi
  `docker compose up` chạy được đầy đủ.
* `ai-agent/` chưa có logic; toàn bộ tác vụ AI hiện nằm trong `backend`.
* PostgreSQL chưa được kết nối — kết quả chỉ lưu ra file trong `backend/output_final/`.
* Frontend React giữ biểu ghi trong bộ nhớ (mất khi refresh); các màn hình
  Tổng quan / Xử lý / Tìm kiếm danh mục là placeholder "phát triển sau".
* Tồn tại 2 bộ ánh xạ MARC21 song song: `extract_module/modules/postprocessing/marc21_mapper.py`
  (dùng bởi `extract_main.py`) và `mapping_module/mappers/*` (dùng bởi `backend/main.py`).
