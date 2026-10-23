import { BarChart3, BookOpen, FlaskConical, LayoutGrid, Library, LogOut, MessageSquare, StickyNote, Target } from 'lucide-react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router'

import { BRAND } from '../../shared/types'
import { useLogout, useMe } from '../lib/api'
import { cx } from '../lib/cx'
import { Avatar, Button } from './ui'

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

const NAV = [
  { to: '/', label: 'Learn', icon: BookOpen, end: true },
  { to: '/notes', label: 'Notes', icon: StickyNote },
  { to: '/flashcards', label: 'Cards', icon: Library },
  { to: '/quiz', label: 'Quiz', icon: Target },
  { to: '/labs', label: 'Labs', icon: FlaskConical },
  { to: '/projects', label: 'Projects', icon: LayoutGrid },
  { to: '/resources', label: 'Library', icon: Library },
  { to: '/reports', label: 'Reports', icon: BarChart3 },
  { to: '/tutor', label: 'Tutor', icon: MessageSquare },
]

export function Shell() {
  const { data: me } = useMe()
  const logout = useLogout()
  const navigate = useNavigate()
  const link = 'inline-flex h-9 items-center gap-1.5 rounded-control px-3 text-[13.5px] font-medium transition-colors'

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1120px] items-center justify-between gap-4 px-5 sm:px-8">
          <div className="flex items-center gap-6">
            <Logo />
            <nav className="hidden items-center gap-1 lg:flex">
              {NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => cx(link, isActive ? 'bg-surface text-fg shadow-card' : 'text-muted hover:text-fg')}
                >
                  <item.icon className="size-4" />
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-2">
            {me && (
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Sign out"
                onClick={() => {
                  logout.mutate()
                  navigate('/')
                }}
              >
                <LogOut />
              </Button>
            )}
            {me && <Avatar name={me.displayName || me.email} hue={250} size={32} />}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[1120px] px-5 py-8 sm:px-8 sm:py-10">
        <Outlet />
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-around gap-1 overflow-x-auto border-t border-line bg-bg/90 p-2 backdrop-blur-xl lg:hidden">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => cx('flex h-11 flex-1 items-center justify-center gap-1 rounded-control text-[12px] font-medium', isActive ? 'bg-surface shadow-card' : 'text-muted')}
          >
            <item.icon className="size-4" />
            <span className="hidden sm:inline">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
