# Project Chatbox - Hệ Thống Thu Thập & Xử Lý Dữ Liệu Tự Động

Dự án được xây dựng theo kiến trúc phân tán (Microservices) áp dụng mô hình thiết kế **Service - View - Model (SVM)**. Hệ thống phân tách rõ ràng luồng hiển thị giao diện, xử lý nghiệp vụ cốt lõi và các tác vụ AI Agent độc lập.

## Cấu Trúc Thư Mục (Folder Tree)

Dự án được quản lý tập trung bởi một kho lưu trữ Git duy nhất tại thư mục gốc với cấu trúc như sau:

```text
Project_Chatbox/
├── backend/            # Module Backend (API, Services, Models, Prompts)
│   ├── api/            # Định nghĩa các đầu mút API
│   ├── configs/        # Cấu hình hệ thống backend
│   ├── models/         # Lớp dữ liệu (Database Models)
│   ├── prompts/        # Thư mục quản lý Prompt cho AI
│   ├── services/       # Lớp xử lý logic nghiệp vụ chính & cào dữ liệu
│   ├── Dockerfile      # Cấu hình Docker cho Backend (Python 3.12.3-slim + uv)
│   ├── main.py         # File khởi chạy HTTP Server (FastAPI)
│   ├── pyproject.toml  # Khai báo thư viện của Backend
│   └── uv.lock         # File khóa phiên bản thư viện của Backend
├── ai-agent/           # Module xử lý các tác vụ AI độc lập
│   ├── agent/          # Logic cốt lõi của Agent
│   ├── Dockerfile      # Cấu hình Docker cho AI Agent (Python 3.12.3-slim + uv)
│   ├── main.py         # Script giữ container hoạt động liên tục
│   ├── pyproject.toml  # Khai báo thư viện của AI Agent
│   └── uv.lock         # File khóa phiên bản thư viện của AI Agent
├── frontend/           # Module giao diện người dùng (UI)
│   ├── assets/         # Tài nguyên tĩnh (Hình ảnh, css)
│   ├── components/     # Các thành phần giao diện dùng chung
│   ├── views/          # Các trang giao diện chính (Views)
│   └── Dockerfile      # Cấu hình Docker Stub cho Frontend (Node:20-alpine)
├── docs/
│   └── BUILD.md        # Hướng dẫn chi tiết cài đặt & vận hành môi trường
├── docker-compose.yml  # File duy nhất quản lý cấu hình và kết nối toàn bộ Services
├── .env.example        # File cấu hình môi trường mẫu
├── .env                # File cấu hình thực tế ở local (Đã chặn bởi .gitignore)
└── .gitignore          # File cấu hình các tệp tin loại trừ không push lên Git
```

## Công Nghệ Cốt Lõi (Tech Stack)

* **Ngôn ngữ môi trường:** Python 3.12.3 (Backend & AI Agent) & Node.js 20 (Frontend).
* **Quản lý Package:** [uv](https://github.com/astral-sh/uv) (Package manager thế hệ mới viết bằng Rust, thay thế hoàn toàn cho `pip` và `requirements.txt`).
* **Hạ tầng ảo hóa:** Docker & Docker Compose V2.
* **Cơ sở dữ liệu:** PostgreSQL 15 (Alpine vĩnh viễn lưu dữ liệu qua Docker Volume).

## Quy Tắc Hoạt Động Của Dự Án (Onboarding Rules)

1. **Quản lý Git:** Toàn bộ dự án chỉ sử dụng **MỘT kho Git duy nhất ở thư mục gốc**. Không chạy lệnh `git init` bên trong các thư mục con. Phát triển tính năng theo cấu trúc nhánh:
   * `feature/ui`: Chuyên code Frontend.
   * `feature/backend`: Chuyên code Backend (API, Crawling, Prompts).
   * `feature/ai-agent`: Chuyên code AI Logic.
   * `feature/database`: Cấu hình hạ tầng Compose và DB.
2. **Quản lý Thư viện:** Không tạo hoặc sử dụng file `requirements.txt`. Mọi thao tác thêm/bớt thư viện phải sử dụng công cụ `uv` thông qua lệnh `uv add <tên_thư_viện>` hoặc `uv remove <tên_thư_viện>` trực tiếp bên trong thư mục của module đó để hệ thống tự cập nhật `pyproject.toml` và `uv.lock`.
3. **Bảo mật:** Tuyệt đối không chỉnh sửa hoặc push file `.env` lên GitHub. Mọi cấu hình phân hệ phải được thực hiện thông qua việc nhân bản từ file `.env.example`.

---
👉 **Để bắt đầu cài đặt và chạy thử nghiệm hệ thống, vui lòng đọc tiếp hướng dẫn tại:** [`docs/BUILD.md`](docs/BUILD.md)