import { motion } from 'motion/react'
import { ArrowRight, Database } from 'lucide-react'
import { useState } from 'react'

import { Logo } from '../components/Shell'
import { Button, Field, Input } from '../components/ui'
import { useLogin, useRegister } from '../lib/api'

/** Sign in / create account. One toggle switches between the two modes. */
export function SignIn() {
  const [mode, setMode] = useState<'signin' | 'register'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const login = useLogin()
  const register = useRegister()

  const busy = login.isPending || register.isPending

  function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const onSuccess = () => window.location.reload()
    if (mode === 'signin') {
      login.mutate(
        { email, password },
        { onSuccess, onError: (err) => setError(err.message) },
      )
    } else {
      register.mutate(
        { email, password, displayName },
        { onSuccess, onError: (err) => setError(err.message) },
      )
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="mx-auto flex h-16 w-full max-w-[1120px] items-center px-5 sm:px-8">
        <Logo />
      </header>
      <main className="mx-auto grid w-full max-w-[1120px] flex-1 items-center gap-12 px-5 pb-16 sm:px-8 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-md"
        >
          <h1 className="text-balance text-[38px] font-bold leading-[1.05] tracking-[-0.03em] sm:text-[48px]">
            {mode === 'signin' ? 'Welcome back' : 'Start learning'}
          </h1>
          <p className="mt-3 text-[15px] leading-relaxed text-muted">
            A personal study platform for algorithmic trading — education and research only.
          </p>

          <form onSubmit={submit} className="mt-8 flex flex-col gap-4">
            {mode === 'register' && (
              <Field label="Display name">
                <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="How should we greet you?" autoComplete="name" />
              </Field>
            )}
            <Field label="Email">
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required />
            </Field>
            <Field label="Password" hint={mode === 'register' ? 'At least 10 characters.' : undefined}>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                required
              />
            </Field>

            {error && <p className="text-[13px] text-danger">{error}</p>}

            <Button type="submit" variant="primary" size="md" loading={busy} className="mt-1 h-11">
              {mode === 'signin' ? 'Sign in' : 'Create account'}
              {!busy && <ArrowRight className="size-4" />}
            </Button>
          </form>

          <button
            type="button"
            onClick={() => {
              setMode(mode === 'signin' ? 'register' : 'signin')
              setError(null)
            }}
            className="mt-5 text-[13.5px] text-muted transition-colors hover:text-fg"
          >
            {mode === 'signin' ? 'No account yet? Create one' : 'Already have an account? Sign in'}
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24, rotate: -2 }}
          animate={{ opacity: 1, y: 0, rotate: -2 }}
          transition={{ duration: 0.8, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
          className="relative mx-auto hidden w-full max-w-[460px] lg:block"
        >
          <div className="absolute inset-0 translate-x-4 translate-y-4 rotate-3 rounded-[28px] bg-accent-soft" />
          <div className="absolute inset-0 translate-x-2 translate-y-2 rotate-1 rounded-[28px] bg-surface shadow-card" />
          <div className="relative aspect-[5/3] rounded-[28px] bg-surface p-10 shadow-float">
            <p className="text-[13px] text-muted">Risk management</p>
            <p className="mt-6 text-[34px] font-bold tracking-tight">Position sizing</p>
            <p className="mt-3 text-[16px] text-muted">Risk a fixed fraction of capital per trade so no single loss compounds.</p>
            <div className="absolute bottom-8 left-10 right-10 flex items-center justify-between text-[13px] text-faint">
              <span>Sample curriculum</span>
              <span className="inline-flex items-center gap-1.5 text-success">
                <span className="round size-2 rounded-full bg-success" />
                Research only
              </span>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  )
}

/** Shown when the backend is unreachable or not provisioned. */
export function SetupNeeded({ message }: { message: string }) {
  return (
    <div className="grid min-h-screen place-items-center p-6">
      <div className="max-w-md text-center">
        <div className="mx-auto grid size-12 place-items-center rounded-card bg-surface-2 text-muted">
          <Database className="size-5" />
        </div>
        <h1 className="mt-4 text-[20px] font-semibold tracking-tight">Almost there</h1>
        <p className="mt-2 text-[14px] leading-relaxed text-muted">{message}</p>
        <p className="mt-4 text-[13px] text-faint">Start the FastAPI backend, then reload this page.</p>
      </div>
    </div>
  )
}
