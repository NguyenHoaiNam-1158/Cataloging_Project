from pymarc import Subfield
from typing import List

def add_end_period(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    return text if text.endswith('.') else f"{text}."

def safe_isbd_punctuation(subfields: List[Subfield]) -> List[Subfield]:
    """Đảm bảo phân cách ISBD giữa các trường con chính xác."""
    for i in range(len(subfields)):
        val = subfields[i].value.strip()
        if i == len(subfields) - 1:
            if not val.endswith('.'):
                val += '.'
        else:
            if not val.endswith(('.', ',', '-')):
                val += ','
        subfields[i] = Subfield(subfields[i].code, val)
    return subfields