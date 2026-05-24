# Hướng Dẫn Cài Đặt & Vận Hành Hệ Thống

Tài liệu này cung cấp các bước chi tiết để khởi tạo môi trường, cài đặt dependencies và vận hành hệ thống thông qua Docker. Kiến trúc dự án được thiết kế theo mô hình phân tán, chia thành các module độc lập: Frontend (UI), Backend (API/Services/Models), AI Agent và Database.

## 1. Yêu cầu tiền quyết (Prerequisites)

Hệ thống được tối ưu để chạy ổn định nhất trên môi trường **Linux** hoặc **WSL (Windows Subsystem for Linux)**. Trước khi bắt đầu, hãy đảm bảo hệ thống của bạn đã cài đặt sẵn các công cụ sau:

* **Docker & Docker Compose:** Nền tảng cốt lõi để build và chạy các container.
* **Git:** Để quản lý mã nguồn và luồng làm việc trên các nhánh (branches).
* **uv (Tùy chọn):** Khuyến nghị cài đặt để quản lý môi trường và test code Backend/AI Agent nhanh ở local trước khi đưa vào Docker.

---

## 2. Thiết lập dự án ban đầu

### Bước 2.1: Clone mã nguồn
Tải repository về máy local và di chuyển vào thư mục gốc của dự án:
```bash
git clone <URL_CUA_REPO>
cd project
```

**Chiến lược rẽ nhánh (Git Branching):**
Dự án áp dụng mô hình phát triển tách biệt theo module. Vui lòng `checkout` sang đúng nhánh làm việc tương ứng trước khi tiến hành code:
* `feature/ui`: Nhánh phát triển giao diện (Frontend).
* `feature/backend`: Nhánh phát triển logic server (Models, Services, Prompts).
* `feature/ai-agent`: Nhánh phát triển các tác vụ AI độc lập.
* `feature/database`: Nhánh quản lý schema cơ sở dữ liệu và cấu hình `docker-compose.yml`.

### Bước 2.2: Cấu hình biến môi trường (.env)
File `.env` chứa các thông tin bảo mật và cấu hình hệ thống, do đó không được đẩy lên Github (đã nằm trong `.gitignore`). Bạn cần tự khởi tạo file này từ template có sẵn:

```bash
cp .env.example .env
```

Mở file `.env` và thiết lập các thông số môi trường. Dưới đây là một số cấu hình mẫu:
```env
# Database Credentials
POSTGRES_USER=admin
POSTGRES_PASSWORD=secretpassword
POSTGRES_DB=app_database

# System & Crawling Configuration
SYSTEM_TIMEOUT=60
CRAWL_CATEGORIES=coffee,restaurant
```

---

## 3. Khởi chạy hệ thống với Docker

Toàn bộ các dịch vụ đã được định nghĩa trong file `docker-compose.yml` tại thư mục gốc. 

### Bước 3.1: Build và chạy các container
Sử dụng lệnh sau để tiến hành build các image (nếu có thay đổi ở `Dockerfile` hoặc `pyproject.toml`) và chạy các dịch vụ ngầm (detached mode):

```bash
docker compose up --build -d
```
> **Lưu ý:** Quá trình build lần đầu cho Backend và AI Agent có thể cần thời gian để tải base image (`python:3.12.3-slim`) và phân giải dependencies qua `uv`. Nhờ cơ chế Docker Layer Cache, các lần build tiếp theo khi thay đổi code logic sẽ diễn ra gần như tức thì.

### Bước 3.2: Kiểm tra trạng thái hệ thống
Để liệt kê danh sách các container đang hoạt động:
```bash
docker compose ps
```

Để theo dõi log của hệ thống nhằm kiểm tra lỗi hoặc tiến trình:
```bash
# Xem log của toàn bộ các service
docker compose logs -f

# Xem log riêng lẻ của một service (ví dụ: backend)
docker compose logs -f backend_service
```

---

## 4. Cấu hình bổ sung bên trong Container

Đối với các tác vụ thu thập dữ liệu tự động hoặc chạy bot, bạn có thể cần cài đặt thêm các trình duyệt nhân (browser binaries) trực tiếp vào bên trong container sau khi quá trình build hoàn tất. 

Thao tác cài đặt qua shell của container Backend (hoặc AI Agent):
```bash
# Truy cập vào shell của container
docker compose exec backend_service /bin/bash

# Thực thi lệnh cài đặt browser engine (ví dụ với Playwright)
uv run playwright install chromium
```

---

## 5. Quy hoạch Port mạng (Port Mapping)

Khi các container đã chạy thành công, các dịch vụ sẽ giao tiếp nội bộ và mở port ra máy host (`localhost`) theo quy chuẩn sau:

| Module | Tên Service | Cổng Mở (Port) | Chức năng |
| :--- | :--- | :--- | :--- |
| **Frontend** | `frontend_service` | `3000` | Cung cấp giao diện người dùng |
| **Backend** | `backend_service` | `8000` | Xử lý API, Services và tương tác Database Models |
| **AI Agent** | `ai_agent_service` | `8001` | Chạy logic AI, giao tiếp nội bộ với Backend |
| **Database** | `db_service` | `5432` / `27017` | Quản lý hệ quản trị CSDL (PostgreSQL / MongoDB) |

---

## 6. Dừng và dọn dẹp hệ thống

Khi cần giải phóng tài nguyên CPU/RAM hoặc thiết lập lại từ đầu, hãy sử dụng các lệnh dưới đây.

```bash
# Tắt hệ thống container (Dữ liệu database vẫn được bảo toàn trong volume)
docker compose down

# Tắt hệ thống và XÓA TOÀN BỘ volumes chứa dữ liệu (Cảnh báo: Dữ liệu DB sẽ mất)
docker compose down -v
```