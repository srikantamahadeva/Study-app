import { AnimatePresence, motion } from 'motion/react'
import { Check, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { StudyFrame } from '../components/Shell'
import { Summary, shuffle } from '../components/Summary'
import { Spinner } from '../components/ui'
import { useDeck } from '../lib/api'
import { cx } from '../lib/cx'
import type { Card, SessionResult } from '../../shared/types'

const ROUND = 10

type Question = { card: Card; options: string[]; answer: number }

function buildRound(cards: Card[]): Question[] {
  // Weak and due cards first, then the rest, so each round targets what you
  // are most likely to forget.
  const now = Date.now()
  const prioritised = [...cards].sort((a, b) => {
    const dueA = a.progress.nextDue === null || a.progress.nextDue <= now ? 0 : 1
    const dueB = b.progress.nextDue === null || b.progress.nextDue <= now ? 0 : 1
    return dueA - dueB || a.progress.mastery - b.progress.mastery || Math.random() - 0.5
  })
  const chosen = shuffle(prioritised.slice(0, Math.min(ROUND, cards.length)))
  return chosen.map((card) => {
    const distractors = shuffle(cards.filter((c) => c.id !== card.id)).slice(0, 3)
    const options = shuffle([card, ...distractors].map((c) => c.definition))
    return { card, options, answer: options.indexOf(card.definition) }
  })
}

export function Learn() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data, isLoading } = useDeck(id)
  const [round, setRound] = useState(0)
  const questions = useMemo(() => (data ? buildRound(data.cards) : []), [data, round])
  const [index, setIndex] = useState(0)
  const [picked, setPicked] = useState<number | null>(null)
  const [results, setResults] = useState<SessionResult[]>([])
  const [startedAt, setStartedAt] = useState(Date.now())

  const question = questions[index]
  const done = Boolean(data) && index >= questions.length

  function pick(option: number) {
    if (picked !== null || !question) return
    setPicked(option)
    const correct = option === question.answer
    setResults((r) => [...r, { cardId: question.card.id, correct }])
    window.setTimeout(
      () => {
        setPicked(null)
        setIndex((i) => i + 1)
      },
      correct ? 700 : 1400,
    )
  }

  function restart() {
    setRound((r) => r + 1)
    setIndex(0)
    setPicked(null)
    setResults([])
    setStartedAt(Date.now())
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const n = Number(e.key)
      if (n >= 1 && n <= 4) pick(n - 1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  if (isLoading || !data) {
    return (
      <div className="grid min-h-screen place-items-center">
        <Spinner />
      </div>
    )
  }

  const score = results.filter((r) => r.correct).length

  return (
    <StudyFrame
      title={data.deck.title}
      progress={questions.length ? index / questions.length : 0}
      onExit={() => navigate(`/decks/${id}`)}
      right={!done && <span className="text-[13px] tabular-nums text-muted">{score} correct</span>}
    >
      {done ? (
        <Summary deckId={data.deck.id} mode="learn" results={results} startedAt={startedAt} onAgain={restart} />
      ) : (
        <AnimatePresence mode="wait">
          {question && (
            <motion.div key={question.card.id + index} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }} className="flex flex-1 flex-col">
              <div className="flex min-h-[220px] flex-col items-center justify-center rounded-[28px] bg-surface p-8 shadow-float sm:min-h-[260px]">
                <span className="text-[12.5px] font-medium text-faint">
                  {index + 1} of {questions.length}
                </span>
                {question.card.hasImage && <img src={`/api/decks/${data.deck.id}/cards/${question.card.id}/image`} alt="" className="mt-4 max-h-[140px] rounded-[16px] object-cover" />}
                <p className="mt-4 text-balance text-center text-[30px] font-bold tracking-tight sm:text-[38px]">{question.card.term}</p>
                <p className="mt-3 text-[14px] text-muted">Choose the definition</p>
              </div>
              <div className="mt-4 grid gap-2.5 sm:grid-cols-2">
                {question.options.map((option, i) => {
                  const isAnswer = i === question.answer
                  const isPicked = picked === i
                  const state = picked === null ? 'idle' : isAnswer ? 'correct' : isPicked ? 'wrong' : 'dim'
                  return (
                    <button
                      key={i}
                      type="button"
                      onClick={() => pick(i)}
                      disabled={picked !== null}
                      className={cx(
                        'flex min-h-[72px] items-center gap-3 rounded-[18px] border-2 bg-surface px-4 py-3 text-left text-[15px] leading-snug shadow-card transition-[border-color,background-color,transform,opacity] duration-200',
                        state === 'idle' && 'border-transparent hover:border-accent/50 hover:bg-accent-soft/40 active:scale-[0.99]',
                        state === 'correct' && 'border-success bg-success-soft',
                        state === 'wrong' && 'border-danger bg-danger-soft',
                        state === 'dim' && 'border-transparent opacity-50',
                      )}
                    >
                      <span
                        className={cx(
                          'grid size-7 shrink-0 place-items-center rounded-[9px] text-[12.5px] font-semibold',
                          state === 'correct' ? 'bg-success text-white' : state === 'wrong' ? 'bg-danger text-white' : 'bg-surface-2 text-muted',
                        )}
                      >
                        {state === 'correct' ? <Check className="size-4" /> : state === 'wrong' ? <X className="size-4" /> : i + 1}
                      </span>
                      <span className="flex-1">{option}</span>
                    </button>
                  )
                })}
              </div>
              <p className="mt-4 text-center text-[12.5px] text-faint">Press 1 to 4 to answer</p>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </StudyFrame>
  )
}
