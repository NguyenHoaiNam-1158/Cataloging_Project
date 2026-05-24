# Hướng Dẫn Cài Đặt & Vận Hành Hệ Thống (Build Guide)

Tài liệu này hướng dẫn chi tiết các bước thiết lập, xây dựng cấu hình và khởi chạy toàn bộ 4 phân hệ dịch vụ của dự án trên môi trường Local (Khuyến nghị sử dụng **Linux** hoặc **WSL**).

## 1. Chuẩn Bị Biến Môi Trường (.env)

Tại thư mục gốc của dự án, tiến hành sao chép file cấu hình mẫu để tạo file cấu hình thực tế:
```bash
cp .env.example .env
```

Mở file `.env` vừa tạo và kiểm tra/điền các thông số bắt buộc cho luồng xử lý thu thập dữ liệu và thông tin kết nối Cơ sở dữ liệu:
```env
# Cấu hình Cơ sở dữ liệu Postgres
POSTGRES_USER=admin
POSTGRES_PASSWORD=secretpassword
POSTGRES_DB=app_database

# Biến cấu hình bắt buộc cho luồng xử lý dữ liệu
CRAWL_CATEGORIES=coffee,restaurant
SYSTEM_TIMEOUT=60
```

## 2. Khởi Chạy Hệ Thống Bằng Docker Compose

Dự án tuân thủ chuẩn mã nguồn Docker Compose V2 mới nhất (Dòng khai báo thuộc tính `version` lỗi thời đã được loại bỏ khỏi file cấu hình để tránh xung đột hệ thống).

Để tiến hành build toàn bộ các Dockerfile và kích hoạt dịch vụ chạy ngầm, thực thi lệnh:
```bash
docker compose up --build -d
```

Kiểm tra trạng thái hoạt động của các container để đảm bảo không có phân hệ nào bị crash đột ngột:
```bash
docker compose ps
```
Hệ thống khởi chạy thành công khi tất cả 4 dịch vụ sau đều hiển thị trạng thái `Up`:
* `project_db` (PostgreSQL - Cổng `5432`)
* `project_backend` (FastAPI Server - Cổng `8000`)
* `project_ai_agent` (AI Process Loop - Cổng `8001`)
* `project_frontend` (UI Stub Node - Cổng `3000`)

## 3. Cài Đặt Trình Duyệt Phụ Trợ Cho Luồng Cào Dữ Liệu

Vì Module Backend chịu trách nhiệm thực thi các đường ống thu thập dữ liệu tự động (Scraping/Crawling Pipelines) sử dụng thư viện Playwright, bạn cần cài đặt thêm nhân trình duyệt Chromium trực tiếp vào bên trong container sau khi hệ thống đã ở trạng thái chạy ổn định (`Up`):

```bash
docker compose exec backend uv run playwright install chromium
```
*Lưu ý: Thao tác này bắt buộc phải thực hiện ở lần đầu tiên thiết lập hệ thống hoặc sau khi xóa hoàn toàn các layer cache của Docker.*

## 4. Kiểm Tra Kết Nối API & Điều Hướng Port

Sau khi hệ thống khởi chạy, bạn có thể kiểm tra trực tiếp trạng thái phản hồi của API Backend bằng cách truy cập vào giao diện Swagger UI tự động tại địa chỉ:
👉 **http://localhost:8000/docs**

## 5. Dừng Hệ Thống

Để tắt các container và giải phóng tài nguyên RAM/CPU cho máy tính:
```bash
# Dừng container (Giữ lại dữ liệu Database trong Volume cứng)
docker compose down

# Dừng container và XÓA SẠCH toàn bộ dữ liệu Database làm lại từ đầu
docker compose down -v
```