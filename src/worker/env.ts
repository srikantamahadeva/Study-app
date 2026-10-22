import type { FreebuffUser } from '@freebuff/auth'

export interface Env {
  ASSETS: Fetcher
  // Attached by Freebuff Sites once provisioned (sites_add_storage). Optional so
  // the app can explain what is missing instead of crashing.
  DB?: D1Database
  FILES?: R2Bucket
  // Injected on deploy once Sign in with Freebuff is enabled (sites_enable_auth).
  FREEBUFF_CLIENT_ID?: string
  FREEBUFF_ISSUER?: string
  APP_ORIGIN?: string
}

export type Variables = {
  user: FreebuffUser
  db: D1Database
}

export type AppContext = { Bindings: Env; Variables: Variables }
