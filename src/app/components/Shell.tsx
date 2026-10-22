import { Flame } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router'

import { BRAND } from '../../shared/types'
import { useMe } from '../lib/api'
import { cx } from '../lib/cx'
import { Avatar } from './ui'

export function Logo({ className }: { className?: string }) {
  return (
    <Link to="/" className={cx('inline-flex items-center gap-2.5 text-[16px] font-semibold tracking-tight', className)}>
      <span className="relative grid size-8 place-items-center rounded-[11px] bg-accent">
        <span className="absolute h-[12px] w-[18px] -rotate-12 rounded-[4px] bg-white/35" />
        <span className="relative h-[12px] w-[18px] rounded-[4px] bg-white" />
      </span>
      {BRAND}
    </Link>
  )
}

export function Shell() {
  const { data: me } = useMe()
  const link = 'inline-flex h-9 items-center rounded-control px-3.5 text-[14px] font-medium transition-colors'
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1120px] items-center justify-between px-5 sm:px-8">
          <div className="flex items-center gap-8">
            <Logo />
            <nav className="hidden items-center gap-1 sm:flex">
              <NavLink to="/" end className={({ isActive }) => cx(link, isActive ? 'bg-surface text-fg shadow-card' : 'text-muted hover:text-fg')}>
                Library
              </NavLink>
              <NavLink to="/stats" className={({ isActive }) => cx(link, isActive ? 'bg-surface text-fg shadow-card' : 'text-muted hover:text-fg')}>
                Progress
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-2">
            {me && me.streak > 0 && (
              <Link to="/stats" className="inline-flex h-9 items-center gap-1.5 rounded-control bg-warning-soft px-3 text-[13.5px] font-semibold text-warning">
                <Flame className="size-4" />
                {me.streak}
              </Link>
            )}
            <NavLink to="/settings" className="grid size-9 place-items-center rounded-full">
              {me && <Avatar name={me.user.name ?? me.user.email ?? 'You'} hue={250} src={me.user.picture} size={32} />}
            </NavLink>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[1120px] px-5 py-8 sm:px-8 sm:py-10">
        <Outlet />
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-2 border-t border-line bg-bg/90 p-2 backdrop-blur-xl sm:hidden">
        <NavLink to="/" end className={({ isActive }) => cx('flex h-11 items-center justify-center rounded-control text-[14px] font-medium', isActive ? 'bg-surface shadow-card' : 'text-muted')}>
          Library
        </NavLink>
        <NavLink to="/stats" className={({ isActive }) => cx('flex h-11 items-center justify-center rounded-control text-[14px] font-medium', isActive ? 'bg-surface shadow-card' : 'text-muted')}>
          Progress
        </NavLink>
      </nav>
    </div>
  )
}

/** Full-screen frame for study modes: a slim header with a way out. */
export function StudyFrame({ title, progress, onExit, children, right }: { title: string; progress?: number; onExit: () => void; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 bg-bg/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[920px] items-center gap-4 px-5 sm:px-8">
          <button type="button" onClick={onExit} className="inline-flex h-9 items-center rounded-control px-3 text-[14px] font-medium text-muted transition-colors hover:bg-surface hover:text-fg">
            Exit
          </button>
          <p className="min-w-0 flex-1 truncate text-center text-[14px] font-medium">{title}</p>
          <div className="flex min-w-[64px] justify-end">{right}</div>
        </div>
        {progress !== undefined && (
          <div className="mx-auto h-1 max-w-[920px] px-5 sm:px-8">
            <div className="h-full overflow-hidden rounded-[2px] bg-raised">
              <div className="h-full rounded-[2px] bg-accent transition-[width] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]" style={{ width: `${Math.round(progress * 100)}%` }} />
            </div>
          </div>
        )}
      </header>
      <main className="mx-auto flex w-full max-w-[920px] flex-1 flex-col px-5 py-8 sm:px-8">{children}</main>
    </div>
  )
}
