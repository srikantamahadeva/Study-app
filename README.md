# Study app

A flashcard study app in the spirit of Quizlet: a library of decks, three study
modes (flashcards, multiple-choice learn and a timed match game), per-card
mastery with a light spaced-repetition schedule, streaks, and a progress page
with an activity heatmap and accuracy history. Cards can carry an image. It
runs on Freebuff Sites with Sign in with Freebuff, D1 for data and R2 for
images, and everything is scoped to the signed-in user.

The product name is `BRAND` in `src/shared/types.ts`; change it once.

## Run it

```sh
bun install
bun run dev        # http://localhost:5173 with local D1 and R2 (Miniflare)
bun run build      # dist/client (assets) + dist/study/index.js (Worker)
```

On localhost without a `FREEBUFF_CLIENT_ID`, the app signs you in as a local
development user so everything works before auth is provisioned. A new
account is seeded with three sample decks and some history; Settings can
restore or clear them.

## Connect it to Freebuff

1. `sites_create`, then `sites_add_storage` for D1 named `DB` and R2 named `FILES`.
2. `sites_enable_auth` (pass `http://localhost:5173` as the local origin while
   developing). Copy the development variables into `.dev.vars` (see
   `.dev.vars.example`) to use real accounts locally.
3. `bun run build`, then `sites_deploy` with `deploy.json`.

## Where things are

- `src/worker/` is the Hono API. `db.ts` owns the schema (created on first
  request) and the streak maths, `seed.ts` the sample decks, `auth.ts` the
  Freebuff integration and the loopback-only development user,
  `routes/decks.ts` decks, cards, images and session recording (where mastery
  and due dates are updated), `routes/account.ts` the profile and stats.
- `src/app/` is the React app. `pages/Flashcards.tsx`, `Learn.tsx` and
  `Match.tsx` are the study modes; each ends in `components/Summary.tsx`,
  which records the session once. `components/ui.tsx` holds the primitives.
- `src/styles.css` holds the design tokens. Everything rounded is a squircle
  via `corner-shape`; true circles use the `round` class.

## Security notes

Every `/api/*` route requires a signed-in user and scopes queries by
`owner_sub`. Mutations must be same-origin. Images are addressed by card row,
never by R2 key. Personalised responses are `Cache-Control: private, no-store`.
