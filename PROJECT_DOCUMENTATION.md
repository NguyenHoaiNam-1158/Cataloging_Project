# CATALOGING_PROJECT — TÀI LIỆU TOÀN DIỆN VỀ KIẾN TRÚC & HƯỚNG DẪN VẬN HÀNH

> **Dự án:** Hệ thống Biên mục Thư viện Tự động (Cataloging Automation System)  
> **Đơn vị ứng dụng:** Thư viện Trường Đại học Y Dược TP.HCM (UMP / DHYD)  
> **Mục tiêu:** Tự động hóa quá trình trích xuất siêu dữ liệu từ file PDF/ảnh trang bìa tài liệu học thuật (sách, luận văn, luận án, báo cáo NCKH, tạp chí y dược), tự động phân loại chuẩn quốc tế (LCC, NLM) và sinh biểu ghi chuẩn **MARC21** (`.mrc`, `.json`) cùng **Dublin Core** (`.json`).

---

## MỤC LỤC
1. [Tổng quan hệ thống & Luồng dữ liệu](#1-tổng-quan-hệ-thống--luồng-dữ-liệu)
2. [Cấu trúc thư mục toàn dự án](#2-cấu-trúc-thư-mục-toàn-dự-án)
3. [Chi tiết các thành phần & Chức năng](#3-chi-tiết-các-thành-phần--chức-năng)
   - [3.1. Phân hệ Backend (`backend/`)](#31-phân-hệ-backend-backend)
   - [3.2. Module Trích xuất AI (`extract_module/`)](#32-module-trích-xuất-ai-extract_module)
   - [3.3. Module Ánh xạ MARC21 & RAG (`mapping_module/`)](#33-module-ánh-xạ-marc21--rag-mapping_module)
   - [3.4. Module Dublin Core (`dublin_core_module/`)](#34-module-dublin-core-dublin_core_module)
   - [3.5. Giao diện người dùng chính (`frontend_react/`)](#35-giao-diện-người-dùng-chính-frontend_react)
   - [3.6. Giao diện thay thế (`frontend_streamlit/`)](#36-giao-diện-thay-thế-frontend_streamlit)
   - [3.7. Module AI Agent nền (`ai-agent/`)](#37-module-ai-agent-nền-ai-agent)
   - [3.8. Bộ kịch bản Windows (`scripts/`)](#38-bộ-kịch-bản-windows-scripts)
4. [Cấu hình & Biến môi trường (`.env`)](#4-cấu-hình--biến-môi-trường-env)
5. [Hướng dẫn khởi chạy dự án](#5-hướng-dẫn-khởi-chạy-dự-án)
   - [Cách 1: Khởi chạy Local Native với `uv` & `npm` (Khuyến nghị cho Dev Windows)](#cách-1-khởi-chạy-local-native-với-uv--npm-khuyến-nghị-cho-dev-windows)
   - [Cách 2: Khởi chạy qua Docker Compose](#cách-2-khởi-chạy-qua-docker-compose)
   - [Cách 3: Chạy xử lý hàng loạt CLI (Batch Processing)](#cách-3-chạy-xử-lý-hàng-loạt-cli-batch-processing)
6. [Hướng dẫn từng bước cho người mới (Onboarding Step-by-Step)](#6-hướng-dẫn-từng-bước-cho-người-mới-onboarding-step-by-step)
7. [Các lưu ý kỹ thuật quan trọng & Xử lý sự cố (Troubleshooting)](#7-các-lưu-ý-kỹ-thuật-quan-trọng--xử-lý-sự-cố-troubleshooting)

---

## 1. TỔNG QUAN HỆ THỐNG & LUỒNG DỮ LIỆU

### 1.1. Bài toán nghiệp vụ
Trong quy trình quản trị thư viện truyền thống, thủ thư phải đọc thủ công từng trang bìa, trang phụ bìa và trang mục lục của sách, luận văn, luận án để gõ từng trường dữ liệu vào phần mềm quản lý (như Koha, DSpace, PMB) theo chuẩn MARC21. Quá trình này mất rất nhiều thời gian và dễ sai sót trong việc định dạng chỉ thị (indicators), mã trường con (subfields), cũng như tra cứu khung phân loại chuyên ngành y học (NLM Classification) và Thư viện Quốc hội Mỹ (LCC).

Hệ thống **Cataloging_Project** giải quyết bài toán này thông qua luồng tự động hóa 3 tầng:

```mermaid
flowchart TD
    A["Tài liệu đầu vào (PDF / Ảnh bìa)"] --> B["FastAPI Backend (/api/v1/process-document)"]
    
    subgraph ExtractModule ["Tầng 1: Extract Module (Trích xuất siêu dữ liệu)"]
        B --> C{"Chế độ trích xuất"}
        C -->|Image Mode (Mặc định)| D["Render trang 1 PDF thành Ảnh<br/>(pypdfium2 / pdfplumber)"]
        C -->|OCR Mode| E["PaddleOCR tiếng Việt"]
        D --> F["Prompt Manager<br/>(sach / luan_van / nckh)"]
        E --> F
        F --> G["LLM Manager<br/>(Google Gemini 2.5 / Fallback Qwen)"]
        G --> H["DataParser<br/>(Kiểm chuẩn JSON theo Schema ~40 trường)"]
    end
    
    H --> I["Dữ liệu JSON thô"]
    
    subgraph MappingModule ["Tầng 2: Ánh xạ chuẩn thư viện"]
        I --> J["Dublin Core Pipeline"]
        I --> K["MARC21 Pipeline (9 Mappers)"]
        K --> L["RAG Engine (FAISS + SentenceTransformers)<br/>Gán mã LCC / NLM & Độ tin cậy (Confidence)"]
        J --> M["Biểu ghi Dublin Core<br/>(*_dc.json)"]
        L --> N["Biểu ghi MARC21<br/>(*.mrc + *_marc.json)"]
    end
    
    subgraph FrontendUI ["Tầng 3: Kiểm soát & Biên tập Thủ thư"]
        N --> O["Giao diện React (Vite :5173)"]
        O --> P["Bảng biên tập MARC trực quan<br/>(Cảnh báo trường Confidence thấp)"]
        P -->|Thủ thư chỉnh sửa| Q["Lưu file đè .mrc / Xuất JSON"]
    end
```

---

## 2. CẤU TRÚC THƯ MỤC TOÀN DỰ ÁN

```text
Cataloging_Project/
├── .env                              # File biến môi trường thực tế (chứa API Keys)
├── .env.example                      # File mẫu biến môi trường
├── docker-compose.yml                # Cấu hình đa container Docker (db, backend, ai-agent, extract)
├── control_number_counter.json       # Bộ đếm số kiểm soát trường 001 theo năm
├── README.md                         # Tóm tắt tổng quan dự án
├── start-dev.bat                     # Shortcut Windows gọi start-dev.ps1
├── start-dev.ps1                     # Script PowerShell khởi động Docker Backend + Vite Frontend
│
├── backend/                          # ỨNG DỤNG BACKEND CHÍNH (FastAPI & Pipeline AI)
│   ├── main.py                       # Server FastAPI (endpoint /process-document, chế độ --batch)
│   ├── pyproject.toml                # Khai báo toàn bộ phụ thuộc Python (quản lý bởi uv)
│   ├── uv.lock                       # Lockfile phiên bản thư viện Python
│   ├── Dockerfile                    # Dockerfile build backend (cài uv, bake model embeddings)
│   ├── temp_uploads/                 # Thư mục lưu trữ tạm file tải lên trong phiên làm việc
│   ├── output_final/                 # Thư mục chứa kết quả xuất ra (.mrc, _marc.json, _dc.json)
│   │
│   ├── extract_module/               # MODULE 1: TRÍCH XUẤT THÔNG TIN TỪ TÀI LIỆU
│   │   ├── extract_main.py           # Entrypoint CLI chạy độc lập cho trích xuất
│   │   ├── config/                   # Cấu hình model, API keys, số trang trích xuất
│   │   │   ├── model_config.py
│   │   │   └── settings.py
│   │   ├── core/
│   │   │   └── orchestrator.py       # Bộ điều phối luồng (PDF -> Image/OCR -> LLM -> JSON Parser)
│   │   ├── modules/
│   │   │   ├── llm_adapters/         # Kết nối API LLM (GeminiAdapter, QwenAdapter, LLMManager)
│   │   │   ├── ocr_adapters/         # OCR quang học (PaddleOCRAdapter tiếng Việt)
│   │   │   ├── preprocessing/        # Xử lý ảnh (ImageProcessor), quản lý Prompt (PromptManager)
│   │   │   └── postprocessing/       # Phân tích văn bản thành JSON (DataParser), mapper phụ
│   │   ├── resources/
│   │   │   ├── prompts/              # Prompt chuyên biệt: sách, luận văn (lv_la), NCKH (nckh)
│   │   │   └── schema/               # extraction_schema.json (~40 trường dữ liệu)
│   │   └── data/                     # Thư mục chứa PDF đầu vào cho chế độ Batch CLI
│   │
│   ├── mapping_module/               # MODULE 2: ÁNH XẠ MARC21 & PHÂN LOẠI RAG
│   │   ├── main.py                   # FastAPI con / API test riêng cho mapping & save-record
│   │   ├── config/settings.py        # Thiết lập cơ quan biên mục (DHYD), ngôn ngữ, mã quy tắc
│   │   ├── core/
│   │   │   ├── base_mapper.py        # Lớp cha trừu tượng cho các trường MARC
│   │   │   ├── converters.py         # Chuyển đổi JSON sang MARC nhị phân và ngược lại
│   │   │   ├── models.py             # Pydantic models chuẩn hóa dữ liệu thô
│   │   │   ├── rag_bridge.py         # Cầu nối gọi RAG Engine phân loại sách
│   │   │   └── serializers.py        # Chuyển đổi giữa pymarc.Record và Dict/JSON
│   │   ├── mappers/                  # 9 Mapper chuyên trách từng trường MARC21:
│   │   │   ├── control_fields.py     # Leader, 001 (Control Number), 005, 008 (Fixed Field)
│   │   │   ├── identifier_fields.py  # 020 (ISBN), 022 (ISSN), 024 (Mã định danh khác)
│   │   │   ├── title_fields.py       # 245 (Nhan đề chính, phụ, trách nhiệm), 246 (Nhan đề song song)
│   │   │   ├── author_fields.py      # 100/700 (Tác giả cá nhân), 110/710 (Tác giả tập thể)
│   │   │   ├── pub_phys_fields.py    # 260/264 (Nơi, nhà XB, năm XB), 300 (Trang, kích thước)
│   │   │   ├── note_fields.py        # 500 (Ghi chú chung), 502 (Luận văn), 504 (Thư mục), 520 (Tóm tắt)
│   │   │   ├── rag_fields.py         # Ánh xạ cơ bản mã LCC/NLM
│   │   │   ├── rag_enriched_fields.py# Làm giàu dữ liệu: FAISS + SentenceTransformers + Gemini suy luận LCC/NLM
│   │   │   └── local_field.py        # Các trường địa phương: 090 (Mã xếp giá), 852 (Kho), 915, 927
│   │   ├── pipeline/
│   │   │   └── marc_pipeline.py      # Đường ống ráp nối tất cả các mapper và sinh pymarc.Record
│   │   ├── LCC_and_NLM/              # RAG Engine & Tool cào dữ liệu tra cứu NLM Classification
│   │   │   ├── rag_engine.py         # FAISS Vector Search + SentenceTransformer ('all-MiniLM-L6-v2')
│   │   │   └── scraper.py            # Công cụ quét sơ đồ phân loại NLM
│   │   ├── rag_index/                # Chỉ mục FAISS index và từ điển phân loại nạp sẵn
│   │   └── utils/                    # Xử lý dấu phân cách AACR2, trích xuất text PDF
│   │
│   └── dublin_core_module/           # MODULE 3: ÁNH XẠ DUBLIN CORE (15 THUỘC TÍNH)
│       ├── converters.py             # Bộ chuyển đổi cấp cao xuất ra file JSON DC
│       ├── validator.py              # Kiểm tra tính toàn vẹn 15 phần tử
│       ├── core/dc_record.py         # Cấu trúc lưu trữ biểu ghi Dublin Core
│       ├── mappers/                  # Chia nhóm: descriptive, publication, technical
│       └── pipeline/dc_pipeline.py   # Đường ống ánh xạ 15 thuộc tính DC
│
├── frontend_react/                   # GIAO DIỆN CHÍNH (React 18 + Vite + Tailwind CSS)
│   ├── package.json                  # Cấu hình thư viện NPM (react, lucide-react, react-router-dom)
│   ├── vite.config.js                # Cấu hình Vite Dev Server & Reverse Proxy (/api -> :8000)
│   ├── tailwind.config.js            # Thiết lập bảng màu, kiểu dáng giao diện
│   └── src/
│       ├── App.jsx                   # Định tuyến Router (Trang Upload, Biên tập MARC, Coming Soon)
│       ├── store.jsx                 # BatchContext quản lý trạng thái tài liệu trong phiên
│       ├── lib/api.js                # Gọi REST API backend (/process-document, /save-record)
│       ├── components/
│       │   ├── Sidebar.jsx           # Thanh điều hướng bên trái
│       │   ├── ui.jsx                # Các component giao diện: Card, Button, Badge, Spinner
│       │   └── ComingSoon.jsx        # Màn hình placeholder cho các phân hệ tương lai
│       └── pages/
│           ├── UploadPage.jsx        # Trang kéo thả tải PDF/ảnh, chọn loại tài liệu, chạy trích xuất
│           └── MarcEditorPage.jsx    # Bảng biên tập trực tiếp MARC21, cảnh báo độ tin cậy thấp
│
├── frontend_streamlit/               # GIAO DIỆN PHỤ (Streamlit Python UI)
│   ├── app.py                        # Entrypoint giao diện Streamlit
│   ├── pages/upload.py               # Trang upload & biên tập thử nghiệm
│   └── utils/                        # Tạo worksheet, bảng MARC phục vụ Streamlit
│
├── ai-agent/                         # PHÂN HỆ NỀN TẢNG MỞ RỘNG (AI Agent Worker)
│   ├── main.py                       # Vòng lặp nền giữ container sống (chờ gắn tác vụ phức tạp)
│   ├── Dockerfile                    # Image Docker riêng biệt trên cổng 8001
│   └── pyproject.toml
│
├── scripts/                          # BỘ SCRIPT HỖ TRỢ WINDOWS (Chạy 1-Click)
│   ├── setup.bat                     # Cài đặt tự động môi trường (Node, uv, thư viện Python, npm)
│   ├── start-dev.bat                 # Mở song song 2 cửa sổ chạy Backend và Frontend
│   ├── start-backend.bat             # Khởi chạy FastAPI server (cổng 8000)
│   ├── start-frontend.bat            # Khởi chạy Vite dev server (cổng 5173)
│   └── README.md                     # Hướng dẫn chi tiết sử dụng bộ scripts
│
└── docs/
    └── BUILD.md                      # Hướng dẫn kỹ thuật hạ tầng
```

---

## 3. CHI TIẾT CÁC THÀNH PHẦN & CHỨC NĂNG

### 3.1. Phân hệ Backend (`backend/`)
- **Vai trò:** Là trung tâm xử lý dữ liệu và cung cấp API RESTful cho toàn bộ hệ thống.
- **File kích hoạt chính:** [`backend/main.py`](file:///e:/Cataloging_Project/backend/main.py)
- **Công nghệ cốt lõi:** Python 3.12, FastAPI, Uvicorn, Pydantic, PyMuPDF, PyPDFium2, Pymarc.
- **Cơ chế khởi động:**
  - `warm_up_rag()`: Khi ứng dụng khởi động (`@app.on_event("startup")`), một thread nền tự động nạp trước SentenceTransformer (`all-MiniLM-L6-v2`) và FAISS Index vào RAM, giúp người dùng không bị nghẽn (freeze) ở lượt request đầu tiên.
  - Quản lý file tạm: File tải lên được ghi tạm vào `temp_uploads/` bằng UUID ngẫu nhiên để tránh lỗi ghi đè đồng thời và chống tấn công Path Traversal. Sau khi API phản hồi xong, file tạm được tự động xóa bằng `BackgroundTasks`.

#### Các API Endpoint chính:
| Phương thức | Đường dẫn | Tham số đầu vào | Mô tả chức năng |
|---|---|---|---|
| `POST` | `/api/v1/process-document` | `file` (Multipart/form-data), `doc_type` (str), `additional_info` (str) | Tiếp nhận file PDF/ảnh bìa, thực hiện chu trình trích xuất AI, phân loại RAG, ánh xạ MARC21 và Dublin Core. Trả về JSON tổng hợp. |
| `POST` | `/api/v1/save-record` *(Tại `mapping_module/main.py`)* | `{ "source_file": "...", "marc_record": {...} }` | Nhận dữ liệu biểu ghi do thủ thư chỉnh sửa trên giao diện, cập nhật và ghi đè file `.mrc` và `_marc.json` tương ứng. |
| `GET` | `/docs` | Không | Giao diện Swagger UI tương tác trực tiếp với API. |

---

### 3.2. Module Trích xuất AI (`extract_module/`)
- **Vai trò:** Tiếp nhận tài liệu thô (PDF nhiều trang hoặc ảnh scan), nhận diện cấu trúc văn bản và sử dụng các mô hình ngôn ngữ lớn (LLM) để trích xuất ra ~40 trường thông tin siêu dữ liệu có cấu trúc.
- **Thành phần chi tiết:**
  1. **`core/orchestrator.py` (`CentralOrchestrator`):** Điều phối toàn bộ quy trình trích xuất. Tự động rẽ nhánh theo cấu hình:
     - *Image Mode (Mặc định):* Dùng `ImageProcessor` render trang 1 của PDF ra ảnh độ phân giải cao, nén tối ưu rồi gửi thẳng cho mô hình thị giác (Vision LLM).
     - *OCR Mode:* Kích hoạt `PaddleOCRAdapter` để nhận diện chữ tiếng Việt, sau đó kết hợp văn bản với Prompt gửi cho LLM.
  2. **`modules/preprocessing/prompt_manager.py`:** Đọc và tinh chỉnh prompt từ thư mục `resources/prompts/` theo loại tài liệu:
     - `sach`: Trích xuất Nhan đề, Tác giả, Nhà xuất bản, Năm XB, Số trang, Kích thước, ISBN, Tùng thư.
     - `luan_van`: Trích xuất Học vị (ThS/TS), Người hướng dẫn, Chuyên ngành đào tạo, Cơ sở đào tạo (UMP), Năm bảo vệ.
     - `nckh`: Trích xuất Chủ nhiệm đề tài, Mã số đề tài nghiên cứu, Thời gian nghiệm thu, Tóm tắt (Abstract).
  3. **`modules/llm_adapters/llm_manager.py`:** Cơ chế High-Availability cho AI:
     - Ưu tiên gọi **Google Gemini** (`gemini-2.5-flash` / API Google GenAI).
     - Nếu Gemini hết hạn mức (Rate limit) hoặc gặp lỗi, tự động chuyển hướng sang mô hình dự phòng **Qwen** thông qua OpenRouter.
  4. **`modules/postprocessing/data_parser.py`:** Tiếp nhận chuỗi JSON do LLM trả về, làm sạch chuỗi markdown (````json ... ````), kiểm tra tính hợp lệ của từng trường theo `resources/schema/extraction_schema.json` và định dạng danh sách lỗi/cảnh báo.

---

### 3.3. Module Ánh xạ MARC21 & RAG (`mapping_module/`)
- **Vai trò:** Biến đổi JSON dữ liệu thô từ tầng trích xuất thành biểu ghi thư mục chuẩn quốc tế **MARC21** (Machine-Readable Cataloging) theo quy tắc biên mục **AACR2** và định dạng nhị phân ISO 2709 (`.mrc`).
- **Kiến trúc Pipeline & 9 Mappers chuyên trách:**
  1. `ControlFieldMapper`: Tạo trường `Leader` (độ dài bản ghi, trạng thái bản ghi), `001` (Số kiểm soát tự tăng từ `control_number_counter.json`), `003` (`VN-HCMUMP`), `005` (Thời gian giao dịch dạng `YYYYMMDDHHMMSS.0`), `008` (40 ký tự mã hóa cố định: ngày nhập, ngôn ngữ `vie`, nơi xuất bản `vm `).
  2. `IdentifierMapper`: Ánh xạ trường `020` (ISBN chuẩn hóa bỏ dấu gạch ngang), `022` (ISSN).
  3. `TitleMapper`: Xử lý trường `245` theo chuẩn AACR2: `$a` Nhan đề chính, `$b` Nhan đề phụ (ngăn cách bởi ` : `), `$c` Thông tin trách nhiệm/tác giả (ngăn cách bởi ` / `), `$p`/`$n` Tên/phần tập. Trường `246` cho nhan đề song song tiếng Anh.
  4. `AuthorCorporateMapper`: Phân tích tác giả chính `100` (`$a` Tên dạng đảo Họ Tên, `$e` vai trò: tác giả/chủ biên/người hướng dẫn), `700` cho đồng tác giả; trường `110`/`710` cho tác giả cơ quan/tập thể (Đại học Y Dược TP.HCM).
  5. `PublicationPhysicalMapper`: Trường `260`/`264` (`$a` Nơi xuất bản, `$b` Nhà xuất bản, `$c` Năm xuất bản); trường `300` mô tả vật lý (`$a` số trang `... tr.`, `$b` minh họa `hình vẽ`, `$c` kích thước `... cm`).
  6. `NoteMapper`: Trường `500` (Ghi chú chung), `502` (Phụ chú luận án: học vị, trường đào tạo, năm bảo vệ), `504` (Thư mục tài liệu tham khảo), `520` (Tóm tắt nội dung/Abstract).
  7. `RAGFieldMapper` & `RAGEnrichedFieldMapper`:
     - Tích hợp **RAG Engine** (`LCC_and_NLM/rag_engine.py`): Sử dụng mô hình nhúng `sentence-transformers/all-MiniLM-L6-v2` kết hợp cơ sở dữ liệu véc-tơ **FAISS** tra cứu chỉ mục NLM Classification (Y học lâm sàng & tiền lâm sàng: QS–QZ, W–WZ) và LCC.
     - Tự động sinh trường `060` (Mã phân loại Thư viện Y khoa Quốc gia Hoa Kỳ - NLM) và trường `050` (Mã phân loại Thư viện Quốc hội Mỹ - LCC) kèm theo **chỉ số độ tin cậy (Confidence Score)**.
     - Tự động sinh trường `650` (Chủ đề / MeSH Keywords) bằng thuật toán so khớp ngữ nghĩa.
  8. `LocalFieldMapper`: Sinh các trường nội bộ của Thư viện Đại học Y Dược:
     - `090`: Ký hiệu xếp giá nội bộ (Call Number kết hợp mã phân loại + Cutter tác giả).
     - `852`: Vị trí kho lưu giữ tài liệu (`$a VN-HCMUMP $b Kho Sách/Kho Luận Văn`).
     - `915`, `927`: Mã chuyên ngành và dạng lưu thông tài liệu.

---

### 3.4. Module Dublin Core (`dublin_core_module/`)
- **Vai trò:** Tạo biểu ghi siêu dữ liệu chuẩn **Dublin Core Metadata Element Set (ISO 15836)** phục vụ kết nối và tích hợp vào các kho học liệu mở (như DSpace).
- **15 Phần tử chuẩn được ánh xạ:**
  - Nhóm mô tả (`descriptive.py`): `title`, `subject`, `description`, `type`, `coverage`.
  - Nhóm xuất bản & tác quyền (`publication.py`): `creator`, `contributor`, `publisher`, `date`, `rights`.
  - Nhóm kỹ thuật & định danh (`technical.py`): `format`, `identifier`, `source`, `language`, `relation`.
- Kết quả được xuất dưới dạng file JSON chuẩn `[tên_file]_dc.json`.

---

### 3.5. Giao diện người dùng chính (`frontend_react/`)
- **Vai trò:** Cung cấp trải nghiệm web trực quan cho thủ thư, tối ưu hóa thao tác kiểm duyệt và chỉnh sửa dữ liệu biên mục.
- **Công nghệ:** React 18, Vite, Tailwind CSS, Lucide React, React Router 7.
- **Các trang & màn hình chính:**
  1. **Trang Tải lên (`UploadPage.jsx`):**
     - Vùng kéo thả tệp (Drag & Drop Dropzone) hỗ trợ PDF và ảnh (JPG, PNG).
     - Bộ chọn loại tài liệu: *Sách*, *Luận văn / Luận án*, *Báo cáo Nghiên cứu khoa học*.
     - Ô nhập metadata bổ sung (Bộ sưu tập, Đơn vị đào tạo, Ghi chú nghiệp vụ).
     - Hiển thị thanh tiến trình xử lý từng file và báo cáo kết quả trích xuất thời gian thực.
  2. **Trang Biên tập MARC21 (`MarcEditorPage.jsx`):**
     - Hiển thị bản ghi MARC21 dưới dạng bảng chi tiết gồm: Nhãn trường (Tag), Chỉ thị 1 & 2 (Indicators), Mã trường con (Subfield Code), Nội dung dữ liệu (Value).
     - **Cảnh báo trường độ tin cậy thấp (Low Confidence Alert):** Các trường mà AI phân loại chưa chắc chắn sẽ được gắn nhãn màu vàng/cam để thủ thư lưu ý kiểm tra đối soát.
     - Cho phép chỉnh sửa trực tiếp trên từng ô, thêm/xóa trường con.
     - Nút **Lưu bản ghi**: Gửi biểu ghi đã hoàn thiện về backend để ghi đè file `.mrc` và `_marc.json`.
     - Nút **Tải JSON**: Tải ngay file biểu ghi về máy tính của thủ thư.
  3. **Quản lý trạng thái (`store.jsx`):**
     - Sử dụng React Context (`BatchProvider`) lưu trữ danh sách các tài liệu đã xử lý trong phiên làm việc, cho phép chuyển đổi qua lại giữa các file mượt mà mà không mất dữ liệu.

---

### 3.6. Giao diện thay thế (`frontend_streamlit/`)
- Cung cấp giao diện prototype bằng Streamlit (`app.py`), cho phép chạy thử nghiệm nhanh các thuật toán hoặc kiểm thử mà không cần cài đặt môi trường Node.js.

### 3.7. Module AI Agent nền (`ai-agent/`)
- Chứa skeleton dịch vụ container chạy ngầm trên cổng `8001`. Hiện đóng vai trò placeholder cho các tác vụ tác nhân AI dài hạn (ví dụ: tự động giám sát thư mục, quét định kỳ kho số hoặc thực hiện các thuật toán suy luận phức tạp trong tương lai).

### 3.8. Bộ kịch bản Windows (`scripts/`)
- Tập hợp các file `.bat` thiết kế riêng cho người dùng Windows, giúp người mới bắt đầu có thể cài đặt toàn bộ phụ thuộc phức tạp và chạy ứng dụng chỉ bằng các cú nháy đúp chuột mà không cần gõ lệnh phức tạp.

---

## 4. CẤU HÌNH & BIẾN MÔI TRƯỜNG (`.env`)

Để hệ thống hoạt động, cần tạo file `.env` tại thư mục gốc của dự án dựa trên file `.env.example`:

```ini
# ==========================================
# CƠ SỞ DỮ LIỆU (PostgreSQL) — Cấu hình cho Docker
# ==========================================
POSTGRES_USER=admin
POSTGRES_PASSWORD=secretpassword
POSTGRES_DB=app_database

# ==========================================
# KHÓA KẾT NỐI AI / TRÍCH XUẤT (extract_module)
# ==========================================
# Bắt buộc: Lấy key miễn phí tại https://aistudio.google.com/apikey
GEMINI_API_KEY=AIzaSy...

# Tùy chọn: Dùng fallback khi Gemini gặp lỗi (OpenRouter / Qwen)
QWEN_API_KEY=

# Số lần thử lại tối đa khi gọi API LLM
MAX_RETRIES=4

# Số trang đầu tiên được chuyển thành ảnh để phân tích (mặc định trang 1)
DEFAULT_EXTRACT_PAGES=1

# true: Sử dụng PaddleOCR trước khi đưa vào LLM; false: gửi ảnh trực tiếp cho Gemini
USE_OCR=false

# Kích thước mô hình PaddleOCR: tiny / small / medium
PADDLE_MODEL_SIZE=tiny

# ==========================================
# THIẾT LẬP ĐƯỜNG DẪN RAG (Chỉ cần set khi chạy Docker)
# ==========================================
# LCC_PDF_FOLDER=/app/mapping_module/file_tailieu
# SUBJECT_650_PDF_FOLDER=/app/mapping_module/file_subject_650
```

---

## 5. HƯỚNG DẪN KHỞI CHẠY DỰ ÁN

Hệ thống hỗ trợ 3 phương thức vận hành chính tùy thuộc vào nhu cầu:

### Cách 1: Khởi chạy Local Native với `uv` & `npm` (Khuyến nghị cho Dev Windows)
*Đây là phương án nhẹ nhất, tốc độ phản hồi nhanh nhất và thuận tiện nhất khi phát triển trên Windows.*

1. **Khởi chạy Backend (Terminal 1):**
   ```cmd
   scripts\start-backend.bat
   ```
   *Hoặc bằng lệnh:*
   ```bash
   cd backend
   uv run python main.py
   ```
   👉 Backend sẵn sàng tại: **http://localhost:8000** (Tài liệu API Swagger tại **http://localhost:8000/docs**)

2. **Khởi chạy Frontend (Terminal 2):**
   ```cmd
   scripts\start-frontend.bat
   ```
   *Hoặc bằng lệnh:*
   ```bash
   cd frontend_react
   npm run dev
   ```
   👉 Frontend sẵn sàng tại: **http://localhost:5173**

3. **Chạy cả 2 cùng lúc (1-Click):**
   - Nháy đúp file `scripts\start-dev.bat` để tự động mở cả 2 cửa sổ console.

---

### Cách 2: Khởi chạy qua Docker Compose
*Dành cho môi trường đóng gói container.*

1. **Khởi động các dịch vụ cốt lõi:**
   ```bash
   docker compose up -d --build db backend
   ```
2. **Khởi chạy Frontend React ngoài host kết nối vào Docker:**
   ```bash
   cd frontend_react
   npm run dev
   ```
3. **Dừng toàn bộ container:**
   ```bash
   docker compose down
   ```

---

### Cách 3: Chạy xử lý hàng loạt CLI (Batch Processing)
*Dành cho trường hợp thủ thư muốn xử lý hàng loạt hàng trăm file PDF có sẵn mà không cần mở giao diện Web.*

1. Sao chép các file PDF cần biên mục vào thư mục:
   `backend/extract_module/data/`
2. *(Tùy chọn)* Khai báo thông tin phân loại trước trong file `backend/extract_module/data/batch_metadata.json`:
   ```json
   [
     {
       "path": "GiaoTrinhNoiKhoa.pdf",
       "doc_type": "sach",
       "additional_info": "Bộ môn Nội tổng quát"
     }
   ]
   ```
3. Chạy lệnh thực thi batch:
   ```bash
   cd backend
   uv run python main.py --batch
   ```
   *(Nếu muốn kích hoạt thêm OCR, thêm cờ `--use-ocr`)*:
   ```bash
   uv run python main.py --batch --use-ocr
   ```
4. Kết quả `.mrc`, `_marc.json` và `_dc.json` sẽ được lưu tự động theo ngày vào:
   `backend/output_final/YYYY-MM-DD/`

---

## 6. HƯỚNG DẪN TỪNG BƯỚC CHO NGƯỜI MỚI (ONBOARDING STEP-BY-STEP)

Nếu bạn là thành viên mới tiếp nhận dự án trên một máy tính Windows mới toanh, hãy thực hiện tuần tự 5 bước sau:

### Bước 1: Cài đặt công cụ nền tảng
Mở PowerShell (quyền Administrator) và cài đặt các công cụ cần thiết:
```powershell
# 1. Cài đặt Git (nếu chưa có)
winget install Git.Git

# 2. Cài đặt Node.js LTS (phiên bản 20 hoặc 22)
winget install OpenJS.NodeJS.LTS
```
> Sau khi cài xong, hãy **đóng toàn bộ cửa sổ terminal và mở lại** để biến môi trường có hiệu lực.

### Bước 2: Chạy script thiết lập tự động
Tại thư mục gốc của dự án `Cataloging_Project`, chạy file kịch bản:
```cmd
scripts\setup.bat
```
Script sẽ tự động:
- Kiểm tra `git`, `node`, `npm`.
- Tự động tải và cài đặt trình quản lý gói siêu tốc `uv` (từ Astral).
- Tự động tải môi trường Python 3.12 biệt lập (bạn không cần cài Python thủ công vào Windows).
- Tự động tạo file cấu hình `.env` từ `.env.example`.
- Đồng bộ toàn bộ thư viện backend (PyTorch, FAISS, Pymarc, FastAPI...) và cài đặt `node_modules` cho frontend.

### Bước 3: Điền Google Gemini API Key
1. Truy cập vào trang quản lý API miễn phí của Google: [Google AI Studio](https://aistudio.google.com/apikey).
2. Đăng nhập bằng tài khoản Google và bấm **Create API key**.
3. Mở file `.env` tại thư mục gốc của dự án bằng Notepad hoặc VS Code.
4. Tìm dòng `GEMINI_API_KEY=` và dán key vừa tạo:
   ```ini
   GEMINI_API_KEY=AIzaSyD-abcxyz123456789...
   ```
5. Lưu file lại.

### Bước 4: Khởi động hệ thống
Nháy đúp vào file:
```cmd
scripts\start-dev.bat
```
Hai cửa sổ CMD sẽ hiện lên đại diện cho:
- Cửa sổ 1: Máy chủ FastAPI backend chạy tại `http://localhost:8000/docs`
- Cửa sổ 2: Giao diện Vite dev server chạy tại `http://localhost:5173`

Trình duyệt web sẽ tự động mở trang web ứng dụng hoặc bạn có thể mở thủ công tại địa chỉ:  
👉 **http://localhost:5173**

### Bước 5: Thực hành biên mục tài liệu mẫu đầu tiên
1. Trên giao diện web, chọn menu **Tải lên tài liệu**.
2. Chọn loại tài liệu tương ứng: **Sách / Book** hoặc **Luận văn / Luận án**.
3. Kéo thả 1 file PDF bìa sách y học hoặc tài liệu học tập vào khung nét đứt.
4. Bấm **Bắt đầu trích xuất**.
5. Đợi khoảng 5–15 giây để mô hình AI xử lý:
   - Hệ thống tự động phân tích nhan đề, tác giả, nhà xuất bản, năm xuất bản.
   - Hệ thống tự động chạy RAG tra cứu mã NLM/LCC và gán mã xếp giá.
6. Sau khi hoàn thành, giao diện sẽ chuyển hướng sang trang **Biên tập MARC21**:
   - Kiểm tra các trường hiển thị trên bảng.
   - Nếu có ô cảnh báo độ tin cậy thấp, nháy vào để kiểm tra đối soát với trang bìa.
   - Chỉnh sửa nội dung nếu cần.
7. Bấm **Lưu bản ghi** hoặc **Xuất JSON** để nhận kết quả. File kết quả `.mrc` sẽ nằm tại thư mục `backend/output_final/`.

---

## 7. CÁC LƯU Ý KỸ THUẬT QUAN TRỌNG & XỬ LÝ SỰ CỐ (TROUBLESHOOTING)

### 7.1. Điểm lưu ý về API `/api/v1/save-record`
> [!WARNING]
> Hiện tại logic xử lý endpoint `POST /api/v1/save-record` (dùng để lưu lại biểu ghi sau khi thủ thư sửa tay trên Web) đang nằm tại [`backend/mapping_module/main.py`](file:///e:/Cataloging_Project/backend/mapping_module/main.py#L129), trong khi entrypoint chạy hàng ngày của backend lại là [`backend/main.py`](file:///e:/Cataloging_Project/backend/main.py).  
> Để tính năng "Lưu bản ghi" trên giao diện React hoạt động ổn định nhất, cần đảm bảo endpoint `/api/v1/save-record` được khai báo đầy đủ trong `backend/main.py`.

### 7.2. Lần đầu tải Model Embeddings (HuggingFace Cache)
- Hệ thống sử dụng mô hình nhúng ngữ nghĩa `all-MiniLM-L6-v2` cho RAG.
- Khi chạy lần đầu tiên trên máy mới, thư viện `sentence-transformers` sẽ tải model này về cache cá nhân (khoảng 90MB). Quá trình này cần kết nối Internet.
- Trong Dockerfile, lệnh tải model đã được cấu hình chạy sẵn lúc build image (`RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`), kèm theo biến môi trường `HF_HUB_OFFLINE=1` để tăng tốc độ khởi động container.

### 7.3. Cổng mạng bị chiếm dụng (Port Conflict)
- Nếu cổng `8000` (FastAPI) bị ứng dụng khác chiếm dụng, bạn có thể đổi port trong lệnh chạy: `uvicorn main:app --port 8080`. Khi đổi port backend, hãy cập nhật lại mục `proxy` trong file `frontend_react/vite.config.js`.
- Nếu cổng `5173` bị bận, Vite sẽ tự động nhảy sang `5174` hoặc kế tiếp; script `start-dev.ps1` có cơ chế tự đọc log của Vite để mở đúng URL trên trình duyệt.

### 7.4. Quản lý số kiểm soát Control Number (Trường 001)
- Số kiểm soát của biểu ghi MARC21 được lưu vết trong file [`control_number_counter.json`](file:///e:/Cataloging_Project/control_number_counter.json) theo cấu trúc `{"YY": sequence}` (ví dụ `{"26": 162}` ứng với năm 2026, bản ghi số 162).
- Nếu cần reset lại số kiểm soát cho đợt biên mục mới, bạn có thể chỉnh sửa giá trị số thứ tự trong file này.

---
*Tài liệu được cập nhật tự động và kiểm chuẩn theo hiện trạng mã nguồn thực tế của dự án.*
