## How to run

```bash
npm install
npm run dev        # mở http://localhost:5173
```

Backend FastAPI cần chạy sẵn ở `http://localhost:8000`. Vite đã cấu hình proxy
`/api → localhost:8000` (xem `vite.config.js`) nên không vướng CORS khi dev.
Muốn trỏ backend khác: đặt `VITE_API_BASE` trong file `.env`.


## Cấu trúc

```
src/
├── App.jsx              router + layout (sidebar + nội dung)
├── store.jsx           BatchProvider: giữ kết quả đã xử lý trong phiên
├── lib/api.js          client gọi backend (processDocument, saveRecord)
├── components/         Sidebar, ui primitives (Card/Button/Badge), ComingSoon
└── pages/              UploadPage, MarcEditorPage
```

