import { Hono } from 'hono'

import { privateJson } from '../auth'
import { CARD_SELECT, DECK_SELECT, hueFor, id, mapCard, mapDeck, mapSession, now } from '../db'
import type { AppContext } from '../env'
import type { SessionResult, StudyMode } from '../../shared/types'

export const decks = new Hono<AppContext>()

const MODES = new Set<StudyMode>(['flashcards', 'learn', 'match'])
const DAY = 86_400_000

decks.get('/', async (c) => {
  const rows = await c.get('db').prepare(`${DECK_SELECT} WHERE d.owner_sub = ? ORDER BY COALESCE(d.last_studied_at, d.updated_at) DESC`).bind(now(), c.get('user').sub).all()
  return privateJson(c, { items: (rows.results as Record<string, unknown>[]).map(mapDeck) })
})

decks.post('/', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const input = await c.req.json<{ title?: string; description?: string; cards?: { term: string; definition: string }[] }>()
  const title = input.title?.trim().slice(0, 80)
  if (!title) return c.json({ error: 'Give the deck a title.' }, 400)
  const deckId = id()
  const t = now()
  const statements = [
    db
      .prepare(`INSERT INTO decks (id, owner_sub, title, description, hue, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)`)
      .bind(deckId, owner, title, input.description?.trim().slice(0, 300) || null, hueFor(title), t, t),
  ]
  cleanCards(input.cards).forEach((card, i) => {
    statements.push(
      db.prepare(`INSERT INTO cards (id, owner_sub, deck_id, term, definition, position, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)`).bind(id(), owner, deckId, card.term, card.definition, i, t + i),
    )
  })
  for (let i = 0; i < statements.length; i += 40) await db.batch(statements.slice(i, i + 40))
  const row = await db.prepare(`${DECK_SELECT} WHERE d.owner_sub = ? AND d.id = ?`).bind(t, owner, deckId).first()
  return privateJson(c, { deck: mapDeck(row as Record<string, unknown>) }, 201)
})

decks.get('/:id', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const deckId = c.req.param('id')
  const [deck, cards, sessions] = await db.batch([
    db.prepare(`${DECK_SELECT} WHERE d.owner_sub = ? AND d.id = ?`).bind(now(), owner, deckId),
    db.prepare(`${CARD_SELECT} WHERE c.owner_sub = ? AND c.deck_id = ? ORDER BY c.position ASC, c.created_at ASC`).bind(owner, deckId),
    db.prepare(`SELECT * FROM sessions WHERE owner_sub = ? AND deck_id = ? ORDER BY created_at DESC LIMIT 10`).bind(owner, deckId),
  ])
  if (!deck.results[0]) return c.json({ error: 'Not found.' }, 404)
  return privateJson(c, {
    deck: mapDeck(deck.results[0] as Record<string, unknown>),
    cards: (cards.results as Record<string, unknown>[]).map(mapCard),
    sessions: (sessions.results as Record<string, unknown>[]).map(mapSession),
  })
})

decks.patch('/:id', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const deckId = c.req.param('id')
  const input = await c.req.json<{ title?: string; description?: string | null }>()
  const existing = await db.prepare(`SELECT * FROM decks WHERE owner_sub = ? AND id = ?`).bind(owner, deckId).first<Record<string, unknown>>()
  if (!existing) return c.json({ error: 'Not found.' }, 404)
  const title = (input.title ?? (existing.title as string)).trim().slice(0, 80)
  if (!title) return c.json({ error: 'Give the deck a title.' }, 400)
  const description = input.description === undefined ? (existing.description as string | null) : input.description?.trim().slice(0, 300) || null
  await db.prepare(`UPDATE decks SET title = ?, description = ?, updated_at = ? WHERE owner_sub = ? AND id = ?`).bind(title, description, now(), owner, deckId).run()
  return privateJson(c, { ok: true })
})

decks.delete('/:id', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const deckId = c.req.param('id')
  const keys = await db.prepare(`SELECT image_key FROM cards WHERE owner_sub = ? AND deck_id = ? AND image_key IS NOT NULL`).bind(owner, deckId).all<{ image_key: string }>()
  await db.batch([
    db.prepare(`DELETE FROM sessions WHERE owner_sub = ? AND deck_id = ?`).bind(owner, deckId),
    db.prepare(`DELETE FROM card_progress WHERE owner_sub = ? AND deck_id = ?`).bind(owner, deckId),
    db.prepare(`DELETE FROM cards WHERE owner_sub = ? AND deck_id = ?`).bind(owner, deckId),
    db.prepare(`DELETE FROM decks WHERE owner_sub = ? AND id = ?`).bind(owner, deckId),
  ])
  if (c.env.FILES && keys.results.length) await c.env.FILES.delete(keys.results.map((r) => r.image_key))
  return privateJson(c, { ok: true })
})

// Cards

