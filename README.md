# Algo Study

A personal AI-powered algorithmic trading **study platform** — education and
research only. It never places orders, holds no exchange credentials, and
makes no profitability claims. A structured curriculum (modules and lessons),
quiz and flashcard review with spaced repetition, coding labs with static
checks, multi-milestone projects, a document library with extracted-text
search, and an optional AI tutor grounded in your own material with citations.

The product name is `BRAND` in `src/shared/types.ts`; change it once.

## Architecture

- `server/` — FastAPI + SQLAlchemy backend. Session auth (HttpOnly cookie,
  argon2 hashes, CSRF via same-origin enforcement), Postgres (embedded
  pgserver for development, any Postgres via `DATABASE_URL`), local file
  storage for uploads, and the SPA host. `server/fixtures/` holds the sample
  curriculum.
- `src/app/` — the React SPA (Vite, Tailwind v4, TanStack Query, react-router).
  `lib/api.ts` is the typed client for every `/api` endpoint; `pages/` holds
  one file per screen; `components/ui.tsx` the primitives.
- `src/shared/types.ts` — types mirroring the API's JSON contract.

## Run it

```sh
# backend (uv)
cd server && uv sync && uv run uvicorn app.main:app --port 8000

# frontend (bun) — proxies /api to the backend on :8000
bun install
bun run dev        # http://localhost:5173
```

Install the sample curriculum for a user:

```sh
cd server && uv run python -m app.seed --email you@example.com
```

Production is a single process: `bun run build` writes the SPA to
`server/web/dist`, which FastAPI serves with an SPA fallback (client routes
like `/reports` deep-link correctly). AI features need only an
OpenAI-compatible endpoint: set `AI_API_KEY` (plus optionally `AI_BASE_URL`,
`AI_MODEL`); without them the tutor reports "not configured" and never fakes
an answer.

## Where things are

- `server/app/routers/` — one router per domain: `auth`, `curriculum`, `quiz`
  (decks, cards, review), `notes` (+ glossary concepts), `labs`, `projects`,
  `resources`, `search`, `reports`, `tutor`, `account`.
- `server/app/deps.py` — the request dependencies: `CurrentUser` (every query
  is scoped to the signed-in owner), `SameOrigin` (CSRF for mutations).
- `src/app/pages/` — `Curriculum`, `Lesson`, `Quiz`/`Review`, `Flashcards`,
  `Notes`, `Labs`, `Projects`, `Resources`, `Reports`, `Tutor`, `Search`.
- `src/styles.css` holds the design tokens. Everything rounded is a squircle
  via `corner-shape`; true circles use the `round` class.

## Security notes

Every `/api/*` route except register/login requires a signed-in user and
scopes queries by owner id. Mutations must be same-origin. Passwords are
argon2-hashed with rehash-on-login; login attempts are rate-limited.
Personalised responses are `Cache-Control: private, no-store`. Uploads are
stored under `server/data/uploads` and addressed by row, never by raw path.
