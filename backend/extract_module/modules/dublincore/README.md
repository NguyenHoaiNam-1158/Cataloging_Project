# Dublin Core Module

Module chuyển đổi biểu ghi thư viện từ chuẩn **MARC21** sang chuẩn **Dublin Core** (DC), hỗ trợ xuất ra XML (OAI_DC) và JSON.

---

## 1. Giới thiệu

**Dublin Core** là bộ metadata gồm 15 phần tử cốt lõi, được dùng phổ biến trong mô tả tài nguyên số. Module này nhận đầu vào là MARC-in-JSON (output từ thư viện `pymarc` với `record.as_dict()`), ánh xạ các trường MARC21 sang 15 trường DC tương ứng, và cho phép serialization ra XML chuẩn OAI_DC hoặc JSON.

---

## 2. Cấu trúc thư mục

```
dublincore/
├── __init__.py          # Package init (rỗng)
├── models.py            # DublinCoreRecord dataclass (15 trường DC)
├── base_converter.py    # Abstract base class cho converter
├── marc21_to_dc.py      # Ánh xạ MARC21 → Dublin Core (chính)
├── dc_serializer.py     # Serialize DC record ra XML / JSON
├── run_dub.py           # CLI tool chạy trực tiếp
└── README.md            # Tài liệu này
```

---

## 3. models.py – DublinCoreRecord

Dataclass đại diện cho một biểu ghi Dublin Core, chứa 15 trường:

| Trường        | Mô tả                                           |
|---------------|--------------------------------------------------|
| `title`       | Nhan đề tài liệu                                |
| `creator`     | Tác giả / người tạo                             |
| `subject`     | Chủ đề                                          |
| `description` | Mô tả (tóm tắt, ghi chú)                        |
| `publisher`   | Nhà xuất bản                                    |
| `date`        | Ngày tháng xuất bản                             |
| `type`        | Kiểu tài liệu (text, image, sound, …)           |
| `format`      | Định dạng vật lý (số trang, kích thước, …)      |
| `identifier`  | Định danh (ISBN, ISSN, URL, …)                  |
| `language`    | Ngôn ngữ                                        |
| `contributor` | Đồng tác giả / người đóng góp khác             |
| `coverage`    | Phạm vi (địa lý, thời gian)                    |
| `rights`      | Thông tin bản quyền                             |
| `relation`    | Quan hệ với tài liệu khác                      |
| `source`      | Nguồn gốc tài liệu gốc                         |

Mỗi trường là `List[str]` (một trường DC có thể lặp lại). Các method hữu ích:

- **`to_dict()`**: Trả về dict chỉ chứa các trường có dữ liệu.
- **`has_content()`**: Kiểm tra record có ít nhất một trường không rỗng.

---

## 4. base_converter.py – Abstract Base

```python
class BaseDublinCoreConverter(ABC):
    @abstractmethod
    def convert(self, source: Union[dict, list]) -> DublinCoreRecord:
        ...
```

Lớp cơ sở để dễ dàng mở rộng: sau này nếu cần converter từ format khác (XML MARC, CSV, …) chỉ cần kế thừa và implement `convert()`.

---

## 5. marc21_to_dc.py – Ánh xạ MARC21 → DC

### 5.1 Lớp chính

`Marc21ToDublinCoreConverter` kế thừa `BaseDublinCoreConverter`, nhận đầu vào là MARC record dạng dict (từ `pymarc`), trả về `DublinCoreRecord`.

### 5.2 Bảng ánh xạ MARC21 → DC

| DC Field      | MARC21 Fields (tags)                              | Ghi chú                          |
|---------------|---------------------------------------------------|----------------------------------|
| `title`       | 245 (ab), 246 (a), 130 (a), 240 (a), 730 (a)     | 245$a : $b là nhan đề chính     |
| `creator`     | 100 (a), 110 (a), 111 (a)                        | Tác giả chính                   |
| `subject`     | 600, 610, 611, 630, 650, 651, 653, 655           | Lấy $a                          |
| `description` | 500, 502, 504, 505, 520, 530                    | Ghi chú, tóm tắt                |
| `publisher`   | 260 ($b), 264 ($b)                                | Nhà xuất bản                    |
| `date`        | 260c, 264c, 046k                                 | Năm xuất bản                    |
| `type`        | Leader/06 + 655, 927                              | Suy từ vị trí 06 của leader     |
| `format`      | 300 (abc), 856 (q)                                | Mô tả vật lý + định dạng điện tử|
| `identifier`  | 020 (ISBN), 022 (ISSN), 001, 856 (URL), 024      | Nhiều loại định danh            |
| `language`    | 041 ($a), 008 (pos 35-37)                         | Mã ngôn ngữ 3 ký tự             |
| `contributor` | 700, 710, 711, 720                               | Loại trừ trùng với creator      |
| `coverage`    | 260/264 ($a – nơi XB), 651 ($a – địa danh)       | Phạm vi địa lý                  |
| `rights`      | 506, 540, 542, 932                               | Thông tin bản quyền/truy cập    |
| `relation`    | 490, 773, 776, 780, 785, 830                    | Quan hệ với ấn phẩm khác        |
| `source`      | 541, 786, 534                                     | Nguồn gốc tài liệu              |

### 5.3 Các hàm tiện ích

