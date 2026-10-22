import { ArrowLeft, Brain, Check, Image as ImageIcon, Layers, MoreHorizontal, Pencil, Plus, Shuffle, Trash2, X } from 'lucide-react'
import { useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { ProgressRing } from '../components/DeckCard'
import { Button, ConfirmDialog, Dialog, Field, Input, Menu, Spinner, Textarea, useFieldId, useToast } from '../components/ui'
import { api, uploadCardImage, useApiMutation, useDeck, useMe } from '../lib/api'
import { cx } from '../lib/cx'
import { relativeTime } from '../lib/format'
import { parseCards } from './Library'
import type { Card } from '../../shared/types'

const modes = [
  { key: 'flashcards', label: 'Flashcards', detail: 'Flip through and sort what you know', icon: Layers },
  { key: 'learn', label: 'Learn', detail: 'Multiple choice, focused on weak cards', icon: Brain },
  { key: 'match', label: 'Match', detail: 'Pair terms and definitions against the clock', icon: Shuffle },
] as const

export function Deck() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { data, isLoading } = useDeck(id)
  const { data: me } = useMe()
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [editingCard, setEditingCard] = useState<Card | null>(null)

  const remove = useApiMutation(() => api(`/decks/${id}`, { method: 'DELETE' }), ['decks', 'stats', 'me'], { onSuccess: () => navigate('/') })
  const removeCard = useApiMutation((cardId: string) => api(`/decks/${id}/cards/${cardId}`, { method: 'DELETE' }), ['deck', 'decks'])
  const imageMutation = useApiMutation((input: { cardId: string; file: File }) => uploadCardImage(id!, input.cardId, input.file), ['deck'], { onSuccess: () => toast('Image added') })
  const removeImage = useApiMutation((cardId: string) => api(`/decks/${id}/cards/${cardId}/image`, { method: 'DELETE' }), ['deck'])
  const fileInput = useRef<HTMLInputElement>(null)
  const [imageTarget, setImageTarget] = useState<string | null>(null)

  if (isLoading || !data) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <Spinner />
      </div>
    )
  }
  const { deck, cards, sessions } = data
  const weak = cards.filter((c) => c.progress.mastery < 40).length

  return (
    <div>
      <Link to="/" className="inline-flex h-8 items-center gap-1.5 text-[13.5px] text-muted hover:text-fg">
        <ArrowLeft className="size-4" />
        Library
      </Link>

      <header className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="relative grid place-items-center">
            <ProgressRing value={deck.mastery} size={64} stroke={5} hue={deck.hue} />
            <span className="absolute text-[13px] font-bold tabular-nums">{deck.mastery}%</span>
          </div>
          <div>
            <h1 className="text-[28px] font-bold tracking-[-0.02em]">{deck.title}</h1>
            {deck.description && <p className="mt-1 max-w-xl text-[14.5px] text-muted">{deck.description}</p>}
            <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[13px] text-faint">
              <span>{deck.cardCount} cards</span>
              <span>{deck.mastered} mastered</span>
              {weak > 0 && <span className="text-warning">{weak} still learning</span>}
              {deck.lastStudiedAt && <span>Studied {relativeTime(deck.lastStudiedAt)}</span>}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setAdding(true)}>
            <Plus />
            Add cards
          </Button>
          <Menu
            trigger={
              <Button size="icon" aria-label="More">
                <MoreHorizontal />
              </Button>
            }
            items={[
              { label: 'Edit deck', icon: <Pencil />, onSelect: () => setEditing(true) },
              { label: 'Delete deck', icon: <Trash2 />, danger: true, onSelect: () => setDeleting(true) },
            ]}
          />
        </div>
      </header>

      <div className="mt-8 grid gap-3 sm:grid-cols-3">
        {modes.map(({ key, label, detail, icon: Icon }) => {
          const disabled = cards.length < (key === 'match' ? 3 : key === 'learn' ? 4 : 1)
          return (
            <button
              key={key}
              type="button"
              disabled={disabled}
              onClick={() => navigate(`/decks/${deck.id}/${key}`)}
              className="group flex h-[108px] flex-col justify-between rounded-card bg-surface p-4 text-left shadow-card transition-[box-shadow,transform] hover:-translate-y-0.5 hover:shadow-pop disabled:pointer-events-none disabled:opacity-50"
            >
              <span className="grid size-9 place-items-center rounded-[12px] bg-accent-soft text-accent">
                <Icon className="size-4" />
              </span>
              <span>
                <span className="block text-[15px] font-semibold">{label}</span>
                <span className="block text-[12.5px] text-muted">{disabled ? `Needs at least ${key === 'match' ? 3 : 4} cards` : detail}</span>
              </span>
            </button>
          )
        })}
      </div>

      <div className="mt-10 flex items-center justify-between">
        <h2 className="text-[14px] font-semibold text-muted">Cards</h2>
        {sessions[0] && (
          <span className="text-[13px] text-faint">
            Last session {sessions[0].accuracy}% in {sessions[0].mode}
          </span>
        )}
      </div>
      <ul className="mt-3 flex flex-col gap-2">
        {cards.map((card, i) => (
          <li key={card.id} className="group grid grid-cols-[1fr_1fr_auto] items-center gap-4 rounded-card bg-surface px-5 py-3.5 shadow-card">
            <div className="flex items-start gap-4">
              <span className="w-6 shrink-0 pt-0.5 text-[12px] tabular-nums text-faint">{i + 1}</span>
              <div className="min-w-0">
                <p className="text-[15px] font-medium leading-snug">{card.term}</p>
                {card.hasImage && <img src={`/api/decks/${deck.id}/cards/${card.id}/image`} alt="" className="mt-2 h-20 w-28 rounded-[12px] object-cover" />}
              </div>
            </div>
            <p className="border-l border-line pl-4 text-[14.5px] leading-snug text-muted">{card.definition}</p>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
                {me?.capabilities.files && (
                  <button
                    type="button"
                    aria-label={card.hasImage ? 'Remove image' : 'Add image'}
                    onClick={() => {
                      if (card.hasImage) removeImage.mutate(card.id)
                      else {
                        setImageTarget(card.id)
                        fileInput.current?.click()
                      }
                    }}
                    className={cx('grid size-8 place-items-center rounded-tile text-faint hover:bg-surface-2 hover:text-fg', card.hasImage && 'text-accent')}
                  >
                    <ImageIcon className="size-4" />
                  </button>
                )}
                <button type="button" aria-label="Edit card" onClick={() => setEditingCard(card)} className="grid size-8 place-items-center rounded-tile text-faint hover:bg-surface-2 hover:text-fg">
                  <Pencil className="size-4" />
                </button>
                <button type="button" aria-label="Delete card" onClick={() => removeCard.mutate(card.id)} className="grid size-8 place-items-center rounded-tile text-faint hover:bg-surface-2 hover:text-danger">
                  <Trash2 className="size-4" />
                </button>
              </div>
              <span className="w-[88px] text-right"><MasteryPill value={card.progress.mastery} /></span>
            </div>
          </li>
        ))}
        {cards.length === 0 && (
          <li className="rounded-card border-2 border-dashed border-line-strong py-12 text-center">
            <p className="text-[15px] font-medium">No cards yet</p>
            <Button variant="primary" className="mt-4" onClick={() => setAdding(true)}>
              <Plus />
              Add cards
            </Button>
          </li>
        )}
      </ul>
      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file && imageTarget) imageMutation.mutate({ cardId: imageTarget, file })
          e.target.value = ''
        }}
      />

      <AddCardsDialog open={adding} onClose={() => setAdding(false)} deckId={deck.id} />
      <EditDeckDialog open={editing} onClose={() => setEditing(false)} deckId={deck.id} title={deck.title} description={deck.description ?? ''} />
      <EditCardDialog card={editingCard} deckId={deck.id} onClose={() => setEditingCard(null)} />
      <ConfirmDialog
        open={deleting}
        onClose={() => setDeleting(false)}
        onConfirm={() => remove.mutate(undefined)}
        loading={remove.isPending}
        title={`Delete ${deck.title}?`}
        description="All its cards, progress and session history are removed."
      />
    </div>
  )
}

