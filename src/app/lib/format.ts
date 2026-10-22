const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const compact = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1 })

export const money = (value: number) => currency.format(value)
export const moneyCompact = (value: number) => compact.format(value)

export function relativeTime(ts: number, now = Date.now()): string {
  const diff = now - ts
  const minutes = Math.round(diff / 60_000)
  if (Math.abs(minutes) < 1) return 'just now'
  if (Math.abs(minutes) < 60) return minutes > 0 ? `${minutes}m ago` : `in ${-minutes}m`
  const hours = Math.round(minutes / 60)
  if (Math.abs(hours) < 24) return hours > 0 ? `${hours}h ago` : `in ${-hours}h`
  const days = Math.round(hours / 24)
  if (Math.abs(days) < 7) return days > 0 ? `${days}d ago` : `in ${-days}d`
  return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function shortDate(value: number | string | null | undefined): string {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(`${value}T00:00:00`) : new Date(value)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function longDate(value: number | string | null | undefined): string {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(`${value}T00:00:00`) : new Date(value)
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
}

export function dueLabel(dueAt: number | null): { label: string; tone: 'danger' | 'warning' | 'muted' } {
  if (!dueAt) return { label: 'No date', tone: 'muted' }
  const now = Date.now()
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  const dayEnd = start.getTime() + 86_400_000
  if (dueAt < now) return { label: 'Overdue', tone: 'danger' }
  if (dueAt < dayEnd) return { label: 'Today', tone: 'warning' }
  if (dueAt < dayEnd + 86_400_000) return { label: 'Tomorrow', tone: 'muted' }
  return { label: shortDate(dueAt), tone: 'muted' }
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('')
}

export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export const toDateInput = (ts: number | null) => (ts ? new Date(ts - new Date().getTimezoneOffset() * 60_000).toISOString().slice(0, 10) : '')
export const fromDateInput = (value: string) => (value ? new Date(`${value}T09:00:00`).getTime() : null)
