from typing import Any, Dict, List

from dublin_core_module.config.settings import settings
from dublin_core_module.core.base_mapper import BaseDCElementMapper
from dublin_core_module.utils.normalizers import to_text, pick_organization


class PublisherMapper(BaseDCElementMapper):
    
    element = "publisher"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        place = to_text(raw.get("place_of_publication"))
        publisher = to_text(raw.get("publisher_name")) or pick_organization(
            raw.get("corporate_name"), settings.CORPORATE_SEPARATOR
        )
        if publisher and place:
            return [f"{place} : {publisher}"]
        if publisher:
            return [publisher]
        if place:
            return [place]
        return []


class DateMapper(BaseDCElementMapper):
    
    element = "date"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        values: List[str] = []
        year = to_text(raw.get("publication_year"))
        copyright_year = to_text(raw.get("copyright_year"))
        if year:
            values.append(year)
        if copyright_year and copyright_year != year:
            values.append(f"© {copyright_year}")
        return values


class RelationMapper(BaseDCElementMapper):
    
    element = "relation"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        series = to_text(raw.get("series_statement"))
        if not series:
            return []
        volume = to_text(raw.get("series_volume"))
        return [f"{series} ; {volume}" if volume else series]


class CoverageMapper(BaseDCElementMapper):
    
    element = "coverage"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        country = to_text(raw.get("country_of_publication"))
        return [country] if country else []


class RightsMapper(BaseDCElementMapper):
    
    element = "rights"

    def map(self, raw: Dict[str, Any]) -> List[str]:
        copyright_year = to_text(raw.get("copyright_year"))
        return [f"Bản quyền {copyright_year}"] if copyright_year else []