function cleanCards(input: { term?: string; definition?: string }[] | undefined) {
  return (input ?? [])
    .map((card) => ({ term: card.term?.trim().slice(0, 300) ?? '', definition: card.definition?.trim().slice(0, 600) ?? '' }))
    .filter((card) => card.term && card.definition)
    .slice(0, 500)
}

decks.post('/:id/cards', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const deckId = c.req.param('id')
  const deck = await db.prepare(`SELECT id FROM decks WHERE owner_sub = ? AND id = ?`).bind(owner, deckId).first()
  if (!deck) return c.json({ error: 'Not found.' }, 404)
  const input = await c.req.json<{ cards?: { term: string; definition: string }[] }>()
  const cards = cleanCards(input.cards)
  if (cards.length === 0) return c.json({ error: 'Each card needs a term and a definition.' }, 400)
  const top = await db.prepare(`SELECT COALESCE(MAX(position), -1) AS p FROM cards WHERE owner_sub = ? AND deck_id = ?`).bind(owner, deckId).first<{ p: number }>()
  const t = now()
  const statements = cards.map((card, i) =>
    db
      .prepare(`INSERT INTO cards (id, owner_sub, deck_id, term, definition, position, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)`)
      .bind(id(), owner, deckId, card.term, card.definition, (top?.p ?? -1) + 1 + i, t + i),
  )
  statements.push(db.prepare(`UPDATE decks SET updated_at = ? WHERE owner_sub = ? AND id = ?`).bind(t, owner, deckId))
  for (let i = 0; i < statements.length; i += 40) await db.batch(statements.slice(i, i + 40))
  return privateJson(c, { added: cards.length }, 201)
})

decks.patch('/:id/cards/:cardId', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const input = await c.req.json<{ term?: string; definition?: string }>()
  const [card] = cleanCards([{ term: input.term, definition: input.definition }])
  if (!card) return c.json({ error: 'Each card needs a term and a definition.' }, 400)
  const result = await db
    .prepare(`UPDATE cards SET term = ?, definition = ? WHERE owner_sub = ? AND id = ? AND deck_id = ?`)
    .bind(card.term, card.definition, owner, c.req.param('cardId'), c.req.param('id'))
    .run()
  if (!result.meta.changes) return c.json({ error: 'Not found.' }, 404)
  return privateJson(c, { ok: true })
})

decks.delete('/:id/cards/:cardId', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const cardId = c.req.param('cardId')
  const existing = await db.prepare(`SELECT image_key FROM cards WHERE owner_sub = ? AND id = ?`).bind(owner, cardId).first<{ image_key: string | null }>()
  if (!existing) return c.json({ error: 'Not found.' }, 404)
  await db.batch([
    db.prepare(`DELETE FROM card_progress WHERE owner_sub = ? AND card_id = ?`).bind(owner, cardId),
    db.prepare(`DELETE FROM cards WHERE owner_sub = ? AND id = ?`).bind(owner, cardId),
  ])
  if (existing.image_key && c.env.FILES) await c.env.FILES.delete(existing.image_key)
  return privateJson(c, { ok: true })
})

// Card images (R2). One image per card, replaced on upload.

const IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/gif'])

decks.put('/:id/cards/:cardId/image', async (c) => {
  const bucket = c.env.FILES
  if (!bucket) return c.json({ error: 'storage_missing', message: 'No file storage is attached yet. Add R2 storage named FILES and redeploy.' }, 503)
  const db = c.get('db')
  const owner = c.get('user').sub
  const cardId = c.req.param('cardId')
  const existing = await db.prepare(`SELECT image_key FROM cards WHERE owner_sub = ? AND id = ?`).bind(owner, cardId).first<{ image_key: string | null }>()
  if (!existing) return c.json({ error: 'Not found.' }, 404)
  const form = await c.req.formData()
  const file = form.get('file')
  if (!(file instanceof File) || !IMAGE_TYPES.has(file.type)) return c.json({ error: 'Choose a PNG, JPEG, WebP or GIF image.' }, 400)
  if (file.size > 4 * 1024 * 1024) return c.json({ error: 'Images are limited to 4 MB.' }, 400)
  const key = `${owner}/cards/${cardId}/${crypto.randomUUID()}`
  await bucket.put(key, file.stream(), { httpMetadata: { contentType: file.type } })
  await db.prepare(`UPDATE cards SET image_key = ? WHERE owner_sub = ? AND id = ?`).bind(key, owner, cardId).run()
  if (existing.image_key) await bucket.delete(existing.image_key)
  return privateJson(c, { ok: true })
})

decks.delete('/:id/cards/:cardId/image', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const cardId = c.req.param('cardId')
  const existing = await db.prepare(`SELECT image_key FROM cards WHERE owner_sub = ? AND id = ?`).bind(owner, cardId).first<{ image_key: string | null }>()
  if (!existing) return c.json({ error: 'Not found.' }, 404)
  await db.prepare(`UPDATE cards SET image_key = NULL WHERE owner_sub = ? AND id = ?`).bind(owner, cardId).run()
  if (existing.image_key && c.env.FILES) await c.env.FILES.delete(existing.image_key)
  return privateJson(c, { ok: true })
})

