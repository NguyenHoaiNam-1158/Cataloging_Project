import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Upload, ScanText, BookMarked, Search,
  Globe, LogOut, BookOpen,
} from 'lucide-react'

const NAV = [
  { to: '/', label: 'Tổng quan', icon: LayoutDashboard, end: true },
  { to: '/upload', label: 'Tải lên tài liệu', icon: Upload },
  { to: '/processing', label: 'Xử lý OCR/AI', icon: ScanText },
  { to: '/marc', label: 'Biên tập MARC21', icon: BookMarked },
  { to: '/catalog', label: 'Tìm kiếm danh mục', icon: Search },
]

export default function Sidebar() {
  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col bg-sidebar text-slate-300">
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-brand text-white">
          <BookOpen size={20} />
        </div>
        <div>
          <div className="text-sm font-semibold text-white">Library AI</div>
          <div className="text-xs text-sidebar-muted">Đại học Y Dược</div>
        </div>
      </div>

      <div className="px-5 pb-2 pt-4 text-[11px] font-semibold tracking-wider text-sidebar-muted">
        ĐIỀU HƯỚNG
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'bg-brand text-white'
                  : 'text-slate-300 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="space-y-3 border-t border-white/10 px-5 py-4 text-xs">
        <div className="flex items-center gap-2 text-sidebar-muted">
          <Globe size={14} /> Ngôn ngữ
          <span className="ml-1 rounded bg-brand px-1.5 py-0.5 text-[10px] font-semibold text-white">VI</span>
          <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px]">EN</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-full bg-brand text-[11px] font-semibold text-white">TV</div>
            <div>
              <div className="font-medium text-white">Thủ thư</div>
              <div className="text-[11px] text-sidebar-muted">librarian@ump.edu.vn</div>
            </div>
          </div>
          <LogOut size={16} className="cursor-pointer text-sidebar-muted hover:text-white" />
        </div>
      </div>
    </aside>
  )
}
