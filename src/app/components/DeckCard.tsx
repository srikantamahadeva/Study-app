import { motion } from 'motion/react'
import { Link } from 'react-router'

import type { Deck } from '../../shared/types'
import { relativeTime } from '../lib/format'

export function ProgressRing({ value, size = 44, stroke = 4, hue }: { value: number; size?: number; stroke?: number; hue: number }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0 -rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--color-raised)" strokeWidth={stroke} />
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={`hsl(${hue} 70% 55%)`}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={c}
        initial={{ strokeDashoffset: c }}
        animate={{ strokeDashoffset: c * (1 - value / 100) }}
        transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
      />
    </svg>
  )
}

export function DeckCard({ deck, index = 0 }: { deck: Deck; index?: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: index * 0.04, ease: [0.22, 1, 0.36, 1] }}>
      <Link to={`/decks/${deck.id}`} className="group flex h-[168px] flex-col rounded-card bg-surface p-5 shadow-card transition-[box-shadow,transform] hover:-translate-y-0.5 hover:shadow-pop">
        <div className="flex items-start justify-between gap-4">
          <span className="grid size-10 place-items-center rounded-[13px] text-[15px] font-bold text-white" style={{ background: `linear-gradient(135deg, hsl(${deck.hue} 70% 60%), hsl(${deck.hue + 30} 70% 48%))` }}>
            {deck.title[0]?.toUpperCase()}
          </span>
          <div className="relative grid place-items-center">
            <ProgressRing value={deck.mastery} hue={deck.hue} />
            <span className="absolute text-[11px] font-semibold tabular-nums">{deck.mastery}%</span>
          </div>
        </div>
        <h3 className="mt-4 line-clamp-1 text-[16px] font-semibold tracking-tight">{deck.title}</h3>
        <p className="mt-auto flex items-center gap-3 text-[13px] text-muted">
          <span>{deck.cardCount} cards</span>
          {deck.dueCount > 0 && <span className="text-accent">{deck.dueCount} due</span>}
          {deck.lastStudiedAt && <span>{relativeTime(deck.lastStudiedAt)}</span>}
        </p>
      </Link>
    </motion.div>
  )
}
