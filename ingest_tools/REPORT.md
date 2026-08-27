# BÁO CÁO - Pipeline Ingest PDF Phụ Lục Tham Khảo

**Dự án:** Hệ thống biên mục cho Thư viện Đại học Y Dược TP.HCM
**Module:** `ingest_tools/`
**Mục đích PR:** Bổ sung pipeline ingest tài liệu PDF phụ lục tham khảo thành dữ liệu máy đọc được (CSV/JSON) để đưa vào hệ thống biên mục.

---

## 1. Tóm tắt

Xây dựng pipeline ingest, đã test thực tế với **Phụ lục 6** (danh sách tên đơn vị):

| Chức năng | Mô tả |
|-----------|-------|
| **Ingest PDF → CSV/JSON** | Đọc bảng biểu từ PDF phụ lục tham khảo |
| **Ingest DOCX → JSON** | Đọc quy ước MARC21 (Phụ lục 1) từ file Word |
| **So sánh (validate-dept)** | Đối chiếu dữ liệu PDF mới với dữ liệu hiện có, phát hiện thêm/bớt/sửa |
| **AI fallback** | Hỗ trợ PDF dạng hình ảnh/scan qua Gemini |

---

## 2. Chi tiết

### Ingest PDF → CSV/JSON (`ingest_tools/`)

**Mục tiêu:** Tự động hóa việc đọc dữ liệu từ các phụ lục tham khảo (PDF) thành dữ liệu máy đọc được cho hệ thống biên mục.

**Khả năng chính:**
- Trích xuất bảng từ PDF **text-based** (dùng `pdfplumber` + `pymupdf`)
- Trích xuất bảng từ **Word DOCX** (dùng `python-docx`) — dành cho Phụ lục 1
- **AI fallback** bằng Gemini cho PDF **dạng hình ảnh/scan** (image-based) — không dùng Google API/upload thủ công
- Parse nhiều dạng phụ lục: Phụ lục 1 (MARC21 spec — PDF/DOCX), Phụ lục 6 (tên đơn vị), rubric, bảng tổng quát
- Xuất CSV (**UTF-8 BOM** — mở đúng tiếng Việt trong Excel) hoặc JSON có metadata
- Lệnh `validate-dept` để **so sánh** dữ liệu PDF mới với dữ liệu hiện có, phát hiện thêm/bớt/sửa

**Kết quả test thực tế (Phụ lục 6: 340KB, 3 trang, 117 dòng):**
- ✅ Trích xuất thành công **110 biểu ghi** đơn vị
- ✅ Phát hiện **14 điểm khác biệt** so với `ump_departments.json` hiện có (chủ yếu là lỗi dấu/chữ hoa thường: "Hoá học" → "Hóa học", "ký sinh" → "Ký sinh")
- ✅ Output CSV/JSON đúng cấu trúc 4 cột (STT, Tên đơn vị, Cap1, Cap2)

**Kết quả test thực tế (Phụ lục 1: quy ước nhập liệu MARC21, file DOCX):**
- ✅ Trích xuất thành công các **quy tắc MARC** (001, 005, 008...) từ bảng DOCX
- ✅ Output **JSON** đầy đủ các trường: tag, field_name, repeatable, description, reference_url, notes, mandatory
- ✅ Dữ liệu là cơ sở để **AI phân tích, suy luận** chuẩn MARC21

**Cấu trúc code:**
```
ingest_tools/
├── main.py                  # CLI entry point
├── ai_extractor.py          # Gemini fallback (PDF image-based)
├── extractors/              # pdf_extractor (PDF), docx_extractor (DOCX)
├── parsers/                 # table, marc_spec, dept_lookup, rubric
├── exporters/               # csv (UTF-8 BOM), json
└── prompts/                 # Prompt Gemini cho từng loại phụ lục
```

---

## 3. Luồng xử lý

```
[PDF phụ lục / DOCX phụ lục]
        │
        ▼
 ingest_tools/  ──►  CSV / JSON sạch  ──►  đưa vào hệ thống
 (PDF: pdfplumber+pymupdf; DOCX: python-docx)
                     (Phụ lục 6 → CSV; Phụ lục 1 → JSON MARC rules)
```

---

## 4. Dependencies

Đã có sẵn trong `backend/pyproject.toml`:
- `pdfplumber` — trích xuất bảng từ PDF text-based
- `pymupdf` — xử lý PDF, hỗ trợ image
- `python-docx` — đọc file Word DOCX (Phụ lục 1)
- `google-genai` / `google-generativeai` — AI fallback
- Cần `GEMINI_API_KEY` trong `.env` (chỉ khi dùng AI cho PDF scan)

---

## 5. Hướng dẫn sử dụng (tóm tắt)

```bash
# 1. Ingest Phụ lục 6 (PDF) → CSV
python ingest_tools/main.py ingest <phu_luc_6.pdf> -t departments -o output.csv

# 2. Ingest Phụ lục 1 (PDF hoặc DOCX) → JSON MARC rules
python ingest_tools/main.py ingest <phu_luc_1.docx> -t marc -o marc_rules.json

# 3. So sánh với dữ liệu hiện có
python ingest_tools/main.py validate-dept <phu_luc_6.pdf> -e backend/mapping_module/resources/ump_departments.json
```

Xem README kỹ thuật đầy đủ: [README.md](README.md)

---

## 6. Kiến nghị / Việc cần làm tiếp theo

1. **Bổ sung đủ nội dung Phụ lục 1 (MARC spec)** — hiện file docx mới có 3 trường (001, 005, 008); cần đầy đủ các trường bắt buộc còn lại để AI suy luận đầy đủ chuẩn MARC21
2. **Quyết định policy** cho **14 điểm khác biệt** Phụ lục 6 so với hiện có (giữ `Hoá` hay đổi `Hóa`?)
3. **Test AI path** — nếu có PDF scan thật, thử fallback Gemini (cần `GEMINI_API_KEY`)

---

## 7. Ghi chú

- File CSV xuất chuẩn **UTF-8 with BOM** để Excel mở đúng tiếng Việt
- Đã sửa 1 bug nhỏ: JSON exporter signature trong `main.py`
- Toàn bộ code hoạt động theo mô hình test-thực-tế trên dữ liệu PDF Phụ lục 6