export function MasteryPill({ value }: { value: number }) {
  const tone = value >= 80 ? 'bg-success-soft text-success' : value >= 40 ? 'bg-warning-soft text-warning' : value > 0 ? 'bg-danger-soft text-danger' : 'bg-surface-2 text-faint'
  const label = value >= 80 ? 'Mastered' : value >= 40 ? 'Learning' : value > 0 ? 'Weak' : 'New'
  return <span className={cx('inline-flex h-6 items-center gap-1 rounded-[8px] px-2 text-[12px] font-medium', tone)}>{value >= 80 && <Check className="size-3" />}{label}</span>
}

function FieldInput(props: React.ComponentPropsWithoutRef<typeof Input>) {
  const id = useFieldId()
  return <Input id={id} {...props} />
}
function FieldTextarea(props: React.ComponentPropsWithoutRef<typeof Textarea>) {
  const id = useFieldId()
  return <Textarea id={id} {...props} />
}

function AddCardsDialog({ open, onClose, deckId }: { open: boolean; onClose: () => void; deckId: string }) {
  const toast = useToast()
  const [rows, setRows] = useState([{ term: '', definition: '' }])
  const [bulk, setBulk] = useState('')
  const [tab, setTab] = useState<'one' | 'bulk'>('one')
  const cards = tab === 'one' ? rows.filter((r) => r.term.trim() && r.definition.trim()) : parseCards(bulk)
  const add = useApiMutation(() => api<{ added: number }>(`/decks/${deckId}/cards`, { method: 'POST', json: { cards } }), ['deck', 'decks'], {
    onSuccess: (r) => {
      toast(`${r.added} ${r.added === 1 ? 'card' : 'cards'} added`)
      setRows([{ term: '', definition: '' }])
      setBulk('')
      onClose()
    },
  })
  function submit(e: FormEvent) {
    e.preventDefault()
    if (cards.length) add.mutate(undefined)
  }
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Add cards"
      width={560}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" type="submit" form="add-cards" loading={add.isPending} disabled={cards.length === 0}>
            Add {cards.length > 0 ? cards.length : ''} {cards.length === 1 ? 'card' : 'cards'}
          </Button>
        </>
      }
    >
      <div className="grid h-9 grid-cols-2 rounded-control bg-surface-2 p-1 text-[13px] font-medium">
        {(['one', 'bulk'] as const).map((t) => (
          <button key={t} type="button" onClick={() => setTab(t)} className={cx('rounded-[10px] transition-colors', tab === t ? 'bg-surface shadow-card' : 'text-muted')}>
            {t === 'one' ? 'One by one' : 'Paste a list'}
          </button>
        ))}
      </div>
      <form id="add-cards" onSubmit={submit} className="mt-4">
        {tab === 'one' ? (
          <div className="flex flex-col gap-2">
            {rows.map((row, i) => (
              <div key={i} className="grid grid-cols-[1fr_1fr_36px] gap-2">
                <Input placeholder="Term" value={row.term} onChange={(e) => setRows(rows.map((r, j) => (j === i ? { ...r, term: e.target.value } : r)))} />
                <Input placeholder="Definition" value={row.definition} onChange={(e) => setRows(rows.map((r, j) => (j === i ? { ...r, definition: e.target.value } : r)))} />
                <Button size="icon" variant="ghost" aria-label="Remove row" disabled={rows.length === 1} onClick={() => setRows(rows.filter((_, j) => j !== i))}>
                  <X />
                </Button>
              </div>
            ))}
            <Button variant="ghost" className="self-start" onClick={() => setRows([...rows, { term: '', definition: '' }])}>
              <Plus />
              Another card
            </Button>
          </div>
        ) : (
          <Field label="Cards" hint="One per line: term, then a dash, colon or tab, then the definition.">
            <FieldTextarea value={bulk} onChange={(e) => setBulk(e.target.value)} className="min-h-[180px] font-mono text-[13px]" placeholder={'photosynthesis - how plants make food from light\nosmosis - water moving across a membrane'} />
          </Field>
        )}
        {add.error && <p className="mt-3 text-[13px] text-danger">{add.error.message}</p>}
      </form>
    </Dialog>
  )
}

