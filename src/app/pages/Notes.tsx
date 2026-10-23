import { Lightbulb, Pencil, Pin, Plus, Search, StickyNote, Trash2 } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Badge, Button, Card, ConfirmDialog, Dialog, EmptyState, Field, Input, PageHeader, Spinner, Textarea, useToast } from '../components/ui'
import { useConcepts, useCreateConcept, useCreateNote, useDeleteNote, useNotes, useUpdateNote } from '../lib/api'
import { cx } from '../lib/cx'
import { relativeTime } from '../lib/format'
import type { Note, NoteKind } from '../../shared/types'

const KINDS: { value: NoteKind; label: string }[] = [
  { value: 'research', label: 'Research' },
  { value: 'lesson', label: 'Lesson' },
  { value: 'snippet', label: 'Snippet' },
  { value: 'mistake', label: 'Mistake' },
  { value: 'spec', label: 'Spec' },
  { value: 'bookmark', label: 'Bookmark' },
  { value: 'concept', label: 'Concept' },
]

export function Notes() {
  const [tab, setTab] = useState<'notes' | 'concepts'>('notes')
  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState<Note | null>(null)
  const [creating, setCreating] = useState(false)
  const [deleting, setDeleting] = useState<Note | null>(null)

  const notes = useNotes()
  const deleteNote = useDeleteNote()
  const updateNote = useUpdateNote()
  const toast = useToast()

  const filtered = useMemo(() => {
    const items = notes.data?.items ?? []
    const q = query.trim().toLowerCase()
    const list = q
      ? items.filter((n) => n.title.toLowerCase().includes(q) || n.bodyMarkdown.toLowerCase().includes(q) || n.tags.some((t) => t.toLowerCase().includes(q)))
      : items
    // Pinned first, then most recently updated.
    return [...list].sort((a, b) => Number(b.isPinned) - Number(a.isPinned) || b.updatedAt - a.updatedAt)
  }, [notes.data, query])

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Notes"
        subtitle="Your research, snippets and mistakes in one place."
        actions={
          <Button variant="primary" onClick={() => setCreating(true)}>
            <Plus className="size-4" />
            New note
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-faint" />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search notes…" className="pl-9" />
        </div>
        <div className="flex rounded-control bg-surface-2 p-0.5">
          {(['notes', 'concepts'] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={cx('h-8 rounded-tile px-3 text-[13px] font-medium capitalize transition-colors', tab === t ? 'bg-surface text-fg shadow-card' : 'text-muted')}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {tab === 'notes' ? (
        notes.isLoading ? (
          <Spinner />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<StickyNote />}
            title={query ? 'No matching notes' : 'No notes yet'}
            description={query ? 'Try a different search term.' : 'Capture your first note to start building your knowledge base.'}
            action={!query ? <Button variant="primary" onClick={() => setCreating(true)}><Plus className="size-4" />New note</Button> : undefined}
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((note) => (
              <Card key={note.id} className="group flex flex-col p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <Badge tone="neutral">{note.kind}</Badge>
                    {note.aiDraft && <Badge tone="info">AI draft</Badge>}
                  </div>
                  <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Pin"
                      onClick={() => updateNote.mutate({ id: note.id, isPinned: !note.isPinned })}
                    >
                      <Pin className={cx('size-4', note.isPinned ? 'text-accent' : 'text-faint')} />
                    </Button>
                    <Button variant="ghost" size="icon-sm" aria-label="Edit" onClick={() => setEditing(note)}>
                      <Pencil className="size-4" />
                    </Button>
                    <Button variant="ghost" size="icon-sm" aria-label="Delete" onClick={() => setDeleting(note)}>
                      <Trash2 className="size-4 text-danger" />
                    </Button>
                  </div>
                </div>
                <h3 className="mt-2 line-clamp-2 text-[15px] font-medium leading-snug">{note.title}</h3>
                {note.bodyMarkdown && <p className="mt-1 line-clamp-3 text-[13px] leading-relaxed text-muted">{note.bodyMarkdown}</p>}
                <div className="mt-auto flex flex-wrap gap-1 pt-3">
                  {note.tags.slice(0, 3).map((t) => (
                    <span key={t} className="rounded-[6px] bg-surface-2 px-1.5 py-0.5 text-[11.5px] text-muted">#{t}</span>
                  ))}
                  <span className="ml-auto text-[11.5px] text-faint">{relativeTime(note.updatedAt)}</span>
                </div>
              </Card>
            ))}
          </div>
        )
      ) : (
        <ConceptsPanel />
      )}

      <NoteDialog key={editing?.id ?? 'new'} open={creating || Boolean(editing)} note={editing} onClose={() => { setCreating(false); setEditing(null) }} />
      <ConfirmDialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (!deleting) return
          deleteNote.mutate(deleting.id, { onSuccess: () => { toast('Note deleted'); setDeleting(null) } })
        }}
        title="Delete note"
        description={deleting ? `“${deleting.title}” will be permanently removed.` : ''}
      />
    </div>
  )
}

