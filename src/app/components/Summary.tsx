import { motion } from 'motion/react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

import { recordSession, useInvalidate } from '../lib/api'
import { Button } from './ui'
import type { SessionResult, StudyMode } from '../../shared/types'

/** End-of-round screen. Records the session once, then shows the result. */
export function Summary({
  deckId,
  mode,
  results,
  startedAt,
  onAgain,
  extra,
}: {
  deckId: string
  mode: StudyMode
  results: SessionResult[]
  startedAt: number
  onAgain: () => void
  extra?: React.ReactNode
}) {
  const navigate = useNavigate()
  const invalidate = useInvalidate()
  const [saved, setSaved] = useState<{ accuracy: number } | null>(null)
  const [error, setError] = useState('')
  const correct = results.filter((r) => r.correct).length
  const accuracy = results.length ? Math.round((correct / results.length) * 100) : 0

  useEffect(() => {
    let cancelled = false
    recordSession(deckId, mode, results, Date.now() - startedAt)
      .then((r) => {
        if (cancelled) return
        setSaved({ accuracy: r.session.accuracy })
        void invalidate('deck', 'decks', 'stats', 'me')
      })
      .catch((e: Error) => !cancelled && setError(e.message))
    return () => {
      cancelled = true
    }
    // Record exactly once for this set of results.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const headline = accuracy === 100 ? 'Perfect round' : accuracy >= 80 ? 'Nicely done' : accuracy >= 50 ? 'Getting there' : 'Keep going'

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }} className="mx-auto flex w-full max-w-[520px] flex-1 flex-col items-center justify-center text-center">
      <div className="relative grid size-40 place-items-center">
        <svg viewBox="0 0 100 100" className="absolute inset-0 -rotate-90">
          <circle cx="50" cy="50" r="44" fill="none" stroke="var(--color-raised)" strokeWidth="8" />
          <motion.circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke={accuracy >= 80 ? 'var(--color-success)' : accuracy >= 50 ? 'var(--color-warning)' : 'var(--color-danger)'}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={2 * Math.PI * 44}
            initial={{ strokeDashoffset: 2 * Math.PI * 44 }}
            animate={{ strokeDashoffset: 2 * Math.PI * 44 * (1 - accuracy / 100) }}
            transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
          />
        </svg>
        <span className="text-[36px] font-bold tabular-nums tracking-tight">{accuracy}%</span>
      </div>
      <h1 className="mt-6 text-[28px] font-bold tracking-[-0.02em]">{headline}</h1>
      <p className="mt-2 text-[15px] text-muted">
        {correct} of {results.length} correct in {Math.max(1, Math.round((Date.now() - startedAt) / 60_000))} {Math.round((Date.now() - startedAt) / 60_000) <= 1 ? 'minute' : 'minutes'}
      </p>
      {extra}
      <p className="mt-3 h-5 text-[13px] text-faint">{error ? <span className="text-danger">{error}</span> : saved ? 'Progress saved' : 'Saving progress'}</p>
      <div className="mt-6 grid w-full grid-cols-2 gap-2">
        <Button onClick={() => navigate(`/decks/${deckId}`)}>Back to deck</Button>
        <Button variant="primary" onClick={onAgain}>
          Go again
        </Button>
      </div>
    </motion.div>
  )
}

export function shuffle<T>(items: T[]): T[] {
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}
