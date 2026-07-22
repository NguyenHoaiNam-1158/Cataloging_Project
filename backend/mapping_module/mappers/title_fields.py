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

        nonfiling_count = self._count_nonfiling_chars(raw_data.title_main)

        # [VÁ M02] $c = statement of responsibility. Ưu tiên trường
        # statement_of_responsibility đã trích xuất; nếu trống mới suy ra từ
        # tên tác giả cá nhân. Trước đây SOR bị bỏ hoàn toàn.
        sor = None
        if raw_data.statement_of_responsibility and raw_data.statement_of_responsibility.strip():
            sor = raw_data.statement_of_responsibility.strip()
        elif raw_data.author_personal_name and raw_data.author_personal_name.strip():
            sor = raw_data.author_personal_name.strip()

        has_b = bool(raw_data.title_remainder and raw_data.title_remainder.strip())
        has_c = bool(sor)

        subfields: List[Subfield] = []

        # [VÁ M01] Dấu ISBD chuẩn cho 245:
        #   $a kết thúc ' :' nếu có $b (phụ đề); ' /' nếu không $b nhưng có $c; '.' nếu không cả hai.
        #   $b kết thúc ' /' nếu có $c; '.' nếu không.
        #   $c kết thúc '.'.
        title_a = raw_data.title_main.strip().rstrip(" .:/")
        if has_b:
            title_a = f"{title_a} :"
        elif has_c:
            title_a = f"{title_a} /"
        else:
            title_a = self._ensure_period(title_a)
        subfields.append(Subfield("a", title_a))

        if has_b:
            title_b = raw_data.title_remainder.strip().rstrip(" .:/")
            title_b = f"{title_b} /" if has_c else self._ensure_period(title_b)
            subfields.append(Subfield("b", title_b))

        if has_c:
            subfields.append(Subfield("c", self._ensure_period(sor)))

        # Chỉ thị 1: '1' nếu có tác giả cá nhân (trường 100) để tạo điểm truy cập nhan đề
        ind1 = "1" if raw_data.author_personal_name else "0"
        ind2 = str(nonfiling_count)

        return Field(tag="245", indicators=[ind1, ind2], subfields=subfields)

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

    def _ensure_period(self, text: str) -> str:
        text = text.strip()
        return text if text.endswith('.') else f"{text}."

    def _count_nonfiling_chars(self, title: str) -> int:
        title_lower = title.lower()

        for article in self.NONFILING_ARTICLES:
            if title_lower.startswith(article):
                return len(article)

        return 0