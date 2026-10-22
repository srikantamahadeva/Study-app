import { motion } from 'motion/react'
import { ArrowRight, Database } from 'lucide-react'

import { Logo } from '../components/Shell'

export function SignIn() {
  const returnTo = encodeURIComponent(`${window.location.pathname}${window.location.search}`)
  return (
    <div className="flex min-h-screen flex-col">
      <header className="mx-auto flex h-16 w-full max-w-[1120px] items-center px-5 sm:px-8">
        <Logo />
      </header>
      <main className="mx-auto grid w-full max-w-[1120px] flex-1 items-center gap-12 px-5 pb-16 sm:px-8 lg:grid-cols-2">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }} className="max-w-md">
          <h1 className="text-balance text-[40px] font-bold leading-[1.05] tracking-[-0.03em] sm:text-[52px]">Remember what you learn</h1>
          <p className="mt-4 text-[16px] leading-relaxed text-muted">Flashcards, quizzes and matching games that schedule themselves around what you forget. Sign in to open your library.</p>
          <a
            href={`/auth/freebuff/signin?returnTo=${returnTo}`}
            className="mt-8 inline-flex h-12 items-center gap-2 rounded-control bg-fg px-5 text-[15px] font-medium text-white transition-colors hover:bg-[#2a2838]"
          >
            <span className="grid size-5 place-items-center rounded-[6px] bg-white text-[11px] font-bold text-fg">F</span>
            Sign in with Freebuff
            <ArrowRight className="size-4" />
          </a>
          <p className="mt-4 text-[13px] text-faint">Uses your Freebuff account. No password to remember, which is the point.</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 24, rotate: -2 }} animate={{ opacity: 1, y: 0, rotate: -2 }} transition={{ duration: 0.8, delay: 0.15, ease: [0.22, 1, 0.36, 1] }} className="relative mx-auto hidden w-full max-w-[460px] lg:block">
          <div className="absolute inset-0 translate-x-4 translate-y-4 rotate-3 rounded-[28px] bg-accent-soft" />
          <div className="absolute inset-0 translate-x-2 translate-y-2 rotate-1 rounded-[28px] bg-surface shadow-card" />
          <div className="relative aspect-[5/3] rounded-[28px] bg-surface p-10 shadow-float">
            <p className="text-[13px] text-muted">Cell biology</p>
            <p className="mt-6 text-[34px] font-bold tracking-tight">Mitochondrion</p>
            <p className="mt-3 text-[16px] text-muted">Produces ATP through cellular respiration</p>
            <div className="absolute bottom-8 left-10 right-10 flex items-center justify-between text-[13px] text-faint">
              <span>12 of 16</span>
              <span className="inline-flex items-center gap-1.5 text-success">
                <span className="round size-2 rounded-full bg-success" />
                Mastered
              </span>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  )
}

export function SetupNeeded({ message }: { message: string }) {
  return (
    <div className="grid min-h-screen place-items-center p-6">
      <div className="max-w-md text-center">
        <div className="mx-auto grid size-12 place-items-center rounded-card bg-surface-2 text-muted">
          <Database className="size-5" />
        </div>
        <h1 className="mt-4 text-[20px] font-semibold tracking-tight">Almost there</h1>
        <p className="mt-2 text-[14px] leading-relaxed text-muted">{message}</p>
        <p className="mt-4 text-[13px] text-faint">In Freebuff, ask the agent to add D1 storage named DB and R2 storage named FILES, then deploy again.</p>
      </div>
    </div>
  )
}
