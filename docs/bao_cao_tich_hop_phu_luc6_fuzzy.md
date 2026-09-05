# Báo cáo: Tích hợp dữ liệu Phụ lục 6 vào pipeline biên mục — Sửa tên đơn vị bằng Fuzzy Matching

**Ngày:** 06/09/2026
**Phạm vi:** Pipeline ingest Phụ lục 6 → chuẩn hóa tên đơn vị (`corporate_name`) → Xuất MARC21
**Người thực hiện:** [Em]

---

## 1. Tóm tắt điều hành

- **Mục đích:** Đưa danh mục 110 đơn vị trong Phụ lục 6 (Hệ thống trường/khoa/bộ môn/trung tâm của Đại học Y Dược TP.HCM) vào pipeline biên mục dưới dạng bộ tra cứu, tự sửa tên đơn vị cho đúng chuẩn trước khi ghi vào biểu ghi MARC21.
- **Độ chính xác (hiệu suất) theo quy tắc nghiệp vụ:** Phụ lục 6 được xem là **từ điển chính tả tên đơn vị**: ca nào thuộc Phụ lục 6 mà **không sửa cũng tính là sai**, và **mọi ca đều phải ghi rõ lý do** (trường `reason` đã bổ sung ở tất cả nhánh). Kết quả 10 tài liệu thực tế: **7/10 đạt** (1 ca sửa đúng chuẩn + 6 ca tên cấp đại học giữ nguyên vì ngoài phạm vi danh mục, có lý do), **2 ca sai** (dương tính giả — gán cơ quan bên ngoài thành đơn vị UMP), **1 ca phân vân** ("Khoa Y" ↔ "Trường Y", chờ chốt chính sách). Cả 10 ca đều cờ `needs_review`.
- **Tốc độ (hiệu năng):** Chi phí của khâu sửa tên gần như bằng 0 so với pipeline: tải bộ tra cứu **4,3 ms**, mỗi lần gọi **0,76 ms trung bình (tối đa 2,3 ms)** trong khi một tài liệu mất ~**41 giây** (Gemini + OCR). Tỷ phần hao phí ~**0,002%**.
- **Rủi ro chính đã phát hiện (qua test nội bộ):** Khi đưa đúng tên chuẩn (chính Phụ lục 6) vào, **14/91 tên cấp 2 bị match nhầm sang tên khác**, trong đó **14/14 có điểm tự tin ≥ 90 → không bị cờ rà soát** (lỗi "im lặng"). Cần sửa bằng khuyến nghị ở mục 6.
- **Khuyến nghị ngắn:** Chỉ tự ghi đè tên khi khớp **chính xác hoặc duy nhất** ở mức điểm ≥ 90; thêm danh sách loại trừ cơ quan bên ngoài (Sở/Viện/Bộ/Cục); xây **self-match test** thành regression để ngăn tái diễn 14 ca nói trên. Đã bổ sung ngay trong đợt này trường **`reason`** (lý do tiếng Việt cho từng ca, với `no_match` kèm đơn vị gần nhất + điểm) tại cả `extract_module` lẫn `mapping_module`.

---

## 2. Pipeline xử lý thực tế

> **Sơ đồ tương tác:** `docs/diagrams/pipeline_phu_luc6.html` (mở bằng trình duyệt; đổi sáng/tối, pan/zoom, lọc).

Hệ thống gồm **hai luồng**:

### 2.1. Luồng 1 — Ingest Phụ lục 6 (thủ công một lần, tái chạy khi phụ lục đổi)

```
[PDF Phụ lục 6 – 340 KB, 3 trang, 117 dòng]
        │  pdfplumber (đọc bảng có khung) → pymupdf (fallback text)
        ▼
[Trích xuất 110 dòng: STT | Tên Cấp 1 | Tên Cấp 2]
        │
        ├─► validate-dept: so với bộ dữ liệu cũ → phát hiện 14 khác biệt
        │        (chủ yếu lỗi dấu/chữ hoa: "Hoá học"→"Hoá học", "ký sinh"→"Ký sinh" — đã rà soát thủ công)
        ▼
[ump_departments.json — 110 đơn vị, 26 tên Cấp 1, 91 tên Cấp 2]
```

- Nguồn PDF phụ lục 6 là **file text-based** nên không cần OCR ở bước này.
- Đầu ra duy nhất được tích hợp là `ump_departments.json` (bộ tra cứu, không phải code).

### 2.2. Luồng 2 — Tích hợp vào pipeline biên mục (tự động, theo tài liệu)

