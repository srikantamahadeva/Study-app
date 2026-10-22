import type { MiddlewareHandler } from 'hono'

import type { AppContext } from './env'

// Schema lives with the Worker: D1 has no migration tool on Freebuff Sites, so
// tables are created on the first request of each isolate. Add new statements
// at the end; never edit existing ones in place once deployed.
const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS users (
    owner_sub TEXT PRIMARY KEY,
    seeded_at INTEGER,
    created_at INTEGER NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS decks (
    id TEXT PRIMARY KEY,
    owner_sub TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    hue INTEGER NOT NULL DEFAULT 250,
    last_studied_at INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
  )`,
  `CREATE INDEX IF NOT EXISTS decks_owner ON decks(owner_sub, updated_at DESC)`,
  `CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    owner_sub TEXT NOT NULL,
    deck_id TEXT NOT NULL,
    term TEXT NOT NULL,
    definition TEXT NOT NULL,
    image_key TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
  )`,
  `CREATE INDEX IF NOT EXISTS cards_deck ON cards(owner_sub, deck_id, position)`,
  `CREATE TABLE IF NOT EXISTS card_progress (
    card_id TEXT PRIMARY KEY,
    owner_sub TEXT NOT NULL,
    deck_id TEXT NOT NULL,
    correct INTEGER NOT NULL DEFAULT 0,
    incorrect INTEGER NOT NULL DEFAULT 0,
    streak INTEGER NOT NULL DEFAULT 0,
    mastery INTEGER NOT NULL DEFAULT 0,
    next_due INTEGER,
    last_seen INTEGER
  )`,
  `CREATE INDEX IF NOT EXISTS progress_deck ON card_progress(owner_sub, deck_id)`,
  `CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    owner_sub TEXT NOT NULL,
    deck_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
  )`,
  `CREATE INDEX IF NOT EXISTS sessions_owner ON sessions(owner_sub, created_at DESC)`,
]

let ready: Promise<void> | undefined

export function ensureSchema(db: D1Database): Promise<void> {
  ready ??= db.batch(SCHEMA.map((sql) => db.prepare(sql))).then(
    () => undefined,
    (error) => {
      ready = undefined
      throw error
    },
  )
  return ready
}

export const requireDb: MiddlewareHandler<AppContext> = async (c, next) => {
  const db = c.env.DB
  if (!db) {
    return c.json({ error: 'database_missing', message: 'No database is attached yet. Add D1 storage named DB and redeploy.' }, 503)
  }
  await ensureSchema(db)
  c.set('db', db)
  await next()
}

export const id = () => crypto.randomUUID()
export const now = () => Date.now()

export function hueFor(text: string): number {
  let h = 0
  for (const ch of text) h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
}

type Row = Record<string, unknown>

export const DECK_SELECT = `
  SELECT d.*,
    (SELECT COUNT(*) FROM cards c WHERE c.deck_id = d.id AND c.owner_sub = d.owner_sub) AS card_count,
    (SELECT COUNT(*) FROM card_progress p WHERE p.deck_id = d.id AND p.owner_sub = d.owner_sub AND p.mastery >= 80) AS mastered,
    (SELECT COALESCE(AVG(COALESCE(p.mastery, 0)), 0) FROM cards c LEFT JOIN card_progress p ON p.card_id = c.id WHERE c.deck_id = d.id AND c.owner_sub = d.owner_sub) AS mastery,
    (SELECT COUNT(*) FROM cards c LEFT JOIN card_progress p ON p.card_id = c.id WHERE c.deck_id = d.id AND c.owner_sub = d.owner_sub AND (p.next_due IS NULL OR p.next_due <= ?)) AS due_count
  FROM decks d`

export function mapDeck(r: Row) {
  return {
    id: r.id as string,
    title: r.title as string,
    description: (r.description as string | null) ?? null,
    hue: Number(r.hue ?? 250),
    cardCount: Number(r.card_count ?? 0),
    mastered: Number(r.mastered ?? 0),
    mastery: Math.round(Number(r.mastery ?? 0)),
    dueCount: Number(r.due_count ?? 0),
    lastStudiedAt: r.last_studied_at === null || r.last_studied_at === undefined ? null : Number(r.last_studied_at),
    createdAt: Number(r.created_at),
    updatedAt: Number(r.updated_at),
  }
}

export const CARD_SELECT = `
  SELECT c.*, p.correct, p.incorrect, p.streak, p.mastery, p.next_due, p.last_seen
  FROM cards c LEFT JOIN card_progress p ON p.card_id = c.id`

export function mapCard(r: Row) {
  return {
    id: r.id as string,
    deckId: r.deck_id as string,
    term: r.term as string,
    definition: r.definition as string,
    hasImage: Boolean(r.image_key),
    position: Number(r.position ?? 0),
    progress: {
      correct: Number(r.correct ?? 0),
      incorrect: Number(r.incorrect ?? 0),
      streak: Number(r.streak ?? 0),
      mastery: Number(r.mastery ?? 0),
      nextDue: r.next_due === null || r.next_due === undefined ? null : Number(r.next_due),
      lastSeen: r.last_seen === null || r.last_seen === undefined ? null : Number(r.last_seen),
    },
  }
}

export function mapSession(r: Row) {
  const total = Number(r.total)
  const score = Number(r.score)
  return {
    id: r.id as string,
    deckId: r.deck_id as string,
    deckTitle: (r.deck_title as string | undefined) ?? undefined,
    mode: r.mode as 'flashcards' | 'learn' | 'match',
    score,
    total,
    accuracy: total ? Math.round((score / total) * 100) : 0,
    durationMs: Number(r.duration_ms ?? 0),
    createdAt: Number(r.created_at),
  }
}

/** Consecutive days with at least one session, ending today or yesterday. */
export function streakFrom(days: Set<string>): { current: number; longest: number } {
  const key = (d: Date) => d.toISOString().slice(0, 10)
  const cursor = new Date()
  cursor.setUTCHours(0, 0, 0, 0)
  if (!days.has(key(cursor))) cursor.setUTCDate(cursor.getUTCDate() - 1)
  let current = 0
  while (days.has(key(cursor))) {
    current++
    cursor.setUTCDate(cursor.getUTCDate() - 1)
  }
  const sorted = [...days].sort()
  let longest = 0
  let run = 0
  let previous: string | null = null
  for (const day of sorted) {
    if (previous) {
      const prev = new Date(previous)
      prev.setUTCDate(prev.getUTCDate() + 1)
      run = key(prev) === day ? run + 1 : 1
    } else run = 1
    longest = Math.max(longest, run)
    previous = day
  }
  return { current, longest: Math.max(longest, current) }
}
