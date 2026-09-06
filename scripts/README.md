# scripts/ — Cài đặt & chạy trên Windows

Bộ script `.bat` để dựng dự án trên một **máy mới** và chạy hằng ngày.
Chạy bằng cách **nháy đúp** hoặc gọi từ CMD ở thư mục gốc dự án.

| Script | Chức năng |
|--------|-----------|
| `setup.bat` | **Chạy 1 lần trên máy mới.** Kiểm tra công cụ → tự cài `uv` → tạo `.env` → `uv sync` cho `backend` + `ai-agent` → `npm install` cho `frontend_react`. |
| `start-backend.bat` | Chạy FastAPI tại http://localhost:8000/docs. Truyền tham số được: `start-backend.bat --batch --use-ocr`. |
| `start-frontend.bat` | Chạy Vite dev server tại http://localhost:5173 (tự proxy `/api` sang backend). |
| `start-dev.bat` | Mở cả backend + frontend, mỗi cái một cửa sổ. |

## Yêu cầu cài sẵn (script sẽ báo nếu thiếu)

| Công cụ | Cài |
|---------|-----|
| Git | `winget install Git.Git` |
| Node.js 20+ (khuyến nghị LTS 22) | `winget install OpenJS.NodeJS.LTS` |
| `uv` | `setup.bat` tự cài (winget hoặc script astral). Không cần cài Python tay — `uv` tự tải Python 3.12. |
| Docker Desktop | *tùy chọn*, chỉ cần nếu chạy qua `docker compose` |

> Sau khi cài Git/Node, **mở lại cửa sổ CMD** rồi mới chạy `setup.bat`.

## Các bước trên máy mới

```
1. git clone https://github.com/NguyenHoaiNam-1158/Cataloging_Project.git
2. cd Cataloging_Project
3. scripts\setup.bat
4. Mở file  .env  →  điền  GEMINI_API_KEY=...
5. scripts\start-dev.bat
```

## Ghi chú

- Lần `setup.bat` đầu tiên tải khá nặng (~1–2 GB: torch, faiss-cpu, sentence-transformers,
  paddleocr/paddlepaddle) — bình thường.
- `.env` **bắt buộc** có `GEMINI_API_KEY`. `QWEN_API_KEY` là tùy chọn (fallback).
- Toàn bộ dependency Python của backend nằm ở `backend/pyproject.toml` + `uv.lock`
  (đã bao trùm `extract_module`, `mapping_module`, `dublin_core_module`, Streamlit).
  Các file `requirements.txt` trong module con là bản cũ, không dùng cho luồng `uv`.
- RAG index (`backend/mapping_module/rag_index/*.faiss`) đã có sẵn trong repo nên
  không cần build lại; nếu thiếu, hệ thống tự bỏ qua bước gán mã LCC/NLM.
- Chạy bằng Docker: `docker compose up --build -d` — **hiện chưa chạy đủ** vì
  `docker-compose.yml` còn trỏ service `frontend` tới `./frontend` (không tồn tại);
  cần sửa context sang `frontend_react`/`frontend_streamlit` trước.