```
[Tài liệu PDF (báo cáo NCKH...)]
        │  Render trang → gửi Gemini (2.5-flash) / hoặc PaddleOCR nếu là ảnh
        ▼
[Trích xuất các trường — có corporate_name = tên đơn vị/cơ quan]
        │
        ▼  ◄── DepartmentCorrector đọc ump_departments.json (tải 1 lần)
[Fuzzy matching Phụ lục 6]
        │  ghi thêm: original_corporate_name, corporate_name (chuẩn),
        │           _corporate_validation = {cap1, cap2, confidence, match_method, needs_review, reason}
        ▼
[Marc21Mapper]
        │  110 $a = Cấp 1, 110 $b = Cấp 2 (khi có cap2);
        │  qua mapping module: 710 $a khi có tác giả cá nhân 100
        ▼
[Đầu ra: JSON trích xuất + MARC-in-JSON + .mrc]
```

Điểm chốt: việc "sửa tên" **xảy ra trước khi map MARC**, nên cả file JSON lẫn MARC đều dùng đúng tên đã chuẩn hóa, và luôn còn dấu vết `original_corporate_name` để đối chiếu.

### 2.3. Quy tắc nghiệp vụ (đã áp dụng cho đánh giá và báo cáo)

1. **Phụ lục 6 là "từ điển chính tả" tên đơn vị** của UMP: mục đích của khâu sửa tên là đưa tên đơn vị về **đúng chính tả / đúng tên chuẩn** theo danh mục.
2. **Ca thuộc Phụ lục 6 mà không sửa ⇒ tính là sai** (missed fix), không tính là "an toàn".
3. **Mọi ca đều phải ghi rõ lý do** qua trường `reason` (tiếng Việt), đặc biệt nhánh `no_match` — kèm đơn vị gần nhất và điểm để người duyệt tự quyết.
4. Tên thuộc **cấp đại học** ("Đại học Y Dược TP.HCM"…) không nằm trong danh mục đơn vị → giữ nguyên là **đạt** với điều kiện có `reason` giải thích đầy đủ.

---

## 3. Lưu đồ thuật toán (DepartmentCorrector)

> **Sơ đồ tương tác:** `docs/diagrams/thuat_toan_fuzzy.html` (mở bằng trình duyệt; đổi sáng/tối, pan/zoom, lọc).

Thuật toán thực thi (fuzzy matching nhiều tầng, ưu tiên khớp tên Cấp 2 trước vì đặc trưng hơn):

### Sơ đồ Mermaid

```mermaid
flowchart TD
    A[corporate_name từ Gemini / OCR] --> B[Normalize: bỏ dấu NFKD + viết thường]
    B --> C{Không rỗng?}
    C -- Không --> Z1[empty<br/>giữ nguyên, needs_review=true]
    C -- Có --> D{Nhận dạng cấu trúc tên}
    D -- Bắt đầu bằng Bộ môn/Trung tâm<br/>HOẶC không có dấu tách --> E[fuzzy_cap2: token_set_ratio]
    D -- Có dấu tách (- , |) --> F{Có prefix Cấp 1?}
    F -- Có --> G[partial_ratio: tìm cap2 nằm trong chuỗi]
    E --> H{Điểm ≥ 85?}
    G --> I{Điểm ≥ 75? (tie-break tên ngắn, 75–88)}
    H -- Có --> J[cap2 khớp → corrected = Cap1|Cap2, conf<90 thì cờ review]
    H -- Không --> K
    I -- Có --> J
    I -- Không --> K[fuzzy_cap1: token_set_ratio]
    K --> L{Điểm ≥ 85?}
    L -- Có --> M{Query chứa tên cap2?}
    M -- Có --> N[cap1_with_cap2 → Cap1|Cap2, conf<90 cờ review]
    M -- Không --> O{Số cap2 dưới Cap1 đó}
    O -- 1 --> P[cap1_single → Cap1|Cap2, conf<90 cờ review]
    O -- >1 hoặc 0 --> Q[cap1_multi / cap1_only → giữ Cap1, LUÔN cờ review]
    L -- Không --> Z2[no_match → giữ nguyên tên, cờ review]
```

