# Phân Hệ AI Agent (Isolated Processing Layer)

Module chịu trách nhiệm tiếp nhận, phân tích và thực thi các thuật toán AI phức tạp một cách độc lập, tách biệt hoàn toàn khỏi luồng xử lý API chính của Backend để đảm bảo hiệu năng tải của toàn hệ thống.

## Cấu Cấu Kỹ Thuật Nội Bộ

* **Môi trường chạy:** Python 3.12.3 (`python:3.12.3-slim`).
* **Cổng mạng (Port Exposed):** Hoạt động tại cổng `8001`.
* **Giao tiếp nội bộ:** Kết nối trực tiếp với Database (`project_db`) và Backend (`project_backend`) trong mạng ảo `project_network` của Docker.

## Tiến Trình Khởi Chạy (`main.py`)

Để đảm bảo container không bị rơi vào vòng lặp khởi động lại (`Crash Loop / Restarting status`) do bản chất Docker sẽ tự động tắt container khi không còn tiến trình chạy nền, file `main.py` của phân hệ hiện đang cấu hình một luồng duy trì vô hạn:

```python
import time

print("AI Agent is running and waiting for tasks...")

if __name__ == "__main__":
    while True:
        time.sleep(3600)  # Giữ tiến trình luôn thức để lắng nghe tác vụ từ mạng nội bộ
```

## Quản Lý Thư Viện dependencies

* Thư viện cài đặt sẵn mặc định: `pydantic` (Quản lý cấu trúc dữ liệu mô hình).
* **Quy trình thêm thư viện:** Di chuyển vào thư mục và thực hiện lệnh thông qua công cụ quản lý package toàn cục:
  ```bash
  cd ai-agent
  uv add <tên_thư_viện>
  cd ..
  ```
  *(File `pyproject.toml` và file khóa phiên bản mã băm thư viện con `uv.lock` sẽ tự động được đồng bộ và cập nhật chính xác).*