function NoteDialog({ open, note, onClose }: { open: boolean; note: Note | null; onClose: () => void }) {
  const [title, setTitle] = useState(note?.title ?? '')
  const [body, setBody] = useState(note?.bodyMarkdown ?? '')
  const [kind, setKind] = useState<NoteKind>('research')
  const [tags, setTags] = useState(note?.tags.join(', ') ?? '')
  const create = useCreateNote()
  const update = useUpdateNote()
  const toast = useToast()

  const tagList = tags.split(',').map((t) => t.trim()).filter(Boolean)

  function save() {
    if (!title.trim()) return
    if (note) {
      // Replacing an existing body needs an explicit confirm (backend enforces too).
      update.mutate(
        { id: note.id, title: title.trim(), bodyMarkdown: body, tags: tagList, confirmOverwrite: true },
        { onSuccess: () => { toast('Note saved'); onClose() } },
      )
    } else {
      create.mutate(
        { title: title.trim(), bodyMarkdown: body, kind, tags: tagList },
        { onSuccess: () => { toast('Note created'); onClose() } },
      )
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={note ? 'Edit note' : 'New note'}
      width={560}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" loading={create.isPending || update.isPending} onClick={save} disabled={!title.trim()}>
            {note ? 'Save' : 'Create'}
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Field label="Title">
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Note title" />
        </Field>
        {!note && (
          <Field label="Kind">
            <div className="flex flex-wrap gap-1.5">
              {KINDS.map((k) => (
                <button
                  key={k.value}
                  type="button"
                  onClick={() => setKind(k.value)}
                  className={cx('h-8 rounded-tile px-3 text-[13px] font-medium transition-colors', kind === k.value ? 'bg-accent text-white' : 'bg-surface-2 text-muted')}
                >
                  {k.label}
                </button>
              ))}
            </div>
          </Field>
        )}
        <Field label="Body" hint="Markdown supported.">
          <Textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Write your note…" className="min-h-[160px]" />
        </Field>
        <Field label="Tags" hint="Comma-separated.">
          <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="risk, sizing, journal" />
        </Field>
      </div>
    </Dialog>
  )
}

function ConceptsPanel() {
  const concepts = useConcepts()
  const create = useCreateConcept()
  const toast = useToast()
  const [term, setTerm] = useState('')
  const [definition, setDefinition] = useState('')

  function add() {
    if (!term.trim() || !definition.trim()) return
    create.mutate(
      { term: term.trim(), definition: definition.trim() },
      { onSuccess: () => { setTerm(''); setDefinition(''); toast('Term added') }, onError: (e) => toast(e.message, 'danger') },
    )
  }

  if (concepts.isLoading) return <Spinner />

  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-col gap-3 p-4 sm:flex-row sm:items-end">
        <Field label="Term" className="sm:w-1/3">
          <Input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="Drawdown" />
        </Field>
        <Field label="Definition" className="flex-1">
          <Input value={definition} onChange={(e) => setDefinition(e.target.value)} placeholder="Peak-to-trough decline of equity." />
        </Field>
        <Button variant="primary" onClick={add} disabled={!term.trim() || !definition.trim()}>
          <Plus className="size-4" />
          Add
        </Button>
      </Card>

      {(concepts.data?.items.length ?? 0) === 0 ? (
        <EmptyState icon={<Lightbulb />} title="No terms yet" description="Build a glossary of the concepts you keep running into." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {concepts.data?.items.map((c) => (
            <Card key={c.id} className="p-4">
              <h3 className="text-[14.5px] font-semibold">{c.term}</h3>
              <p className="mt-1 text-[13.5px] leading-relaxed text-muted">{c.definition}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
