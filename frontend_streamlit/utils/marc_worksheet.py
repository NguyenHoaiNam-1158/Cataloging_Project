# frontend/utils/marc_worksheet.py
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fpdf import FPDF
from fpdf.enums import Align

from utils.marc_common import (
    LOCAL_FIELDS_NO_INDICATOR,
    as_subfield_list,
    field_label,
    get_material_code,
    material_code_label,
    read_subfield,
)

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
_FONT_REGULAR = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
_FONT_BOLD = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")

_FALLBACK_FONTS = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

FONT_NAME = "DejaVu"

COL_TAG = 14
COL_IND = 10
COL_SUB = 10
COL_LABEL = 40
COL_VALUE = 106

_COLOR_HEADER_BG = (232, 236, 242)
_COLOR_BORDER = (150, 158, 170)
_COLOR_MUTED = (110, 116, 128)
_COLOR_LOCAL_BG = (255, 248, 225) 


def _resolve_font_paths() -> tuple:
    """Tìm cặp font (regular, bold). Ưu tiên font đóng gói trong repo."""
    if os.path.exists(_FONT_REGULAR) and os.path.exists(_FONT_BOLD):
        return _FONT_REGULAR, _FONT_BOLD

    for regular, bold in _FALLBACK_FONTS:
        if os.path.exists(regular) and os.path.exists(bold):
            return regular, bold

    raise FileNotFoundError(
        "Không tìm thấy font Unicode để in tiếng Việt.\n"
        f"Hãy chép DejaVuSans.ttf và DejaVuSans-Bold.ttf vào: {os.path.abspath(_FONT_DIR)}\n"
        "Tải tại: https://dejavu-fonts.github.io/"
    )


class _WorksheetPDF(FPDF):
    """FPDF có sẵn header/footer cho phiếu biên mục."""

    def __init__(self, doc_title: str = "", org_name: str = ""):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.doc_title = doc_title
        self.org_name = org_name
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(auto=True, margin=18)

        regular, bold = _resolve_font_paths()
        self.add_font(FONT_NAME, "", regular)
        self.add_font(FONT_NAME, "B", bold)

    def header(self):
        self.set_font(FONT_NAME, "B", 8)
        self.set_text_color(*_COLOR_MUTED)
        self.cell(0, 4, self.org_name, align=Align.C, new_x="LMARGIN", new_y="NEXT")

        self.set_font(FONT_NAME, "B", 13)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, "PHIẾU BIÊN MỤC MARC21", align=Align.C, new_x="LMARGIN", new_y="NEXT")

        self.set_draw_color(*_COLOR_BORDER)
        self.line(10, self.get_y() + 1, 200, self.get_y() + 1)
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font(FONT_NAME, "", 7)
        self.set_text_color(*_COLOR_MUTED)
        stamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 4, f"In ngày {stamp}", align=Align.L)
        self.cell(0, 4, f"Trang {self.page_no()}/{{nb}}", align=Align.R)


def _fit_text(pdf: FPDF, text: str, width: float) -> str:
    if not text:
        return ""
    if pdf.get_string_width(text) <= width:
        return text

    ellipsis = "…"
    limit = width - pdf.get_string_width(ellipsis)
    cut = text
    while cut and pdf.get_string_width(cut) > limit:
        cut = cut[:-1]
    return (cut.rstrip() + ellipsis) if cut else ellipsis


def _info_row(pdf: FPDF, label: str, value: str, width: float):
    x, y = pdf.get_x(), pdf.get_y()
    inner = width - 2  

    pdf.set_font(FONT_NAME, "", 7)
    pdf.set_text_color(*_COLOR_MUTED)
    pdf.cell(inner, 4, _fit_text(pdf, label, inner), new_x="LEFT", new_y="NEXT")

    pdf.set_font(FONT_NAME, "B", 8.5)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(inner, 5, _fit_text(pdf, value or "—", inner), new_x="LEFT", new_y="NEXT")

    pdf.set_xy(x + width, y)


