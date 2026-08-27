# Ingest Tools - PDF to CSV/JSON Pipeline

Công cụ CLI để trích xuất dữ liệu từ file PDF (bảng biểu, phụ lục) và xuất ra CSV/JSON cho hệ thống biên mục thư viện.

## Cấu trúc thư mục

```
ingest_tools/
├── main.py                  # CLI entry point
├── ai_extractor.py          # Gemini AI fallback (cho PDF image-based)
├── extractors/
│   ├── base_extractor.py    # Interface chung
│   ├── pdf_extractor.py     # Extract từ PDF (pdfplumber + pymupdf)
│   └── docx_extractor.py    # Extract từ Word DOCX (python-docx)
├── parsers/
│   ├── base_parser.py       # Interface chung
│   ├── table_parser.py      # Parse bảng tổng quát
│   ├── marc_spec_parser.py  # Parse Phụ lục 1 (quy tắc MARC21 / DOCX, PDF)
│   ├── dept_lookup_parser.py# Parse Phụ 6 (tên đơn vị)
│   └── rubric_parser.py     # Parse bộ tiêu chí đánh giá
├── exporters/
│   ├── csv_exporter.py      # Xuất CSV (UTF-8 BOM)
│   └── json_exporter.py     # Xuất JSON
└── prompts/                 # Prompt cho Gemini AI
    ├── phu_luc_6_extract.txt
    └── marc_spec_extract.txt
```

## Cài đặt

```bash
# Dependencies (đã có trong backend/pyproject.toml)
pip install pdfplumber pymupdf python-docx google-genai
```

## Sử dụng

### Ingest PDF -> CSV

```bash
# Ingest Phụ lục 6 (tên đơn vị) -> CSV
python ingest_tools/main.py ingest <file.pdf> -t departments -o output.csv

# Ingest Phụ lục 1 (quy tắc MARC21) từ PDF hoặc DOCX -> JSON
python ingest_tools/main.py ingest <phu_luc_1.pdf> -t marc -o output.json
python ingest_tools/main.py ingest <phu_luc_1.docx> -t marc -o output.json

# Ingest PDF bảng biểu tổng quát
python ingest_tools/main.py ingest <file.pdf> -t generic -o output.csv

# Ingest với AI fallback (cho PDF scan/image)
python ingest_tools/main.py ingest <file.pdf> -t departments -o output.csv

# Chỉ extract 1-2 trang cụ thể
python ingest_tools/main.py ingest <file.pdf> -t departments --pages 1 2

# Xuất JSON thay vì CSV
python ingest_tools/main.py ingest <file.pdf> -t marc -o output.json
```

### So sánh với dữ liệu hiện có

```bash
# So sánh PDF mới với departments.json hiện tại
python ingest_tools/main.py validate-dept <file.pdf> -e backend/mapping_module/resources/ump_departments.json

# Xuất diff report
python ingest_tools/main.py validate-dept <file.pdf> -e existing.json -o diff.json
```

### Loại tài liệu (`-t`)

| Giá trị | Mô tả |
|---------|-------|
| `departments` / `phu_luc_6` | Phụ lục 6 - tên đơn vị ĐHYD |
| `marc_spec` / `marc` | Phụ lục 1 - quy tắc MARC21 (hỗ trợ PDF + DOCX) |
| `rubric` | Bộ tiêu chí đánh giá (từ spreadsheet) |
| `generic` | Bảng biểu tổng quát |

## Ví dụ thực tế

### Output CSV từ Phụ lục 6

```csv
STT,tenDonViCap1,tenDonViCap2
1,Trường Y,Bộ môn Chẩn đoán hình ảnh
2,Trường Y,Bộ môn Chấn thương chỉnh hình - PHCN
3,Trường Y,Bộ môn Da liễu
...
117,Trung tâm Phẫu thuật thực nghiệm,
```

### Diff report khi so sánh

```json
{
  "added": [],
  "removed": [],
  "modified": [
    {
      "stt": 49,
      "old": {"tenDonViCap2": "Bộ môn Hoá hữu cơ"},
      "new": {"tenDonViCap2": "Bộ môn Hóa hữu cơ"}
    }
  ]
}
```

## Pipeline tổng thể

```
PDF Upload --> pdf_extractor (text) --> table_parser --> csv_exporter --> .csv
    |                     |                       |
    v                     v                       v
  ai_extractor (Gemini)  dept_lookup_parser   marc_spec_parser
                            |                       |
                            v                       v
                    validate-dept (so sánh)   JSON (MARC rules)
DOCX Upload --> docx_extractor (python-docx) --> marc_spec_parser --> .json
```

## Lưu ý

- File CSV xuất ra dùng encoding **UTF-8 with BOM** để Excel mở đúng tiếng Việt
- AI extractor cần `GEMINI_API_KEY` trong file `.env`
- Nếu PDF là text-based (như Phụ lục 6), không cần AI
- Nếu PDF là image scan, tool sẽ tự fallback sang Gemini
- Hỗ trợ file **DOCX** (Word) cho Phụ lục 1 — dùng `python-docx`
- Output MARC spec (Phụ lục 1) ở dạng **JSON** gồm: tag, ind1, ind2, subfields, field_name, repeatable, description, reference_url, notes, mandatory