decks.get('/:id/cards/:cardId/image', async (c) => {
  const bucket = c.env.FILES
  if (!bucket) return c.json({ error: 'Not found.' }, 404)
  const owner = c.get('user').sub
  const card = await c.get('db').prepare(`SELECT image_key FROM cards WHERE owner_sub = ? AND id = ?`).bind(owner, c.req.param('cardId')).first<{ image_key: string | null }>()
  if (!card?.image_key) return c.json({ error: 'Not found.' }, 404)
  const object = await bucket.get(card.image_key)
  if (!object) return c.json({ error: 'Not found.' }, 404)
  return new Response(object.body, {
    headers: {
      'Content-Type': object.httpMetadata?.contentType ?? 'image/jpeg',
      'Cache-Control': 'private, max-age=300',
      'X-Content-Type-Options': 'nosniff',
    },
  })
})

// Sessions: the client plays the round, the server records it and updates
// each card's mastery and due date (a light spaced-repetition schedule).

decks.post('/:id/sessions', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const deckId = c.req.param('id')
  const input = await c.req.json<{ mode?: StudyMode; results?: SessionResult[]; durationMs?: number }>()
  if (!input.mode || !MODES.has(input.mode)) return c.json({ error: 'Unknown study mode.' }, 400)
  const results = (input.results ?? []).filter((r) => typeof r.cardId === 'string' && typeof r.correct === 'boolean').slice(0, 500)
  if (results.length === 0) return c.json({ error: 'Nothing to record.' }, 400)
  const deck = await db.prepare(`SELECT id FROM decks WHERE owner_sub = ? AND id = ?`).bind(owner, deckId).first()
  if (!deck) return c.json({ error: 'Not found.' }, 404)

  const ids = [...new Set(results.map((r) => r.cardId))]
  const owned = await db
    .prepare(`SELECT c.id, p.correct, p.incorrect, p.streak, p.mastery FROM cards c LEFT JOIN card_progress p ON p.card_id = c.id WHERE c.owner_sub = ? AND c.deck_id = ? AND c.id IN (${ids.map(() => '?').join(',')})`)
    .bind(owner, deckId, ...ids)
    .all<{ id: string; correct: number | null; incorrect: number | null; streak: number | null; mastery: number | null }>()
  const byId = new Map(owned.results.map((r) => [r.id, r]))

  const t = now()
  const statements: D1PreparedStatement[] = []
  let score = 0
  const seen = new Set<string>()
  for (const r of results) {
    const row = byId.get(r.cardId)
    if (!row) continue
    seen.add(r.cardId)
    if (r.correct) score++
    const correct = Number(row.correct ?? 0) + (r.correct ? 1 : 0)
    const incorrect = Number(row.incorrect ?? 0) + (r.correct ? 0 : 1)
    const streak = r.correct ? Number(row.streak ?? 0) + 1 : 0
    const previous = Number(row.mastery ?? 0)
    const mastery = r.correct ? Math.min(100, previous + Math.max(10, Math.round((100 - previous) * 0.35))) : Math.max(0, Math.round(previous * 0.5))
    const interval = r.correct ? Math.min(30, Math.pow(2, streak)) * DAY : 0
    statements.push(
      db
        .prepare(
          `INSERT INTO card_progress (card_id, owner_sub, deck_id, correct, incorrect, streak, mastery, next_due, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(card_id) DO UPDATE SET correct = excluded.correct, incorrect = excluded.incorrect, streak = excluded.streak, mastery = excluded.mastery, next_due = excluded.next_due, last_seen = excluded.last_seen`,
        )
        .bind(r.cardId, owner, deckId, correct, incorrect, streak, mastery, t + interval, t),
    )
    byId.set(r.cardId, { id: r.cardId, correct, incorrect, streak, mastery })
  }
  const total = results.filter((r) => byId.has(r.cardId)).length
  const sessionId = id()
  statements.push(
    db
      .prepare(`INSERT INTO sessions (id, owner_sub, deck_id, mode, score, total, duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(sessionId, owner, deckId, input.mode, score, total, Math.max(0, Math.round(Number(input.durationMs) || 0)), t),
  )
  statements.push(db.prepare(`UPDATE decks SET last_studied_at = ?, updated_at = ? WHERE owner_sub = ? AND id = ?`).bind(t, t, owner, deckId))
  for (let i = 0; i < statements.length; i += 40) await db.batch(statements.slice(i, i + 40))
  return privateJson(c, { session: { id: sessionId, score, total, accuracy: total ? Math.round((score / total) * 100) : 0 } }, 201)
})
