from typing import Any, List, Optional


def to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        text = to_text(value)
        return [text] if text else []

    out: List[str] = []
    for item in value:
        if isinstance(item, dict):
            number = to_text(item.get("isbn_number"))
            if number:
                out.append(number)
        else:
            text = to_text(item)
            if text:
                out.append(text)
    return out


def pick_organization(corporate_name: Any, separator: str = "|") -> Optional[str]:
    text = to_text(corporate_name)
    if not text:
        return None
    parts = [p.strip() for p in text.split(separator) if p.strip()]
    if not parts:
        return None
    for part in parts:
        upper = part.upper()
        if "ĐẠI HỌC" in upper or "TRƯỜNG" in upper:
            return part
    return parts[0]
