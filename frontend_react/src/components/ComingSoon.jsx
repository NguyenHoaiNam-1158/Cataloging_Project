import { Construction } from 'lucide-react'
import { PageHeader, Card } from './ui.jsx'

export default function ComingSoon({ title, subtitle, needs = [] }) {
  return (
    <div>
      <PageHeader title={title} subtitle={subtitle} />
      <Card className="p-10">
        <div className="mx-auto max-w-lg text-center">
          <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-amber-50 text-amber-600">
            <Construction size={24} />
          </div>
          <h2 className="text-lg font-semibold text-slate-800">Màn hình này sẽ phát triển sau</h2>
          <p className="mt-2 text-sm text-slate-500">
            Still Update.
          </p>
          {needs.length > 0 && (
            <div className="mt-5 rounded-lg bg-slate-50 p-4 text-left">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Cần bổ sung ở backend</div>
              <ul className="space-y-1 text-sm text-slate-600">
                {needs.map((n) => (
                  <li key={n} className="flex gap-2"><span className="text-slate-400">—</span>{n}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
