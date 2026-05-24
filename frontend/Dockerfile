# Sử dụng môi trường Node.js nhẹ nhàng cho UI
FROM node:20-alpine

# Thiết lập thư mục làm việc
WORKDIR /app

# Mở cổng 3000 như đã cấu hình
EXPOSE 3000

# Lệnh giả để giữ container luôn chạy ngầm mà không bị crash
CMD ["tail", "-f", "/dev/null"]