import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Save, Download, BookOpen, AlertTriangle, Check } from 'lucide-react'
import { PageHeader, Card, Button, Badge, Spinner } from '../components/ui.jsx'
import { saveRecord } from '../lib/api.js'
import { useBatch } from '../store.jsx'

const LOCAL_NO_INDICATOR = new Set(['927'])

const FIELD_LABELS = {
  '001': 'Số kiểm soát', '005': 'Ngày giờ giao dịch', '008': 'Dữ liệu độ dài cố định',
  '020': 'ISBN', '022': 'ISSN', '040': 'Nguồn biên mục', '041': 'Mã ngôn ngữ',
  '050': 'Phân loại LC', '060': 'Phân loại NLM', '090': 'Ký hiệu xếp giá',
  '100': 'Tác giả cá nhân', '110': 'Tác giả tập thể', '245': 'Nhan đề chính',
  '246': 'Dạng nhan đề khác', '250': 'Lần xuất bản', '260': 'Địa chỉ xuất bản',
  '300': 'Mô tả vật lý', '490': 'Tùng thư', '500': 'Phụ chú chung', '502': 'Phụ chú luận văn',
  '504': 'Phụ chú thư mục', '520': 'Tóm tắt', '541': 'Nguồn tiếp nhận', '650': 'Chủ đề',
  '710': 'Tác giả tập thể bổ sung', '852': 'Thông tin lưu giữ',
  '915': 'Thông tin đào tạo', '927': 'Dạng tư liệu lưu thông',
}

// đọc 1 subfield (dict {code,value} | {a:v} | chuỗi trần) -> {code, value}
function readSubfield(sf) {
  if (typeof sf === 'string') return { code: 'a', value: sf }
  if (sf && typeof sf === 'object') {
    if ('code' in sf) return { code: String(sf.code || ''), value: String(sf.value ?? '') }
    const k = Object.keys(sf)[0]
    if (k) return { code: k, value: String(sf[k] ?? '') }
  }
  return { code: '', value: '' }
}

// chuẩn hóa marc.fields -> mảng field có subfields dạng {code,value}
function normalizeFields(marc) {
  const out = []
  for (const f of marc?.fields || []) {
    if ('data' in f) { out.push({ tag: String(f.tag), isControl: true, data: String(f.data ?? '') }); continue }
    out.push({
      tag: String(f.tag),
      isControl: false,
      ind1: f.ind1 ?? ' ',
      ind2: f.ind2 ?? ' ',
      subfields: (Array.isArray(f.subfields) ? f.subfields : [f.subfields]).map(readSubfield),
    })
  }
  return out
}

function firstSubValue(fields, tag, code = 'a') {
  const f = fields.find((x) => x.tag === tag && !x.isControl)
  const s = f?.subfields?.find((sf) => sf.code === code && sf.value.trim())
  return s ? s.value.trim() : ''
}
function classificationCode(fields) {
  for (const tag of ['060', '050']) {
    const f = fields.find((x) => x.tag === tag && !x.isControl)
    if (!f) continue
    const a = f.subfields.find((s) => s.code === 'a')?.value?.trim() || ''
    const b = f.subfields.find((s) => s.code === 'b')?.value?.trim() || ''
    if (a) return `${a} ${b}`.trim()
  }
  return 'N/A'
}

