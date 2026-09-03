# REPORT: Phụ lục 6 – DepartmentCorrector (Fuzzy Matching)

**Module:** `backend/mapping_module/`
**Mục đích:** Ràng quy tắc **Phụ lục 6** (danh mục Khoa/Phòng/Bộ môn ĐHYD) vào quá trình biên mục sau OCR bằng **Fuzzy Matching**, chuẩn hóa `corporate_name` về đúng tên đơn vị trước khi ánh xạ sang MARC21.

---

## 1. Bối cảnh / Vấn đề

Trước đây, việc khớp tên đơn vị ở `mappers/author_fields.py::_match_departments()` dùng so sánh **string `in` cứng**:

```python
if cap2 and cap2.lower() in corp_lower:
    return cap1, cap2
```

Cách này fail hoàn toàn khi OCR trích xuất tên đơn vị bị:
- **Thiếu dấu tiếng Việt**: `"Truong Dieu duong"` vs `"Trường Điều dưỡng - Kỹ thuật y học"`
- **Sai hoa/thường**: `"KHOA Y TE CONG CONG"`
- **Từ bị đảo / lệch chuỗi** do OCR

Kết quả là field `110`/`710` có `corporate_name` sai hoặc không tách được `$a`/`$b`. Phụ lục 1 và 6 chưa được ràng vào quá trình OCR/biên mục.

---

## 2. Giải pháp

Xây dựng lớp **corrector** chèn giữa OCR → raw JSON và mapper, dùng `rapidfuzz` để fuzzy-match tên đơn vị theo Phụ lục 6:

```
OCR → Gemini → DataParser → raw JSON → [DepartmentCorrector] → corrected JSON → MarcPipeline
                                                                    ↑
                                                              Fuzzy Match vs
                                                              Phụ lục 6 store
```

Kiến trúc **3 lớp**:

### 2.1 `utils/fuzzy_matcher.py` (FuzzyMatcher)
- Normalize tiếng Việt: **bỏ dấu** (NFKD) + **lowercase** → máy so sánh "đi dấu" không còn lệch.
- Dùng `fuzz.token_set_ratio` (bỏ qua thứ tự từ) — tốt cho OCR errors.
- **Tie-break**: khi 2 ứng viên cùng điểm chênh lệch ≤ 5, ưu tiên tên **ngắn hơn** (đặc trưng hơn cho đơn vị nhỏ).

### 2.2 `core/department_corrector.py` (DepartmentCorrector)
Load `ump_departments.json` (Phụ lục 6) một lần, build 2 matcher (cap1 & cap2) + map `cap2 → (cap1, cap2)`. Method chính: `correct_corporate_name(raw_name) -> dict`.

### 2.3 Tích hợp
- `mappers/author_fields.py`: thay `_match_departments()` bằng `DepartmentCorrector`, lưu `_last_correction` để log cảnh báo.
- `main.py`: sau khi extract (API `/process-document` và batch), gọi corrector cập nhật `corporate_name` + gắn `_corporate_validation` vào response cho thủ thư.

---

## 3. Chiến lược match

| Loại đầu vào | Ví dụ | Chiến lược | `needs_review` |
|---|---|---|---|
| **Cap2 - pure** | `"Bộ môn Dịch tễ học"`, `"Bo mon Hoa sinh"` | match cap2 (token_set) | score < 90 |
| **Tổ hợp** (cap1 + cap2, có dấu `-`/`|`) | `"Trường Điều dưỡng ... - Bộ môn Điều dưỡng"` | partial-match cap2 trong query | score < 90 |
| **Cap1 - only** | `"Khoa Y te cong cong"`, `"Trường Y"` | match cap1; nếu 1 cap2 → tự chọn, nhiều cap2 → cần review | nhiều cap2 → true |
| **No match** | `"Khoa ABC XYZ"` | giữ nguyên gốc | true |

**Threshold mặc định:** `85` cho `find_best`, `90` cho auto-correct không cần review. Dưới ngưỡng → giữ nguyên + flag.

---

## 4. Files thay đổi

| File | Hành động | Chức năng |
|---|---|---|
| `utils/fuzzy_matcher.py` | **Tạo mới** | Normalize tiếng Việt + fuzzy match có tie-break |
| `core/department_corrector.py` | **Tạo mới** | Logic sửa `corporate_name` theo Phụ lục 6 |
| `tests/test_department_corrector.py` | **Tạo mới** | 19 test cases |
| `mappers/author_fields.py` | **Sửa** | Dùng `DepartmentCorrector` thay so sánh cứng |
| `main.py` | **Sửa** | Thêm correction step (API + batch) |
| `resources/ump_departments.json` | **Sync** | 110 records, clean newline |
| `mapping_module/requirements.txt`, `backend/pyproject.toml` | **Sửa** | Thêm `rapidfuzz>=3.0.0` |

---

## 5. Kết quả test

**19/19 tests pass** (chạy: `python -m pytest backend/mapping_module/tests/test_department_corrector.py`).

Các trường hợp điển hình:

| Input (OCR) | Output chuẩn (Phụ lục 6) |
|---|---|
| `"Bo mon Dich te hoc"` | `"Khoa Y tế công cộng\|Bộ môn Dịch tễ học"` |
| `"BỘ MÔN DỊCH TỆ HỌC"` (sai hoa) | vẫn match đúng cap2 |
| `"Truong Dieu duong ... - Bo mon Dieu duong"` (tổ hợp, thiếu dấu) | `"Trường Điều dưỡng - Kỹ thuật y học\|Bộ môn Điều dưỡng"` |
| `"Khoa Y te cong cong - Bo mon Dich te hoc"` (tổ hợp) | `"Khoa Y tế công cộng\|Bộ môn Dịch tễ học"` |
| `"Khoa ABC XYZ"` (không tồn tại) | giữ nguyên + `needs_review: true` |

Smoke test mapper tạo field 110 đúng chuẩn:
```
Tag 110: Trường Điều dưỡng - Kỹ thuật y học. Bộ môn Điều dưỡng.
Tag 110: Khoa Y tế công cộng. Bộ môn Dịch tễ học.
```

---

## 6. Hành vi khi không match

Khi fuzzy không khớp (hoặc quá mơ hồ), hệ thống **giữ nguyên `corporate_name` gốc** — không force match sai — và gắn metadata:

```json
{
  "corporate_name": "Khoa ABC XYZ",
  "_corporate_validation": {
    "corrected_name": "Khoa ABC XYZ",
    "cap1": "Khoa ABC XYZ",
    "cap2": null,
    "confidence": 0,
    "match_method": "no_match",
    "needs_review": true
  }
}
```

`needs_review=true` → thủ thư kiểm tra/sửa trên giao diện.

---

## 7. Lưu ý / hạn chế đã biết

- **Correction chạy 2 lần** cho mỗi document: một trong `main.py` (để gắn `_corporate_validation` vào response) và một trong `AuthorCorporateMapper`. Không gây lỗi nhưng hơi redundant — có thể tối ưu sau bằng cách truyền corrector dùng chung.
- **`ump_departments.json`** đã được sync từ `ingest_tools/output_phu_luc_6.json` (110 records) và làm sạch ký tự xuống dòng trong tên.
- Phụ lục 6 tập trung chuẩn hóa **tên đơn vị**; **Phụ lục 1** (quy tắc MARC21 field) chưa được tích hợp — là bước tiếp theo khi có bản Phụ lục 1 đầy đủ.
