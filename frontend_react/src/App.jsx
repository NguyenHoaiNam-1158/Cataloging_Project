import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import ComingSoon from './components/ComingSoon.jsx'
import UploadPage from './pages/UploadPage.jsx'
import MarcEditorPage from './pages/MarcEditorPage.jsx'

function Layout({ children }) {
  return (
    <div className="flex">
      <Sidebar />
      <main className="h-screen flex-1 overflow-y-auto thin-scroll">
        <div className="mx-auto max-w-[1400px] px-8 py-7">{children}</div>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/marc" element={<MarcEditorPage />} />

        {/* 3 màn hình quy về "phát triển sau" */}
        <Route path="/" element={
          <ComingSoon
            title="Tổng quan hệ thống"
            subtitle="Quản lý và theo dõi quá trình trích xuất dữ liệu thư viện bằng AI"
            needs={['Cơ sở dữ liệu lưu biểu ghi', 'Lớp metrics tổng hợp (số liệu thẻ, biểu đồ tuần)']}
          />
        } />
        <Route path="/processing" element={
          <ComingSoon
            title="Xử lý OCR / AI"
            subtitle="Theo dõi tiến trình trích xuất và phân tích siêu dữ liệu"
            needs={['Hàng đợi job có trạng thái + job-id', 'Kênh cập nhật thời gian thực (SSE/WebSocket) cho 8 bước xử lý']}
          />
        } />
        <Route path="/catalog" element={
          <ComingSoon
            title="Tìm kiếm danh mục"
            subtitle="Tra cứu và quản lý bộ sưu tập thư viện"
            needs={['Cơ sở dữ liệu + endpoint tìm kiếm/lọc/phân trang', 'Xuất CSV từ dữ liệu đã lưu']}
          />
        } />

        <Route path="*" element={<Navigate to="/upload" replace />} />
      </Routes>
    </Layout>
  )
}