**Lưu ý:** Mọi nhánh trả về đều kèm trường **`reason`** (lý do tiếng Việt). Riêng nhánh `no_match`, lý do tự tính **đơn vị gần nhất Cấp 1 / Cấp 2 và điểm** (dù dưới ngưỡng) để người duyệt có căn cứ quyết định, ví dụ: "Không có đơn vị nào trong Phụ lục 6 đạt ngưỡng 85 — cap1 gần nhất 'Khoa Y tế công cộng' = 60.0, cap2 gần nhất 'Bộ môn Chấn thương chỉnh hình - PHCN' = 50.6".

### Sơ đồ ASCII (tương đương)

```
corporate_name
   │ normalize (bỏ dấu, viết thường)
   ▼
rỗng? ──yes──► empty (giữ nguyên, review=true)
   │ no
   ▼
cap2-prefix hoặc không có dấu tách? ──yes──► fuzzy_cap2 (token_set_ratio)
   │ no (có dấu tách "-|,–")                          │ điểm ≥ 85 ──yes──► Cap1|Cap2 (conf<90 review)
   ▼                                                │ < 85 ──▼
có prefix Cấp 1? ──yes──► partial_ratio tìm cap2    fuzzy_cap1 (token_set_ratio)
   │                   │ điểm ≥ 75 ──► Cap1|Cap2            │ ≥ 85 ──► thêm cap2 nếu có
   ▼                   └  < 75 ──► fuzzy_cap1                │            ├─ 1 cap2:  cap1_single
fuzzy_cap1 (token set)                                          │            └─ nhiều cap2: cap1_multi (review luôn)
   │ < 85 ──► no_match (giữ nguyên, review luôn)                     └  cap1_only (review luôn)
```

**Các hằng số ngưỡng** (đang vận hành):

| Nhánh | Hàm chấm điểm | Ngưỡng nhận | Tie-break | Cờ rà soát |
|---|---|---|---|---|
| `fuzzy_cap2` (tên đầy đủ cấp 2) | `token_set_ratio` | ≥ 85 | chênh ≤5 điểm → chọn tên ngắn hơn | điểm < 90 |
| `partial cap2` (cap2 nằm trong chuỗi ghép) | `partial_ratio` | ≥ 75 | vùng 75–88: chênh ≤5 → chọn tên ngắn hơn | điểm < 90 |
| `fuzzy_cap1` / `with_cap2` / `single` | `token_set_ratio` | ≥ 85 | chênh ≤5 điểm → chọn tên ngắn hơn | điểm < 90 |
| `fuzzy_cap1_multi` / `cap1_only` | `token_set_ratio` | ≥ 85 | — | **luôn** rà soát |
| `no_match` | — | dưới ngưỡng | — | **luôn** rà soát |

---

## 4. Hiệu suất (độ chính xác)

### 4.1. Kết quả trên 10 tài liệu thực tế (báo cáo NCKH)

| # | Tài liệu | Tên trích xuất (gốc) | Kết quả sau sửa | Lý do (`reason`) | Điểm | Đánh giá theo quy tắc chính tả |
|---|---|---|---|---|---|---|
| 1 | Ngo Van Cong | `BỘ Y TẾ \| ĐHYD TP.HCM \| ... \| Trường Y, ĐHYD Tp HCM` | **Trường Y** | Khớp Cấp 1 'Trường Y' (100); có 26 Cấp 2 con, không tự chọn | 100 | ✅ **Đạt** — sửa đúng chuẩn |
| 2 | Tran Cong Thang | `Khoa Y – Đại học Y Dược TP.HCM` | giữ nguyên | Không đạt ngưỡng — cap1 gần nhất 'Khoa Y tế công cộng' = 60.0, cap2 'Bộ môn Chấn thương chỉnh hình - PHCN' = 50.6 | 0 | ⚠️ **Phân vân** — "Khoa Y" đáng lẽ = "Trường Y" (chờ chốt chính sách/alias) |
| 3 | Tran Thi Trung Chien | `ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH` | giữ nguyên | Không đạt ngưỡng — cap1 gần nhất = 43.8, cap2 gần nhất = 50.8 | 0 | ✅ **Đạt** — tên cấp đại học, ngoài phạm vi danh mục (có lý do) |
| 4 | Nguyen Thi Hong Chuyen | `Đại học Y Dược TP.HCM` | giữ nguyên | như trên | 0 | ✅ **Đạt** |
| 5 | Nguyen Thi Hai Lien | `ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH` | giữ nguyên | như trên | 0 | ✅ **Đạt** |
| 6 | Nguyen Thi Ngoc Phuong | `Bộ Khoa học và Công nghệ, ĐHYD TP.HCM` | ⚠️ **Khoa Y tế công cộng** | Chỉ khớp Cấp 1 'Khoa Y tế công cộng' (88); nhiều Cấp 2 con, không tự chọn | 88 | ❌ **Sai** — dương tính giả (cơ quan ngoài UMP) |
| 7 | Le Bao Luu | `ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH` | giữ nguyên | như trên | 0 | ✅ **Đạt** |
| 8 | Le Thi Tuyet Lan | `SỞ KHOA HỌC VÀ CÔNG NGHỆ` | ⚠️ **Trung tâm Khoa học và Công nghệ UMP** | Chỉ khớp Cấp 1 'Trung tâm Khoa học và Công nghệ UMP' (93,3); chưa xác định Cấp 2 | 93,3 | ❌ **Sai** — dương tính giả (cơ quan ngoài UMP) |
| 9 | Hoang Trong Kim | `ĐẠI HỌC Y DƯỢC TP. HỒ CHÍ MINH` | giữ nguyên | như trên | 0 | ✅ **Đạt** |
| 10 | Nguyen Tien Vien | `ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH` | giữ nguyên | như trên | 0 | ✅ **Đạt** |

