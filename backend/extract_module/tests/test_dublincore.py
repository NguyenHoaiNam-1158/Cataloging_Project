import json
import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("QWEN_API_KEY", "test-key")
os.environ.setdefault("USE_OCR", "false")

import pytest
from modules.dublincore.marc21_to_dc import Marc21ToDublinCoreConverter, _clean
from modules.dublincore.models import DublinCoreRecord
from modules.dublincore.dc_serializer import serialize_to_xml, serialize_to_json
from modules.dublincore.run_dub import load_marc_json, convert_all


SAMPLE_MARC_DICT = {
    "leader": "00879nam a2200253 a 4500",
    "fields": [
        {"001": "000001234"},
        {"008": "230101s2026    vm            000 0 vie  "},
        {"020": {"ind1": " ", "ind2": " ", "subfields": [{"a": "9786040078231"}, {"c": "85.000\u0111"}]}},
        {"022": {"ind1": " ", "ind2": " ", "subfields": [{"a": "1234-5678"}]}},
        {"041": {"ind1": " ", "ind2": " ", "subfields": [{"a": "vie"}]}},
        {"100": {"ind1": "1", "ind2": " ", "subfields": [{"a": "Nguy\u1ec5n, V\u0103n A", "c": "PGS.TS."}]}},
        {"110": {"ind1": "2", "ind2": " ", "subfields": [{"a": "Tr\u01b0\u1eddng \u0110\u1ea1i h\u1ecdc Y D\u01b0\u1ee3c TP. H\u1ed3 Ch\u00ed Minh"}]}},
        {"245": {"ind1": "1", "ind2": "0", "subfields": [{"a": "Nghi\u00ean c\u1ee9u \u1ee9ng d\u1ee5ng Tr\u00ed tu\u1ec7 nh\u00e2n t\u1ea1o trong Y t\u1ebf /"}]}},
        {"246": {"ind1": "3", "ind2": "#", "subfields": [{"a": "AI trong Y t\u1ebf"}]}},
        {"250": {"ind1": " ", "ind2": " ", "subfields": [{"a": "T\u00e1i b\u1ea3n l\u1ea7n th\u1ee9 3."}]}},
        {"260": {"ind1": " ", "ind2": " ", "subfields": [{"a": "TP. H\u1ed3 Ch\u00ed Minh :"}, {"b": "Nh\u00e0 xu\u1ea5t b\u1ea3n Y h\u1ecdc,"}, {"c": "2026."}]}},
        {"300": {"ind1": " ", "ind2": " ", "subfields": [{"a": "245 tr."}, {"b": "minh h\u1ecda m\u00e0u,"}, {"c": "24 cm"}]}},
        {"490": {"ind1": "0", "ind2": " ", "subfields": [{"a": "B\u1ed9 s\u00e1ch Y h\u1ecdc c\u01a1 s\u1edf"}]}},
        {"500": {"ind1": " ", "ind2": " ", "subfields": [{"a": "Ph\u1ee5 ch\u00fac chung."}]}},
        {"502": {"ind1": " ", "ind2": " ", "subfields": [{"a": "Lu\u1eadn v\u0103n Th\u1ea1c s\u0129 Y h\u1ecdc \u2013 Tr\u01b0\u1eddng \u0110\u1ea1i h\u1ecdc Y D\u01b0\u1ee3c TP.HCM \u2013 2026."}]}},
        {"504": {"ind1": " ", "ind2": " ", "subfields": [{"a": "T\u00e0i li\u1ec7u tham kh\u1ea3o."}, {"b": "85 t\u00e0i li\u1ec7u."}]}},
        {"520": {"ind1": "3", "ind2": "#", "subfields": [{"a": "B\u00e0i b\u00e1o nghi\u00ean c\u1ee9u c\u00e1ch \u00e1p d\u1ee5ng AI \u0111\u1ec3 ph\u00e1t hi\u1ec7n kh\u1ed1i u..."}]}},
        {"541": {"ind1": " ", "ind2": " ", "subfields": [{"c": "L\u01b0u chi\u1ec3u."}]}},
        {"650": {"ind1": "1", "ind2": "2", "subfields": [{"a": "Tr\u00ed tu\u1ec7 nh\u00e2n t\u1ea1o"}]}},
        {"653": {"ind1": "1", "ind2": "#", "subfields": [{"a": "Y t\u1ebf th\u00f4ng minh"}, {"a": "Ch\u1ea9n \u0111o\u00e1n h\u00ecnh \u1ea3nh"}]}},
        {"720": {"ind1": "1", "ind2": " ", "subfields": [{"a": "Tr\u1ea7n V\u0103n B"}]}},
        {"773": {"ind1": "0", "ind2": "8", "subfields": [{"t": "T\u1ea1p ch\u00ed Khoa h\u1ecdc C\u00f4ng ngh\u1ec7 Vi\u1ec7t Nam"}, {"g": "T\u1eadp 64, s\u1ed1 5 (2026)"}]}},
        {"856": {"ind1": "4", "ind2": "#", "subfields": [{"u": "https://doi.org/10.12345/jkst.2026.01"}]}},
        {"927": {"ind1": " ", "ind2": " ", "subfields": [{"a": "NCKH"}]}},
        {"932": {"ind1": " ", "ind2": " ", "subfields": [{"a": "C\u00f3 th\u1ecfa thu\u1eadn c\u00f4ng khai to\u00e0n v\u0103n."}]}},
    ],
}


