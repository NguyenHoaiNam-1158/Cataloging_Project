from typing import Any, Dict, List

from dublin_core_module.core.base_mapper import BaseDCElementMapper
from dublin_core_module.utils.normalizers import to_text, to_list


class TitleMapper(BaseDCElementMapper):
    
    element = "title"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        values: List[str] = []
        main = to_text(raw.get("title_main"))
        remainder = to_text(raw.get("title_remainder"))
        if main:
            values.append(f"{main} : {remainder}" if remainder else main)
        values.extend(to_list(raw.get("title_variant")))
        return values


class CreatorMapper(BaseDCElementMapper):
    
    element = "creator"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        values: List[str] = []
        name = to_text(raw.get("author_personal_name"))
        role = to_text(raw.get("author_role"))
        if name:
            values.append(f"{name} ({role})" if role else name)
        sor = to_text(raw.get("statement_of_responsibility"))
        if sor and sor != name:
            values.append(sor)
        return values


class ContributorMapper(BaseDCElementMapper):
    
    element = "contributor"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        advisor = to_text(raw.get("advisor_name"))
        if not advisor:
            return []
        title = to_text(raw.get("advisor_title"))
        label = f"{title} {advisor}" if title else advisor
        return [f"{label} (Người hướng dẫn)"]


class SubjectMapper(BaseDCElementMapper):
    
    element = "subject"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        values = to_list(raw.get("subject_terms"))
        major = to_text(raw.get("major"))
        if major:
            values.append(major)
        return values


class DescriptionMapper(BaseDCElementMapper):
    
    element = "description"

    NOTE_FIELDS = [
        "dissertation_note",
        "nature_of_content",
        "bibliography_note",
        "number_of_references",
    ]

    def map(self, raw: Dict[str, Any]) -> List[str]:
        values: List[str] = []
        for field in self.NOTE_FIELDS:
            text = to_text(raw.get(field))
            if text:
                values.append(text)
        values.extend(to_list(raw.get("general_notes")))
        return values
