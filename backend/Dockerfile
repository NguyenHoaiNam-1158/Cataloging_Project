# 1. Quy định phiên bản Python cụ thể là 3.12.3 bản tối giản (slim)
FROM python:3.12.3-slim

# 2. Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# 3. Cài đặt package manager uv toàn cục trong container
RUN pip install uv

# 4. Sao chép file cấu hình quản lý dependency vào trước để tận dụng Docker Cache
COPY pyproject.toml uv.lock ./

# 5. Sử dụng uv để cài đặt các package thẳng vào hệ thống của container
RUN uv pip install --system -r pyproject.toml

# 6. Sao chép toàn bộ mã nguồn còn lại từ máy host vào container
COPY . .

# 7. Khai báo cổng mạng (Port) ứng dụng sẽ lắng nghe
EXPOSE 8000

# 8. Lệnh khởi chạy ứng dụng khi container bắt đầu chạy
CMD ["python", "main.py"]