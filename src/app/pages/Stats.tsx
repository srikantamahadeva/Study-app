import { motion } from 'motion/react'
import { Flame } from 'lucide-react'
import { Link } from 'react-router'

import { Card, Skeleton } from '../components/ui'
import { useStats } from '../lib/api'
import { cx } from '../lib/cx'
import { relativeTime } from '../lib/format'

export function StatsPage() {
  const { data, isLoading } = useStats()

  if (isLoading || !data) {
    return (
      <div className="grid gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-[104px] rounded-card" />
        ))}
      </div>
    )
  }

  const kpis = [
    { label: 'Current streak', value: `${data.streak}`, unit: data.streak === 1 ? 'day' : 'days', icon: <Flame className="size-4 text-warning" /> },
    { label: 'Longest streak', value: `${data.longestStreak}`, unit: 'days' },
    { label: 'Cards mastered', value: `${data.cardsMastered}`, unit: `of ${data.cardsTotal}` },
    { label: 'Time studied', value: `${data.minutes}`, unit: 'minutes' },
  ]

  const weeks: typeof data.days[] = []
  for (let i = 0; i < data.days.length; i += 7) weeks.push(data.days.slice(i, i + 7))
  const maxSessions = Math.max(1, ...data.days.map((d) => d.sessions))
  const accuracyDays = data.days.slice(-28)

  return (
    <div>
      <h1 className="text-[26px] font-bold tracking-[-0.02em]">Progress</h1>
      <p className="mt-1 text-[14.5px] text-muted">{data.sessions} study sessions so far</p>

      <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {kpis.map((k) => (
          <Card key={k.label} className="flex h-[104px] flex-col justify-between p-4">
            <p className="flex items-center gap-1.5 text-[13px] text-muted">
              {k.icon}
              {k.label}
            </p>
            <p className="text-[26px] font-bold tracking-tight tabular-nums">
              {k.value} <span className="text-[13px] font-medium text-faint">{k.unit}</span>
            </p>
          </Card>
        ))}
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-[1.4fr_1fr]">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-[14px] font-semibold">Activity</h2>
            <span className="text-[12.5px] text-faint">Last 12 weeks</span>
          </div>
          <div className="mt-4 grid grid-flow-col grid-rows-7 gap-1.5" style={{ gridTemplateColumns: `repeat(${weeks.length}, minmax(0, 1fr))` }}>
            {weeks.map((week, wi) =>
              week.map((day, di) => (
                <motion.span
                  key={day.date}
                  title={`${day.date}: ${day.sessions} ${day.sessions === 1 ? 'session' : 'sessions'}`}
                  initial={{ opacity: 0, scale: 0.6 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: (wi * 7 + di) * 0.006 }}
                  className="aspect-square rounded-[5px]"
                  style={{ background: day.sessions === 0 ? 'var(--color-surface-2)' : `color-mix(in srgb, var(--color-accent) ${35 + (day.sessions / maxSessions) * 65}%, white)` }}
                />
              )),
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-[14px] font-semibold">Accuracy</h2>
            <span className="text-[12.5px] text-faint">Last 4 weeks</span>
          </div>
          <div className="mt-4 flex h-[128px] items-end gap-1">
            {accuracyDays.map((d) => (
              <div key={d.date} className="flex h-full flex-1 flex-col justify-end" title={d.accuracy === null ? d.date : `${d.date}: ${d.accuracy}%`}>
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: `${d.accuracy ?? 4}%` }}
                  transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                  className={cx('rounded-[4px]', d.accuracy === null ? 'bg-surface-2' : d.accuracy >= 80 ? 'bg-success' : d.accuracy >= 50 ? 'bg-warning' : 'bg-danger')}
                />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <Card className="p-5">
          <h2 className="text-[14px] font-semibold">Decks</h2>
          <ul className="mt-4 flex flex-col gap-3.5">
            {data.decks.map((d) => (
              <li key={d.id}>
                <Link to={`/decks/${d.id}`} className="grid grid-cols-[1fr_auto] items-center gap-3 text-[13.5px]">
                  <span className="truncate font-medium">{d.title}</span>
                  <span className="tabular-nums text-muted">{d.mastery}%</span>
                  <span className="col-span-2 h-2 overflow-hidden rounded-[4px] bg-surface-2">
                    <motion.span className="block h-full rounded-[4px]" style={{ background: `hsl(${d.hue} 70% 55%)` }} initial={{ width: 0 }} animate={{ width: `${d.mastery}%` }} transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }} />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
        <Card className="p-5">
          <h2 className="text-[14px] font-semibold">Recent sessions</h2>
          <ul className="mt-2 divide-y divide-line">
            {data.recent.map((s) => (
              <li key={s.id} className="flex items-center gap-3 py-2.5 text-[13.5px]">
                <span className={cx('round size-2 shrink-0 rounded-full', s.accuracy >= 80 ? 'bg-success' : s.accuracy >= 50 ? 'bg-warning' : 'bg-danger')} />
                <span className="min-w-0 flex-1 truncate">
                  <span className="font-medium">{s.deckTitle ?? 'Deck'}</span>
                  <span className="text-muted"> in {s.mode}</span>
                </span>
                <span className="tabular-nums text-muted">{s.accuracy}%</span>
                <span className="w-16 text-right tabular-nums text-faint">{relativeTime(s.createdAt)}</span>
              </li>
            ))}
            {data.recent.length === 0 && <li className="py-6 text-center text-[13px] text-muted">No sessions yet</li>}
          </ul>
        </Card>
      </div>
    </div>
  )
}