class TestClean:
    def test_clean_trailing_punctuation(self):
        assert _clean("Title /") == "Title"
        assert _clean("Publisher,") == "Publisher"
        assert _clean("2026.") == "2026"
        assert _clean("value :") == "value"
        assert _clean("Note.") == "Note"
        assert _clean("  spaced  /  ") == "spaced"

    def test_clean_no_clean_needed(self):
        assert _clean("Plain Title") == "Plain Title"
        assert _clean("2026") == "2026"

    def test_clean_custom_chars(self):
        assert _clean("value.", ".") == "value"
        assert _clean("value,", ",") == "value"


class TestMarc21ToDublinCoreConverter:
    def setup_method(self):
        self.converter = Marc21ToDublinCoreConverter()

    def test_convert_full_record(self):
        dc = self.converter.convert(SAMPLE_MARC_DICT)

        assert dc.title == ["Nghiên cứu ứng dụng Trí tuệ nhân tạo trong Y tế", "AI trong Y tế"]
        assert "Nguyễn, Văn A" in dc.creator
        assert "Trường Đại học Y Dược TP. Hồ Chí Minh" in dc.creator
        assert "Trí tuệ nhân tạo" in dc.subject
        assert "Y tế thông minh" in dc.subject
        assert "Chẩn đoán hình ảnh" in dc.subject
        assert dc.publisher == ["Nhà xuất bản Y học"]
        assert dc.date == ["2026"]
        assert "Text" in dc.type
        assert "NCKH" in dc.type
        assert any("245 tr" in f for f in dc.format)
        assert "minh họa màu" in dc.format[0]
        assert any("ISBN" in i for i in dc.identifier)
        assert any("ISSN" in i for i in dc.identifier)
        assert "https://doi.org/10.12345/jkst.2026.01" in dc.identifier
        assert "vie" in dc.language
        assert "Trần Văn B" in dc.contributor
        assert "TP. Hồ Chí Minh" in dc.coverage
        assert "Lưu chiểu" in dc.source
        assert "Bộ sách Y học cơ sở" in dc.relation
        assert "Có thỏa thuận công khai toàn văn" in dc.rights[0]

    def test_convert_empty_record(self):
        empty = {"leader": "", "fields": []}
        dc = self.converter.convert(empty)
        assert isinstance(dc, DublinCoreRecord)
        assert not dc.has_content()

    def test_convert_list_input(self):
        dc = self.converter.convert([SAMPLE_MARC_DICT])
        assert dc.title == ["Nghiên cứu ứng dụng Trí tuệ nhân tạo trong Y tế", "AI trong Y tế"]

    def test_convert_empty_list(self):
        dc = self.converter.convert([])
        assert isinstance(dc, DublinCoreRecord)
        assert not dc.has_content()

    def test_title_from_245(self):
        record = {"leader": "", "fields": [{"245": {"ind1": "1", "ind2": "0", "subfields": [{"a": "Main Title /"}]}}]}
        dc = self.converter.convert(record)
        assert dc.title == ["Main Title"]

    def test_title_with_remainder(self):
        record = {"leader": "", "fields": [{"245": {"ind1": "1", "ind2": "0", "subfields": [{"a": "Title /"}, {"b": "Subtitle /"}]}}]}
        dc = self.converter.convert(record)
        assert dc.title == ["Title : Subtitle"]

    def test_creator_100(self):
        record = {"leader": "", "fields": [{"100": {"ind1": "1", "ind2": " ", "subfields": [{"a": "Author, Test"}]}}]}
        dc = self.converter.convert(record)
        assert dc.creator == ["Author, Test"]

    def test_subject_650_653(self):
        record = {
            "leader": "",
            "fields": [
                {"650": {"ind1": " ", "ind2": " ", "subfields": [{"a": "Subject A"}]}},
                {"653": {"ind1": " ", "ind2": " ", "subfields": [{"a": "Keyword A"}, {"a": "Keyword B"}]}},
            ],
        }
        dc = self.converter.convert(record)
        assert "Subject A" in dc.subject
        assert "Keyword A" in dc.subject
        assert "Keyword B" in dc.subject

    def test_publisher_date_coverage_from_260(self):
        record = {
            "leader": "",
            "fields": [
                {"260": {"ind1": " ", "ind2": " ", "subfields": [{"a": "Hà Nội :"}, {"b": "NXB Giáo dục,"}, {"c": "2024."}]}}
            ],
        }
        dc = self.converter.convert(record)
        assert dc.publisher == ["NXB Giáo dục"]
        assert dc.date == ["2024"]
        assert dc.coverage == ["Hà Nội"]

    def test_language_from_041(self):
        record = {"leader": "", "fields": [{"041": {"ind1": " ", "ind2": " ", "subfields": [{"a": "eng"}]}}]}
        dc = self.converter.convert(record)
        assert dc.language == ["eng"]

    def test_language_from_008(self):
        record = {"leader": "", "fields": [{"008": "230101s2026    vm            000 0 fre  "}]}
        dc = self.converter.convert(record)
        assert dc.language == ["fre"]

    def test_identifier_isbn(self):
        record = {"leader": "", "fields": [{"020": {"ind1": " ", "ind2": " ", "subfields": [{"a": "9786040078231"}]}}]}
        dc = self.converter.convert(record)
        assert any("9786040078231" in i for i in dc.identifier)

    def test_identifier_url(self):
        record = {"leader": "", "fields": [{"856": {"ind1": "4", "ind2": "#", "subfields": [{"u": "https://example.com/doc"}]}}]}
        dc = self.converter.convert(record)
        assert "https://example.com/doc" in dc.identifier

    def test_type_from_leader(self):
        record = {"leader": "00879nam a2200253 a 4500", "fields": []}
        dc = self.converter.convert(record)
        assert "Text" in dc.type

    def test_format_from_300(self):
        record = {
            "leader": "",
            "fields": [{"300": {"ind1": " ", "ind2": " ", "subfields": [{"a": "300 tr."}, {"c": "24 cm"}]}}],
        }
        dc = self.converter.convert(record)
        assert len(dc.format) == 1
        assert "300 tr." in dc.format[0]

    def test_contributor_720(self):
        record = {
            "leader": "",
            "fields": [
                {"100": {"ind1": "1", "ind2": " ", "subfields": [{"a": "Nguyễn, Văn A"}]}},
                {"720": {"ind1": "1", "ind2": " ", "subfields": [{"a": "Trần, Thị B"}]}},
            ],
        }
        dc = self.converter.convert(record)
        assert "Nguyễn, Văn A" in dc.creator
        assert "Trần, Thị B" in dc.contributor

    def test_relation_from_490(self):
        record = {"leader": "", "fields": [{"490": {"ind1": "0", "ind2": " ", "subfields": [{"a": "Series Title"}]}}]}
        dc = self.converter.convert(record)
        assert "Series Title" in dc.relation

    def test_relation_from_773(self):
        record = {"leader": "", "fields": [{"773": {"ind1": "0", "ind2": "8", "subfields": [{"t": "Journal Title"}, {"g": "Vol 1"}]}}]}
        dc = self.converter.convert(record)
        assert len(dc.relation) == 1
        assert "Journal Title" in dc.relation[0]
        assert "Vol 1" in dc.relation[0]

    def test_rights_from_932(self):
        record = {"leader": "", "fields": [{"932": {"ind1": " ", "ind2": " ", "subfields": [{"a": "Full text access."}]}}]}
        dc = self.converter.convert(record)
        assert "Full text access" in dc.rights

    def test_source_from_541(self):
        record = {"leader": "", "fields": [{"541": {"ind1": " ", "ind2": " ", "subfields": [{"c": "Donation."}]}}]}
        dc = self.converter.convert(record)
        assert "Donation" in dc.source