**Kết luận hiệu suất theo quy tắc nghiệp vụ (mục 2.3):** **7/10 đạt, 1 ca phân vân, 2 ca sai**. Khác với cách chấm trước (đếm "không gán sai" thành 8/10, gộp cả ca Trần Công Thắng): nay **ca thuộc Phụ lục 6 mà không sửa cũng tính sai/đáng bàn**, và mọi ca kể cả `no_match` đều có `reason` rõ ràng. 2 ca sai cùng bản chất: chuỗi chứa cụm "Khoa học và Công nghệ" của **cơ quan bên ngoài** (Sở / Bộ KH&CN) bị fuzzy `cap1` hút vào đơn vị cùng tên trong UMP — cả 2 đã **ghi nhầm vào MARC 110 $a** (kiểm chứng trực tiếp trên `MARC21_Mau bao cao NCKH_Le Thi Tuyet Lan.json` và `..._Nguyen Thi Ngoc Phuong.json`), nhưng vẫn có cờ `needs_review=true` để khoa kiểm soát khi biên mục.

### 4.2. Test nội bộ — "tự khớp chính mình" (self-match) trên toàn bộ Phụ lục 6

Đưa **chính tên chuẩn trong Phụ lục 6** vào thuật toán (giả lập trường hợp lý tưởng: tài liệu ghi đúng tên đơn vị, chỉ sai hoa/thường/thiếu dấu):

- 91 tên Cấp 2 được test → **77/91 (85%) tự khớp đúng**.
- **14/91 (15%) bị match nhầm sang tên khác**, và **14/14 đều có điểm tự tin ≥ 90** → vượt qua cả cờ rà soát (lỗi "im lặng", không ai biết).

Bảng 14 ca match nhầm:

| Tên gốc (chuẩn, cần giữ nguyên) | Bị sửa thành | Điểm tin |
|---|---|---|
| Bộ môn Ngoại Nhi | Bộ môn Nhi | 100 |
| Bộ môn Ngoại Thần kinh | Bộ môn Thần kinh | 100 |
| Bộ môn Ngoại tổng quát | Bộ môn Nội tổng quát | 95,2 |
| Bộ môn Sinh lý - Sinh lý bệnh miễn dịch - Dược lý | Bộ môn Dược lý | 100 |
| Bộ môn Dược liệu - Dược học cổ truyền | Bộ môn Dược học cổ truyền | 100 |
| Bộ môn Tổ chức quản lý dược | Bộ môn Dược lý | 100 |
| Bộ môn Chẩn đoán hình ảnh Răng Hàm Mặt | Bộ môn Mắt | 100 |
| Bộ môn Phẫu thuật hàm mặt | Bộ môn Mắt | 100 |
| Bộ môn Chỉnh hình răng mặt | Bộ môn Mắt | 100 |
| Bộ môn Kỹ thuật phục hình răng | Bộ môn Phục hình răng | 100 |
| Bộ môn Bào chế đông dược | Bộ môn Bào chế | 100 |
| Bộ môn Nhi khoa Đông y | Bộ môn Nhi | 100 |
| Bộ môn Thống kê y học - Tin học | Bộ môn Tin học | 100 |
| Bộ môn Sinh học | Bộ môn Hộ sinh | 96,6 |

