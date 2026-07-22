import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  UploadCloud, FileText, Image as ImageIcon, X, Check, Play, Trash2,
} from 'lucide-react'
import { PageHeader, Card, Button, Badge, Spinner } from '../components/ui.jsx'
import { processDocument } from '../lib/api.js'
import { useBatch } from '../store.jsx'

// Nhãn hiển thị -> mã doc_type mà backend hiểu
const DOC_TYPES = [
  { key: 'sach', label: 'Sách / Book', hint: 'Trích xuất: ISBN, tác giả, NXB, năm, trường MARC21' },
  { key: 'luan_van', label: 'Luận văn / Luận án', hint: 'Trích xuất: tiêu đề, tác giả, người hướng dẫn, chuyên ngành, từ khóa' },
  { key: 'bao_cao_nckh', label: 'Nghiên cứu khoa học', hint: 'Trích xuất: tiêu đề, tóm tắt, từ khóa, tạp chí, năm' },
]

function fileIcon(name) {
  return name.toLowerCase().endsWith('.pdf') ? FileText : ImageIcon
}
function prettySize(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function UploadPage() {
  const navigate = useNavigate()
  const { addDoc } = useBatch()
  const inputRef = useRef(null)

  const [files, setFiles] = useState([])
  const [docType, setDocType] = useState('sach')
  const [collection, setCollection] = useState('')
  const [org, setOrg] = useState('Đại học Y Dược TP.HCM')
  const [note, setNote] = useState('')
  const [dragOver, setDragOver] = useState(false)

  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState({ done: 0, total: 0, current: '' })
  const [results, setResults] = useState([]) // {name, ok, error}

  function addFiles(list) {
    const incoming = Array.from(list).filter((f) =>
      /\.(pdf|jpg|jpeg|png|tiff?)$/i.test(f.name)
    )
    setFiles((prev) => {
      const seen = new Set(prev.map((f) => f.name))
      return [...prev, ...incoming.filter((f) => !seen.has(f.name))]
    })
  }

  function removeFile(name) {
    setFiles((prev) => prev.filter((f) => f.name !== name))
  }

  async function startExtraction() {
    if (files.length === 0) return
    setRunning(true)
    setResults([])
    const outcome = []
    // Ghép ghi chú có cấu trúc thành 1 chuỗi additional_info cho backend hiện tại.
    const additionalInfo = [
      collection && `Bộ sưu tập: ${collection}`,
      org && `Đơn vị: ${org}`,
      note && `Ghi chú: ${note}`,
    ].filter(Boolean).join(' | ')

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setProgress({ done: i, total: files.length, current: file.name })
      try {
        const data = await processDocument(file, { docType, additionalInfo })
        addDoc(file.name, {
          marc: data.marc21_record,
          raw: data.extracted_raw_data,
          dc: data.dublin_core_record,
          errors: { marc: data.marc_error, dc: data.dc_error },
        })
        outcome.push({ name: file.name, ok: true })
      } catch (err) {
        outcome.push({ name: file.name, ok: false, error: err.message })
      }
      setResults([...outcome])
    }
    setProgress({ done: files.length, total: files.length, current: '' })
    setRunning(false)
  }

  const successCount = results.filter((r) => r.ok).length

  return (
    <div>
      <PageHeader
        title="Tải lên tài liệu"
        subtitle="Tải lên PDF hoặc hình ảnh để trích xuất siêu dữ liệu thư mục bằng AI"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* CỘT TRÁI: dropzone + danh sách tệp */}
        <div className="space-y-6 lg:col-span-2">
          <Card
            className={`border-2 border-dashed p-10 text-center transition-colors ${
              dragOver ? 'border-brand bg-blue-50/50' : 'border-slate-200'
            }`}
            /* eslint-disable */
          >
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files) }}
            >
              <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-slate-100 text-slate-400">
                <UploadCloud size={26} />
              </div>
              <div className="text-base font-medium text-slate-700">Kéo &amp; thả tệp vào đây</div>
              <div className="mt-1 text-sm text-slate-400">hoặc nhấn để chọn từ máy tính</div>
              <Button className="mt-4" onClick={() => inputRef.current?.click()}>Chọn tệp</Button>
              <input
                ref={inputRef}
                type="file"
                multiple
                accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff"
                className="hidden"
                onChange={(e) => addFiles(e.target.files)}
              />
              <div className="mt-4 text-xs text-slate-400">Hỗ trợ: PDF, JPG, PNG, TIFF (Tối đa 50MB)</div>
            </div>
          </Card>

          {files.length > 0 && (
            <Card className="p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="text-sm font-semibold text-slate-700">Danh sách tệp ({files.length})</div>
                <button onClick={() => setFiles([])} className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-500">
                  <Trash2 size={13} /> Xóa tất cả
                </button>
              </div>
              <ul className="space-y-2">
                {files.map((f) => {
                  const Icon = fileIcon(f.name)
                  const r = results.find((x) => x.name === f.name)
                  return (
                    <li key={f.name} className="flex items-center gap-3 rounded-lg border border-slate-100 px-3 py-2.5">
                      <Icon size={18} className="shrink-0 text-red-400" />
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm text-slate-700">{f.name}</div>
                        <div className="text-xs text-slate-400">{prettySize(f.size)}</div>
                      </div>
                      {r ? (
                        r.ok
                          ? <Badge tone="green"><Check size={12} className="mr-1" />Xong</Badge>
                          : <Badge tone="red">Lỗi</Badge>
                      ) : (
                        <Badge tone="green">Sẵn sàng</Badge>
                      )}
                      <button onClick={() => removeFile(f.name)} className="text-slate-300 hover:text-red-500">
                        <X size={16} />
                      </button>
                    </li>
                  )
                })}
              </ul>
            </Card>
          )}

          {results.some((r) => !r.ok) && (
            <Card className="border-red-100 bg-red-50/40 p-4">
              <div className="text-sm font-semibold text-red-700">Một số tệp lỗi</div>
              <ul className="mt-2 space-y-1 text-sm text-red-600">
                {results.filter((r) => !r.ok).map((r) => (
                  <li key={r.name}><span className="font-medium">{r.name}:</span> {r.error}</li>
                ))}
              </ul>
            </Card>
          )}
        </div>

        {/* CỘT PHẢI: cấu hình xử lý */}
        <div className="space-y-6">
          <Card className="p-5">
            <div className="mb-3 text-sm font-semibold text-slate-700">Loại tài liệu</div>
            <div className="space-y-2">
              {DOC_TYPES.map((d) => (
                <button
                  key={d.key}
                  onClick={() => setDocType(d.key)}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    docType === d.key ? 'border-brand bg-blue-50/60 ring-1 ring-brand' : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-800">{d.label}</span>
                    {docType === d.key && <Check size={16} className="text-brand" />}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">{d.hint}</div>
                </button>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <div className="mb-2 text-sm font-semibold text-slate-700">Mô hình AI</div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
              Gemini (mặc định)
            </div>
          </Card>

          <Card className="p-5">
            <div className="mb-3 text-sm font-semibold text-slate-700">Dữ liệu bổ sung</div>
            <label className="mb-1 block text-xs text-slate-500">Bộ sưu tập</label>
            <input value={collection} onChange={(e) => setCollection(e.target.value)}
              placeholder="VD: Y học cơ sở"
              className="mb-3 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand" />
            <label className="mb-1 block text-xs text-slate-500">Đơn vị</label>
            <input value={org} onChange={(e) => setOrg(e.target.value)}
              className="mb-3 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand" />
            <label className="mb-1 block text-xs text-slate-500">Ghi chú</label>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2}
              placeholder="Ghi chú thêm..."
              className="w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand" />
          </Card>
        </div>
      </div>

      {/* THANH HÀNH ĐỘNG */}
      <div className="mt-6">
        {running && (
          <div className="mb-3">
            <div className="mb-1 flex justify-between text-xs text-slate-500">
              <span>Đang xử lý: {progress.current}</span>
              <span>{progress.done}/{progress.total}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div className="h-full bg-brand transition-all"
                style={{ width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%` }} />
            </div>
          </div>
        )}

        {!running && successCount > 0 && (
          <Card className="mb-3 border-emerald-100 bg-emerald-50/50 p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-emerald-700">
                Đã xử lý xong lô. Thành công <b>{successCount}/{results.length}</b> tệp.
              </div>
              <Button variant="ghost" onClick={() => navigate('/marc')}>Sang biên tập MARC21 →</Button>
            </div>
          </Card>
        )}

        <Button className="w-full py-3 text-base" disabled={running || files.length === 0} onClick={startExtraction}>
          {running ? <><Spinner className="h-4 w-4" /> Đang trích xuất...</> : <><Play size={16} /> Bắt đầu trích xuất</>}
        </Button>
      </div>
    </div>
  )
}
