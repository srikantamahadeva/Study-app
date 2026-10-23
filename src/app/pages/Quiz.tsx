import { CheckCircle2, Play, RotateCcw, Target, XCircle } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import { Badge, Button, Card, PageHeader, Spinner, Textarea } from '../components/ui'
import { useAnswerQuestion, useDueCards, useMastery, useReviewCard, useReviewStats, useStartQuiz } from '../lib/api'
import { cx } from '../lib/cx'
import type { AnswerResult, Question, QuizSession, ReviewGrade } from '../../shared/types'

const GRADES: { grade: ReviewGrade; label: string; tone: string }[] = [
  { grade: 'again', label: 'Again', tone: 'bg-danger text-white' },
  { grade: 'difficult', label: 'Hard', tone: 'bg-warning text-white' },
  { grade: 'good', label: 'Good', tone: 'bg-success text-white' },
  { grade: 'easy', label: 'Easy', tone: 'bg-accent text-white' },
]

/** One question card. Emits the graded result so the runner can advance. */
function QuestionCard({ question, onAnswer }: { question: Question; onAnswer: (result: AnswerResult, correct: boolean) => void }) {
  const answer = useAnswerQuestion()
  const [givenIndex, setGivenIndex] = useState<number | null>(null)
  const [text, setText] = useState('')
  const [result, setResult] = useState<AnswerResult | null>(null)

  const isChoice = question.kind === 'mcq' || question.kind === 'truefalse' || question.options.length > 0
  const canSubmit = isChoice ? givenIndex !== null : text.trim().length > 0

  function submit() {
    if (!canSubmit) return
    const payload = {
      sessionId: 'local',
      questionId: question.id,
      ...(isChoice ? { givenIndex: givenIndex! } : { givenAnswer: text }),
    }
    answer.mutate(payload, {
      onSuccess: (res) => {
        setResult(res)
        onAnswer(res, res.correct)
      },
    })
  }

  return (
    <Card className="flex flex-col gap-4 p-6">
      <div className="flex items-center gap-2">
        <Badge tone="accent">{question.kind.replace('_', ' ')}</Badge>
        {question.topics.map((t) => (
          <Badge key={t} tone="neutral">{t}</Badge>
        ))}
      </div>

      <p className="text-[16px] font-medium leading-relaxed">{question.prompt}</p>

      {isChoice ? (
        <div className="flex flex-col gap-2">
          {question.options.map((option, i) => {
            const chosen = givenIndex === i
            const showCorrect = result?.correct === true && chosen
            const showWrong = result?.correct === false && chosen
            return (
              <button
                key={i}
                type="button"
                disabled={Boolean(result)}
                onClick={() => setGivenIndex(i)}
                className={cx(
                  'flex items-center gap-2.5 rounded-tile border px-3.5 py-2.5 text-left text-[14px] transition-colors',
                  showCorrect
                    ? 'border-success bg-success-soft'
                    : showWrong
                      ? 'border-danger bg-danger-soft'
                      : chosen
                        ? 'border-accent bg-accent-soft'
                        : 'border-line-strong hover:bg-surface-2',
                )}
              >
                <span className="grid size-5 shrink-0 place-items-center rounded-full border border-line-strong text-[12px] font-medium">
                  {String.fromCharCode(65 + i)}
                </span>
                <span className="flex-1">{option}</span>
                {showCorrect && <CheckCircle2 className="size-4 text-success" />}
                {showWrong && <XCircle className="size-4 text-danger" />}
              </button>
            )
          })}
        </div>
      ) : (
        <Textarea
          value={text}
          disabled={Boolean(result)}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type your answer…"
          className="min-h-[100px]"
        />
      )}

      {result ? (
        <div className="flex flex-col gap-3 rounded-tile bg-surface-2 p-4">
          <div className="flex items-center gap-2">
            {result.correct ? <CheckCircle2 className="size-5 text-success" /> : <XCircle className="size-5 text-danger" />}
            <span className={cx('text-[14px] font-semibold', result.correct ? 'text-success' : 'text-danger')}>
              {result.correct ? 'Correct' : 'Not quite'}
            </span>
          </div>
          {result.explanation && <p className="text-[13.5px] leading-relaxed text-muted">{result.explanation}</p>}
          {!result.correct && result.acceptedAnswers.length > 0 && (
            <p className="text-[13px] text-muted">
              Accepted: <span className="font-medium text-fg">{result.acceptedAnswers.join(', ')}</span>
            </p>
          )}
          {result.reviewCardCreated && (
            <p className="text-[12.5px] text-accent">Added to your review queue for tomorrow.</p>
          )}
        </div>
      ) : (
        <Button variant="primary" loading={answer.isPending} disabled={!canSubmit} onClick={submit}>
          Submit answer
        </Button>
      )}
    </Card>
  )
}

