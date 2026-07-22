import re
import unicodedata
import json
from typing import List, Optional, Tuple
from pymarc import Field, Subfield

from mapping_module.config.settings import Settings
from mapping_module.core.base_mapper import BaseFieldMapper
from mapping_module.core.models import RawExtractionData
from mapping_module.utils.marc_punctuation import add_end_period


class NoteMapper(BaseFieldMapper):
    # [VÁ M05] Nhãn 502 theo đúng loại tài liệu, không còn cứng "Luận văn".
    DISSERTATION_LABELS = {
        "luan_van": "Luận văn",
        "luan_an": "Luận án",
        "khoa_luan": "Khóa luận",
    }

    def can_handle(self, raw_data: RawExtractionData) -> bool:
        return bool(
            raw_data.general_notes
            or raw_data.dissertation_note
            or raw_data.bibliography_note
            or raw_data.number_of_references
            or raw_data.nature_of_content
            or raw_data.acquisition_source
            or raw_data.document_type
            or raw_data.summary
            or raw_data.title_main
        )

    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        fields: List[Field] = []

        holding_subfields: List[Subfield] = []
        for note in raw_data.general_notes or []:
            if not (note and note.strip()):
                continue
            tag, code, value = self._route_note(note.strip())
            if tag == "852":
                holding_subfields.append(Subfield(code, value))
            else:
                fields.append(
                    Field(
                        tag="500",
                        indicators=[" ", " "],
                        subfields=[Subfield("a", add_end_period(value))],
                    )
                )

        if holding_subfields:
            fields.append(
                Field(tag="852", indicators=[" ", " "], subfields=holding_subfields)
            )

        if raw_data.dissertation_note:
            fields.append(
                Field(
                    tag="502",
                    indicators=[" ", " "],
                    subfields=[Subfield("a", add_end_period(raw_data.dissertation_note))],
                )
            )
        elif raw_data.document_type in self.DISSERTATION_LABELS:
            # [VÁ M05] lấy nhãn đúng theo loại (Luận văn / Luận án / Khóa luận)
            parts = [self.DISSERTATION_LABELS[raw_data.document_type]]
            if raw_data.major:
                parts.append(f"({raw_data.major.strip()})")
            if raw_data.corporate_name:
                corp_clean = raw_data.corporate_name.replace("|", "-").strip()
                parts.append(f"-- {corp_clean}")

            pub_year = raw_data.publication_year
            if pub_year and len(parts) > 1:
                parts[-1] = f"{parts[-1]}, {pub_year.strip()}"
            elif pub_year:
                parts.append(pub_year.strip())

            note_text = " ".join(parts) + "."
            fields.append(Field(tag="502", indicators=[" ", " "], subfields=[Subfield("a", note_text)]))

        if raw_data.bibliography_note:
            fields.append(
                Field(
                    tag="504",
                    indicators=[" ", " "],
                    subfields=[Subfield("a", add_end_period(raw_data.bibliography_note))],
                )
            )

        if raw_data.number_of_references:
            fields.append(
                Field(
                    tag="500",
                    indicators=[" ", " "],
                    subfields=[Subfield("a", add_end_period(raw_data.number_of_references))],
                )
            )

        if raw_data.nature_of_content:
            fields.append(
                Field(
                    tag="520",
                    indicators=["3", " "],
                    subfields=[Subfield("a", add_end_period(raw_data.nature_of_content))],
                )
            )

        if raw_data.acquisition_source:
            fields.append(
                Field(
                    tag="541",
                    indicators=["0", " "],
                    subfields=[Subfield("a", add_end_period(raw_data.acquisition_source))],
                )
            )

        material_code = self._resolve_material_code(raw_data)
        if material_code:
            fields.append(
                Field(
                    tag="927",
                    indicators=[" ", " "],
                    subfields=[Subfield("a", material_code)],
                )
            )

        return fields

    def _route_note(self, text: str) -> Tuple[str, str, str]:
        if re.fullmatch(r'C\.?\s*\d+', text, re.IGNORECASE):
            return ("852", "t", text)

        if re.fullmatch(r'[A-Za-z0-9]+-\d+', text):
            return ("852", "p", text)

        if any(k in text.lower() for k in ["bản in", "bản", "file", "đĩa", "cd", "tt"]):
            return ("852", "z", text)

        if len(text) <= 4 and " " not in text:
            return ("852", "k", text)

        return ("500", "a", text)

    def _resolve_material_code(self, raw_data: RawExtractionData) -> Optional[str]:
        def normalize(text: str) -> str:
            text = text.replace("_", " ")
            text = unicodedata.normalize("NFKD", text)
            return "".join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()

        if raw_data.document_type:
            normalized_type = normalize(raw_data.document_type)
            if normalized_type in Settings.NATURE_CONTENT_MAP:
                return Settings.NATURE_CONTENT_MAP[normalized_type]
            for token, code in Settings.DOCUMENT_TYPE_MAP.items():
                if token == normalized_type or token in normalized_type:
                    return code

        if raw_data.nature_of_content:
            normalized_nature = normalize(raw_data.nature_of_content)
            for token, code in Settings.DOCUMENT_TYPE_MAP.items():
                if token in normalized_nature:
                    return code
            for key, code in Settings.NATURE_CONTENT_MAP.items():
                if key in normalized_nature:
                    return code

        return None