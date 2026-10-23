import { CheckCircle2, Circle, LayoutGrid, Play } from 'lucide-react'
import { useNavigate, useParams } from 'react-router'

import { Markdown } from '../components/Markdown'
import { Badge, Button, Card, EmptyState, PageHeader, Spinner } from '../components/ui'
import { useProject, useProjects, useSetProjectStatus, useToggleMilestone } from '../lib/api'
import { cx } from '../lib/cx'
import type { ProjectStatus } from '../../shared/types'

const statusMeta: Record<ProjectStatus, { label: string; tone: 'neutral' | 'accent' | 'success' }> = {
  not_started: { label: 'Not started', tone: 'neutral' },
  in_progress: { label: 'In progress', tone: 'accent' },
  done: { label: 'Done', tone: 'success' },
}

/** Capstone project list with progress and status control. */
export function Projects() {
  const { data, isLoading } = useProjects()
  const navigate = useNavigate()

  if (isLoading) return <Spinner />
  const items = data?.items ?? []

  if (items.length === 0) {
    return <EmptyState icon={<LayoutGrid />} title="No projects" description="Capstone projects will appear here once your account has curriculum data." />
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Capstone projects" subtitle="End-to-end builds that pull the whole curriculum together." />
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((p) => {
          const meta = statusMeta[p.status]
          const pct = p.milestoneCount ? Math.round((p.milestonesDone / p.milestoneCount) * 100) : 0
          return (
            <Card key={p.id} className="flex flex-col p-5">
              <div className="flex items-start justify-between gap-2">
                <span className="grid size-9 place-items-center rounded-tile bg-surface-2 text-[14px] font-semibold text-muted">{p.key}</span>
                <Badge tone={meta.tone}>{meta.label}</Badge>
              </div>
              <h3 className="mt-3 text-[15px] font-medium leading-snug">{p.title}</h3>
              {p.objectives.length > 0 && <p className="mt-1 line-clamp-2 text-[13.5px] leading-relaxed text-muted">{p.objectives[0]}</p>}

              {p.milestoneCount ? (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-[12px] text-muted">
                    <span>
                      {p.milestonesDone}/{p.milestoneCount} milestones
                    </span>
                    <span>{pct}%</span>
                  </div>
                  <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-raised">
                    <div className="h-full rounded-full bg-accent transition-[width] duration-500" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              ) : (
                <div className="mt-4 text-[12px] text-muted">No milestones</div>
              )}

              <Button className="mt-4 self-start" variant="secondary" onClick={() => navigate(`/projects/${p.id}`)}>
                <Play className="size-4" />
                Open
              </Button>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

/** One project: objectives, steps, milestones, and the research-only framing. */
export function Project() {
  const { id } = useParams()
  const { data, isLoading } = useProject(id)
  const setStatus = useSetProjectStatus()
  const toggle = useToggleMilestone()

  if (isLoading) return <Spinner />
  if (!data) return <EmptyState icon={<LayoutGrid />} title="Project not found" description="This project may have been removed." />

  const { project, milestones } = data
  const meta = statusMeta[project.status]

  const sections: { title: string; items: string[] }[] = [
    { title: 'Objectives', items: project.objectives },
    { title: 'Prerequisites', items: project.prerequisites },
    { title: 'Steps', items: project.steps },
    { title: 'Required files', items: project.requiredFiles },
    { title: 'Acceptance tests', items: project.acceptanceTests },
    { title: 'Failure scenarios', items: project.failureScenarios },
    { title: 'Security checks', items: project.securityChecks },
  ]

  return (
    <div className="mx-auto flex max-w-[760px] flex-col gap-5">
      <div className="flex items-center gap-3">
        <span className="grid size-11 place-items-center rounded-tile bg-surface-2 text-[16px] font-semibold text-muted">{project.key}</span>
        <div className="min-w-0">
          <h1 className="text-[21px] font-semibold tracking-tight">{project.title}</h1>
          <div className="mt-1 flex items-center gap-2">
            <Badge tone={meta.tone}>{meta.label}</Badge>
            {milestones.length > 0 && (
              <span className="text-[12.5px] text-muted">
                {milestones.filter((m) => m.done).length}/{milestones.length} milestones
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {(['not_started', 'in_progress', 'done'] as ProjectStatus[]).map((s) => (
          <Button
            key={s}
            variant={project.status === s ? 'primary' : 'secondary'}
            size="sm"
            loading={setStatus.isPending}
            onClick={() => setStatus.mutate({ id: project.id, status: s })}
          >
            {statusMeta[s].label}
          </Button>
        ))}
      </div>

      {project.completionCriteria && (
        <Card className="border-l-2 border-accent/40 p-5">
          <h3 className="text-[13.5px] font-semibold uppercase tracking-wide text-muted">Completion criteria</h3>
          <p className="mt-1.5 text-[14px] leading-relaxed">{project.completionCriteria}</p>
        </Card>
      )}

      {milestones.length > 0 && (
        <Card className="p-5">
          <h3 className="text-[13.5px] font-semibold uppercase tracking-wide text-muted">Milestones</h3>
          <div className="mt-3 flex flex-col gap-1">
            {milestones.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => toggle.mutate({ milestoneId: m.id, done: !m.done })}
                className="flex items-start gap-2.5 rounded-tile px-2 py-2 text-left transition-colors hover:bg-surface-2"
              >
                {m.done ? <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" /> : <Circle className="mt-0.5 size-4 shrink-0 text-faint" />}
                <span className="min-w-0">
                  <span className={cx('block text-[14px]', m.done && 'text-muted line-through')}>{m.title}</span>
                  {m.detail && <span className="mt-0.5 block text-[13px] text-muted">{m.detail}</span>}
                </span>
              </button>
            ))}
          </div>
        </Card>
      )}

      {sections
        .filter((s) => s.items.length > 0)
        .map((section) => (
          <Card key={section.title} className="p-5">
            <h3 className="text-[13.5px] font-semibold uppercase tracking-wide text-muted">{section.title}</h3>
            <div className="mt-2">
              {section.title === 'Steps' ? (
                <Markdown source={section.items.map((s, i) => `${i + 1}. ${s}`).join('\n')} />
              ) : (
                <ul className="flex flex-col gap-1.5 text-[14px] leading-relaxed">
                  {section.items.map((item, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="mt-2 size-1 shrink-0 rounded-full bg-faint" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Card>
        ))}

      {project.finalAssessment && (
        <Card className="p-5">
          <h3 className="text-[13.5px] font-semibold uppercase tracking-wide text-muted">Final assessment</h3>
          <Markdown source={project.finalAssessment} className="mt-1.5 text-[14px] leading-relaxed" />
        </Card>
      )}

      <p className="text-[12.5px] leading-relaxed text-faint">
        This project is educational. It builds research tooling only — no live trading, no order routing, and no performance or profitability claims.
      </p>
    </div>
  )
}
