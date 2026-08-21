import re
from typing import Dict, List, Optional, Union

from modules.dublincore.base_converter import BaseDublinCoreConverter
from modules.dublincore.models import DublinCoreRecord


def _clean(value: str, strip_chars: str = " /:,.!;-") -> str:
    return value.rstrip(strip_chars).strip()


def _get_subfields(field: dict, *codes: str) -> List[str]:
    values = []
    for sf in field.get("subfields", []):
        for code, val in sf.items():
            if code in codes and val:
                values.append(val.strip())
    return values


def _get_first_subfield(field: dict, *codes: str) -> Optional[str]:
    vals = _get_subfields(field, *codes)
    return vals[0] if vals else None


def _iter_fields(record_dict: dict) -> List[dict]:
    return record_dict.get("fields", [])


def _find_fields(record_dict: dict, *tags: str) -> List[dict]:
    result = []
    for entry in _iter_fields(record_dict):
        for tag, content in entry.items():
            if tag in tags:
                result.append({"tag": tag, "content": content})
    return result


def _parse_leader_language(leader: str) -> Optional[str]:
    if len(leader) >= 11:
        pos9 = leader[9] if len(leader) > 9 else ""
        if pos9 == "a":
            return None
    return None


def _parse_008_language(field_008: str) -> Optional[str]:
    if field_008 and len(field_008) >= 38:
        lang = field_008[35:38].strip()
        return lang if lang else None
    return None


LEADER_TYPE_MAP = {
    "a": "Text",
    "c": "Music",
    "d": "Music",
    "e": "Map",
    "f": "Map",
    "g": "Image",
    "i": "Sound",
    "j": "Sound",
    "k": "Image",
    "m": "Software",
    "o": "Kit",
    "p": "Mixed",
    "r": "Object",
    "t": "Text",
}


