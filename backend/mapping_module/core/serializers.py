from typing import Any, Dict, List, Tuple

from pymarc import Field, Record, Subfield


class MARCFieldSerializer:
    """Chuyển đổi hai chiều giữa Field/Record pymarc và dict JSON."""

    # ==================================================================
    # Record/Field  ->  dict   (giữ nguyên như cũ)
    # ==================================================================
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

    # ==================================================================
    # [VÁ F04]  dict  ->  Record   (đảo ngược, phục vụ lưu bản đã sửa)
    # ==================================================================
    @staticmethod
    def _read_subfield_any(subfield: Any) -> Tuple[str, str]:
        """Đọc 1 subfield về (code, value), chấp nhận:
          - {"code": "a", "value": "x"}   (chuẩn hiện tại)
          - {"a": "x"}                    (dạng rút gọn)
          - "x"                           (chuỗi trần, vd 927 -> mặc định code 'a')
        """
        if isinstance(subfield, dict):
            if "code" in subfield:
                return str(subfield.get("code", "")).strip(), str(subfield.get("value", ""))
            if subfield:
                code = str(next(iter(subfield.keys()))).strip()
                value = str(next(iter(subfield.values())))
                return code, value
            return "", ""
        if isinstance(subfield, str):
            return "a", subfield
        return "", ""

    @staticmethod
    def record_from_dict(data: Dict[str, Any]) -> Record:
        """Dựng lại pymarc.Record từ dict {leader, fields} do người dùng sửa.

        Bỏ qua subfield rỗng (code trống). Chỉ thị rỗng được chuẩn hóa về ' '.
        """
        record = Record()

        leader = data.get("leader")
        if isinstance(leader, str) and len(leader) == 24:
            record.leader = leader

        for field_obj in data.get("fields", []):
            if not isinstance(field_obj, dict):
                continue
            tag = str(field_obj.get("tag", "")).strip()
            if not tag:
                continue

            # Trường điều khiển (001, 005, 008...) -> có khóa 'data'
            if "data" in field_obj:
                record.add_field(Field(tag=tag, data=str(field_obj.get("data", ""))))
                continue

            ind1 = (str(field_obj.get("ind1", " ")) or " ")[:1] or " "
            ind2 = (str(field_obj.get("ind2", " ")) or " ")[:1] or " "

            subfields: List[Subfield] = []
            for sf in field_obj.get("subfields", []):
                code, value = MARCFieldSerializer._read_subfield_any(sf)
                if code:
                    subfields.append(Subfield(code=code, value=value))

            if subfields:
                record.add_field(
                    Field(tag=tag, indicators=[ind1, ind2], subfields=subfields)
                )

        return record