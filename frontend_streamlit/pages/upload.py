# frontend/pages/2_📤_Tai_len.py
import streamlit as st
import requests
import pypdfium2 as pdfium
from PIL import Image
import io

st.title("Tải lên tài liệu (Hàng loạt)")
st.caption("Tải lên nhiều file PDF để trích xuất siêu dữ liệu thư mục bằng AI")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_files = st.file_uploader("Kéo & thả các tệp PDF vào đây", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"📚 Đã chọn **{len(uploaded_files)}** tệp sẵn sàng xử lý.")
        with st.expander("Xem danh sách tệp"):
            for f in uploaded_files:
                st.write(f"- {f.name}")

with col2:
    st.subheader("Cấu hình xử lý")
    doc_type_mapping = {
        "Luận văn / Luận án": "luan_van",
        "Báo cáo Nghiên cứu khoa học": "bao_cao_nckh",
        "Sách / Book": "sach",
        "Tạp chí": "tap_chi"
    }
    selected_type = st.radio("Loại tài liệu", list(doc_type_mapping.keys()))
    
    with st.expander("Siêu dữ liệu bổ sung (Tùy chọn)", expanded=True):
        additional_info = st.text_area("Ghi chú cho AI", placeholder="VD: Tài liệu mượn từ cơ sở 2...")

st.markdown("---")
if st.button("🚀 Bắt đầu trích xuất hàng loạt", type="primary", use_container_width=True):
    if not uploaded_files:
        st.error("⚠️ Bạn chưa tải lên file PDF nào!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        if 'processed_batch' not in st.session_state:
            st.session_state['processed_batch'] = {}
            
        success_count = 0

        for idx, file_obj in enumerate(uploaded_files):
            status_text.info(f"⏳ Đang xử lý ({idx + 1}/{len(uploaded_files)}): **{file_obj.name}**...")
            
            try:
                # 1. Gửi file sang Backend FastAPI xử lý dữ liệu chữ và MARC
                files = {"file": (file_obj.name, file_obj.getvalue(), "application/pdf")}
                data = {"doc_type": doc_type_mapping[selected_type], "additional_info": additional_info}
                
                BACKEND_URL = "http://localhost:8000/api/v1/process-document"
                response = requests.post(BACKEND_URL, files=files, data=data, timeout=120)  
                
                if response.status_code == 200:
                    result_data = response.json()
                    
                    # Khởi tạo vùng lưu trữ cho file này
                    st.session_state['processed_batch'][file_obj.name] = {
                        "marc_data": result_data.get("marc21_record", {}),
                        "raw_data": result_data.get("extracted_raw_data", {}),
                        "preview_image": None  # Nơi sẽ chứa ảnh chân thực
                    }
                    
                    # 2. [CỐT LÕI SỬA LỖI]: Tự render ảnh trang đầu ngay tại Frontend bằng pypdfium2
                    try:
                        pdf_bytes = file_obj.getvalue()
                        doc = pdfium.PdfDocument(pdf_bytes)
                        page = doc[0]  # Lấy trang đầu tiên (index 0)
                        bitmap = page.render(scale=2)  # Nhân đôi độ nét ảnh chống vỡ hạt
                        pil_img = bitmap.to_pil()
                        
                        # Cất tấm ảnh này vào vùng nhớ RAM của file tương ứng
                        st.session_state['processed_batch'][file_obj.name]["preview_image"] = pil_img
                    except Exception as img_err:
                        st.warning(f"⚠️ Không thể trích xuất ảnh xem trước cho {file_obj.name}: {img_err}")
                    
                    st.success(f"✅ Hoàn thành: {file_obj.name}")
                    success_count += 1
                else:
                    st.error(f"❌ Lỗi với {file_obj.name} (Mã {response.status_code})")
                    
            except requests.exceptions.ConnectionError:
                st.error("🚨 Không thể kết nối tới Backend! Hệ thống tạm dừng.")
                break
            except Exception as e:
                st.error(f"⚠️ Lỗi xử lý file {file_obj.name}: {e}")
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
        status_text.success(f"🎉 Đã xử lý xong lô dữ liệu! Thành công: {success_count}/{len(uploaded_files)} tệp.")
        
        # Đồng bộ biến mặc định để trang sửa không bị trống
        if st.session_state['processed_batch']:
            last_file_name = list(st.session_state['processed_batch'].keys())[-1]
            st.session_state['selected_file_name'] = last_file_name
            st.session_state['marc_data'] = st.session_state['processed_batch'][last_file_name]['marc_data']
            st.session_state['raw_data'] = st.session_state['processed_batch'][last_file_name]['raw_data']
            
            st.info("👉 Hãy chuyển sang tab **'Biên tập MARC21'** trên thanh điều hướng để xem kết quả đối chiếu hình ảnh!")