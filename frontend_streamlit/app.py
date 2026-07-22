# frontend/app.py
import streamlit as st

# 1. Cấu hình trang toàn cục (Phải đặt ở dòng đầu tiên)
st.set_page_config(
    page_title="UMP Library AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Xây dựng Sidebar giống Figma
with st.sidebar:
    st.markdown("### 🎓 UMP Library AI")
    st.caption("Đại học Y Dược")
    st.divider()
    
    st.markdown("**ĐIỀU HƯỚNG**")
    # Streamlit tự động chèn các trang từ folder 'pages/' vào đây
    
    st.markdown("<br>" * 15, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("🌐 **Ngôn ngữ:** VN | EN")
    st.markdown("👤 **Thủ thư**\n\nlibrarian@ump.edu.vn")

# 3. Trang chào mừng (Khi user vừa mở App)
st.title("Chào mừng đến với Hệ thống Biên mục AI")
st.info("👈 Vui lòng chọn một chức năng từ thanh điều hướng bên trái để bắt đầu.")