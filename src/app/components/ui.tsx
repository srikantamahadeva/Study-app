import { AnimatePresence, motion } from 'motion/react'
import { ChevronDown, Loader2, X } from 'lucide-react'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  type ComponentPropsWithoutRef,
  type ReactNode,
} from 'react'

import { cx } from '../lib/cx'
import { initials } from '../lib/format'

// Buttons, inputs and selects share one height per size so controls that sit
// beside each other line up: md = 36px, sm = 32px.

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
type ButtonSize = 'md' | 'sm' | 'icon' | 'icon-sm'

const buttonBase =
  'inline-flex shrink-0 select-none items-center justify-center gap-1.5 whitespace-nowrap rounded-control font-medium transition-[background-color,color,box-shadow,transform] duration-150 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0'
const buttonVariants: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-white shadow-[inset_0_1px_0_rgb(255_255_255/0.15)] hover:bg-accent-deep',
  secondary: 'border border-line-strong bg-surface text-fg shadow-[0_1px_1px_rgb(20_20_24/0.04)] hover:bg-surface-2',
  ghost: 'text-muted hover:bg-surface-2 hover:text-fg',
  danger: 'bg-danger text-white hover:bg-[#bf3b26]',
}
const buttonSizes: Record<ButtonSize, string> = {
  md: 'h-9 px-3.5 text-[13.5px]',
  sm: 'h-8 px-3 text-[13px] rounded-tile',
  icon: 'size-9',
  'icon-sm': 'size-8 rounded-tile',
}

export function Button({
  variant = 'secondary',
  size = 'md',
  className,
  loading,
  children,
  ...rest
}: ComponentPropsWithoutRef<'button'> & { variant?: ButtonVariant; size?: ButtonSize; loading?: boolean }) {
  return (
    <button type="button" className={cx(buttonBase, buttonVariants[variant], buttonSizes[size], className)} disabled={loading || rest.disabled} {...rest}>
      {loading ? <Loader2 className="animate-spin" /> : children}
    </button>
  )
}

export const inputClass =
  'h-9 w-full min-w-0 rounded-control border border-line-strong bg-surface px-3 text-[13.5px] text-fg placeholder:text-faint transition-[border-color,box-shadow] focus:border-accent focus:outline-none focus:ring-[3px] focus:ring-accent/15 disabled:opacity-60'

export function Input({ className, ...rest }: ComponentPropsWithoutRef<'input'>) {
  return <input className={cx(inputClass, className)} {...rest} />
}

export function Textarea({ className, ...rest }: ComponentPropsWithoutRef<'textarea'>) {
  return <textarea className={cx(inputClass, 'h-auto min-h-[88px] resize-y py-2 leading-relaxed', className)} {...rest} />
}

export function Select({ className, children, ...rest }: ComponentPropsWithoutRef<'select'>) {
  return (
    <span className={cx('relative block', className)}>
      <select className={cx(inputClass, 'appearance-none pr-9')} {...rest}>
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-faint" />
    </span>
  )
}

export function Checkbox({ className, ...rest }: ComponentPropsWithoutRef<'input'>) {
  return (
    <span className={cx('relative inline-grid size-4.5 shrink-0 place-items-center', className)}>
      <input
        type="checkbox"
        className="peer absolute inset-0 size-full cursor-pointer appearance-none rounded-[6px] border border-line-strong bg-surface transition-colors checked:border-fg checked:bg-fg disabled:cursor-default"
        {...rest}
      />
      <svg viewBox="0 0 16 16" className="pointer-events-none relative size-3 opacity-0 transition-opacity peer-checked:opacity-100" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M3.5 8.5l2.8 2.8L12.5 5" />
      </svg>
    </span>
  )
}

export function Field({ label, children, hint, className }: { label: string; children: ReactNode; hint?: string; className?: string }) {
  const id = useId()
  return (
    <label htmlFor={id} className={cx('flex flex-col gap-1.5', className)}>
      <span className="text-[13px] font-medium text-fg">{label}</span>
      <FieldIdContext.Provider value={id}>{children}</FieldIdContext.Provider>
      {hint && <span className="text-[12px] text-faint">{hint}</span>}
    </label>
  )
}
const FieldIdContext = createContext<string | undefined>(undefined)
export const useFieldId = () => useContext(FieldIdContext)