class Marc21ToDublinCoreConverter(BaseDublinCoreConverter):
    def convert(self, source: Union[dict, list]) -> DublinCoreRecord:
        if isinstance(source, list):
            if not source:
                return DublinCoreRecord()
            source = source[0]
        record = source
        dc = DublinCoreRecord()

        dc.title = self._extract_titles(record)
        dc.creator = self._extract_creators(record)
        dc.subject = self._extract_subjects(record)
        dc.description = self._extract_descriptions(record)
        dc.publisher = self._extract_publishers(record)
        dc.date = self._extract_dates(record)
        dc.type = self._extract_types(record)
        dc.format = self._extract_formats(record)
        dc.identifier = self._extract_identifiers(record)
        dc.language = self._extract_languages(record)
        dc.contributor = self._extract_contributors(record)
        dc.coverage = self._extract_coverage(record)
        dc.rights = self._extract_rights(record)
        dc.relation = self._extract_relations(record)
        dc.source = self._extract_sources(record)

        return dc

    def _extract_titles(self, record: dict) -> List[str]:
        titles = []
        for f in _find_fields(record, "245", "246", "130", "240", "730"):
            content = f["content"]
            if isinstance(content, str):
                titles.append(content)
                continue
            if f["tag"] == "245":
                a = _get_first_subfield(content, "a")
                b = _get_first_subfield(content, "b")
                parts = []
                if a:
                    parts.append(_clean(a, " /:;"))
                if b:
                    parts.append(_clean(b, " /:;."))
                if parts:
                    titles.append(" : ".join(parts))
            elif f["tag"] == "246":
                a = _get_first_subfield(content, "a")
                if a:
                    titles.append(_clean(a, " /:;."))
            else:
                a = _get_first_subfield(content, "a")
                if a:
                    titles.append(_clean(a, " /:;."))
        return titles

    def _extract_creators(self, record: dict) -> List[str]:
        creators = []
        for f in _find_fields(record, "100", "110", "111"):
            content = f["content"]
            if isinstance(content, str):
                creators.append(content)
                continue
            if f["tag"] == "100":
                a = _get_first_subfield(content, "a")
                if a:
                    creators.append(_clean(a, " /:;.,"))
            elif f["tag"] == "110":
                a = _get_first_subfield(content, "a")
                if a:
                    creators.append(_clean(a, " /:;.,"))
            elif f["tag"] == "111":
                a = _get_first_subfield(content, "a")
                if a:
                    creators.append(_clean(a, " /:;.,"))
        return creators

    def _extract_subjects(self, record: dict) -> List[str]:
        subjects = []
        for f in _find_fields(record, "600", "610", "611", "630", "650", "651", "653", "655"):
            content = f["content"]
            if isinstance(content, str):
                subjects.append(content)
                continue
            vals = _get_subfields(content, "a")
            subjects.extend(_clean(v, " /:;.,") for v in vals if v)
        return subjects

    def _extract_descriptions(self, record: dict) -> List[str]:
        descriptions = []
        for f in _find_fields(record, "500", "502", "504", "505", "520", "530"):
            content = f["content"]
            if isinstance(content, str):
                descriptions.append(content)
                continue
            vals = _get_subfields(content, "a")
            descriptions.extend(_clean(v) for v in vals if v)
        return descriptions

    def _extract_publishers(self, record: dict) -> List[str]:
        publishers = []
        for f in _find_fields(record, "260", "264"):
            content = f["content"]
            if isinstance(content, str):
                publishers.append(content)
                continue
            vals = _get_subfields(content, "b")
            publishers.extend(_clean(v, " ,;") for v in vals if v)
        return publishers

    def _extract_dates(self, record: dict) -> List[str]:
        dates = []
        for f in _find_fields(record, "260", "264"):
            content = f["content"]
            if isinstance(content, str):
                dates.append(content)
                continue
            c = _get_first_subfield(content, "c")
            if c:
                dates.append(_clean(c, " .;,"))
        for f in _find_fields(record, "046"):
            content = f["content"]
            if isinstance(content, str):
                continue
            k = _get_first_subfield(content, "k")
            if k:
                dates.append(k)
        return dates

    def _extract_types(self, record: dict) -> List[str]:
        types = []
        leader = record.get("leader", "")
        if leader and len(leader) > 6:
            pos06 = leader[6] if len(leader) > 6 else ""
            dc_type = LEADER_TYPE_MAP.get(pos06)
            if dc_type:
                types.append(dc_type)
        for f in _find_fields(record, "655", "927"):
            content = f["content"]
            if isinstance(content, str):
                types.append(content)
                continue
            vals = _get_subfields(content, "a")
            types.extend(v for v in vals if v)
        return types

    def _extract_formats(self, record: dict) -> List[str]:
        formats = []
        for f in _find_fields(record, "300"):
            content = f["content"]
            if isinstance(content, str):
                formats.append(content)
                continue
            parts = []
            a = _get_first_subfield(content, "a")
            b = _get_first_subfield(content, "b")
            c = _get_first_subfield(content, "c")
            if a:
                parts.append(_clean(a, " ;:"))
            if b:
                parts.append(_clean(b, " ;:"))
            if c:
                parts.append(_clean(c, " ;:"))
            if parts:
                formats.append(" ; ".join(parts))
        for f in _find_fields(record, "856"):
            content = f["content"]
            if isinstance(content, str):
                continue
            q = _get_first_subfield(content, "q")
            if q:
                formats.append(q)
        return formats

    def _extract_identifiers(self, record: dict) -> List[str]:
        identifiers = []
        for f in _find_fields(record, "020"):
            content = f["content"]
            if isinstance(content, str):
                identifiers.append(content)
                continue
            a = _get_first_subfield(content, "a")
            if a:
                identifiers.append(f"ISBN: {_clean(a)}")
        for f in _find_fields(record, "022"):
            content = f["content"]
            if isinstance(content, str):
                identifiers.append(content)
                continue
            a = _get_first_subfield(content, "a")
            if a:
                identifiers.append(f"ISSN: {_clean(a)}")
        for f in _find_fields(record, "001"):
            content = f["content"]
            if isinstance(content, str) and content.strip():
                identifiers.append(f"ControlNo: {content.strip()}")
        for f in _find_fields(record, "856"):
            content = f["content"]
            if isinstance(content, str):
                identifiers.append(content)
                continue
            u = _get_first_subfield(content, "u")
            if u:
                identifiers.append(_clean(u))
        for f in _find_fields(record, "024"):
            content = f["content"]
            if isinstance(content, str):
                continue
            a = _get_first_subfield(content, "a")
            ind1 = content.get("ind1", " ")
            if a:
                prefix = {"0": "UPC", "1": "UPC", "2": "ISMN", "3": "EAN", "7": "ID", "8": "ID"}.get(ind1, "ID")
                identifiers.append(f"{prefix}: {_clean(a)}")
        return identifiers

    def _extract_languages(self, record: dict) -> List[str]:
        languages = []
        for f in _find_fields(record, "041"):
            content = f["content"]
            if isinstance(content, str):
                languages.append(content)
                continue
            vals = _get_subfields(content, "a")
            languages.extend(v for v in vals if v)
        for f in _find_fields(record, "008"):
            content = f["content"]
            if isinstance(content, str):
                lang = _parse_008_language(content)
                if lang and lang not in languages:
                    languages.append(lang)
                break
        return languages

    def _extract_contributors(self, record: dict) -> List[str]:
        contributors = []
        existing_creators = set(self._extract_creators(record))
        for f in _find_fields(record, "700", "710", "711", "720"):
            content = f["content"]
            if isinstance(content, str):
                if content not in existing_creators:
                    contributors.append(content)
                continue
            if f["tag"] in ("700", "720"):
                a = _get_first_subfield(content, "a")
                if a:
                    val = _clean(a, " /:;.,")
                    if val not in existing_creators:
                        contributors.append(val)
            else:
                a = _get_first_subfield(content, "a")
                if a:
                    val = _clean(a, " /:;.,")
                    if val not in existing_creators:
                        contributors.append(val)
        return contributors

    def _extract_coverage(self, record: dict) -> List[str]:
        coverage = []
        for f in _find_fields(record, "260", "264"):
            content = f["content"]
            if isinstance(content, str):
                continue
            a = _get_first_subfield(content, "a")
            if a:
                coverage.append(_clean(a, " :;"))
        for f in _find_fields(record, "651"):
            content = f["content"]
            if isinstance(content, str):
                coverage.append(content)
                continue
            vals = _get_subfields(content, "a")
            coverage.extend(_clean(v, " /:;.,") for v in vals if v)
        return coverage

    def _extract_rights(self, record: dict) -> List[str]:
        rights = []
        for f in _find_fields(record, "506", "540", "542", "932"):
            content = f["content"]
            if isinstance(content, str):
                rights.append(content)
                continue
            vals = _get_subfields(content, "a")
            rights.extend(_clean(v) for v in vals if v)
        return rights

    def _extract_relations(self, record: dict) -> List[str]:
        relations = []
        for f in _find_fields(record, "490", "773", "776", "780", "785", "830"):
            content = f["content"]
            if isinstance(content, str):
                relations.append(content)
                continue
            if f["tag"] == "490":
                a = _get_first_subfield(content, "a")
                if a:
                    relations.append(_clean(a, " /:;."))
            elif f["tag"] == "773":
                t = _get_first_subfield(content, "t")
                if t:
                    parts = [t]
                    g = _get_first_subfield(content, "g")
                    if g:
                        parts.append(g)
                    relations.append(" : ".join(parts))
            elif f["tag"] == "830":
                a = _get_first_subfield(content, "a")
                if a:
                    relations.append(_clean(a, " /:;."))
            else:
                a = _get_first_subfield(content, "t")
                if a:
                    relations.append(_clean(a, " /:;."))
        return relations

    def _extract_sources(self, record: dict) -> List[str]:
        sources = []
        for f in _find_fields(record, "541", "786", "534"):
            content = f["content"]
            if isinstance(content, str):
                sources.append(content)
                continue
            if f["tag"] == "541":
                c = _get_first_subfield(content, "c")
                if c:
                    sources.append(_clean(c))
                a = _get_first_subfield(content, "a")
                if a:
                    sources.append(_clean(a))
            else:
                a = _get_first_subfield(content, "a")
                t = _get_first_subfield(content, "t")
                if t:
                    sources.append(_clean(t))
                if a and a != t:
                    sources.append(_clean(a))
        return sources
