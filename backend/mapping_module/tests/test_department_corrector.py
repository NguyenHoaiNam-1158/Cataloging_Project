"""Tests for DepartmentCorrector - Fuzzy Matching vs Phu luc 6."""

import sys
import os
import pytest

backend_dir = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.abspath(backend_dir))

from mapping_module.core.department_corrector import DepartmentCorrector


@pytest.fixture(scope="module")
def corrector():
    return DepartmentCorrector()


class TestFuzzyMatchCap2:
    """Fuzzy match truc tiep ten cap2 (Bo mon, Trung tam)."""

    def test_exact_match(self, corrector):
        result = corrector.correct_corporate_name("Bộ môn Dịch tễ học")
        assert result["cap2"] == "Bộ môn Dịch tễ học"
        assert result["cap1"] == "Khoa Y tế công cộng"
        assert result["confidence"] == 100
        assert result["needs_review"] is False

    def test_no_diacritics(self, corrector):
        result = corrector.correct_corporate_name("Bo mon Dich te hoc")
        assert result["cap2"] == "Bộ môn Dịch tễ học"
        assert result["confidence"] >= 85

    def test_uppercase(self, corrector):
        result = corrector.correct_corporate_name("BỘ MÔN DỊCH TỆ HỌC")
        assert result["cap2"] == "Bộ môn Dịch tễ học"
        assert result["confidence"] >= 85

    def test_partial_match(self, corrector):
        result = corrector.correct_corporate_name("Dich te hoc")
        assert result["cap2"] == "Bộ môn Dịch tễ học"
        assert result["confidence"] >= 85

    def test_hoa_sinh(self, corrector):
        result = corrector.correct_corporate_name("Bo mon Hoa sinh")
        assert result["cap2"] == "Bộ môn Hóa sinh"
        assert result["confidence"] >= 85


class TestFuzzyMatchCap1:
    """Fuzzy match ten cap1 (Truong, Khoa, Phong, etc.)."""

    def test_truong_y(self, corrector):
        result = corrector.correct_corporate_name("Trường Y")
        assert result["cap1"] == "Trường Y"
        assert result["needs_review"] is True

    def test_khoa_y_te_cong_cong(self, corrector):
        result = corrector.correct_corporate_name("Khoa Y te cong cong")
        assert result["cap1"] == "Khoa Y tế công cộng"
        assert result["confidence"] >= 85

    def test_phong_dao_tao(self, corrector):
        result = corrector.correct_corporate_name("Phong Dao tao dai hoc")
        assert result["cap1"] == "Phòng Đào tạo đại học"
        assert result["confidence"] >= 85

    def test_benh_vien(self, corrector):
        result = corrector.correct_corporate_name("Benh vien Dai hoc Y Duoc - Co so 1")
        assert result["cap1"] == "Bệnh viện Đại học Y Dược - Cơ sở 1"
        assert result["confidence"] >= 85

    def test_truong_duoc(self, corrector):
        result = corrector.correct_corporate_name("Truong Duoc")
        assert result["cap1"] == "Trường Dược"
        assert result["confidence"] >= 85


class TestNoMatch:
    """Case khong match - giu nguyen."""

    def test_unknown_name(self, corrector):
        result = corrector.correct_corporate_name("Khoa ABC XYZ")
        assert result["needs_review"] is True
        assert result["corrected_name"] == "Khoa ABC XYZ"

    def test_empty_string(self, corrector):
        result = corrector.correct_corporate_name("")
        assert result["needs_review"] is True

    def test_none(self, corrector):
        result = corrector.correct_corporate_name(None)
        assert result["needs_review"] is True


class TestCompositeNames:
    """Query toc hop: co ca cap1 + cap2."""

    def test_composite_truong_dieu_duong(self, corrector):
        result = corrector.correct_corporate_name(
            "Truong Dieu duong Ky thuat y hoc - Bo mon Dieu duong"
        )
        assert result["cap1"] == "Trường Điều dưỡng - Kỹ thuật y học"
        assert result["cap2"] == "Bộ môn Điều dưỡng"

    def test_composite_khoa_y_te(self, corrector):
        result = corrector.correct_corporate_name(
            "Khoa Y te cong cong - Bo mon Dich te hoc"
        )
        assert result["cap1"] == "Khoa Y tế công cộng"
        assert result["cap2"] == "Bộ môn Dịch tễ học"

    def test_composite_truong_y(self, corrector):
        result = corrector.correct_corporate_name(
            "Truong Y - Bo mon Giai phau hoc"
        )
        assert result["cap1"] == "Trường Y"
        assert result["cap2"] == "Bộ môn Giải phẫu học"


class TestCorrectionOutput:
    """Kiem tra dinh dang output."""

    def test_corrected_name_format(self, corrector):
        result = corrector.correct_corporate_name("Bo mon Dich te hoc")
        assert "|" in result["corrected_name"]
        parts = result["corrected_name"].split("|")
        assert len(parts) == 2

    def test_confidence_range(self, corrector):
        result = corrector.correct_corporate_name("Trường Y")
        assert 0 <= result["confidence"] <= 100

    def test_match_method_values(self, corrector):
        valid_methods = [
            "fuzzy_cap2", "fuzzy_cap1_single", "fuzzy_cap1_multi",
            "fuzzy_cap1_only", "no_match", "empty"
        ]
        result = corrector.correct_corporate_name("Bo mon Dich te hoc")
        assert result["match_method"] in valid_methods


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
