import json
import re
from typing import List, Tuple, Optional
from pymarc import Field, Subfield

from mapping_module.core.base_mapper import BaseFieldMapper
from mapping_module.core.models import RawExtractionData
from mapping_module.config.settings import Settings
from mapping_module.utils.string_utils import reverse_vietnamese_name
from mapping_module.utils.marc_punctuation import safe_isbd_punctuation

class AuthorCorporateMapper(BaseFieldMapper):
    def __init__(self):
        self.departments_data = self._load_departments()

    def _load_departments(self) -> List[dict]:
        try:
            with open(Settings.DEPARTMENTS_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def can_handle(self, raw_data: RawExtractionData) -> bool:
        # Kích hoạt nếu có tác giả, đơn vị tổ chức, người hướng dẫn hoặc đủ điều kiện sinh mã 090
        has_nlm = raw_data.nlm_classification and len(raw_data.nlm_classification) > 0
        return bool(
            raw_data.author_personal_name
            or raw_data.corporate_name
            or raw_data.advisor_name
            or (has_nlm or raw_data.major)
        )

    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        fields: List[Field] = []

        if raw_data.author_personal_name:
            subfields_100 = []
            clean_name = raw_data.author_personal_name.strip()
            
            title_c = None
            match_title = re.match(r"^((?:[A-ZĐÀ-Ỹ]+\.\s*)+)\s*(.+)$", clean_name)
            if match_title:
                title_c = match_title.group(1).strip()
                clean_name = match_title.group(2).strip()

            formatted_name = reverse_vietnamese_name(clean_name)
            subfields_100.append(Subfield('a', formatted_name))

            schema_title_c, role_e = self._parse_role_from_schema(raw_data.author_role, raw_data.document_type)
            
            final_title_c = title_c or schema_title_c
            if final_title_c: 
                subfields_100.append(Subfield('c', final_title_c))
            if role_e: 
                subfields_100.append(Subfield('e', role_e))

            subfields_100 = safe_isbd_punctuation(subfields_100)
            fields.append(Field(tag="100", indicators=["1", " "], subfields=subfields_100))

            if raw_data.corporate_name:
                subfields_710 = self._parse_corporate_name(raw_data.corporate_name)
                fields.append(Field(tag="710", indicators=["2", " "], subfields=subfields_710))
        
        elif raw_data.corporate_name:
            subfields_110 = self._parse_corporate_name(raw_data.corporate_name)
            fields.append(Field(tag="110", indicators=["2", " "], subfields=subfields_110))

        field_090 = self._generate_field_090(raw_data)
        if field_090:
            fields.append(field_090)

        if raw_data.advisor_name and raw_data.document_type in ["luan_van", "luan_an", "khoa_luan"]:
            subfields_915 = []
            if raw_data.major: 
                subfields_915.append(Subfield('a', raw_data.major.title()))
            if raw_data.academic_level: 
                subfields_915.append(Subfield('c', raw_data.academic_level.title()))
            
            advisor_full = raw_data.advisor_name.title()
            if raw_data.advisor_title:
                advisor_full = f"{raw_data.advisor_title.strip()} {advisor_full}"
            subfields_915.append(Subfield('f', advisor_full))

            fields.append(Field(tag="915", indicators=[" ", " "], subfields=subfields_915))

        return fields

    def _generate_field_090(self, raw_data: RawExtractionData) -> Optional[Field]:
        nlm_code = None
        if raw_data.nlm_classification and len(raw_data.nlm_classification) > 0:
            nlm_code = raw_data.nlm_classification[0].code
        
        if not nlm_code and raw_data.major:
            major_mapping = {"Ung Thư": "QZ 200", "Nội Khoa": "WB 115", "Giải phẫu học": "QS 4"}
            nlm_code = major_mapping.get(raw_data.major)

        if nlm_code and raw_data.author_personal_name and raw_data.publication_year:
            clean_name = raw_data.author_personal_name.strip()
            match = re.match(r"^((?:[A-ZĐÀ-Ỹ]+\.\s*)+)\s*(.+)$", clean_name)
            if match:
                clean_name = match.group(2).strip()
            
            name_parts = clean_name.split()
            if name_parts:
                last_name = name_parts[0]  # Lấy họ người Việt đầu tiên
                short_last_name = last_name[:3].upper()  # Trích xuất 3 ký tự đầu viết HOA
                call_number_b = f"{short_last_name} {raw_data.publication_year.strip()}"
                
                return Field(
                    tag="090",
                    indicators=[" ", " "],
                    subfields=[
                        Subfield("a", nlm_code.strip()),
                        Subfield("b", call_number_b)
                    ]
                )
        return None

    def _parse_corporate_name(self, corp_name: str) -> List[Subfield]:
        corp_clean = corp_name.strip()
        corp_lower = corp_clean.lower()
        matched_cap1, matched_cap2 = None, None

        for dept in self.departments_data:
            cap1 = dept.get("tenDonViCap1")
            cap2 = dept.get("tenDonViCap2")
            if cap2 and cap2.lower() in corp_lower:
                matched_cap1, matched_cap2 = cap1, cap2
                break
            if cap1 and cap1.lower() in corp_lower and not matched_cap1:
                matched_cap1 = cap1

        subfields = []
        if matched_cap1 and matched_cap2:
            subfields.append(Subfield('a', matched_cap1 if matched_cap1.endswith('.') else f"{matched_cap1}."))
            subfields.append(Subfield('b', matched_cap2 if matched_cap2.endswith('.') else f"{matched_cap2}."))
        elif matched_cap1:
            subfields.append(Subfield('a', matched_cap1 if matched_cap1.endswith('.') else f"{matched_cap1}."))
        else:
            subfields.append(Subfield('a', corp_clean if corp_clean.endswith('.') else f"{corp_clean}."))
        return subfields

    def _parse_role_from_schema(self, author_role: Optional[str], doc_type: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        title_c, role_e = None, None
        if author_role:
            role_lower = author_role.lower()
            if any(kw in role_lower for kw in ["chủ biên", "biên soạn", "dịch", "chủ nhiệm", "chủ trì", "hướng dẫn"]):
                role_e = author_role.strip()
            else:
                title_c = author_role.strip()
        if doc_type == "bao_cao_nckh" and not role_e:
            role_e = "chủ nhiệm đề tài"
        return title_c, role_e