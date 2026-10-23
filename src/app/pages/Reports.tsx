import { BarChart3, Flame, Target, TrendingUp } from 'lucide-react'

import { Badge, Card, EmptyState, PageHeader, Spinner } from '../components/ui'
import { useOverview, useRecommendations, useWeekly } from '../lib/api'
import { cx } from '../lib/cx'
import { shortDate } from '../lib/format'

function Metric({ icon, label, value, tone = 'accent' }: { icon: React.ReactNode; label: string; value: string; tone?: 'accent' | 'success' | 'warning' | 'info' }) {
  const tones = { accent: 'bg-accent-soft text-accent', success: 'bg-success-soft text-success', warning: 'bg-warning-soft text-warning', info: 'bg-info-soft text-info' }
  return (
    <Card className="flex items-center gap-3 p-4">
      <div className={cx('grid size-10 shrink-0 place-items-center rounded-tile', tones[tone])}>{icon}</div>
      <div className="min-w-0">
        <p className="text-[20px] font-semibold leading-tight">{value}</p>
        <p className="text-[13px] text-muted">{label}</p>
      </div>
    </Card>
  )
}

/** Dashboard: everything traced to recorded activity — nothing invented. */
export function Reports() {
  const { data: overview, isLoading } = useOverview()
  const { data: weekly } = useWeekly(4)
  const { data: recs } = useRecommendations()

  if (isLoading) return <Spinner />
  if (!overview) return <EmptyState icon={<BarChart3 />} title="No data yet" description="Start a lesson or take a quiz to see your progress here." />

  const maxMinutes = Math.max(1, ...(weekly?.weeks.map((w) => w.minutes) ?? [1]))

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Reports" subtitle="Your study activity, computed from what you have actually recorded." />

      {/* Top metrics */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric icon={<TrendingUp className="size-5" />} label="Course complete" value={`${overview.progress.percent}%`} tone="accent" />
        <Metric icon={<Flame className="size-5" />} label="Day streak" value={String(overview.streak.current)} tone="warning" />
        <Metric icon={<Target className="size-5" />} label="Quiz accuracy" value={overview.quiz.accuracy === null ? '—' : `${overview.quiz.accuracy}%`} tone="success" />
        <Metric icon={<BarChart3 className="size-5" />} label="Reviews due" value={String(overview.revisions.dueNow)} tone="info" />
      </div>

      {/* Progress + study */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="text-[14px] font-semibold">Curriculum progress</h3>
          <p className="mt-1 text-[13px] text-muted">
            {overview.progress.lessonsCompleted} of {overview.progress.lessonsTotal} lessons complete
          </p>
          <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-raised">
            <div className="h-full rounded-full bg-accent transition-[width] duration-500" style={{ width: `${overview.progress.percent}%` }} />
          </div>
          {overview.nextLesson && (
            <p className="mt-3 text-[13px] text-muted">
              Up next: <span className="font-medium text-fg">{overview.nextLesson.title}</span>
            </p>
          )}
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-semibold">Study minutes</h3>
            <Badge tone="neutral">Last 4 weeks</Badge>
          </div>
          <div className="mt-4 flex h-32 items-end gap-1.5">
            {(weekly?.weeks ?? []).map((w) => (
              <div key={w.weekStart} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t-[4px] bg-accent/80 transition-[height] duration-500"
                  style={{ height: `${Math.round((w.minutes / maxMinutes) * 100)}%`, minHeight: w.minutes > 0 ? 3 : 1 }}
                />
                <span className="text-[10.5px] text-faint">{shortDate(w.weekStart)}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Weak topics */}
      {overview.weakestTopics.length > 0 && (
        <Card className="p-5">
          <h3 className="text-[14px] font-semibold">Weakest topics</h3>
          <p className="mt-0.5 text-[13px] text-muted">Lowest mastery first — focus here next.</p>
          <div className="mt-3 flex flex-col gap-2.5">
            {overview.weakestTopics.map((t) => (
              <div key={t.topic} className="flex items-center gap-3">
                <span className="w-36 shrink-0 truncate text-[13px] capitalize">{t.topic}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-raised">
                  <div className={cx('h-full rounded-full', t.mastery >= 70 ? 'bg-success' : t.mastery >= 40 ? 'bg-warning' : 'bg-danger')} style={{ width: `${t.mastery}%` }} />
                </div>
                <span className="w-20 shrink-0 text-right text-[12px] text-muted">
                  {Math.round(t.mastery)}% · {t.attempts} tries
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recommendations */}
      {recs && (recs.dueReviews > 0 || recs.weakTopics.length > 0 || recs.inProgressLessons.length > 0) && (
        <Card className="p-5">
          <h3 className="text-[14px] font-semibold">Recommendations</h3>
          <ul className="mt-3 flex flex-col gap-2 text-[13.5px] leading-relaxed">
            {recs.dueReviews > 0 && (
              <li className="flex gap-2">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-accent" />
                <span>
                  <span className="font-medium">{recs.dueReviews} cards</span> are due for review.
                </span>
              </li>
            )}
            {recs.weakTopics.length > 0 && (
              <li className="flex gap-2">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-warning" />
                <span>Review these topics: {recs.weakTopics.map((t) => t.topic).join(', ')}.</span>
              </li>
            )}
            {recs.inProgressLessons.length > 0 && (
              <li className="flex gap-2">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-info" />
                <span>
                  {recs.inProgressLessons.length} lesson{recs.inProgressLessons.length === 1 ? '' : 's'} in progress — finish one to keep momentum.
                </span>
              </li>
            )}
          </ul>
        </Card>
      )}

      <p className="text-[12.5px] text-faint">All figures derive from recorded activity. No performance or profitability is implied.</p>
    </div>
  )
}