**Nguyên nhân gốc (root cause):** `token_set_ratio` so sánh theo *tập từ sắp xếp*, nên khi tên A là **tập con** các từ của tên B (vd "Bộ môn Nhi" ⊂ "Bộ môn Ngoại Nhi") nó cho chính xác **100 điểm dù hai đơn vị khác nhau**; cộng với luật tie-break "ưu tiên tên ngắn hơn khi cùng điểm" → chọn nhầm bên ngắn. Hệ quả kép: (1) điểm tin bị "thổi phồng" thành 100, (2) cửa rà soát `điểm < 90` không bắt được.

Mẫu 10 tài liệu thật không gặp kịch bản này (đề tài đều thuộc cấp trường/thành phố), nên con số kết quả (7–8 đạt/10) **chưa phản ánh rủi ro nội tại nói trên**.

---

## 5. Hiệu năng (tốc độ & tài nguyên)

Đo trên máy phát triển, Python 3.12, thư viện `rapidfuzz` (C-extension), 3000 lượt gọi lặp:

| Chỉ số | Giá trị | Ghi chú |
|---|---|---|
| Kích thước bộ tra cứu | 110 đơn vị (26 Cấp 1, 91 Cấp 2) | chỉ vài KB dữ liệu |
| Thời gian tải & dựng index | **4,3 ms** | làm mỗi lần khởi động pipeline |
| Độ trễ 1 lần gọi sửa tên (trung bình) | **0,76 ms** | benchmark trên 201 mẫu tên × 3000 lần |
| Độ trễ ca xấu nhất | **2,3 ms** | chuỗi dài nhất (đầu trang gộp nhiều dòng) |
| End-to-end 1 tài liệu | **29–48 s (trung bình 41,2 s)** | 10 file chạy liên tục hết 412 s |
| Phần chi phí của khâu sửa tên | **≈ 0,002%** | 0,76 ms / 41 200 ms |
| Tài nguyên phụ | ~không đáng kể | index nằm trong RAM, không I/O đĩa khi chạy |

- Phần lớn 41 giây là **Gemini (gửi ảnh, chờ phản hồi) + OCR + ghi MARC**; khâu fuzzy gần như miễn phí.
- Khả năng mở rộng: thuật toán quét tuyến tính toàn bộ danh sách mỗi lần gọi (`O(n)` với n = 110). Ước lượng với 1 000–2 000 đơn vị vẫn giữ dưới vài ms/call; không phải điểm nghẽn so với pipeline AI.

---

## 6. Điểm mạnh – Điểm yếu – Rủi ro – Khuyến nghị

### Điểm mạnh (thực tế đã triển khai)
1. **Không phụ thuộc OCR ở khâu ingest phụ lục 6** — PDF text-based đọc trực tiếp, dữ liệu 110 đơn vị rõ ràng, có validate đối chiếu.
2. **Chuẩn hóa tiếng Việt** (bỏ dấu, viết thường) giúp chịu được lỗi thiếu dấu/hoa-thường của OCR và Gemini.
3. **Ưu tiên khớp Cấp 2 trước** — tên bộ môn đặc trưng hơn, giảm trùng nối.
4. **Đẩy yêu cầu rà soát xuống tầng duyệt** qua cờ `needs_review` (nhánh không chắc chắn luôn được cờ); giữ `original_corporate_name` để đối chiếu.
5. **Mọi ca đều có `reason` (lý do tiếng Việt)** — kể cả `no_match` kèm đơn vị gần nhất + điểm; đáp ứng quy tắc "ghi rõ lý do" của nghiệp vụ để người duyệt quyết, không phải đoán.
6. **Hiệu năng cao**, gần như không tăng thời gian pipeline; không cần model nặng, không phụ thuộc mạng cho khâu sửa tên.

### Điểm yếu (đã đo)
1. **Dương tính giả với cơ quan bên ngoài** — cụm "Khoa học và Công nghệ" trong `Sở KH&CN` / `Bộ KH&CN` bị hút vào đơn vị UMP cùng tên (2/10 tài liệu thật).
2. **Điểm tin bị thổi phồng với tên là tập con** — `token_set_ratio` cho 100 cho ca khác đơn vị; tie-break "tên ngắn" làm sai chính tên chuẩn (14/91 trong self-match).
3. **Cửa rà soát không bắt được lỗi tự tin cao** — ngưỡng `điểm < 90` vô tác dụng với lỗi ở mục 2.
4. **Không có hiểu biết ngữ nghĩa** — chỉ so khớp ký tự, không biết "Sở" là ngoài UMP, không biết "Khoa Y" ≠ "Trường Y" (ca Trần Công Thắng đứng ở **phân vân** vì điểm này).
5. **Mẫu thật nhỏ** (10 tài liệu) — chưa bao phủ kịch bản tên cap2 bị biến dạng nhẹ.