type Tone = 'neutral' | 'accent' | 'success' | 'warning' | 'danger' | 'info'
const toneClasses: Record<Tone, string> = {
  neutral: 'bg-surface-2 text-muted',
  accent: 'bg-accent-soft text-accent',
  success: 'bg-success-soft text-success',
  warning: 'bg-warning-soft text-warning',
  danger: 'bg-danger-soft text-danger',
  info: 'bg-info-soft text-info',
}
export function Badge({ tone = 'neutral', className, children, dot }: { tone?: Tone; className?: string; children: ReactNode; dot?: boolean }) {
  return (
    <span className={cx('inline-flex h-6 items-center gap-1.5 whitespace-nowrap rounded-[8px] px-2 text-[12px] font-medium', toneClasses[tone], className)}>
      {dot && <span className="round size-1.5 bg-current" />}
      {children}
    </span>
  )
}

export function Avatar({
  name,
  hue,
  src,
  size = 32,
  className,
}: {
  name: string
  hue: number
  src?: string | null
  size?: number
  className?: string
}) {
  const [broken, setBroken] = useState(false)
  useEffect(() => setBroken(false), [src])
  const style = { width: size, height: size, fontSize: Math.max(10, Math.round(size * 0.36)) }
  if (src && !broken) {
    return <img src={src} alt="" onError={() => setBroken(true)} className={cx('round shrink-0 rounded-full object-cover', className)} style={style} />
  }
  return (
    <span
      className={cx('round grid shrink-0 place-items-center rounded-full font-semibold text-white', className)}
      style={{ ...style, background: `linear-gradient(135deg, hsl(${hue} 60% 62%), hsl(${hue + 35} 60% 48%))` }}
      aria-hidden
    >
      {initials(name)}
    </span>
  )
}

export function CompanyMark({ name, hue, size = 32, className }: { name: string; hue: number; size?: number; className?: string }) {
  return (
    <span
      className={cx('grid shrink-0 place-items-center rounded-tile font-semibold', className)}
      style={{
        width: size,
        height: size,
        fontSize: Math.max(10, Math.round(size * 0.4)),
        background: `hsl(${hue} 55% 94%)`,
        color: `hsl(${hue} 50% 38%)`,
        borderRadius: Math.round(size * 0.32),
      }}
      aria-hidden
    >
      {name.trim()[0]?.toUpperCase() ?? '?'}
    </span>
  )
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cx('size-5 animate-spin text-faint', className)} />
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx('animate-pulse rounded-tile bg-raised/70', className)} />
}

export function EmptyState({ icon, title, description, action }: { icon?: ReactNode; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      {icon && <div className="mb-4 grid size-12 place-items-center rounded-card bg-surface-2 text-muted [&_svg]:size-5">{icon}</div>}
      <p className="text-[15px] font-medium">{title}</p>
      {description && <p className="mt-1 max-w-sm text-[13.5px] text-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function Card({ className, children, ...rest }: ComponentPropsWithoutRef<'section'>) {
  return (
    <section className={cx('rounded-card bg-surface shadow-card', className)} {...rest}>
      {children}
    </section>
  )
}

// Dialog and Drawer share the overlay: Escape or backdrop closes, scroll is
// locked while open, focus moves to the first field.

function useOverlay(open: boolean, onClose: () => void) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    const previous = document.activeElement as HTMLElement | null
    const timer = window.setTimeout(() => {
      const first = ref.current?.querySelector<HTMLElement>('input, textarea, select, button:not([data-close])')
      first?.focus()
    }, 30)
    return () => {
      document.removeEventListener('keydown', onKey)
      window.clearTimeout(timer)
      previous?.focus?.()
    }
  }, [open, onClose])
  return ref
}

