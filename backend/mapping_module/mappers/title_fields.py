from typing import List, Optional
from pymarc import Field, Subfield

from mapping_module.core.base_mapper import BaseFieldMapper
from mapping_module.core.models import RawExtractionData


class TitleMapper(BaseFieldMapper):
    NONFILING_ARTICLES = ["a ", "an ", "the ", "những ", "cái ", "chiếc "]

    def can_handle(self, raw_data: RawExtractionData) -> bool:
        return bool(raw_data.title_main)

    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        fields = []
        
        field_245 = self._create_field_245(raw_data)
        if field_245:
            fields.append(field_245)
        
        if raw_data.title_variant:
            fields.extend(self._create_field_246(raw_data.title_variant))
        
        return fields

    def _create_field_245(self, raw_data: RawExtractionData) -> Optional[Field]:
        if not raw_data.title_main:
            return None

        subfields = []
        nonfiling_count = self._count_nonfiling_chars(raw_data.title_main)
        
        title_a = raw_data.title_main.strip()
        
        if raw_data.author_personal_name:
            if not title_a.endswith('.'):
                title_a = title_a.rstrip() + " /"
        else:
            if not title_a.endswith('.'):
                title_a += '.'

        subfields.append(Subfield('a', title_a))

        if raw_data.title_remainder:
            title_b = raw_data.title_remainder.strip()
            if raw_data.author_personal_name:
                title_b = title_b.rstrip() + " /"
            else:
                if not title_b.endswith('.'):
                    title_b += '.'
            subfields.append(Subfield('b', title_b))

        if raw_data.author_personal_name:
            title_c = raw_data.author_personal_name.strip()
            if not title_c.endswith('.'):
                title_c += '.'
            subfields.append(Subfield('c', title_c))

        # Chỉ thị 1: Thường là '1' nếu có tác giả cá nhân (trường 100) để tạo điểm truy cập
        ind1 = "1" if raw_data.author_personal_name else "0"
        ind2 = str(nonfiling_count)

        return Field(
            tag="245",
            indicators=[ind1, ind2],
            subfields=subfields
        )

    def _create_field_246(self, variants: List[str]) -> List[Field]:
        fields = []
        for variant in variants:
            if not variant or variant.strip() == "":
                continue
            
            variant_title = variant.strip()
            if not variant_title.endswith('.'):
                variant_title += '.'
            
            field = Field(
                tag="246",
                indicators=[" ", " "],
                subfields=[Subfield('a', variant_title)]
            )
            fields.append(field)
        
        return fields

    def _count_nonfiling_chars(self, title: str) -> int:
        title_lower = title.lower()
        
        for article in self.NONFILING_ARTICLES:
            if title_lower.startswith(article):
                return len(article)
        
        return 0
