from typing import Any, Dict, List

from dublin_core_module.config.settings import settings
from dublin_core_module.core.base_mapper import BaseDCElementMapper
from dublin_core_module.utils.normalizers import to_text, to_list


class TypeMapper(BaseDCElementMapper):
    
    element = "type"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        values: List[str] = []
        doc_type = to_text(raw.get("document_type"))
        if doc_type:
            values.append(settings.DOC_TYPE_LABELS.get(doc_type, doc_type))
        values.append(settings.DCMI_TYPE)
        return values


class FormatMapper(BaseDCElementMapper):
    
    element = "format"

    FORMAT_FIELDS = ["extent", "physical_details", "dimensions"]

    def map(self, raw: Dict[str, Any]) -> List[str]:
        values: List[str] = []
        for field in self.FORMAT_FIELDS:
            text = to_text(raw.get(field))
            if text:
                values.append(text)
        return values


class IdentifierMapper(BaseDCElementMapper):
    
    element = "identifier"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        values = to_list(raw.get("isbn"))
        issn = to_text(raw.get("issn"))
        if issn:
            values.append(f"ISSN {issn}")
        return values


class SourceMapper(BaseDCElementMapper):
    
    element = "source"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        source = to_text(raw.get("acquisition_source"))
        return [source] if source else []


class LanguageMapper(BaseDCElementMapper):
    
    element = "language"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        return [settings.DEFAULT_LANGUAGE]
