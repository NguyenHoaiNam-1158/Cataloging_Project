from typing import List

from pymarc import Field, Subfield

from mapping_module.core.base_mapper import BaseFieldMapper
from mapping_module.core.models import RawExtractionData
from mapping_module.utils.marc_punctuation import add_end_period


class PublicationPhysicalMapper(BaseFieldMapper):
    def can_handle(self, raw_data: RawExtractionData) -> bool:
        return bool(
            raw_data.edition_statement
            or raw_data.place_of_publication
            or raw_data.publisher_name
            or raw_data.publication_year
            or raw_data.extent
            or raw_data.physical_details
            or raw_data.dimensions
            or raw_data.series_statement
            or raw_data.series_volume
        )

    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        fields: List[Field] = []

        if raw_data.edition_statement:
            fields.append(
                Field(
                    tag="250",
                    indicators=[" ", " "],
                    subfields=[Subfield("a", add_end_period(raw_data.edition_statement))],
                )
            )

        if raw_data.place_of_publication or raw_data.publisher_name or raw_data.publication_year:
            subfields = []
            if raw_data.place_of_publication:
                subfields.append(Subfield("a", raw_data.place_of_publication.strip()))
            if raw_data.publisher_name:
                subfields.append(Subfield("b", raw_data.publisher_name.strip()))
            if raw_data.publication_year:
                subfields.append(Subfield("c", raw_data.publication_year.strip()))
            fields.append(Field(tag="260", indicators=[" ", " "], subfields=subfields))

        if raw_data.extent or raw_data.physical_details or raw_data.dimensions:
            subfields = []
            if raw_data.extent:
                subfields.append(Subfield("a", raw_data.extent.strip()))
            if raw_data.physical_details:
                subfields.append(Subfield("b", raw_data.physical_details.strip()))
            if raw_data.dimensions:
                subfields.append(Subfield("c", raw_data.dimensions.strip()))
            fields.append(Field(tag="300", indicators=[" ", " "], subfields=subfields))

        if raw_data.series_statement:
            series_subfields = [Subfield("a", raw_data.series_statement.strip())]
            if raw_data.series_volume:
                series_subfields.append(Subfield("v", raw_data.series_volume.strip()))
            fields.append(Field(tag="490", indicators=["0", " "], subfields=series_subfields))

        return fields