export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  width = 480,
}: {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
  footer?: ReactNode
  width?: number
}) {
  const ref = useOverlay(open, onClose)
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="overlay"
          className="fixed inset-0 z-50 flex items-end justify-center bg-fg/30 p-4 backdrop-blur-[2px] sm:items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
          onMouseDown={(e) => e.target === e.currentTarget && onClose()}
        >
          <motion.div
            ref={ref}
            role="dialog"
            aria-modal
            aria-label={title}
            className="flex max-h-[90vh] w-full flex-col overflow-hidden rounded-dialog bg-surface shadow-dialog"
            style={{ maxWidth: width }}
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          >
            <header className="flex items-start justify-between gap-4 px-6 pt-5">
              <div>
                <h2 className="text-[16px] font-semibold">{title}</h2>
                {description && <p className="mt-1 text-[13px] text-muted">{description}</p>}
              </div>
              <Button data-close variant="ghost" size="icon-sm" aria-label="Close" onClick={onClose} className="-mr-2 -mt-1">
                <X />
              </Button>
            </header>
            <div className="scrollbar-thin overflow-y-auto px-6 py-5">{children}</div>
            {footer && <footer className="flex items-center justify-end gap-2 border-t border-line px-6 py-4">{footer}</footer>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export function Drawer({
  open,
  onClose,
  title,
  children,
  header,
  width = 520,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  header?: ReactNode
  width?: number
}) {
  const ref = useOverlay(open, onClose)
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="overlay"
          className="fixed inset-0 z-50 bg-fg/20"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
          onMouseDown={(e) => e.target === e.currentTarget && onClose()}
        >
          <motion.aside
            ref={ref}
            role="dialog"
            aria-modal
            aria-label={title}
            className="absolute inset-y-2 right-2 flex w-[calc(100%-16px)] flex-col overflow-hidden rounded-dialog bg-surface shadow-dialog"
            style={{ maxWidth: width }}
            initial={{ x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 40, opacity: 0 }}
            transition={{ duration: 0.26, ease: [0.22, 1, 0.36, 1] }}
          >
            <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
              <div className="min-w-0 flex-1">{header ?? <h2 className="truncate text-[15px] font-semibold">{title}</h2>}</div>
              <Button data-close variant="ghost" size="icon-sm" aria-label="Close" onClick={onClose}>
                <X />
              </Button>
            </header>
            <div className="scrollbar-thin flex-1 overflow-y-auto">{children}</div>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Delete',
  loading,
}: {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description: string
  confirmLabel?: string
  loading?: boolean
}) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={title}
      width={420}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="danger" onClick={onConfirm} loading={loading}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-[13.5px] text-muted">{description}</p>
    </Dialog>
  )
}

// Menus: a small popover anchored to its trigger.
export function Menu({
  trigger,
  items,
  align = 'end',
}: {
  trigger: ReactNode
  items: { label: string; onSelect: () => void; danger?: boolean; icon?: ReactNode }[]
  align?: 'start' | 'end'
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false)
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])
  return (
    <div ref={ref} className="relative inline-flex">
      <span onClick={(e) => (e.stopPropagation(), setOpen((v) => !v))} className="inline-flex">
        {trigger}
      </span>
      <AnimatePresence>
        {open && (
          <motion.ul
            role="menu"
            initial={{ opacity: 0, y: 4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.14 }}
            className={cx('absolute top-full z-40 mt-1 min-w-[180px] rounded-[14px] bg-surface p-1 shadow-pop', align === 'end' ? 'right-0' : 'left-0')}
          >
            {items.map((item) => (
              <li key={item.label}>
                <button
                  type="button"
                  role="menuitem"
                  onClick={(e) => {
                    e.stopPropagation()
                    setOpen(false)
                    item.onSelect()
                  }}
                  className={cx(
                    'flex h-9 w-full items-center gap-2 rounded-tile px-2.5 text-left text-[13.5px] transition-colors [&_svg]:size-4',
                    item.danger ? 'text-danger hover:bg-danger-soft' : 'text-fg hover:bg-surface-2',
                  )}
                >
                  {item.icon}
                  {item.label}
                </button>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  )
}

// Toasts
type Toast = { id: number; message: string; tone: 'neutral' | 'danger' }
const ToastContext = createContext<(message: string, tone?: Toast['tone']) => void>(() => {})
export const useToast = () => useContext(ToastContext)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const push = useCallback((message: string, tone: Toast['tone'] = 'neutral') => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, message, tone }])
    window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3200)
  }, [])
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-5 z-[60] flex flex-col items-center gap-2">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 12, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.96 }}
              className={cx(
                'pointer-events-auto rounded-control px-4 py-2.5 text-[13.5px] font-medium shadow-pop',
                t.tone === 'danger' ? 'bg-danger text-white' : 'bg-fg text-white',
              )}
            >
              {t.message}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-[22px] font-semibold tracking-[-0.02em]">{title}</h1>
        {subtitle && <p className="mt-0.5 text-[13.5px] text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
