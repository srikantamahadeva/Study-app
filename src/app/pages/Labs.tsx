import { CheckCircle2, FlaskConical, XCircle } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { Badge, Button, Card, EmptyState, PageHeader, Spinner } from '../components/ui'
import { useExercise, useExercises, useSubmitExercise } from '../lib/api'
import { cx } from '../lib/cx'

const langTone = { pine: 'accent', python: 'success' } as const

/** Exercise list, filterable by language. */
export function Labs() {
  const [language, setLanguage] = useState<'pine' | 'python' | undefined>(undefined)
  const { data, isLoading } = useExercises(language)
  const navigate = useNavigate()

  if (isLoading) return <Spinner />
  const items = data?.items ?? []

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Coding labs" subtitle="Practice Pine Script and Python with server-side static checks." />

      <div className="flex rounded-control bg-surface-2 p-0.5">
        {(['pine', 'python'] as const).map((lang) => (
          <button
            key={lang}
            type="button"
            onClick={() => setLanguage(lang)}
            className={cx('h-8 rounded-tile px-3 text-[13px] font-medium capitalize transition-colors', language === lang ? 'bg-surface text-fg shadow-card' : 'text-muted')}
          >
            {lang}
          </button>
        ))}
      </div>

      {items.length === 0 ? (
        <EmptyState icon={<FlaskConical />} title="No exercises" description="There are no exercises for this language yet." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((ex) => (
            <Card key={ex.id} className="flex flex-col p-5">
              <div className="flex items-center gap-2">
                <Badge tone={langTone[ex.language]}>{ex.language}</Badge>
              </div>
              <h3 className="mt-2 text-[15px] font-medium">{ex.title}</h3>
              <p className="mt-1 line-clamp-2 text-[13.5px] leading-relaxed text-muted">{ex.requirement}</p>
              <Button className="mt-4 self-start" variant="secondary" onClick={() => navigate(`/labs/${ex.id}`)}>
                Open exercise
              </Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

/** Single exercise: starter code, editor, submit with static-check results. */
export function Exercise() {
  const { id } = useParams()
  const { data, isLoading } = useExercise(id)
  const submit = useSubmitExercise()
  const [code, setCode] = useState<string | null>(null)
  const [result, setResult] = useState<Awaited<ReturnType<typeof submit.mutateAsync>> | null>(null)

  if (isLoading) return <Spinner />
  if (!data) return <EmptyState icon={<FlaskConical />} title="Exercise not found" description="This exercise may have been removed." />

  const editor = code ?? data.starterCode

  function run() {
    submit.mutate({ exerciseId: data!.id, code: editor }, { onSuccess: (res) => setResult(res) })
  }

  const checks = result?.result.staticChecks ?? []

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center gap-2">
        <Badge tone={langTone[data.language]}>{data.language}</Badge>
        <h1 className="text-[20px] font-semibold tracking-tight">{data.title}</h1>
      </div>

      <Card className="p-5">
        <h3 className="text-[13.5px] font-semibold uppercase tracking-wide text-muted">Requirement</h3>
        <p className="mt-1.5 text-[14px] leading-relaxed">{data.requirement}</p>
        {data.expectedBehavior && (
          <>
            <h3 className="mt-4 text-[13.5px] font-semibold uppercase tracking-wide text-muted">Expected behavior</h3>
            <p className="mt-1.5 text-[14px] leading-relaxed">{data.expectedBehavior}</p>
          </>
        )}
      </Card>

      <Card className="overflow-hidden">
        <textarea
          value={editor}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          className="h-72 w-full resize-y bg-fg/95 p-4 font-mono text-[13px] leading-relaxed text-white/90 outline-none"
        />
        <div className="flex items-center justify-between border-t border-line px-4 py-3">
          <p className="text-[12.5px] text-muted">
            {data.language === 'pine' ? 'Static checks only — Pine compiles in TradingView.' : 'Python runs in your browser sandbox (Pyodide).'}
          </p>
          <Button variant="primary" loading={submit.isPending} onClick={run}>
            Run checks
          </Button>
        </div>
      </Card>

      {result && (
        <Card className="p-5">
          <div className="flex items-center gap-2">
            {result.passed ? <CheckCircle2 className="size-5 text-success" /> : <XCircle className="size-5 text-danger" />}
            <span className={cx('text-[15px] font-semibold', result.passed ? 'text-success' : 'text-danger')}>
              {result.passed ? 'All checks passed' : 'Some checks failed'}
            </span>
          </div>
          <div className="mt-3 flex flex-col gap-1.5">
            {checks.map((check, i) => (
              <div key={i} className="flex items-start gap-2 text-[13.5px]">
                {check.passed ? <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" /> : <XCircle className="mt-0.5 size-4 shrink-0 text-danger" />}
                <span className={cx(check.passed ? 'text-muted' : 'text-fg')}>{check.message}</span>
              </div>
            ))}
          </div>
          {result.result.note && <p className="mt-3 text-[12.5px] leading-relaxed text-faint">{result.result.note}</p>}
        </Card>
      )}

      {data.explanation && (
        <Card className="p-5">
          <h3 className="text-[13.5px] font-semibold uppercase tracking-wide text-muted">Explanation</h3>
          <p className="mt-1.5 text-[14px] leading-relaxed text-muted">{data.explanation}</p>
        </Card>
      )}
    </div>
  )
}
