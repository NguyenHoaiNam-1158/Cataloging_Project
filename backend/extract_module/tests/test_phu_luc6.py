import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("QWEN_API_KEY", "test-key")
os.environ.setdefault("USE_OCR", "false")

from modules.postprocessing.department_corrector import DepartmentCorrector
from modules.postprocessing.marc21_mapper import Marc21Mapper


def _build_mapper(corporate_name):
    return Marc21Mapper({"corporate_name": corporate_name})


def test_corrector_fuzzy_cap2():
    corrector = DepartmentCorrector()
    result = corrector.correct_corporate_name("Bo mon Dich te hoc")
    assert result["cap1"] == "Khoa Y tế công cộng"
    assert result["cap2"] == "Bộ môn Dịch tễ học"
    assert "|" in result["corrected_name"]
    assert not result["needs_review"]
    assert "reason" in result and result["reason"].strip()


def test_corrector_no_match_keeps_original():
    corrector = DepartmentCorrector()
    result = corrector.correct_corporate_name("Khoa ABC XYZ Khong Ton Tai")
    assert result["match_method"] == "no_match"
    assert result["needs_review"] is True
    assert result["corrected_name"] == "Khoa ABC XYZ Khong Ton Tai"
    assert "reason" in result and result["reason"].strip()
    assert "gần nhất" in result["reason"]


def test_all_branches_have_reason():
    corrector = DepartmentCorrector()
    cases = {
        "": "empty",
        "Bo mon Dich te hoc": "fuzzy_cap2",
        "Khoa Y tế công cộng, Bộ môn Dịch tễ học": "fuzzy_cap2",
        "Khoa Y tế công cộng": "fuzzy_cap1_",
        "Khoa ABC XYZ Khong Ton Tai": "no_match",
    }
    for query, expected_prefix in cases.items():
        r = corrector.correct_corporate_name(query)
        assert "reason" in r and str(r["reason"]).strip(), (query, r)
        assert r["match_method"].startswith(expected_prefix), (query, r)


def test_mapper_110_splits_cap1_cap2():
    mapper = _build_mapper("Khoa Y tế công cộng|Bộ môn Dịch tễ học")
    record = mapper.to_record()
    f110 = record.get("110")
    assert f110 is not None
    assert f110.subfields[0].code == "a"
    assert f110.subfields[0].value == "Khoa Y tế công cộng"
    assert f110.subfields[1].code == "b"
    assert f110.subfields[1].value == "Bộ môn Dịch tễ học"


def test_mapper_110_plain_no_pipe():
    mapper = _build_mapper("Trường Y")
    record = mapper.to_record()
    f110 = record.get("110")
    assert f110 is not None
    assert len(f110.subfields) == 1
    assert f110.subfields[0].value == "Trường Y"


def test_mapper_502_uses_cap1_only():
    mapper = Marc21Mapper({
        "document_type": "luan_van",
        "major": "Nội khoa",
        "corporate_name": "Khoa Y tế công cộng|Bộ môn Dịch tễ học",
        "publication_year": "2024",
    })
    record = mapper.to_record()
    f502 = record.get("502")
    assert f502 is not None
    note = f502.subfields[0].value
    assert "|" not in note
    assert "Khoa Y tế công cộng" in note