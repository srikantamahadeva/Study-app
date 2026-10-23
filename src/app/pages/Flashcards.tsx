import { Layers, Plus } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router'

import { Badge, Button, Card, Dialog, EmptyState, Field, Input, PageHeader, Spinner, Textarea, useToast } from '../components/ui'
import { useAddCard, useCreateDeck, useDecks, useDeck } from '../lib/api'
import { dueLabel } from '../lib/format'

/** Deck list with counts and due badges. */
export function Flashcards() {
  const decks = useDecks()
  const createDeck = useCreateDeck()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')

  if (decks.isLoading) return <Spinner />

  const items = decks.data?.items ?? []

  function submit() {
    if (!title.trim()) return
    createDeck.mutate(title.trim(), {
      onSuccess: () => {
        setTitle('')
        setOpen(false)
        toast('Deck created')
      },
    })
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Flashcards"
        subtitle="Decks scheduled by spaced repetition."
        actions={
          <Button variant="primary" onClick={() => setOpen(true)}>
            <Plus className="size-4" />
            New deck
          </Button>
        }
      />

      {items.length === 0 ? (
        <EmptyState
          icon={<Layers />}
          title="No decks yet"
          description="Create a deck to start turning what you study into reviewable cards."
          action={
            <Button variant="primary" onClick={() => setOpen(true)}>
              <Plus className="size-4" />
              New deck
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((deck) => (
            <Link key={deck.id} to={`/decks/${deck.id}`}>
              <Card className="flex h-full flex-col p-5 transition-shadow hover:shadow-pop">
                <div className="flex items-start justify-between">
                  <div className="grid size-10 place-items-center rounded-tile bg-accent-soft text-accent">
                    <Layers className="size-5" />
                  </div>
                  {deck.dueCount > 0 && <Badge tone="warning">{deck.dueCount} due</Badge>}
                </div>
                <h3 className="mt-3 line-clamp-2 text-[15px] font-medium leading-snug">{deck.title}</h3>
                <div className="mt-auto flex items-center justify-between pt-3 text-[12.5px] text-muted">
                  <span>{deck.cardCount} cards</span>
                  <span>{deck.dueCount > 0 ? 'Due now' : 'Up to date'}</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="New deck"
        footer={
          <>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button variant="primary" loading={createDeck.isPending} onClick={submit} disabled={!title.trim()}>
              Create
            </Button>
          </>
        }
      >
        <Field label="Deck name">
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Risk management" />
        </Field>
      </Dialog>
    </div>
  )
}

/** One deck: its cards with front/back and review state, plus add-card. */
export function Deck() {
  const { id } = useParams()
  const { data, isLoading } = useDeck(id)
  const addCard = useAddCard(id!)
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [front, setFront] = useState('')
  const [back, setBack] = useState('')

  if (isLoading) return <Spinner />
  if (!data) {
    return <EmptyState icon={<Layers />} title="Deck not found" description="This deck may have been deleted." />
  }

  function submit() {
    if (!front.trim() || !back.trim()) return
    addCard.mutate(
      { front: front.trim(), back: back.trim() },
      {
        onSuccess: () => {
          setFront('')
          setBack('')
          setOpen(false)
          toast('Card added')
        },
      },
    )
  }

  return (
    <div className="flex flex-col gap-5">
      <Link to="/flashcards" className="text-[13.5px] text-muted hover:text-fg">
        ← All decks
      </Link>

      <PageHeader
        title={data.deck.title}
        subtitle={`${data.cards.length} cards · ${data.dueNow} due now`}
        actions={
          <Button variant="primary" onClick={() => setOpen(true)}>
            <Plus className="size-4" />
            Add card
          </Button>
        }
      />

      {data.cards.length === 0 ? (
        <EmptyState icon={<Layers />} title="No cards yet" description="Add your first card to start building this deck." />
      ) : (
        <div className="flex flex-col divide-y divide-line/60">
          {data.cards.map((card) => {
            const due = dueLabel(card.dueAt)
            return (
              <div key={card.id} className="flex flex-col gap-1 py-3.5">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[14.5px] font-medium">{card.front}</p>
                  <span className="shrink-0 text-[12px] text-muted">{due.label}</span>
                </div>
                <p className="text-[13.5px] leading-relaxed text-muted">{card.back}</p>
                <div className="flex items-center gap-2 pt-0.5 text-[11.5px] text-faint">
                  <span className="capitalize">{card.state}</span>
                  {card.repetitions > 0 && <span>· {card.repetitions} reps</span>}
                  {card.ease !== null && <span>· ease {card.ease.toFixed(1)}</span>}
                </div>
              </div>
            )
          })}
        </div>
      )}

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Add card"
        width={520}
        footer={
          <>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button variant="primary" loading={addCard.isPending} onClick={submit} disabled={!front.trim() || !back.trim()}>
              Add
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <Field label="Front">
            <Textarea value={front} onChange={(e) => setFront(e.target.value)} placeholder="Term or question" className="min-h-[64px]" />
          </Field>
          <Field label="Back">
            <Textarea value={back} onChange={(e) => setBack(e.target.value)} placeholder="Definition or answer" className="min-h-[80px]" />
          </Field>
        </div>
      </Dialog>
    </div>
  )
}
