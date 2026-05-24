# Hệ Thống Tự Động Thu Thập & Phân Tích Dữ Liệu (AI-Agent Pipeline)

Dự án này là một hệ thống phân tán được thiết kế theo kiến trúc Service - View - Model (SVM), tích hợp AI Agent để tự động hóa các tác vụ trích xuất và xử lý dữ liệu từ các nền tảng trực tuyến.

## Kiến Trúc Hệ Thống

Dự án được chia thành 4 module hoạt động hoàn toàn độc lập thông qua Docker Network:
* **Frontend (`/frontend`):** Giao diện người dùng (UI).
* **Backend (`/backend`):** Hệ thống API cốt lõi, quản lý Services, Models và xử lý các kịch bản thu thập dữ liệu (crawling).
* **AI Agent (`/ai-agent`):** Module xử lý logic AI độc lập, tự động hóa các luồng trích xuất dữ liệu phức tạp.
* **Database:** Cơ sở dữ liệu lưu trữ thông tin (PostgreSQL/MongoDB).

## Công Nghệ Sử Dụng (Tech Stack)

* **Ngôn ngữ chính:** Python 3.12.3
* **Quản lý Package & Môi trường:** [uv](https://github.com/astral-sh/uv) (Nhanh, an toàn, thay thế pip/virtualenv)
* **Containerization:** Docker & Docker Compose
* **Thư viện AI/Crawling Core:** Crawl4AI, Playwright, BeautifulSoup, Pydantic, v.v.

---

## Hướng Dẫn Tân Thủ

Vui lòng đọc kỹ các quy tắc dưới đây để thiết lập môi trường code ở Local một cách an toàn.

### 1. Tuyệt đối tuân thủ quy tắc quản lý Package bằng `uv`
Dự án sử dụng chuẩn mới của Python (`pyproject.toml` và `uv.lock`) thay cho `requirements.txt`. 

**QUY TẮC QUAN TRỌNG:**
* **KHÔNG** tự tạo file `pyproject.toml` rỗng bằng tay.
* **KHÔNG BAO GIỜ** mở và chỉnh sửa file `uv.lock` bằng tay.

**Cách làm việc với thư viện:**
* Nếu bạn là người khởi tạo một module Python hoàn toàn mới, hãy cd vào thư mục đó và gõ: `uv init`
* Nếu bạn muốn cài thêm thư viện mới (Ví dụ: cần dùng `playwright`), hãy gõ:
  ```bash
  uv add playwright crawl4ai beautifulsoup4
  ```
  *(Công cụ `uv` sẽ tự động cập nhật cả 2 file `.toml` và `.lock` một cách chuẩn xác).*
* Nếu clone project về máy và muốn đồng bộ toàn bộ thư viện để test code:
  ```bash
  uv sync
  ```

### 2. Thiết lập Biến môi trường (.env)
Bắt buộc phải nhân bản file cấu hình trước khi chạy:
```bash
cp .env.example .env
```
Mở file `.env` và thiết lập các thông số cơ bản. Đối với hệ thống crawling, chú ý các cờ cấu hình ưu tiên bộ lọc dữ liệu và hiệu suất:
```env
# Phân loại dữ liệu ưu tiên thu thập
CRAWL_CATEGORIES=coffee,restaurant

# Thiết lập thời gian chờ tối đa cho hệ thống (giây)
SYSTEM_TIMEOUT=60
```

### 3. Luồng làm việc Git (Branching Workflow)
Chúng ta làm việc song song trên các module. Tuyệt đối không đẩy code trực tiếp lên nhánh `main`. Hãy checkout đúng nhánh chứa module bạn đảm nhiệm:
* `feature/ui`: Code giao diện.
* `feature/backend`: Cập nhật logic Backend, chỉnh sửa crawling script.
* `feature/ai-agent`: Cập nhật logic xử lý AI.
* `feature/database`: Quản lý schema và Docker compose.

---

## Khởi Chạy Dự Án (Deployment & Build)

Toàn bộ hệ thống đã được container hóa. Mọi hướng dẫn chi tiết về cách Build Docker, xử lý Port và cài đặt tài nguyên trong container (như cài đặt trình duyệt cho Playwright) đều được tài liệu hóa rõ ràng.

 **Vui lòng xem chi tiết tại file:** [`docs/BUILD.md`](docs/BUILD.md)

---
*Dự án được duy trì và phát triển dựa trên các tiêu chuẩn tối ưu hóa cao nhất về mã nguồn và kiến trúc hạ tầng.*