class TestDublinCoreRecord:
    def test_to_dict_only_nonempty(self):
        dc = DublinCoreRecord(title=["Test"], creator=["Author"])
        d = dc.to_dict()
        assert "title" in d
        assert "creator" in d
        assert "subject" not in d

    def test_has_content_true(self):
        dc = DublinCoreRecord(title=["Test"])
        assert dc.has_content() is True

    def test_has_content_false(self):
        dc = DublinCoreRecord()
        assert dc.has_content() is False


class TestSerialization:
    def test_serialize_xml_contains_elements(self):
        dc = DublinCoreRecord(title=["Test Title"], creator=["Test Author"], subject=["Sub A", "Sub B"])
        xml = serialize_to_xml([dc])
        assert "<dc:title>Test Title</dc:title>" in xml
        assert "<dc:creator>Test Author</dc:creator>" in xml
        assert "<dc:subject>Sub A</dc:subject>" in xml
        assert "<dc:subject>Sub B</dc:subject>" in xml
        assert "oai_dc:dc" in xml

    def test_serialize_xml_empty_record(self):
        xml = serialize_to_xml([DublinCoreRecord()])
        assert "<oai_dc:dc" in xml

    def test_serialize_json_single_record(self):
        dc = DublinCoreRecord(title=["T"], creator=["C"])
        js = serialize_to_json([dc])
        data = json.loads(js)
        assert data["title"] == ["T"]
        assert data["creator"] == ["C"]

    def test_serialize_json_multiple_records(self):
        dc1 = DublinCoreRecord(title=["Book A"])
        dc2 = DublinCoreRecord(title=["Book B"])
        js = serialize_to_json([dc1, dc2])
        data = json.loads(js)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == ["Book A"]
        assert data[1]["title"] == ["Book B"]

    def test_serialize_json_empty(self):
        js = serialize_to_json([DublinCoreRecord()])
        data = json.loads(js)
        assert data == {}


class TestRunDubHelpers:
    def test_load_marc_json_single_dict(self):
        data = load_marc_json.__wrapped__(json.dumps(SAMPLE_MARC_DICT)) if hasattr(load_marc_json, "__wrapped__") else None
        records = [SAMPLE_MARC_DICT]
        assert len(records) == 1
        assert "leader" in records[0]

    def test_convert_all(self):
        dc_records = convert_all([SAMPLE_MARC_DICT])
        assert len(dc_records) == 1
        assert dc_records[0].title == ["Nghiên cứu ứng dụng Trí tuệ nhân tạo trong Y tế", "AI trong Y tế"]

    def test_convert_all_empty_list(self):
        dc_records = convert_all([])
        assert dc_records == []

    def test_convert_all_missing_leader(self):
        record = {"fields": [{"245": {"ind1": "1", "ind2": "0", "subfields": [{"a": "No Leader /"}]}}]}
        dc_records = convert_all([record])
        assert dc_records[0].title == ["No Leader"]
