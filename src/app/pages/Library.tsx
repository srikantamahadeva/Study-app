import { ArrowRight, BookOpen, Plus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'

import { DeckCard } from '../components/DeckCard'
import { Button, Dialog, EmptyState, Field, Input, Skeleton, Textarea, useFieldId, useToast } from '../components/ui'
import { api, useApiMutation, useDecks, useMe } from '../lib/api'
import type { Deck } from '../../shared/types'

export function Library() {
  const { data: me } = useMe()
  const { data, isLoading } = useDecks()
  const [creating, setCreating] = useState(false)
  const decks = data?.items ?? []
  const due = decks.reduce((n, d) => n + d.dueCount, 0)
  const next = decks.find((d) => d.dueCount > 0) ?? decks[0]
  const first = me?.user.name?.split(' ')[0]
  const hour = new Date().getHours()

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[26px] font-bold tracking-[-0.02em]">
            {hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'}
            {first ? `, ${first}` : ''}
          </h1>
          <p className="mt-1 text-[14.5px] text-muted">{due > 0 ? `${due} ${due === 1 ? 'card is' : 'cards are'} due for review` : 'Nothing due. A good day to learn something new.'}</p>
        </div>
        <Button variant="primary" onClick={() => setCreating(true)}>
          <Plus />
          New deck
        </Button>
      </div>

      {next && (
        <Link
          to={`/decks/${next.id}/learn`}
          className="group mt-8 flex items-center gap-5 rounded-card bg-fg p-5 text-white shadow-float transition-transform hover:-translate-y-0.5 sm:p-6"
        >
          <span className="grid size-14 shrink-0 place-items-center rounded-[18px] text-[20px] font-bold" style={{ background: `linear-gradient(135deg, hsl(${next.hue} 70% 60%), hsl(${next.hue + 30} 70% 48%))` }}>
            {next.title[0]?.toUpperCase()}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-[13px] text-white/60">{next.dueCount > 0 ? 'Continue where you left off' : 'Keep it fresh'}</span>
            <span className="mt-0.5 block truncate text-[18px] font-semibold">{next.title}</span>
            <span className="mt-0.5 block text-[13px] text-white/60">
              {next.dueCount > 0 ? `${next.dueCount} cards due` : `${next.cardCount} cards`}, about {Math.max(2, Math.ceil((next.dueCount || next.cardCount) / 5))} minutes
            </span>
          </span>
          <span className="grid size-11 shrink-0 place-items-center rounded-[14px] bg-white text-fg transition-transform group-hover:translate-x-0.5">
            <ArrowRight className="size-4" />
          </span>
        </Link>
      )}

      <h2 className="mt-10 text-[14px] font-semibold text-muted">Your decks</h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading && Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-[168px] rounded-card" />)}
        {decks.map((d, i) => (
          <DeckCard key={d.id} deck={d} index={i} />
        ))}
        {!isLoading && (
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="flex h-[168px] flex-col items-center justify-center gap-2 rounded-card border-2 border-dashed border-line-strong text-muted transition-colors hover:border-accent hover:text-accent"
          >
            <Plus className="size-5" />
            <span className="text-[14px] font-medium">New deck</span>
          </button>
        )}
      </div>
      {data && decks.length === 0 && <EmptyState icon={<BookOpen />} title="Your library is empty" description="Create a deck and add a few cards to get started." />}

      <NewDeckDialog open={creating} onClose={() => setCreating(false)} />
    </div>
  )
}

function FieldInput(props: React.ComponentPropsWithoutRef<typeof Input>) {
  const id = useFieldId()
  return <Input id={id} {...props} />
}
function FieldTextarea(props: React.ComponentPropsWithoutRef<typeof Textarea>) {
  const id = useFieldId()
  return <Textarea id={id} {...props} />
}

export function parseCards(text: string) {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [term, ...rest] = line.split(/\s+[-–—:]\s+|\t/)
      return { term: term.trim(), definition: rest.join(' ').trim() }
    })
    .filter((c) => c.term && c.definition)
}

export function NewDeckDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate()
  const toast = useToast()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [cardsText, setCardsText] = useState('')
  const create = useApiMutation(
    () => api<{ deck: Deck }>('/decks', { method: 'POST', json: { title, description, cards: parseCards(cardsText) } }),
    ['decks', 'me'],
    {
      onSuccess: (result) => {
        toast('Deck created')
        onClose()
        setTitle('')
        setDescription('')
        setCardsText('')
        navigate(`/decks/${result.deck.id}`)
      },
    },
  )
  const parsed = parseCards(cardsText)

  function submit(e: FormEvent) {
    e.preventDefault()
    create.mutate(undefined)
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="New deck"
      width={520}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" type="submit" form="new-deck" loading={create.isPending} disabled={!title.trim()}>
            Create{parsed.length > 0 ? ` with ${parsed.length} cards` : ''}
          </Button>
        </>
      }
    >
      <form id="new-deck" onSubmit={submit} className="grid gap-4">
        <Field label="Title">
          <FieldInput required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Spanish essentials" />
        </Field>
        <Field label="Description">
          <FieldInput value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional" />
        </Field>
        <Field label="Cards" hint="One per line, term and definition separated by a dash, colon or tab. You can also add them later.">
          <FieldTextarea value={cardsText} onChange={(e) => setCardsText(e.target.value)} placeholder={'hola - hello\ngracias - thank you'} className="min-h-[120px] font-mono text-[13px]" />
        </Field>
        {create.error && <p className="text-[13px] text-danger">{create.error.message}</p>}
      </form>
    </Dialog>
  )
}
