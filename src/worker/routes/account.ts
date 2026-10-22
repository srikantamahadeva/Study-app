import { Hono } from 'hono'

import { authMode, privateJson } from '../auth'
import { mapSession, now, streakFrom } from '../db'
import type { AppContext } from '../env'
import { clearUser, seedUser } from '../seed'
import type { Me, Stats } from '../../shared/types'

export const account = new Hono<AppContext>()

async function sessionDays(db: D1Database, owner: string): Promise<Set<string>> {
  const rows = await db.prepare(`SELECT DISTINCT date(created_at / 1000, 'unixepoch') AS day FROM sessions WHERE owner_sub = ?`).bind(owner).all<{ day: string }>()
  return new Set(rows.results.map((r) => r.day))
}

account.get('/me', async (c) => {
  const user = c.get('user')
  const db = c.get('db')
  let row = await db.prepare(`SELECT seeded_at FROM users WHERE owner_sub = ?`).bind(user.sub).first<{ seeded_at: number | null }>()
  if (!row) {
    await db.prepare(`INSERT INTO users (owner_sub, created_at) VALUES (?, ?)`).bind(user.sub, now()).run()
    // First visit: furnish the library with sample decks and some history.
    await seedUser(db, user.sub)
    row = { seeded_at: now() }
  }
  const body: Me = {
    user: { sub: user.sub, name: user.name, email: user.email, picture: user.picture },
    streak: streakFrom(await sessionDays(db, user.sub)).current,
    seeded: Boolean(row.seeded_at),
    capabilities: { database: true, files: Boolean(c.env.FILES), auth: authMode(c.env, c.req.raw) === 'freebuff' ? 'freebuff' : 'development' },
  }
  return privateJson(c, body)
})

account.get('/stats', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  const since = now() - 84 * 86_400_000
  const [totals, mastered, cards, days, recent, decks] = await db.batch([
    db.prepare(`SELECT COUNT(*) AS n, COALESCE(SUM(duration_ms), 0) AS ms FROM sessions WHERE owner_sub = ?`).bind(owner),
    db.prepare(`SELECT COUNT(*) AS n FROM card_progress WHERE owner_sub = ? AND mastery >= 80`).bind(owner),
    db.prepare(`SELECT COUNT(*) AS n FROM cards WHERE owner_sub = ?`).bind(owner),
    db
      .prepare(
        `SELECT date(created_at / 1000, 'unixepoch') AS day, COUNT(*) AS n, SUM(score) AS s, SUM(total) AS t FROM sessions WHERE owner_sub = ? AND created_at >= ? GROUP BY day ORDER BY day`,
      )
      .bind(owner, since),
    db.prepare(`SELECT s.*, d.title AS deck_title FROM sessions s LEFT JOIN decks d ON d.id = s.deck_id WHERE s.owner_sub = ? ORDER BY s.created_at DESC LIMIT 12`).bind(owner),
    db
      .prepare(
        `SELECT d.id, d.title, d.hue,
          (SELECT COUNT(*) FROM cards c WHERE c.deck_id = d.id) AS card_count,
          (SELECT COALESCE(AVG(COALESCE(p.mastery, 0)), 0) FROM cards c LEFT JOIN card_progress p ON p.card_id = c.id WHERE c.deck_id = d.id) AS mastery
         FROM decks d WHERE d.owner_sub = ? ORDER BY mastery DESC`,
      )
      .bind(owner),
  ])

  const byDay = new Map((days.results as { day: string; n: number; s: number; t: number }[]).map((r) => [r.day, r]))
  const series: Stats['days'] = []
  const cursor = new Date()
  cursor.setUTCHours(0, 0, 0, 0)
  cursor.setUTCDate(cursor.getUTCDate() - 83)
  for (let i = 0; i < 84; i++) {
    const key = cursor.toISOString().slice(0, 10)
    const row = byDay.get(key)
    series.push({ date: key, sessions: Number(row?.n ?? 0), accuracy: row && Number(row.t) ? Math.round((Number(row.s) / Number(row.t)) * 100) : null })
    cursor.setUTCDate(cursor.getUTCDate() + 1)
  }
  const streak = streakFrom(new Set((days.results as { day: string }[]).map((r) => r.day).concat([...(await sessionDays(db, owner))])))
  const body: Stats = {
    streak: streak.current,
    longestStreak: streak.longest,
    sessions: Number((totals.results[0] as { n: number }).n),
    cardsMastered: Number((mastered.results[0] as { n: number }).n),
    cardsTotal: Number((cards.results[0] as { n: number }).n),
    minutes: Math.round(Number((totals.results[0] as { ms: number }).ms) / 60_000),
    days: series,
    recent: (recent.results as Record<string, unknown>[]).map(mapSession),
    decks: (decks.results as { id: string; title: string; hue: number; card_count: number; mastery: number }[]).map((d) => ({
      id: d.id,
      title: d.title,
      hue: Number(d.hue),
      cardCount: Number(d.card_count),
      mastery: Math.round(Number(d.mastery)),
    })),
  }
  return privateJson(c, body)
})

account.post('/account/reset', async (c) => {
  const db = c.get('db')
  const owner = c.get('user').sub
  await clearUser(db, owner)
  await seedUser(db, owner)
  return privateJson(c, { ok: true })
})

account.delete('/account/data', async (c) => {
  await clearUser(c.get('db'), c.get('user').sub)
  return privateJson(c, { ok: true })
})
