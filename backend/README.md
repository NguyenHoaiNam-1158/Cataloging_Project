# Phân Hệ Backend (API & Services Layer)

Module này đóng vai trò đảm nhiệm lớp **Service** và lớp **Model** trong kiến trúc kiến tạo SVM của hệ thống. Chịu trách nhiệm cung cấp các đầu mút HTTP API, xử lý kết nối Cơ sở dữ liệu và thực thi các script thu thập dữ liệu tự động từ các nền tảng Web.

## Cấu Cấu Kỹ Thuật Nội Bộ

* **Môi trường chạy:** Python 3.12.3 biên dịch trên Base Image tối giản `python:3.12.3-slim` nhằm tối ưu hóa dung lượng container xuống mức thấp nhất (~200MB - 350MB).
* **Cổng mạng (Port Exposed):** Lắng nghe kết nối tại cổng `8000`.
* **Thành phần cốt lõi:**
  * `main.py`: Khởi tạo ứng dụng FastAPI và kích hoạt tiến trình chạy liên tục thông qua ASGI Server là `uvicorn`. Điều này ngăn chặn lỗi container bị tắt đột ngột do hết tiến trình.
  * `prompts/`: Thư mục chuyên biệt lưu trữ và quản lý cấu trúc các câu lệnh Prompt được nạp vào mô hình AI.

## Quản Lý Thư Viện dependencies (`uv`)

Phân hệ sử dụng hệ sinh thái `pyproject.toml` và file khóa phiên bản `uv.lock`. Các thư viện chính đã được cài đặt bao gồm:
* `fastapi` & `uvicorn`: Tạo dựng và vận hành APIs.
* `pydantic`: Chuẩn hóa dữ liệu đầu vào/đầu ra.
* `playwright`: Công cụ điều khiển trình duyệt không giao diện (headless browser) phục vụ cho tác vụ cào dữ liệu thô.

**Quy trình thêm một thư viện mới:**
Tuyệt đối không sửa file bằng tay hoặc tạo file rỗng. Di chuyển vào thư mục backend và chạy lệnh:
```bash
cd backend
uv add <tên_thư_viện>
cd ..
```
Sau đó chạy lệnh `docker compose up --build -d` ngoài thư mục gốc để cập nhật vùng cài đặt của container.