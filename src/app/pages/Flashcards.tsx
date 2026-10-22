import { AnimatePresence, motion } from 'motion/react'
import { Check, RotateCcw, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { StudyFrame } from '../components/Shell'
import { Summary, shuffle } from '../components/Summary'
import { Spinner } from '../components/ui'
import { useDeck } from '../lib/api'
import { cx } from '../lib/cx'
import type { Card, SessionResult } from '../../shared/types'

export function Flashcards() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data, isLoading } = useDeck(id)
  const [round, setRound] = useState(0)
  const order = useMemo(() => (data ? shuffle(data.cards) : []), [data, round])
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [results, setResults] = useState<SessionResult[]>([])
  const [direction, setDirection] = useState<1 | -1>(1)
  const [startedAt, setStartedAt] = useState(Date.now())

  const card: Card | undefined = order[index]
  const done = Boolean(data) && index >= order.length

  function answer(correct: boolean) {
    if (!card) return
    setDirection(correct ? 1 : -1)
    setResults((r) => [...r, { cardId: card.id, correct }])
    setFlipped(false)
    window.setTimeout(() => setIndex((i) => i + 1), 40)
  }

  function restart() {
    setRound((r) => r + 1)
    setIndex(0)
    setResults([])
    setFlipped(false)
    setStartedAt(Date.now())
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (done) return
      if (e.key === ' ' || e.key === 'Enter') (e.preventDefault(), setFlipped((f) => !f))
      if (e.key === 'ArrowRight') answer(true)
      if (e.key === 'ArrowLeft') answer(false)
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

  const known = results.filter((r) => r.correct).length

  return (
    <StudyFrame
      title={data.deck.title}
      progress={order.length ? Math.min(1, index / order.length) : 0}
      onExit={() => navigate(`/decks/${id}`)}
      right={!done && <span className="text-[13px] tabular-nums text-muted">{Math.min(index + 1, order.length)} of {order.length}</span>}
    >
      {done ? (
        <Summary deckId={data.deck.id} mode="flashcards" results={results} startedAt={startedAt} onAgain={restart} />
      ) : (
        <div className="flex flex-1 flex-col">
          <div className="flex items-center justify-between text-[13px] font-medium">
            <span className="inline-flex h-7 items-center rounded-[9px] bg-danger-soft px-2.5 tabular-nums text-danger">{results.length - known} still learning</span>
            <span className="inline-flex h-7 items-center rounded-[9px] bg-success-soft px-2.5 tabular-nums text-success">{known} known</span>
          </div>

          <div className="relative mt-5 flex-1 [perspective:1600px]" style={{ minHeight: 360 }}>
            <AnimatePresence initial={false} custom={direction} mode="popLayout">
              {card && (
                <motion.button
                  key={card.id}
                  type="button"
                  custom={direction}
                  onClick={() => setFlipped((f) => !f)}
                  variants={{ exit: (d: number) => ({ opacity: 0, x: d * 160, rotate: d * 4, transition: { duration: 0.3 } }) }}
                  initial={{ opacity: 0, x: 0, scale: 0.96 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  exit="exit"
                  transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                  className="preserve-3d absolute inset-0 w-full cursor-pointer text-left"
                  aria-label="Flip card"
                >
                  <motion.div animate={{ rotateY: flipped ? 180 : 0 }} transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }} className="preserve-3d relative size-full">
                    <Face label="Term" className="bg-surface">
                      {card.hasImage && <img src={`/api/decks/${data.deck.id}/cards/${card.id}/image`} alt="" className="mb-6 max-h-[180px] rounded-[16px] object-cover" />}
                      <p className="text-balance text-center text-[32px] font-bold tracking-tight sm:text-[40px]">{card.term}</p>
                    </Face>
                    <Face label="Definition" className="bg-fg text-white [transform:rotateY(180deg)]">
                      <p className="text-balance text-center text-[22px] font-medium leading-snug sm:text-[28px]">{card.definition}</p>
                    </Face>
                  </motion.div>
                </motion.button>
              )}
            </AnimatePresence>
          </div>

          <div className="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
            <button type="button" onClick={() => answer(false)} className="inline-flex h-14 items-center justify-center gap-2 rounded-[16px] border-2 border-danger/30 bg-danger-soft text-[15px] font-semibold text-danger transition-colors hover:border-danger">
              <X className="size-5" />
              Still learning
            </button>
            <button type="button" onClick={() => setFlipped((f) => !f)} aria-label="Flip" className="grid size-14 place-items-center rounded-[16px] border border-line-strong bg-surface text-muted transition-colors hover:text-fg">
              <RotateCcw className="size-5" />
            </button>
            <button type="button" onClick={() => answer(true)} className="inline-flex h-14 items-center justify-center gap-2 rounded-[16px] border-2 border-success/30 bg-success-soft text-[15px] font-semibold text-success transition-colors hover:border-success">
              <Check className="size-5" />
              Got it
            </button>
          </div>
          <p className="mt-3 text-center text-[12.5px] text-faint">Space flips, arrow keys answer</p>
        </div>
      )}
    </StudyFrame>
  )
}

function Face({ label, className, children }: { label: string; className?: string; children: React.ReactNode }) {
  return (
    <div className={cx('backface-hidden absolute inset-0 flex flex-col items-center justify-center rounded-[28px] p-8 shadow-float sm:p-12', className)}>
      <span className="absolute left-6 top-5 text-[12.5px] font-medium opacity-50">{label}</span>
      {children}
    </div>
  )
}
