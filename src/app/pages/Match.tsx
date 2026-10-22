import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { StudyFrame } from '../components/Shell'
import { Summary, shuffle } from '../components/Summary'
import { Spinner } from '../components/ui'
import { useDeck } from '../lib/api'
import { cx } from '../lib/cx'
import type { Card, SessionResult } from '../../shared/types'

const PAIRS = 6

type Tile = { key: string; cardId: string; text: string; side: 'term' | 'definition' }

function buildTiles(cards: Card[]): Tile[] {
  const chosen = shuffle(cards).slice(0, Math.min(PAIRS, cards.length))
  return shuffle(
    chosen.flatMap((c) => [
      { key: `${c.id}-t`, cardId: c.id, text: c.term, side: 'term' as const },
      { key: `${c.id}-d`, cardId: c.id, text: c.definition, side: 'definition' as const },
    ]),
  )
}

export function Match() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data, isLoading } = useDeck(id)
  const [round, setRound] = useState(0)
  const tiles = useMemo(() => (data ? buildTiles(data.cards) : []), [data, round])
  const [selected, setSelected] = useState<string | null>(null)
  const [matched, setMatched] = useState<Set<string>>(new Set())
  const [wrong, setWrong] = useState<string[]>([])
  const [misses, setMisses] = useState<Record<string, number>>({})
  const [startedAt, setStartedAt] = useState(Date.now())
  const [elapsed, setElapsed] = useState(0)
  const done = tiles.length > 0 && matched.size === tiles.length

  useEffect(() => {
    if (done) return
    const t = window.setInterval(() => setElapsed(Date.now() - startedAt), 100)
    return () => window.clearInterval(t)
  }, [done, startedAt])

  function tap(tile: Tile) {
    if (matched.has(tile.key) || wrong.length) return
    if (!selected) return setSelected(tile.key)
    if (selected === tile.key) return setSelected(null)
    const other = tiles.find((t) => t.key === selected)!
    if (other.cardId === tile.cardId && other.side !== tile.side) {
      setMatched((m) => new Set([...m, selected, tile.key]))
      setSelected(null)
    } else {
      setWrong([selected, tile.key])
      setMisses((m) => ({ ...m, [other.cardId]: (m[other.cardId] ?? 0) + 1, [tile.cardId]: (m[tile.cardId] ?? 0) + 1 }))
      window.setTimeout(() => {
        setWrong([])
        setSelected(null)
      }, 500)
    }
  }

  function restart() {
    setRound((r) => r + 1)
    setSelected(null)
    setMatched(new Set())
    setWrong([])
    setMisses({})
    setStartedAt(Date.now())
    setElapsed(0)
  }

  if (isLoading || !data) {
    return (
      <div className="grid min-h-screen place-items-center">
        <Spinner />
      </div>
    )
  }

  const seconds = (elapsed / 1000).toFixed(1)
  const results: SessionResult[] = [...new Set(tiles.map((t) => t.cardId))].map((cardId) => ({ cardId, correct: (misses[cardId] ?? 0) === 0 }))

  return (
    <StudyFrame
      title={data.deck.title}
      progress={tiles.length ? matched.size / tiles.length : 0}
      onExit={() => navigate(`/decks/${id}`)}
      right={<span className="text-[14px] font-semibold tabular-nums">{seconds}s</span>}
    >
      {done ? (
        <Summary
          deckId={data.deck.id}
          mode="match"
          results={results}
          startedAt={startedAt}
          onAgain={restart}
          extra={<p className="mt-2 text-[22px] font-bold tabular-nums">{(elapsed / 1000).toFixed(1)} seconds</p>}
        />
      ) : (
        <div className="flex flex-1 flex-col">
          <p className="text-center text-[14px] text-muted">Tap a term, then its definition</p>
          <div className="mt-5 grid grid-cols-3 gap-3 sm:grid-cols-4">
            <AnimatePresence>
              {tiles.map((tile) => {
                const isMatched = matched.has(tile.key)
                const isSelected = selected === tile.key
                const isWrong = wrong.includes(tile.key)
                return (
                  <motion.button
                    key={tile.key}
                    type="button"
                    layout
                    onClick={() => tap(tile)}
                    disabled={isMatched}
                    animate={isMatched ? { opacity: 0, scale: 0.85 } : isWrong ? { x: [0, -6, 6, -4, 4, 0] } : { opacity: 1, scale: 1, x: 0 }}
                    transition={isWrong ? { duration: 0.35 } : { duration: 0.3 }}
                    className={cx(
                      'flex min-h-[112px] items-center justify-center rounded-[18px] border-2 bg-surface p-3 text-center text-[14px] font-medium leading-snug shadow-card transition-colors sm:min-h-[128px]',
                      isSelected ? 'border-accent bg-accent-soft' : isWrong ? 'border-danger bg-danger-soft' : 'border-transparent hover:border-line-strong',
                      tile.side === 'definition' && 'font-normal text-muted',
                      isMatched && 'pointer-events-none',
                    )}
                  >
                    {tile.text}
                  </motion.button>
                )
              })}
            </AnimatePresence>
          </div>
        </div>
      )}
    </StudyFrame>
  )
}
