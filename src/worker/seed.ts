import { hueFor, id } from './db'

const DAY = 86_400_000

const decks: { title: string; description: string; cards: [string, string][] }[] = [
  {
    title: 'Spanish essentials',
    description: 'The hundred words that get you through a weekend in Madrid.',
    cards: [
      ['hola', 'hello'],
      ['gracias', 'thank you'],
      ['por favor', 'please'],
      ['la cuenta', 'the bill'],
      ['¿dónde está?', 'where is?'],
      ['la estación', 'the station'],
      ['el desayuno', 'breakfast'],
      ['la cena', 'dinner'],
      ['agua', 'water'],
      ['vino tinto', 'red wine'],
      ['izquierda', 'left'],
      ['derecha', 'right'],
      ['mañana', 'tomorrow, or morning'],
      ['ahora', 'now'],
      ['lo siento', 'I am sorry'],
      ['¿cuánto cuesta?', 'how much does it cost?'],
    ],
  },
  {
    title: 'Cell biology',
    description: 'Organelles and what they do. Chapter three.',
    cards: [
      ['Mitochondrion', 'Produces ATP through cellular respiration'],
      ['Ribosome', 'Builds proteins from amino acids using mRNA'],
      ['Nucleus', 'Holds the genetic material and controls the cell'],
      ['Golgi apparatus', 'Modifies, sorts and packages proteins for transport'],
      ['Lysosome', 'Breaks down waste and worn-out cell parts with enzymes'],
      ['Endoplasmic reticulum', 'Network of membranes for protein and lipid synthesis'],
      ['Chloroplast', 'Site of photosynthesis in plant cells'],
      ['Cell membrane', 'Controls what enters and leaves the cell'],
      ['Cytoskeleton', 'Protein filaments that give the cell shape and movement'],
      ['Vacuole', 'Stores water, nutrients and waste'],
      ['Centriole', 'Organises microtubules during cell division'],
      ['Peroxisome', 'Breaks down fatty acids and neutralises hydrogen peroxide'],
    ],
  },
  {
    title: 'Design principles',
    description: 'Gestalt and the vocabulary of visual hierarchy.',
    cards: [
      ['Proximity', 'Elements close together are perceived as a group'],
      ['Similarity', 'Elements that look alike are perceived as related'],
      ['Closure', 'The mind completes incomplete shapes'],
      ['Continuity', 'The eye follows lines and curves beyond their end'],
      ['Figure and ground', 'Separating a subject from its background'],
      ['Contrast', 'Difference that creates emphasis and hierarchy'],
      ['Alignment', 'Placing elements along shared edges or axes'],
      ['Whitespace', 'Empty space that gives content room to breathe'],
      ['Repetition', 'Reusing elements to create consistency and rhythm'],
      ['Hierarchy', 'Arranging elements to show their order of importance'],
    ],
  },
]

export async function seedUser(db: D1Database, owner: string) {
  const t = Date.now()
  const statements: D1PreparedStatement[] = []
  const sessionDays = [0, 1, 2, 4, 5, 6, 7, 9, 12, 13]

  decks.forEach((deck, di) => {
    const deckId = id()
    const lastStudied = di === 0 ? t - 3 * 3_600_000 : di === 1 ? t - 1.2 * DAY : t - 6 * DAY
    statements.push(
      db
        .prepare(`INSERT INTO decks (id, owner_sub, title, description, hue, last_studied_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
        .bind(deckId, owner, deck.title, deck.description, hueFor(deck.title), lastStudied, t - (20 - di * 4) * DAY, lastStudied),
    )
    deck.cards.forEach(([term, definition], ci) => {
      const cardId = id()
      statements.push(
        db
          .prepare(`INSERT INTO cards (id, owner_sub, deck_id, term, definition, position, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)`)
          .bind(cardId, owner, deckId, term, definition, ci, t - (20 - di * 4) * DAY + ci),
      )
      // Progress that looks like a few sessions have happened: early cards
      // are strong, later cards are still new.
      if (di < 2 && ci < deck.cards.length * 0.7) {
        const strength = Math.max(0, 1 - ci / deck.cards.length)
        const correct = Math.round(2 + strength * 6)
        const incorrect = Math.round((1 - strength) * 3)
        const mastery = Math.min(100, Math.round(strength * 100))
        statements.push(
          db
            .prepare(`INSERT INTO card_progress (card_id, owner_sub, deck_id, correct, incorrect, streak, mastery, next_due, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`)
            .bind(cardId, owner, deckId, correct, incorrect, Math.min(correct, 4), mastery, t + (mastery >= 80 ? 3 : mastery >= 40 ? 1 : 0) * DAY, lastStudied),
        )
      }
    })
    // A short session history so stats and streaks are furnished.
    sessionDays.forEach((daysAgo, si) => {
      if ((si + di) % 3 === 2) return
      const total = 10 + ((si * 3 + di) % 6)
      const score = Math.max(4, total - ((si + di * 2) % 5))
      const modes = ['learn', 'flashcards', 'match'] as const
      statements.push(
        db
          .prepare(`INSERT INTO sessions (id, owner_sub, deck_id, mode, score, total, duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
          .bind(id(), owner, deckId, modes[(si + di) % 3], score, total, (90 + ((si * 37) % 200)) * 1000, t - daysAgo * DAY - (di + 1) * 2 * 3_600_000),
      )
    })
  })

  statements.push(db.prepare(`UPDATE users SET seeded_at = ? WHERE owner_sub = ?`).bind(t, owner))
  for (let i = 0; i < statements.length; i += 40) await db.batch(statements.slice(i, i + 40))
}

export async function clearUser(db: D1Database, owner: string) {
  await db.batch(['sessions', 'card_progress', 'cards', 'decks'].map((table) => db.prepare(`DELETE FROM ${table} WHERE owner_sub = ?`).bind(owner)))
  await db.prepare(`UPDATE users SET seeded_at = NULL WHERE owner_sub = ?`).bind(owner).run()
}