function EditDeckDialog({ open, onClose, deckId, title, description }: { open: boolean; onClose: () => void; deckId: string; title: string; description: string }) {
  const [form, setForm] = useState({ title, description })
  const save = useApiMutation(() => api(`/decks/${deckId}`, { method: 'PATCH', json: form }), ['deck', 'decks'], { onSuccess: onClose })
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Edit deck"
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={() => save.mutate(undefined)} loading={save.isPending} disabled={!form.title.trim()}>
            Save
          </Button>
        </>
      }
    >
      <div className="grid gap-4">
        <Field label="Title">
          <FieldInput value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </Field>
        <Field label="Description">
          <FieldInput value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </Field>
      </div>
    </Dialog>
  )
}

function EditCardDialog({ card, deckId, onClose }: { card: Card | null; deckId: string; onClose: () => void }) {
  const [form, setForm] = useState({ term: '', definition: '' })
  const [loadedFor, setLoadedFor] = useState<string | null>(null)
  if (card && loadedFor !== card.id) {
    setForm({ term: card.term, definition: card.definition })
    setLoadedFor(card.id)
  }
  const save = useApiMutation(() => api(`/decks/${deckId}/cards/${card?.id}`, { method: 'PATCH', json: form }), ['deck'], { onSuccess: onClose })
  return (
    <Dialog
      open={Boolean(card)}
      onClose={onClose}
      title="Edit card"
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={() => save.mutate(undefined)} loading={save.isPending} disabled={!form.term.trim() || !form.definition.trim()}>
            Save
          </Button>
        </>
      }
    >
      <div className="grid gap-4">
        <Field label="Term">
          <FieldInput value={form.term} onChange={(e) => setForm({ ...form, term: e.target.value })} />
        </Field>
        <Field label="Definition">
          <FieldTextarea value={form.definition} onChange={(e) => setForm({ ...form, definition: e.target.value })} />
        </Field>
      </div>
    </Dialog>
  )
}