def _draw_summary(pdf: FPDF, marc_data: Dict[str, Any], raw_data: Dict[str, Any],
                  source_file: str):
    title = (raw_data.get("title_main") or "Chưa có nhan đề").strip()
    author = (raw_data.get("author_personal_name") or "Chưa rõ tác giả").strip()

    pdf.set_font(FONT_NAME, "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 5.5, title, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(FONT_NAME, "", 8.5)
    pdf.set_text_color(*_COLOR_MUTED)
    pdf.multi_cell(0, 4.5, f"Tác giả: {author}    |    Tệp nguồn: {source_file}",
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    code_927 = get_material_code(marc_data)
    label_927 = material_code_label(code_927)
    text_927 = f"{code_927} — {label_927}" if label_927 else (code_927 or "—")

    isbn_list = raw_data.get("isbn") or []
    if isinstance(isbn_list, list) and isbn_list:
        first = isbn_list[0]
        isbn_text = first.get("isbn_number", "—") if isinstance(first, dict) else str(first)
    else:
        isbn_text = "—"

    cells = [
        ("DẠNG TƯ LIỆU (927)", text_927),
        ("NĂM XUẤT BẢN", str(raw_data.get("publication_year") or "—")),
        ("ISBN", isbn_text),
        ("NHÀ XUẤT BẢN", str(raw_data.get("publisher_name") or "—")),
    ]

    y_start = pdf.get_y()
    pdf.set_fill_color(*_COLOR_HEADER_BG)
    pdf.rect(10, y_start, 190, 11, style="F")
    pdf.set_xy(12, y_start + 1)

    width = 186 / len(cells)
    for label, value in cells:
        _info_row(pdf, label, str(value), width)

    pdf.set_y(y_start + 11)
    pdf.ln(3)


def _draw_table_header(pdf: FPDF):
    pdf.set_font(FONT_NAME, "B", 7.5)
    pdf.set_fill_color(*_COLOR_HEADER_BG)
    pdf.set_draw_color(*_COLOR_BORDER)
    pdf.set_text_color(*_COLOR_MUTED)

    for width, text in [
        (COL_TAG, "THẺ"), (COL_IND, "I1"), (COL_IND, "I2"), (COL_SUB, "$"),
        (COL_LABEL, "TÊN TRƯỜNG"), (COL_VALUE, "GIÁ TRỊ DỮ LIỆU"),
    ]:
        pdf.cell(width, 6, text, border=1, align=Align.C, fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)


_LINE_H = 4          # chiều cao 1 dòng chữ trong cột giá trị (mm)
_ROW_PAD = 1.5       # đệm trên/dưới trong ô
_MIN_ROW = 5.5       # chiều cao tối thiểu 1 dòng


def _value_lines(pdf: FPDF, value: str) -> List[str]:
    pdf.set_font(FONT_NAME, "", 8)
    return list(
        pdf.multi_cell(COL_VALUE - 2, _LINE_H, value, dry_run=True, output="LINES")
    ) or [""]


def _draw_row(pdf: FPDF, tag: str, ind1: str, ind2: str, code: str,
              label: str, value: str, highlight: bool = False):
    lines = _value_lines(pdf, value)
    first_chunk = True

    while lines:
        available = pdf.page_break_trigger - pdf.get_y()

        if available < _MIN_ROW + _ROW_PAD:
            pdf.add_page()
            _draw_table_header(pdf)
            available = pdf.page_break_trigger - pdf.get_y()

        max_lines = max(1, int((available - _ROW_PAD) // _LINE_H))
        chunk, lines = lines[:max_lines], lines[max_lines:]
        height = max(_MIN_ROW, len(chunk) * _LINE_H + _ROW_PAD)

        _draw_row_chunk(
            pdf,
            tag if first_chunk else "",
            ind1 if first_chunk else "",
            ind2 if first_chunk else "",
            code if first_chunk else "",
            label if first_chunk else "",
            "\n".join(chunk),
            height,
            highlight,
        )
        first_chunk = False


def _draw_row_chunk(pdf: FPDF, tag: str, ind1: str, ind2: str, code: str,
                    label: str, value: str, height: float, highlight: bool):
    x_start, y_start = pdf.get_x(), pdf.get_y()

    if highlight:
        pdf.set_fill_color(*_COLOR_LOCAL_BG)
    fill = bool(highlight)

    pdf.set_draw_color(*_COLOR_BORDER)

    pdf.set_font(FONT_NAME, "B", 8.5)
    pdf.cell(COL_TAG, height, tag, border=1, align=Align.C, fill=fill)

    pdf.set_font(FONT_NAME, "", 8)
    pdf.cell(COL_IND, height, ind1, border=1, align=Align.C, fill=fill)
    pdf.cell(COL_IND, height, ind2, border=1, align=Align.C, fill=fill)
    pdf.cell(COL_SUB, height, code, border=1, align=Align.C, fill=fill)

    pdf.set_font(FONT_NAME, "", 7.5)
    pdf.set_text_color(*_COLOR_MUTED)
    pdf.cell(COL_LABEL, height, _fit_text(pdf, label, COL_LABEL - 2),
             border=1, align=Align.L, fill=fill)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(FONT_NAME, "", 8)
    x_value = x_start + COL_TAG + COL_IND * 2 + COL_SUB + COL_LABEL
    pdf.rect(x_value, y_start, COL_VALUE, height, style="DF" if fill else "D")

    auto, margin = pdf.auto_page_break, pdf.b_margin
    pdf.set_auto_page_break(False)
    pdf.set_xy(x_value + 1, y_start + 0.75)
    pdf.multi_cell(COL_VALUE - 2, _LINE_H, value, border=0, align=Align.L)
    pdf.set_auto_page_break(auto, margin)

    pdf.set_xy(x_start, y_start + height)


def build_worksheet_pdf(
    marc_data: Dict[str, Any],
    raw_data: Optional[Dict[str, Any]] = None,
    source_file: str = "",
    org_name: str = "ĐẠI HỌC Y DƯỢC TP. HỒ CHÍ MINH — THƯ VIỆN",
) -> bytes:
    raw_data = raw_data or {}
    fields: List[Dict[str, Any]] = marc_data.get("fields", [])

    pdf = _WorksheetPDF(org_name=org_name)
    pdf.set_title(f"Phiếu biên mục — {source_file}" if source_file else "Phiếu biên mục")
    pdf.alias_nb_pages()
    pdf.add_page()

    _draw_summary(pdf, marc_data, raw_data, source_file)
    _draw_table_header(pdf)

    for field_obj in fields:
        tag = str(field_obj.get("tag", ""))
        label = field_label(tag)
        highlight = tag in LOCAL_FIELDS_NO_INDICATOR

        if "data" in field_obj:
            _draw_row(pdf, tag, "", "", "", label, str(field_obj.get("data", "")),
                      highlight=highlight)
            continue

        raw_subfields = as_subfield_list(field_obj)
        no_indicator = tag in LOCAL_FIELDS_NO_INDICATOR
        ind1 = "" if no_indicator else str(field_obj.get("ind1", " "))
        ind2 = "" if no_indicator else str(field_obj.get("ind2", " "))

        for sub_idx, subfield in enumerate(raw_subfields):
            code, value = read_subfield(subfield)
            if not code:
                continue
            # Tag và chỉ thị chỉ in ở dòng subfield đầu tiên, giống trên web
            _draw_row(
                pdf,
                tag if sub_idx == 0 else "",
                ind1 if sub_idx == 0 else "",
                ind2 if sub_idx == 0 else "",
                code,
                label if sub_idx == 0 else "",
                value,
                highlight=highlight,
            )

    return bytes(pdf.output())


def build_worksheet_filename(source_file: str, marc_data: Dict[str, Any]) -> str:
    base = os.path.splitext(source_file)[0] if source_file else "bien_muc"
    base = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in base)
    code = get_material_code(marc_data)
    prefix = f"{code}_" if code else ""
    return f"{prefix}{base}_phieu.pdf"
