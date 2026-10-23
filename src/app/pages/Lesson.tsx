import { ArrowLeft, ArrowRight, Bookmark, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { Markdown } from '../components/Markdown'
import { Badge, Button, Card, Dialog, Field, Input, PageHeader, Spinner, Textarea, useToast } from '../components/ui'
import { useAddBookmark, useDeleteBookmark, useLesson, useSetLessonProgress } from '../lib/api'

export function Lesson() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { data, isLoading } = useLesson(id)
  const setProgress = useSetLessonProgress()
  const addBookmark = useAddBookmark()
  const deleteBookmark = useDeleteBookmark()

  const [bookmarkOpen, setBookmarkOpen] = useState(false)
  const [label, setLabel] = useState('')
  const [note, setNote] = useState('')

  if (isLoading || !data) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <Spinner />
      </div>
    )
  }

  const { lesson, navigation, bookmarks } = data

  function markComplete() {
    if (!id) return
    setProgress.mutate(
      { lessonId: id, percent: 100, status: 'completed' },
      {
        onSuccess: () => {
          toast('Lesson completed')
          if (navigation.next) navigate(`/lessons/${navigation.next.id}`)
          else navigate('/')
        },
      },
    )
  }

  function saveBookmark() {
    if (!id || !label.trim()) return
    addBookmark.mutate(
      { lessonId: id, label: label.trim(), note: note.trim() },
      {
        onSuccess: () => {
          setBookmarkOpen(false)
          setLabel('')
          setNote('')
          toast('Bookmark added')
        },
      },
    )
  }

  return (
    <div className="mx-auto flex max-w-[720px] flex-col gap-6">
      <Link to="/" className="inline-flex items-center gap-1.5 text-[13.5px] text-muted hover:text-fg">
        <ArrowLeft className="size-4" />
        Back to curriculum
      </Link>

      <PageHeader
        title={lesson.title}
        subtitle={`${lesson.moduleTitle} · ${lesson.minutes} min read`}
        actions={
          <Badge tone={lesson.contentStatus === 'sample' ? 'warning' : 'success'}>
            {lesson.contentStatus === 'sample' ? 'Sample content' : 'Published'}
          </Badge>
        }
      />

      {lesson.summary && <p className="text-[15px] leading-relaxed text-muted">{lesson.summary}</p>}

      <Card className="p-6">
        <Markdown source={lesson.bodyMarkdown} />
      </Card>

      {/* Bookmarks */}
      {bookmarks.length > 0 && (
        <Card className="p-5">
          <h3 className="text-[14px] font-semibold">Bookmarks</h3>
          <ul className="mt-3 flex flex-col gap-2">
            {bookmarks.map((b) => (
              <li key={b.id} className="flex items-start gap-2 rounded-tile bg-surface-2 p-3">
                <Bookmark className="mt-0.5 size-4 shrink-0 text-accent" />
                <div className="min-w-0 flex-1">
                  <p className="text-[13.5px] font-medium">{b.label}</p>
                  {b.note && <p className="mt-0.5 text-[13px] text-muted">{b.note}</p>}
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Remove bookmark"
                  onClick={() => deleteBookmark.mutate({ bookmarkId: b.id, lessonId: lesson.id })}
                >
                  <Trash2 />
                </Button>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="secondary" onClick={() => setBookmarkOpen(true)}>
          <Bookmark className="size-4" />
          Bookmark
        </Button>
        <Button variant="primary" loading={setProgress.isPending} onClick={markComplete}>
          Mark complete
          <ArrowRight className="size-4" />
        </Button>
      </div>

      {/* Prev / next */}
      <div className="flex items-center justify-between gap-3 border-t border-line pt-5">
        {navigation.prev ? (
          <Link to={`/lessons/${navigation.prev.id}`} className="inline-flex items-center gap-1.5 text-[13.5px] text-muted hover:text-fg">
            <ArrowLeft className="size-4" />
            {navigation.prev.title}
          </Link>
        ) : (
          <span />
        )}
        {navigation.next ? (
          <Link to={`/lessons/${navigation.next.id}`} className="inline-flex items-center gap-1.5 text-right text-[13.5px] text-muted hover:text-fg">
            {navigation.next.title}
            <ArrowRight className="size-4" />
          </Link>
        ) : (
          <span />
        )}
      </div>

      <Dialog
        open={bookmarkOpen}
        onClose={() => setBookmarkOpen(false)}
        title="Add bookmark"
        description="Save a key passage from this lesson."
        footer={
          <>
            <Button onClick={() => setBookmarkOpen(false)}>Cancel</Button>
            <Button variant="primary" loading={addBookmark.isPending} onClick={saveBookmark} disabled={!label.trim()}>
              Save
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <Field label="Label">
            <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Key sentence" />
          </Field>
          <Field label="Note (optional)">
            <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Why this matters" />
          </Field>
        </div>
      </Dialog>
    </div>
  )
}
