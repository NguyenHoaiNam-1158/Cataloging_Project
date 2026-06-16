from typing import List

from pymarc import Field, Subfield

from mapping_module.core.base_mapper import BaseFieldMapper
from mapping_module.core.models import RawExtractionData


class IdentifierMapper(BaseFieldMapper):
    def can_handle(self, raw_data: RawExtractionData) -> bool:
        return bool(raw_data.isbn or raw_data.issn)

    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        fields: List[Field] = []

        for isbn in raw_data.isbn or []:
            if isbn and isbn.isbn_number:
                subfields = [Subfield("a", isbn.isbn_number.strip())]
                if isbn.price:
                    subfields.append(Subfield("c", isbn.price.strip()))
                fields.append(Field(tag="020", indicators=[" ", " "], subfields=subfields))

        if raw_data.issn:
            fields.append(
                Field(
                    tag="022",
                    indicators=[" ", "0"],
                    subfields=[Subfield("a", raw_data.issn.strip())],
                )
            )

        return fields
