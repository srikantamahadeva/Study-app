import { useState } from 'react'

import { Avatar, Badge, Button, ConfirmDialog, useToast } from '../components/ui'
import { api, useApiMutation, useMe } from '../lib/api'

export function Settings() {
  const { data: me } = useMe()
  const toast = useToast()
  const [confirm, setConfirm] = useState<'reset' | 'clear' | null>(null)
  const keys = ['me', 'decks', 'deck', 'stats']
  const reset = useApiMutation(() => api('/account/reset', { method: 'POST' }), keys, {
    onSuccess: () => {
      setConfirm(null)
      toast('Sample decks restored')
    },
  })
  const clear = useApiMutation(() => api('/account/data', { method: 'DELETE' }), keys, {
    onSuccess: () => {
      setConfirm(null)
      toast('Library cleared')
    },
  })
  if (!me) return null

  return (
    <div className="mx-auto max-w-[640px]">
      <h1 className="text-[26px] font-bold tracking-[-0.02em]">Settings</h1>

      <section className="mt-8">
        <h2 className="text-[14px] font-semibold">Account</h2>
        <div className="mt-3 flex items-center gap-4 rounded-card bg-surface p-4 shadow-card">
          <Avatar name={me.user.name ?? me.user.email ?? 'You'} hue={250} src={me.user.picture} size={48} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-[15px] font-medium">{me.user.name ?? 'Signed in'}</p>
            {me.user.email && <p className="truncate text-[13px] text-muted">{me.user.email}</p>}
          </div>
          {me.capabilities.auth === 'freebuff' ? (
            <form method="post" action="/auth/freebuff/signout">
              <input type="hidden" name="returnTo" value="/" />
              <Button type="submit">Sign out</Button>
            </form>
          ) : (
            <Badge tone="warning">Development user</Badge>
          )}
        </div>
        {me.capabilities.auth === 'development' && <p className="mt-2 text-[12.5px] text-faint">Sign in with Freebuff is not configured yet. Run the app with FREEBUFF_CLIENT_ID set to use real accounts.</p>}
      </section>

      <section className="mt-8">
        <h2 className="text-[14px] font-semibold">Connections</h2>
        <ul className="mt-3 divide-y divide-line rounded-card bg-surface shadow-card">
          {[
            ['Database', me.capabilities.database, 'D1 via the DB binding'],
            ['Card images', me.capabilities.files, 'R2 via the FILES binding'],
            ['Sign in with Freebuff', me.capabilities.auth === 'freebuff', 'FREEBUFF_CLIENT_ID'],
          ].map(([label, ok, detail]) => (
            <li key={label as string} className="flex h-13 items-center gap-3 px-4">
              <span className="min-w-0 flex-1">
                <span className="block text-[13.5px] font-medium">{label}</span>
                <span className="block truncate text-[12px] text-faint">{detail}</span>
              </span>
              <Badge tone={ok ? 'success' : 'neutral'} dot>
                {ok ? 'Connected' : 'Not connected'}
              </Badge>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-8">
        <h2 className="text-[14px] font-semibold">Data</h2>
        <div className="mt-3 divide-y divide-line rounded-card bg-surface shadow-card">
          <div className="flex items-center gap-3 p-4">
            <span className="min-w-0 flex-1">
              <span className="block text-[13.5px] font-medium">Restore sample decks</span>
              <span className="block text-[12.5px] text-muted">Replaces your library with the three starter decks.</span>
            </span>
            <Button onClick={() => setConfirm('reset')}>Restore</Button>
          </div>
          <div className="flex items-center gap-3 p-4">
            <span className="min-w-0 flex-1">
              <span className="block text-[13.5px] font-medium">Clear library</span>
              <span className="block text-[12.5px] text-muted">Deletes every deck, card and session. This cannot be undone.</span>
            </span>
            <Button variant="danger" onClick={() => setConfirm('clear')}>
              Clear
            </Button>
          </div>
        </div>
      </section>

      <ConfirmDialog open={confirm === 'reset'} onClose={() => setConfirm(null)} onConfirm={() => reset.mutate(undefined)} loading={reset.isPending} title="Restore sample decks?" description="Your current decks and progress are replaced." confirmLabel="Restore" />
      <ConfirmDialog open={confirm === 'clear'} onClose={() => setConfirm(null)} onConfirm={() => clear.mutate(undefined)} loading={clear.isPending} title="Clear your library?" description="Every deck, card, image and session is deleted." confirmLabel="Clear everything" />
    </div>
  )
}