/** Practice quiz: start a session, answer questions, see explanations. */
export function Quiz() {
  const [session, setSession] = useState<QuizSession | null>(null)
  const [index, setIndex] = useState(0)
  const [correctCount, setCorrectCount] = useState(0)
  const start = useStartQuiz()

  function begin() {
    start.mutate({ limit: 10 }, { onSuccess: (s) => { setSession(s); setIndex(0); setCorrectCount(0) } })
  }

  function onAnswer(result: AnswerResult) {
    if (result.correct) setCorrectCount((c) => c + 1)
  }

  function next() {
    if (!session) return
    if (index + 1 < session.questions.length) setIndex(index + 1)
    else setSession(null) // finished
  }

  if (session) {
    const question = session.questions[index]
    const finished = index + 1 >= session.questions.length
    return (
      <div className="mx-auto flex max-w-[680px] flex-col gap-4">
        <div className="flex items-center justify-between text-[13px] text-muted">
          <span>
            Question {index + 1} of {session.questions.length}
          </span>
          <span className="font-medium text-fg">{correctCount} correct</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-raised">
          <div className="h-full rounded-full bg-accent transition-[width] duration-300" style={{ width: `${((index + (finished ? 1 : 0)) / session.questions.length) * 100}%` }} />
        </div>
        <QuestionCard key={question.id} question={question} onAnswer={onAnswer} />
        <Button variant="secondary" onClick={next}>
          {finished ? 'Finish' : 'Next question'}
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-[680px] flex-col gap-6">
      <PageHeader title="Quiz" subtitle="Test your recall across every topic you have studied." />
      <Card className="flex flex-col items-center gap-4 p-10 text-center">
        <div className="grid size-14 place-items-center rounded-card bg-accent-soft text-accent">
          <Target className="size-7" />
        </div>
        <p className="text-[15px] text-muted">Answer 10 questions drawn from the question bank. Wrong answers join your review queue.</p>
        <Button variant="primary" size="md" loading={start.isPending} onClick={begin}>
          <Play className="size-4" />
          Start quiz
        </Button>
      </Card>
      <MasteryPanel />
      <ReviewQueuePanel />
    </div>
  )
}

/** Per-topic mastery bars, weakest first. */
export function MasteryPanel() {
  const { data, isLoading } = useMastery()
  if (isLoading) return <Spinner />
  if (!data || data.items.length === 0) return null

  return (
    <Card className="p-5">
      <h3 className="text-[14px] font-semibold">Topic mastery</h3>
      <div className="mt-3 flex flex-col gap-2.5">
        {data.items.slice(0, 10).map((row) => (
          <div key={row.topic} className="flex items-center gap-3">
            <span className="w-32 shrink-0 truncate text-[13px] capitalize">{row.topic}</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-raised">
              <div
                className={cx('h-full rounded-full', row.mastery >= 70 ? 'bg-success' : row.mastery >= 40 ? 'bg-warning' : 'bg-danger')}
                style={{ width: `${row.mastery}%` }}
              />
            </div>
            <span className="w-10 shrink-0 text-right text-[12.5px] text-muted">{Math.round(row.mastery)}%</span>
          </div>
        ))}
      </div>
    </Card>
  )
}

/** Spaced-repetition review queue with grade buttons. */
export function ReviewQueuePanel() {
  const { data: due } = useDueCards()
  const { data: stats } = useReviewStats()
  const review = useReviewCard()
  const [current, setCurrent] = useState(0)
  const [flipped, setFlipped] = useState(false)

  const card = due?.items[Math.min(current, (due?.items.length ?? 1) - 1)]

  function grade(g: ReviewGrade) {
    if (!card) return
    review.mutate(
      { cardId: card.cardId, grade: g },
      {
        onSuccess: () => {
          setFlipped(false)
          setCurrent((c) => c + 1)
        },
      },
    )
  }

  if (!due || due.items.length === 0 || !card) {
    return (
      <Card className="p-5">
        <h3 className="text-[14px] font-semibold">Review queue</h3>
        <p className="mt-1 text-[13.5px] text-muted">Nothing due right now. Cards resurface on a spaced schedule.</p>
      </Card>
    )
  }

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-[14px] font-semibold">Review queue</h3>
        {stats && (
          <span className="text-[12.5px] text-muted">
            {due.dueCount} due · {stats.totalCards} total
          </span>
        )}
      </div>

      <div className="mt-3 flex flex-col gap-3">
        <button
          type="button"
          onClick={() => setFlipped((f) => !f)}
          className="rounded-tile border border-line-strong bg-surface-2 p-5 text-left transition-colors hover:bg-surface"
        >
          <p className="text-[15px] font-medium">{card.front}</p>
          {flipped ? (
            <p className="mt-2 text-[14px] leading-relaxed text-muted">{card.back}</p>
          ) : (
            <p className="mt-2 text-[13px] text-faint">Tap to reveal the answer</p>
          )}
        </button>

        {flipped && (
          <div className="grid grid-cols-4 gap-2">
            {GRADES.map((g) => (
              <Button key={g.grade} variant="secondary" className={cx('h-11 border-0', g.tone)} loading={review.isPending} onClick={() => grade(g.grade)}>
                {g.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}

/** Standalone flashcard review route (linked from the Cards page). */
export function Review() {
  return (
    <div className="mx-auto flex max-w-[680px] flex-col gap-6">
      <PageHeader title="Review" subtitle="Work through cards that are due." />
      <ReviewQueuePanel />
      <Link to="/quiz" className="inline-flex items-center gap-1.5 text-[13.5px] text-muted hover:text-fg">
        <RotateCcw className="size-4" />
        Take a quiz instead
      </Link>
    </div>
  )
}
