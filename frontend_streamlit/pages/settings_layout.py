# frontend/pages/4_📝_Bien_tap.py
import os
import sys

import streamlit as st

_FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _FRONTEND_DIR not in sys.path:
    sys.path.insert(0, _FRONTEND_DIR)

from utils.marc_common import (
    LOCAL_FIELDS_NO_INDICATOR,
    as_subfield_list,
    collect_edited_fields,
    read_subfield,
    get_classification_code,
)
from utils.marc_worksheet import build_worksheet_filename, build_worksheet_pdf

st.set_page_config(page_title="Biên tập MARC21", layout="wide")

st.markdown("""
    <style>
    .table-header { font-size: 11px; font-weight: bold; color: #888888; text-transform: uppercase; margin-bottom: 5px; text-align: center; }
    .marc-tag { font-weight: bold; color: #4dabf7; padding-top: 8px; font-size: 15px; text-align: center; }
    div[data-testid="stVerticalBlock"] > div { padding-bottom: 0.1rem; }
    .image-container {
        border: 1px solid #373a40; border-radius: 8px; padding: 10px;
        background-color: #1a1b1e; max-height: 75vh; overflow-y: auto; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Biên tập MARC21")
st.caption("Chỉnh sửa siêu dữ liệu thư mục đối chiếu trực tiếp với ảnh tài liệu trong bộ nhớ")

if 'processed_batch' not in st.session_state or not st.session_state['processed_batch']:
    st.warning("⚠️ Chưa có dữ liệu lô tài liệu nào được xử lý. Vui lòng quay lại trang **Tải lên** trước!")
    st.stop()

file_list = list(st.session_state['processed_batch'].keys())
default_index = file_list.index(st.session_state.get('selected_file_name')) if st.session_state.get('selected_file_name') in file_list else 0

selected_file = st.selectbox("📂 Chọn tài liệu cần biên tập & kiểm tra:", file_list, index=default_index)
st.session_state['selected_file_name'] = selected_file

marc_data = st.session_state['processed_batch'][selected_file]['marc_data']
raw_data = st.session_state['processed_batch'][selected_file]['raw_data']
preview_image = st.session_state['processed_batch'][selected_file]['preview_image']

def _first_isbn(isbn_list):
    if isinstance(isbn_list, list) and isbn_list:
        first = isbn_list[0]
        return first.get("isbn_number", "N/A") if isinstance(first, dict) else str(first)
    return "N/A"

with st.container(border=True):
    col_icon, col_info, col_score = st.columns([1, 8, 1])
    with col_icon:
        st.markdown("<h1 style='text-align: center; margin: 0;'>📘</h1>", unsafe_allow_html=True)
    with col_info:
        title = raw_data.get("title_main", "Chưa có nhan đề")
        author = raw_data.get("author_personal_name", "Chưa rõ tác giả")
        isbn_text = _first_isbn(raw_data.get("isbn", []))
        publisher = raw_data.get("publisher_name", "N/A")
        year = raw_data.get("publication_year", "N/A")
        
        ddc = raw_data.get("ddc_code", "")
        nlm = raw_data.get("nlm_classification", [])
        nlm_code = nlm[0].get("code", "") if isinstance(nlm, list) and nlm else ""
        classification = get_classification_code(marc_data) or "N/A"

        st.subheader(title)
        st.write(f"**Tệp đang sửa:** {selected_file} | **Tác giả:** {author}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.caption(f"ISBN\n\n**{isbn_text}**")
        c2.caption(f"NXB\n\n**{publisher}**")
        c3.caption(f"Năm xuất bản\n\n**{year}**")
        c4.caption(f"Phân loại\n\n**{classification}**")
    with col_score:
        low_conf = (raw_data.get("extraction_metadata") or {}).get("low_confidence_fields") or []
        st.metric(label="Trường cần rà", value=len(low_conf),
                  help="Số trường AI tự đánh dấu độ tin cậy thấp.")

st.divider()

main_col_left, main_col_right = st.columns([45, 55])

with main_col_left:
    st.markdown("### 🖼️ Ảnh trích xuất thực tế")
    st.markdown('<div class="image-container">', unsafe_allow_html=True)
    if preview_image is not None:
        st.image(preview_image, caption=f"Trang bìa: {selected_file}", use_column_width=True)
    else:
        st.error("Không thể tự sinh ảnh xem trước cho file PDF này.")
    st.markdown('</div>', unsafe_allow_html=True)

with main_col_right:
    st.markdown("### 📝 Cấu trúc biên mục MARC21")
    
    hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([1.2, 1, 1, 1, 6.8])
    hcol1.markdown("<div class='table-header'>Thẻ</div>", unsafe_allow_html=True)
    hcol2.markdown("<div class='table-header'>I1</div>", unsafe_allow_html=True)
    hcol3.markdown("<div class='table-header'>I2</div>", unsafe_allow_html=True)
    hcol4.markdown("<div class='table-header'>$</div>", unsafe_allow_html=True)
    hcol5.markdown("<div class='table-header'>Nhãn / Giá trị dữ liệu</div>", unsafe_allow_html=True)
    
    fields = marc_data.get("fields", [])
    
    for idx, field_obj in enumerate(fields):
        tag = field_obj.get("tag", "")
        
        # TRƯỜNG HỢP 1: Control Fields (001, 005...)
        if "data" in field_obj:
            content = field_obj["data"]
            col1, col2, col3, col4, col5 = st.columns([1.2, 1, 1, 1, 6.8])
            with col1:
                st.markdown(f"<div class='marc-tag'>{tag}</div>", unsafe_allow_html=True)
            with col2:
                # [ĐÃ SỬA LỖI]: Gắn selected_file vào key để đảm bảo tính độc lập
                st.text_input("i1", value="", key=f"{selected_file}_i1_{tag}_{idx}", disabled=True, label_visibility="collapsed")
            with col3:
                st.text_input("i2", value="", key=f"{selected_file}_i2_{tag}_{idx}", disabled=True, label_visibility="collapsed")
            with col4:
                st.text_input("sub", value="", key=f"{selected_file}_sub_{tag}_{idx}", disabled=True, label_visibility="collapsed")
            with col5:
                st.text_input("val", value=str(content), key=f"{selected_file}_val_{tag}_{idx}", label_visibility="collapsed")
                
        # TRƯỜNG HỢP 2: Data Fields (040, 090, 245...)
        elif "subfields" in field_obj:
            ind1 = field_obj.get("ind1", " ")
            ind2 = field_obj.get("ind2", " ")
            raw_subfields = as_subfield_list(field_obj)

            no_indicator = tag in LOCAL_FIELDS_NO_INDICATOR

            for sub_idx, subfield in enumerate(raw_subfields):
                sub_code, sub_value = read_subfield(subfield)

                if not sub_code:
                    continue
                
                col1, col2, col3, col4, col5 = st.columns([1.2, 1, 1, 1, 6.8])
                with col1:
                    display_tag = tag if sub_idx == 0 else ""
                    st.markdown(f"<div class='marc-tag'>{display_tag}</div>", unsafe_allow_html=True)
                with col2:
                    # [ĐÃ SỬA LỖI]: Gắn selected_file vào key
                    st.text_input("i1", value="" if no_indicator else (ind1 if sub_idx == 0 else ""), key=f"{selected_file}_i1_{tag}_{idx}_{sub_idx}", disabled=no_indicator, label_visibility="collapsed")
                with col3:
                    st.text_input("i2", value="" if no_indicator else (ind2 if sub_idx == 0 else ""), key=f"{selected_file}_i2_{tag}_{idx}_{sub_idx}", disabled=no_indicator, label_visibility="collapsed")
                with col4:
                    st.text_input("sub", value=sub_code, key=f"{selected_file}_sub_{tag}_{idx}_{sub_idx}", label_visibility="collapsed")
                with col5:
                    st.text_input("val", value=sub_value, key=f"{selected_file}_val_{tag}_{idx}_{sub_idx}", label_visibility="collapsed")

# ==========================================
# 4. NÚT LƯU BẢN GHI ĐÃ ĐỒNG BỘ THEO FILE ĐANG CHỌN
# ==========================================
st.markdown("---")
col_space, col_pdf, col_btn = st.columns([6, 2, 2])

with col_btn:
    if st.button("💾 Lưu bản ghi dữ liệu", type="primary", use_container_width=True):
        # Dùng chung logic thu thập với nút xuất PDF -> hai bên không bao giờ lệch nhau
        updated_fields = collect_edited_fields(fields, selected_file, st.session_state)
        st.session_state['processed_batch'][selected_file]['marc_data']['fields'] = updated_fields
        st.success(f"🎉 Đã lưu các thay đổi của tệp [{selected_file}] thành công!")

with col_pdf:
    # Phiếu được dựng từ dữ liệu ĐANG hiển thị trên bảng, không phải từ bản đã lưu.
    # Nhờ vậy thủ thư quên bấm Lưu vẫn không in ra phiếu cũ.
    try:
        current_fields = collect_edited_fields(fields, selected_file, st.session_state)
        current_marc = dict(marc_data)
        current_marc["fields"] = current_fields

        pdf_bytes = build_worksheet_pdf(
            marc_data=current_marc,
            raw_data=raw_data,
            source_file=selected_file,
        )
        st.download_button(
            "📄 Xuất phiếu PDF",
            data=pdf_bytes,
            file_name=build_worksheet_filename(selected_file, current_marc),
            mime="application/pdf",
            use_container_width=True,
        )
    except FileNotFoundError as font_err:
        st.button("📄 Xuất phiếu PDF", disabled=True, use_container_width=True)
        st.error(f"Thiếu font in tiếng Việt.\n\n{font_err}")
    except Exception as pdf_err:
        st.button("📄 Xuất phiếu PDF", disabled=True, use_container_width=True)
        st.error(f"Không dựng được phiếu PDF: {pdf_err}")