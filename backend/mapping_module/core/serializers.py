from typing import Any, Dict, List

from pymarc import Field


class MARCFieldSerializer:
    """Chuyên biến Field pymarc sang dict JSON."""

    @staticmethod
    def field_to_dict(field: Field) -> Dict[str, Any]:
        """Chuyển đổi trường MARC sang dict."""
        if field.is_control_field():
            return {"tag": field.tag, "data": field.data}

        subfields = []
        raw_subfields = getattr(field, "subfields", [])

        if raw_subfields and hasattr(raw_subfields[0], "code"):
            for subfield in raw_subfields:
                if field.tag == "927":
                    subfields.append(subfield.value)
                else:
                    subfields.append({"code": subfield.code, "value": subfield.value})
        else:
            for idx in range(0, len(raw_subfields), 2):
                code = raw_subfields[idx]
                value = raw_subfields[idx + 1] if idx + 1 < len(raw_subfields) else None
                if field.tag == "927":
                    subfields.append(value)
                else:
                    subfield_entry = {"code": code}
                    if value is not None:
                        subfield_entry["value"] = value
                    subfields.append(subfield_entry)

        return {
            "tag": field.tag,
            "ind1": field.indicator1,
            "ind2": field.indicator2,
            "subfields": subfields,
        }

    @staticmethod
    def record_to_dict(record) -> Dict[str, Any]:
        """Chuyển đổi Record MARC sang dict."""
        leader_value = record.leader
        if hasattr(leader_value, "__str__"):
            leader_value = str(leader_value)

        fields = sorted(record.fields, key=lambda field: field.tag)
        return {
            "leader": leader_value,
            "fields": [MARCFieldSerializer.field_to_dict(field) for field in fields],
        }