### Rủi ro vận hành
- Tên đơn vị ghi sai **im lặng vào MARC 110/710** nếu gặp ca thuộc mục yếu 2 (xác suất thấp trên thực tế nhưng hậu quả khó phát hiện).
- Dữ liệu Phụ lục 6 thay đổi (thêm/sửa bộ môn) sẽ làm thay đổi kết quả match mà không có hồi âm tự động.

### Khuyến nghị (lộ trình khắc phục)
- **Đã làm trong đợt này:** bổ sung trường `reason` cho mọi nhánh (hai module `extract_module` và `mapping_module`), kèm test `test_all_branches_have_reason` (6/6 pass); đánh giá lại 10 ca theo quy tắc "từ điển chính tả" (7 đạt / 2 sai / 1 phân vân).
- **Đề xuất đợt sau:**
1. **Blacklist prefix cơ quan ngoài** (Sở / Viện / Bộ / Cục / Tổng cục / UBND...) → buộc `no_match`, giữ tên gốc + cờ review — xử lý 2 ca sai hiện tại.
2. **Ưu tiên khớp chính xác / duy nhất trước**: nếu tên là "tập con" của tên khác thì không chấp nhận ở điểm 100; chỉ tự ghi đè khi có **một** ứng viên ≥ 90 — xử lý 14/91 ca self-match nhầm.
3. Với `cap1_multi` / `cap1_only`: **không tự ghi đè tên chuẩn**, chỉ đưa gợi ý + cờ review (tránh ghi nhầm `Sở KH&CN`).
4. **Bảng alias** cho các tên chưa dịch được bằng fuzzy ("Khoa Y" → "Trường Y", "Đại học Y Dược TP.HCM" → giữ nguyên cấp đại học) — xử lý ca phân vân.
5. **Đưa self-match test (91 cap2) thành regression test** chạy mỗi khi cập nhật `ump_departments.json` hoặc sửa thuật toán.
6. Mở rộng benchmark lên số tài liệu thật lớn hơn trước khi rollout chính thức.

---

## 7. Phụ lục

### 7.1. Cách tái lập số liệu
- Dữ liệu đầu vào: 10 PDF trong `data/` (bản sao tại `backend/extract_module/data/`), bộ đơn vị `backend/extract_module/resources/ump_departments.json` (110 dòng).
- Chạy pipeline: `cd backend; python -m extract_module.extract_main` (cần `GEMINI_API_KEY`, biến môi trường `PYTHONUTF8=1`); kết quả tại `extract_module/output/<ngày>/`.
- Đo hiệu năng corrector: gọi `DepartmentCorrector.correct_corporate_name(...)` lặp 3000 lần, dùng `time.perf_counter()`; log end-to-end đối chiếu dấu thời gian trong log chạy batch.
- Self-match test: với mỗi `tenDonViCap2` trong JSON, gọi `correct_corporate_name` và so sánh kết quả trả về với chính tên đó.

### 7.2. Các tham số đang vận hành
- Ngưỡng `fuzzy_cap2` / `fuzzy_cap1`: `token_set_ratio ≥ 85`; tie-break chênh ≤ 5 điểm ưu tiên tên ngắn hơn.
- `partial_ratio ≥ 75` (vùng tie-break 75–88) cho nhánh tìm Cap 2 trong chuỗi ghép.
- Cờ rà soát: `needs_review = (score < 90)`, hoặc **luôn bằng true** với `cap1_multi` / `cap1_only` / `no_match` / `empty`.

### 7.3. Nguồn gốc sơ đồ tương tác
- Sơ đồ được tạo bằng skill **Archify** (JSON spec → HTML đóng, inline SVG), nguồn tại `docs/diagrams/*.workflow.json`.
- Đã chạy qua `validate --quality showcase` và `deliver`: **9/9 kiểm tra đạt, 0 lỗi** tại các viewport 1440×900 → 2048×1320; chữ nhỏ nhất đọc được ≥ 6px cả hai chủ đề sáng/tối.
- `visual-check` báo phần bố cục cao hơn chiều khung nhìn (vẫn cuộn dọc được trong Viewer); đây là cảnh báo containment, không phải lỗi render — đánh giá thẩm mỹ cuối cùng do người đọc tự nhận xét trên trình duyệt.