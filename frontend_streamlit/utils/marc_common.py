# frontend/utils/marc_common.py
from typing import Any, Dict, List, Tuple

LOCAL_FIELDS_NO_INDICATOR = {"927"}

FIELD_LABELS: Dict[str, str] = {
    "001": "Số kiểm soát",
    "005": "Ngày giờ giao dịch",
    "008": "Dữ liệu độ dài cố định",
    "020": "ISBN",
    "022": "ISSN",
    "040": "Nguồn biên mục",
    "041": "Mã ngôn ngữ",
    "050": "Phân loại LC",
    "060": "Phân loại NLM",
    "090": "Ký hiệu xếp giá",
    "100": "Tác giả cá nhân",
    "110": "Tác giả tập thể",
    "245": "Nhan đề chính",
    "246": "Dạng nhan đề khác",
    "250": "Lần xuất bản",
    "260": "Địa chỉ xuất bản",
    "300": "Mô tả vật lý",
    "490": "Tùng thư",
    "500": "Phụ chú chung",
    "502": "Phụ chú luận văn",
    "504": "Phụ chú thư mục",
    "520": "Tóm tắt",
    "541": "Nguồn tiếp nhận",
    "650": "Chủ đề",
    "653": "Từ khóa tự do",
    "710": "Tác giả tập thể bổ sung",
    "720": "Tên chưa kiểm soát",
    "852": "Thông tin lưu giữ",
    "915": "Thông tin đào tạo (cục bộ)",
    "927": "Dạng tư liệu lưu thông (cục bộ)",
    "932": "Thỏa thuận toàn văn (cục bộ)",
}

MATERIAL_CODE_LABELS: Dict[str, str] = {
    "LA": "Luận án / Luận văn",
    "KL": "Khóa luận",
    "NCKH": "Báo cáo nghiên cứu khoa học",
    "GT": "Giáo trình",
    "TC": "Tạp chí",
    "TK": "Sách tham khảo",
    "CK": "Sách chuyên khảo",
    "BB": "Bài báo",
    "BGDT": "Bài giảng điện tử",
    "DPT": "Đa phương tiện",
    "HT": "Kỷ yếu hội thảo",
    "TCKT": "Tiêu chuẩn kỹ thuật",
    "VBSC": "Văn bản sưu tập",
}


def read_subfield(subfield: Any) -> Tuple[str, str]:
    """Đọc 1 subfield về cặp (code, value). Chấp nhận nhiều định dạng."""
    if isinstance(subfield, dict):
        if "code" in subfield:
            return str(subfield.get("code", "")), str(subfield.get("value", ""))
        if subfield:
            code = str(next(iter(subfield.keys())))
            value = str(next(iter(subfield.values())))
            return code, value
        return "", ""

    if isinstance(subfield, str):
        return "a", subfield

    return "", ""


def as_subfield_list(field_obj: Dict[str, Any]) -> List[Any]:
    """Lấy danh sách subfield, chấp nhận cả trường hợp bị lưu thành 1 dict."""
    raw = field_obj.get("subfields", [])
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return raw
    return []


def field_label(tag: str) -> str:
    """Nhãn tiếng Việt của trường; trả về chuỗi rỗng nếu chưa khai báo."""
    return FIELD_LABELS.get(tag, "")


def material_code_label(code: str) -> str:
    """Diễn giải mã dạng tư liệu (927 $a)."""
    return MATERIAL_CODE_LABELS.get(code.strip().upper(), "")


def _first_subfield_value(marc_data: Dict[str, Any], target_tag: str, target_code: str = "a") -> str:
    """Rút giá trị subfield đầu tiên khớp (tag, code) từ biểu ghi. '' nếu không có."""
    for field_obj in marc_data.get("fields", []):
        if field_obj.get("tag") != target_tag:
            continue
        for subfield in as_subfield_list(field_obj):
            code, value = read_subfield(subfield)
            if code == target_code and value.strip():
                return value.strip()
    return ""


def get_material_code(marc_data: Dict[str, Any]) -> str:
    """Rút mã dạng tư liệu từ trường 927 $a. Trả về '' nếu không có."""
    return _first_subfield_value(marc_data, "927", "a")


def get_classification_code(marc_data: Dict[str, Any]) -> str:
    """[VÁ F03] Rút mã phân loại để hiển thị, ưu tiên NLM (060) rồi LCC (050).

    Mã này do RAG sinh và nằm TRONG biểu ghi MARC, KHÔNG nằm trong dict thô của
    AI. Trang biên tập trước đây đọc nhầm từ raw_data nên luôn ra 'N/A'.
    Có thể ghép thêm $b (cutter) nếu có.
    """
    for tag in ("060", "050"):
        for field_obj in marc_data.get("fields", []):
            if field_obj.get("tag") != tag:
                continue
            code_a, code_b = "", ""
            for subfield in as_subfield_list(field_obj):
                code, value = read_subfield(subfield)
                if code == "a" and value.strip():
                    code_a = value.strip()
                elif code == "b" and value.strip():
                    code_b = value.strip()
            if code_a:
                return f"{code_a} {code_b}".strip()
    return ""


def collect_edited_fields(
    fields: List[Dict[str, Any]],
    selected_file: str,
    session_state: Any,
) -> List[Dict[str, Any]]:
    """Thu thập dữ liệu người dùng đang sửa trên bảng biên tập."""
    updated_fields: List[Dict[str, Any]] = []

    for idx, field_obj in enumerate(fields):
        tag = field_obj.get("tag", "")

        if "data" in field_obj:
            user_value = session_state.get(
                f"{selected_file}_val_{tag}_{idx}", field_obj["data"]
            )
            updated_fields.append({"tag": tag, "data": user_value})
            continue

        if "subfields" not in field_obj:
            continue

        raw_subfields = as_subfield_list(field_obj)
        no_indicator = tag in LOCAL_FIELDS_NO_INDICATOR

        if no_indicator:
            user_ind1 = field_obj.get("ind1", " ")
            user_ind2 = field_obj.get("ind2", " ")
        else:
            user_ind1 = session_state.get(
                f"{selected_file}_i1_{tag}_{idx}_0", field_obj.get("ind1", " ")
            )
            user_ind2 = session_state.get(
                f"{selected_file}_i2_{tag}_{idx}_0", field_obj.get("ind2", " ")
            )

        updated_subfields = []
        for sub_idx, subfield in enumerate(raw_subfields):
            orig_code, orig_value = read_subfield(subfield)
            user_sub_code = session_state.get(
                f"{selected_file}_sub_{tag}_{idx}_{sub_idx}", orig_code
            )
            user_sub_val = session_state.get(
                f"{selected_file}_val_{tag}_{idx}_{sub_idx}", orig_value
            )
            if user_sub_code:
                updated_subfields.append(
                    {"code": user_sub_code, "value": user_sub_val}
                )

        updated_fields.append(
            {
                "tag": tag,
                "ind1": user_ind1,
                "ind2": user_ind2,
                "subfields": updated_subfields,
            }
        )

    return updated_fields