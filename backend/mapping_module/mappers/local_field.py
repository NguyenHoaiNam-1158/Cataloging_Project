import re
from typing import List, Optional
from pymarc import Field, Subfield
from mapping_module.core.base_mapper import BaseFieldMapper
from mapping_module.core.models import RawExtractionData


class LocalFieldMapper(BaseFieldMapper):
    MAJOR_NLM_FALLBACK = {
        "Ung Thư": "QZ 200",
        "Nội Khoa": "WB 115",
        "Giải phẫu học": "QS 4",
    }

    def can_handle(self, raw_data: RawExtractionData) -> bool:
        has_nlm = bool(raw_data.nlm_classification and len(raw_data.nlm_classification) > 0)
        has_major = bool(raw_data.major and raw_data.major.strip() in self.MAJOR_NLM_FALLBACK)
        return (has_nlm or has_major) and bool(raw_data.author_personal_name) and bool(raw_data.publication_year)

    def _resolve_nlm_code(self, raw_data: RawExtractionData) -> Optional[str]:
        if raw_data.nlm_classification and len(raw_data.nlm_classification) > 0:
            nlm_item = raw_data.nlm_classification[0]
            if isinstance(nlm_item, dict):
                code = nlm_item.get("code", "")
            else:
                code = getattr(nlm_item, "code", "")
            if code:
                return code.strip()

        if raw_data.major:
            return self.MAJOR_NLM_FALLBACK.get(raw_data.major.strip())

        return None

    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        extracted_code = self._resolve_nlm_code(raw_data)
        if not extracted_code:
            return []

        clean_name = raw_data.author_personal_name.strip()
        clean_name = re.sub(r'^(GS\.|PGS\.|TS\.|ThS\.|BS\.|Thầy|Cô)+\s*', '', clean_name, flags=re.IGNORECASE)

        name_parts = clean_name.split()
        if not name_parts:
            return []

        first_word = name_parts[0]          
        short_ho = first_word[:3].upper()   

        pub_year = str(raw_data.publication_year).strip()
        year_match = re.search(r'\d{4}', pub_year)
        clean_year = year_match.group(0) if year_match else pub_year

        call_number_b = f"{short_ho} {clean_year}"

        return [
            Field(
                tag="090",
                indicators=[" ", " "],
                subfields=[
                    Subfield("a", extracted_code),
                    Subfield("b", call_number_b),
                ],
            )
        ]