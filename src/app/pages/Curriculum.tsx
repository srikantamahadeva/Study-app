import { BookOpen, CheckCircle2, Circle, Play, Target, TrendingUp } from 'lucide-react'
import { Link } from 'react-router'

import { Badge, Card, EmptyState, PageHeader, Skeleton } from '../components/ui'
import { useCurriculum, useResume } from '../lib/api'
import { cx } from '../lib/cx'
import type { LessonSummary } from '../../shared/types'

const statusIcon = { completed: CheckCircle2, in_progress: Play, not_started: Circle } as const
const statusTone = { completed: 'success', in_progress: 'accent', not_started: 'neutral' } as const

function LessonRow({ lesson }: { lesson: LessonSummary }) {
  const Icon = statusIcon[lesson.status]

  return (
    <Link
      to={`/lessons/${lesson.id}`}
      className="group flex items-center gap-3 rounded-tile px-3 py-2.5 transition-colors hover:bg-surface-2"
    >
      <Icon className={cx('size-4 shrink-0', lesson.status === 'completed' ? 'text-success' : lesson.status === 'in_progress' ? 'text-accent' : 'text-faint')} />
      <span className="min-w-0 flex-1 truncate text-[14px]">{lesson.title}</span>
      {lesson.status === 'in_progress' && lesson.percent > 0 && (
        <span className="w-16 shrink-0 text-right text-[12px] text-faint">{lesson.percent}%</span>
      )}
      <Badge tone={statusTone[lesson.status]} className="hidden shrink-0 sm:inline-flex">
        {lesson.status.replace('_', ' ')}
      </Badge>
      <span className="shrink-0 text-[12px] text-faint">{lesson.minutes}m</span>
    </Link>
  )
}

export function Curriculum() {
  const { data, isLoading } = useCurriculum()
  const { data: resume } = useResume()

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!data || data.courses.length === 0) {
    return (
      <EmptyState
        icon={<BookOpen />}
        title="No curriculum yet"
        description="Your account has no course material. Run the seeder to install the sample trading curriculum."
      />
    )
  }

  const course = data.courses[0]
  const { progress } = data

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title={course.title} subtitle={course.description} />

      {/* Overview strip */}
      <div className="grid gap-3 sm:grid-cols-3">
        <Card className="flex items-center gap-3 p-4">
          <div className="grid size-10 place-items-center rounded-tile bg-accent-soft text-accent">
            <TrendingUp className="size-5" />
          </div>
          <div>
            <p className="text-[20px] font-semibold">{progress.percent}%</p>
            <p className="text-[13px] text-muted">Complete</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="grid size-10 place-items-center rounded-tile bg-success-soft text-success">
            <CheckCircle2 className="size-5" />
          </div>
          <div>
            <p className="text-[20px] font-semibold">
              {progress.lessonsCompleted}/{progress.lessonsTotal}
            </p>
            <p className="text-[13px] text-muted">Lessons done</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3 p-4">
          <div className="grid size-10 place-items-center rounded-tile bg-warning-soft text-warning">
            <Target className="size-5" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-[14px] font-medium">{resume?.lesson ? resume.lesson.title : 'All done'}</p>
            <p className="text-[13px] text-muted">{resume?.lesson ? 'Up next' : 'Nothing pending'}</p>
          </div>
        </Card>
      </div>

      {/* Progress bar */}
      <div className="h-2 overflow-hidden rounded-full bg-raised">
        <div className="h-full rounded-full bg-accent transition-[width] duration-500" style={{ width: `${progress.percent}%` }} />
      </div>

      {/* Module tree */}
      <div className="flex flex-col gap-3">
        {course.modules.map((module) => (
          <Card key={module.id} className="p-5">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-tile bg-surface-2 text-[13px] font-semibold text-muted">
                {module.number}
              </span>
              <div className="min-w-0">
                <h3 className="text-[16px] font-semibold tracking-tight">{module.title}</h3>
                <p className="mt-0.5 text-[13.5px] text-muted">{module.summary}</p>
              </div>
            </div>
            <div className="mt-3 flex flex-col divide-y divide-line/60">
              {module.lessons.map((lesson) => (
                <LessonRow key={lesson.id} lesson={lesson} />
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