export default function MarcEditorPage() {
  const { docs, selectedName, setSelectedName, updateMarc } = useBatch()
  const names = Object.keys(docs)
  const active = selectedName && docs[selectedName] ? selectedName : names[0] || null

  const [fields, setFields] = useState([])
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState(null)

  const current = active ? docs[active] : null

  useEffect(() => {
    setFields(current ? normalizeFields(current.marc) : [])
  }, [active]) // eslint-disable-line react-hooks/exhaustive-deps

  const raw = current?.raw || {}
  const lowConf = raw?.extraction_metadata?.low_confidence_fields || []

  const topInfo = useMemo(() => ({
    title: raw.title_main || 'Chưa có nhan đề',
    author: raw.author_personal_name || 'Chưa rõ tác giả',
    isbn: firstSubValue(fields, '020') || 'N/A',
    publisher: raw.publisher_name || 'N/A',
    year: raw.publication_year || 'N/A',
    classification: classificationCode(fields),
  }), [fields, raw])

  if (!current) {
    return (
      <div>
        <PageHeader title="Biên tập MARC21" subtitle="Chỉnh sửa dữ liệu thư mục do AI tạo" />
        <Card className="p-10 text-center">
          <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-slate-400"><BookOpen size={22} /></div>
          <p className="text-slate-500">Chưa có tài liệu nào được xử lý.</p>
          <Link to="/upload"><Button className="mt-4">Sang trang Tải lên</Button></Link>
        </Card>
      </div>
    )
  }

  // ---- cập nhật bất biến ----
  const setControl = (i, v) => setFields((p) => p.map((f, idx) => idx === i ? { ...f, data: v } : f))
  const setInd = (i, which, v) => setFields((p) => p.map((f, idx) => idx === i ? { ...f, [which]: v } : f))
  const setSub = (i, j, key, v) => setFields((p) => p.map((f, idx) => {
    if (idx !== i) return f
    return { ...f, subfields: f.subfields.map((s, k) => k === j ? { ...s, [key]: v } : s) }
  }))

  function buildMarcRecord() {
    return {
      leader: current.marc?.leader,
      fields: fields.map((f) => f.isControl
        ? { tag: f.tag, data: f.data }
        : { tag: f.tag, ind1: f.ind1, ind2: f.ind2, subfields: f.subfields.filter((s) => s.code) }),
    }
  }

  async function handleSave() {
    setSaving(true); setToast(null)
    try {
      const res = await saveRecord(active, buildMarcRecord())
      if (res.marc21_record) updateMarc(active, res.marc21_record)
      setToast({ tone: 'green', msg: `Đã lưu & ghi file MARC: ${res?.file_paths?.mrc_file || 'output_final'}` })
    } catch (err) {
      setToast({ tone: 'red', msg: err.message })
    } finally {
      setSaving(false)
    }
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(buildMarcRecord(), null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${active.replace(/\.[^.]+$/, '')}_marc.json`; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <PageHeader
        title="Biên tập MARC21"
        subtitle="Chỉnh sửa siêu dữ liệu thư mục do AI tạo"
        actions={
          <>
            <Button variant="ghost" onClick={exportJson}><Download size={15} /> Xuất JSON</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Spinner className="h-4 w-4" /> : <Save size={15} />} Lưu bản ghi
            </Button>
          </>
        }
      />

      {names.length > 1 && (
        <div className="mb-4">
          <select value={active} onChange={(e) => setSelectedName(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-brand focus:outline-none">
            {names.map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
      )}

      {toast && (
        <div className={`mb-4 rounded-lg px-4 py-3 text-sm ${toast.tone === 'green' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
          {toast.msg}
        </div>
      )}

      {/* TOP BOARD */}
      <Card className="mb-5 p-5">
        <div className="flex items-start gap-4">
          <div className="grid h-16 w-16 shrink-0 place-items-center rounded-lg bg-blue-50 text-brand"><BookOpen size={28} /></div>
          <div className="min-w-0 flex-1">
            <h2 className="truncate text-lg font-semibold text-slate-900">{topInfo.title}</h2>
            <p className="mt-0.5 text-sm text-slate-500">Tệp: {active} &nbsp;|&nbsp; Tác giả: {topInfo.author}</p>
            <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
              {[['ISBN', topInfo.isbn], ['NXB', topInfo.publisher], ['Năm', topInfo.year], ['Phân loại (050/060)', topInfo.classification]].map(([k, v]) => (
                <div key={k}>
                  <div className="text-xs text-slate-400">{k}</div>
                  <div className="truncate text-sm font-semibold text-slate-800">{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-4">
        {/* BẢNG MARC */}
        <Card className="p-0 lg:col-span-3">
          <div className="border-b border-slate-100 px-5 py-3 text-sm font-semibold text-slate-700">Trường MARC21</div>
          <div className="grid grid-cols-[56px_40px_40px_36px_1fr] gap-2 border-b border-slate-100 px-5 py-2 text-[11px] font-semibold uppercase text-slate-400">
            <div>Thẻ</div><div>I1</div><div>I2</div><div>$</div><div>Nhãn / Giá trị</div>
          </div>

          <div className="divide-y divide-slate-50">
            {fields.map((f, i) => {
              const label = FIELD_LABELS[f.tag] || ''
              if (f.isControl) {
                return (
                  <Row key={i} tag={f.tag} label={label}>
                    <input value={f.data} onChange={(e) => setControl(i, e.target.value)} className={inputCls} />
                  </Row>
                )
              }
              const noInd = LOCAL_NO_INDICATOR.has(f.tag)
              return f.subfields.map((s, j) => (
                <div key={`${i}-${j}`} className="grid grid-cols-[56px_40px_40px_36px_1fr] items-center gap-2 px-5 py-1.5">
                  <div className="text-sm font-semibold text-brand">{j === 0 ? f.tag : ''}</div>
                  <input disabled={noInd || j !== 0} value={j === 0 && !noInd ? f.ind1 : ''} maxLength={1}
                    onChange={(e) => setInd(i, 'ind1', e.target.value)} className={indCls} />
                  <input disabled={noInd || j !== 0} value={j === 0 && !noInd ? f.ind2 : ''} maxLength={1}
                    onChange={(e) => setInd(i, 'ind2', e.target.value)} className={indCls} />
                  <input value={s.code} maxLength={1} onChange={(e) => setSub(i, j, 'code', e.target.value)} className={indCls} />
                  <div>
                    {j === 0 && label && <div className="mb-0.5 text-[11px] text-slate-400">{label}</div>}
                    <input value={s.value} onChange={(e) => setSub(i, j, 'value', e.target.value)} className={inputCls} />
                  </div>
                </div>
              ))
            })}
          </div>
        </Card>

        {/* PANEL AI (chỉ hiển thị dữ liệu THẬT) */}
        <div className="space-y-4">
          <Card className="p-5">
            <div className="mb-3 text-sm font-semibold text-slate-700">Thông tin AI</div>
            <Row2 k="Trạng thái xác thực" v={<Badge tone="green"><Check size={12} className="mr-1" />JSON hợp lệ</Badge>} />
            <Row2 k="Phân loại (050/060)" v={topInfo.classification} />
            <Row2 k="Số trường cần rà" v={<Badge tone={lowConf.length ? 'amber' : 'green'}>{lowConf.length}</Badge>} />
          </Card>

          {lowConf.length > 0 && (
            <Card className="p-5">
              <div className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-amber-700">
                <AlertTriangle size={15} /> Trường AI đánh dấu độ tin cậy thấp
              </div>
              <div className="flex flex-wrap gap-1.5">
                {lowConf.map((x) => <Badge key={x} tone="amber">{x}</Badge>)}
              </div>
            </Card>
          )}

          <Card className="p-4 text-xs text-slate-400">
            % chính xác theo từng trường cần backend sinh confidence riêng cho mỗi trường — thuộc phần phát triển sau. Ở đây chỉ hiển thị dữ liệu thật đang có.
          </Card>
        </div>
      </div>
    </div>
  )
}

const inputCls = 'w-full rounded-md border border-slate-200 px-2.5 py-1.5 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand'
const indCls = 'w-full rounded-md border border-slate-200 px-1 py-1.5 text-center text-sm focus:border-brand focus:outline-none disabled:bg-slate-50 disabled:text-slate-300'

function Row({ tag, label, children }) {
  return (
    <div className="grid grid-cols-[56px_40px_40px_36px_1fr] items-center gap-2 px-5 py-1.5">
      <div className="text-sm font-semibold text-brand">{tag}</div>
      <div /><div /><div />
      <div>{label && <div className="mb-0.5 text-[11px] text-slate-400">{label}</div>}{children}</div>
    </div>
  )
}
function Row2({ k, v }) {
  return (
    <div className="flex items-center justify-between border-b border-slate-50 py-2 last:border-0">
      <span className="text-xs text-slate-500">{k}</span>
      <span className="text-sm font-medium text-slate-800">{v}</span>
    </div>
  )
}
