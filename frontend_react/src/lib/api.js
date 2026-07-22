// Nếu VITE_API_BASE trống -> dùng đường dẫn tương đối '/api' (đi qua proxy Vite khi dev).
const BASE = import.meta.env.VITE_API_BASE || ''

/**
 * Gửi 1 file PDF/ảnh sang backend để trích xuất + ánh xạ MARC/Dublin Core.
 * Khớp POST /api/v1/process-document (multipart).
 */
export async function processDocument(file, { docType, additionalInfo } = {}) {
  const form = new FormData()
  form.append('file', file, file.name)
  if (docType) form.append('doc_type', docType)
  if (additionalInfo) form.append('additional_info', additionalInfo)

  const res = await fetch(`${BASE}/api/v1/process-document`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    let detail = ''
    try { detail = JSON.stringify(await res.json()) } catch { /* ignore */ }
    throw new Error(`Backend trả mã ${res.status}. ${detail}`)
  }
  return res.json()
}

/**
 * Ghi biểu ghi đã sửa xuống backend (.mrc + _marc.json).
 * Khớp POST /api/v1/save-record (JSON).
 */
export async function saveRecord(sourceFile, marcRecord) {
  const res = await fetch(`${BASE}/api/v1/save-record`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_file: sourceFile, marc_record: marcRecord }),
  })
  if (!res.ok) {
    let detail = ''
    try { detail = JSON.stringify(await res.json()) } catch { /* ignore */ }
    throw new Error(`Lưu thất bại (mã ${res.status}). ${detail}`)
  }
  return res.json()
}
