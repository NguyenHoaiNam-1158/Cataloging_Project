// Các primitive nhỏ, hand-rolled bằng Tailwind — bám ngôn ngữ thiết kế trong mockup.
import { Loader2 } from 'lucide-react'

export function Card({ className = '', children }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white ${className}`}>
      {children}
    </div>
  )
}

export function Button({ variant = 'primary', className = '', children, ...props }) {
  const base =
    'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-brand/40'
  const variants = {
    primary: 'bg-brand text-white hover:bg-brand-dark',
    ghost: 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50',
    subtle: 'bg-slate-100 text-slate-700 hover:bg-slate-200',
  }
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  )
}

const BADGE_TONES = {
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  blue: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  amber: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  red: 'bg-red-50 text-red-700 ring-red-600/20',
  slate: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}

export function Badge({ tone = 'slate', children }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${BADGE_TONES[tone]}`}>
      {children}
    </span>
  )
}

export function Spinner({ className = '' }) {
  return <Loader2 className={`animate-spin ${className}`} />
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}