- **`_clean(value, strip_chars)`**: Loại bỏ ký tự đặc biệt ở cuối chuỗi.
- **`_get_subfields(field, *codes)`**: Lấy danh sách giá trị các trường con.
- **`_get_first_subfield(field, *codes)`**: Lấy giá trị đầu tiên.
- **`_find_fields(record_dict, *tags)`**: Tìm field theo tag trong dict MARC.
- **`_parse_008_language(field_008)`**: Giải mã mã ngôn ngữ 3 ký tự từ 008.
- **`LEADER_TYPE_MAP`**: Ánh xạ ký tự vị trí 06 leader → kiểu DC.

### 5.4 Logic đặc biệt

- **Contributor**: Loại trừ các giá trị đã xuất hiện ở `creator` để tránh trùng lặp.
- **Identifier**: Tự động thêm tiền tố `ISBN:`, `ISSN:`, `ControlNo:`, `UPC:`, … dựa trên tag MARC và indicator.
- **Format**: Kết hợp các trường con $a, $b, $c của field 300 thành chuỗi ngăn cách ` ; `.
- **Type**: Suy ra từ leader position 06 (vd. `a` → Text, `g` → Image, `j` → Sound).

---

## 6. dc_serializer.py – Serialization

### 6.1 XML (OAI_DC)

Dùng `xml.etree.ElementTree` tạo XML theo chuẩn:

```xml
<?xml version="1.0" ?>
<oai_dc:dc
  xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
                      http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
  <dc:title>...</dc:title>
  <dc:creator>...</dc:creator>
  ...
</oai_dc:dc>
```

Nếu danh sách rỗng, trả về `<oai_dc:dc/>` rỗng.

Hàm `serialize_to_xml(records, pretty=True)` – mặc định pretty-print với indent 2 spaces.

### 6.2 JSON

```json
{
  "title": ["..."],
  "creator": ["..."],
  ...
}
```

- Nếu chỉ 1 record: trả về object.
- Nếu nhiều record: trả về array các object.
- Các trường rỗng được lược bỏ tự động qua `to_dict()`.

Hàm `serialize_to_json(records, indent=2)`.

---

## 7. run_dub.py – CLI

### 7.1 Cách dùng

```bash
# Đầu vào: file JSON chứa MARC record(s) từ pymarc
python run_dub.py "path/to/file.json"

# Chọn format đầu ra
python run_dub.py "path/to/file.json" --format xml
python run_dub.py "path/to/file.json" --format json

# Thư mục đầu ra tùy chỉnh
python run_dub.py "path/to/file.json" --output-dir ./output
```

### 7.2 Định dạng file đầu vào

File JSON chứa một dict (1 record) hoặc list các dict (nhiều record), đúng format `record.as_dict()` của thư viện `pymarc`:

```json
[
  {
    "leader": ".....nam..22.....a.4500",
    "fields": [
      {"245": {"ind1": "0", "ind2": "0", "subfields": [{"a": "Lập trình Python"}]}},
      {"100": {"ind1": "1", "ind2": " ", "subfields": [{"a": "Nguyễn Văn A"}]}}
    ]
  }
]
```

### 7.3 Đầu ra

Mặc định sinh 2 file cùng thư mục với input:
- `{tên_file}_dc.xml`
- `{tên_file}_dc.json`

---

## 8. Dùng trong code

```python
from modules.dublincore.marc21_to_dc import Marc21ToDublinCoreConverter
from modules.dublincore.dc_serializer import serialize_to_xml, serialize_to_json

converter = Marc21ToDublinCoreConverter()

# Chuyển đổi từng record
record = {"leader": "...", "fields": [...]}
dc_record = converter.convert(record)

# Serialize
xml_output = serialize_to_xml([dc_record])
json_output = serialize_to_json([dc_record])
```

---

## 9. Mở rộng

### Thêm converter mới

Kế thừa `BaseDublinCoreConverter` và implement `convert()`:

```python
from modules.dublincore.base_converter import BaseDublinCoreConverter

class CsvToDublinCoreConverter(BaseDublinCoreConverter):
    def convert(self, source):
        # logic chuyển CSV row → DublinCoreRecord
        ...
```

### Thêm field mới

Mở rộng `DublinCoreRecord` trong `models.py` và cập nhật `serialize_to_xml` / `serialize_to_json` trong `dc_serializer.py`.

### Thêm format serialization mới

Thêm hàm vào `dc_serializer.py` (vd. RDF/XML, YAML, …).

---

## 10. Testing

```bash
# Test chuyển đổi
python -c "
from modules.dublincore.marc21_to_dc import Marc21ToDublinCoreConverter
from modules.dublincore.dc_serializer import serialize_to_xml

converter = Marc21ToDublinCoreConverter()
record = {
    'leader': '01234nam a2200265 a 4500',
    'fields': [
        {'245': {'ind1': '0', 'ind2': '0', 'subfields': [{'a': 'Test Title'}]}},
        {'100': {'ind1': '1', 'ind2': ' ', 'subfields': [{'a': 'Author Name'}]}}
    ]
}
dc = converter.convert(record)
print(serialize_to_xml([dc]))
"
```

---

## 11. Quy ước code

- Sử dụng type hints (`List[str]`, `Optional`, `Union`, …).
- Dataclass cho model, ABC cho converter (dễ mở rộng).
- Hàm `_clean()` chuẩn hóa giá trị đầu ra (loại bỏ ký tự thừa).
- Tránh trùng lặp dữ liệu giữa `creator` và `contributor`.
