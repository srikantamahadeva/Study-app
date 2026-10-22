import { Hono } from 'hono'

import { authMode, getAuth, requireUser } from './auth'
import { requireDb } from './db'
import type { AppContext, Env } from './env'
import { account } from './routes/account'
import { decks } from './routes/decks'

const app = new Hono<AppContext>()

app.get('/api/auth/status', (c) => {
  c.header('Cache-Control', 'private, no-store')
  return c.json({ mode: authMode(c.env, c.req.raw), database: Boolean(c.env.DB), files: Boolean(c.env.FILES) })
})
app.get('/api/health', (c) => c.json({ ok: true }))

const api = new Hono<AppContext>()
api.use('*', requireUser, requireDb)
api.route('/', account)
api.route('/decks', decks)
app.route('/api', api)

app.onError((error, c) => {
  console.error(error)
  return c.json({ error: 'Something went wrong.' }, 500)
})
app.notFound((c) => (c.req.path.startsWith('/api/') ? c.json({ error: 'Not found.' }, 404) : c.env.ASSETS.fetch(c.req.raw)))

export default {
  fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // Sign in with Freebuff owns /auth/freebuff/* and keeps sessions fresh.
    // Without a client ID the app falls back to the loopback development user.
    const auth = getAuth(env, request)
    const handler = (req: Request) => Promise.resolve(app.fetch(req, env, ctx))
    return auth ? auth.wrap(handler)(request) : handler(request)
  },
}
