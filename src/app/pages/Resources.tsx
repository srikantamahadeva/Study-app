import { FileText, Trash2, Upload } from 'lucide-react'
import { useRef, useState } from 'react'

import { Badge, Button, Card, ConfirmDialog, EmptyState, PageHeader, Spinner, useToast } from '../components/ui'
import { useDeleteResource, useResources, useUploadResource } from '../lib/api'
import { shortDate } from '../lib/format'

const kindTone = { pdf: 'danger', image: 'info', code: 'success', note: 'neutral', other: 'neutral' } as const

/** Uploaded reference material (PDFs, images, code) for the tutor and search. */
export function Resources() {
  const { data, isLoading } = useResources()
  const upload = useUploadResource()
  const remove = useDeleteResource()
  const toast = useToast()
  const input = useRef<HTMLInputElement>(null)
  const [deleting, setDeleting] = useState<{ id: string; title: string } | null>(null)

  if (isLoading) return <Spinner />
  const items = data?.items ?? []

  function onFiles(files: FileList | null) {
    if (!files?.length) return
    Array.from(files).forEach((file) =>
      upload.mutate(file, {
        onSuccess: (res) => toast(res.indexed ? `Uploaded and indexed ${res.chunks} chunk${res.chunks === 1 ? '' : 's'}` : 'Uploaded'),
        onError: (e) => toast(e.message, 'danger'),
      }),
    )
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Library"
        subtitle="Upload reference material. PDFs and code are indexed for search and the tutor."
        actions={
          <>
            <input ref={input} type="file" multiple className="hidden" onChange={(e) => onFiles(e.target.files)} />
            <Button variant="primary" loading={upload.isPending} onClick={() => input.current?.click()}>
              <Upload className="size-4" />
              Upload
            </Button>
          </>
        }
      />

      {items.length === 0 ? (
        <EmptyState
          icon={<FileText />}
          title="No uploads yet"
          description="Upload a PDF, image, or code file. PDFs and code are indexed so the tutor can cite them."
          action={
            <Button variant="primary" onClick={() => input.current?.click()}>
              <Upload className="size-4" />
              Upload a file
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((r) => (
            <Card key={r.id} className="group flex flex-col p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="grid size-9 place-items-center rounded-tile bg-surface-2 text-muted">
                  <FileText className="size-4" />
                </div>
                <Button variant="ghost" size="icon-sm" aria-label="Delete" onClick={() => setDeleting({ id: r.id, title: r.title })}>
                  <Trash2 className="size-4 text-danger" />
                </Button>
              </div>
              <h3 className="mt-2.5 line-clamp-2 text-[14.5px] font-medium leading-snug">{r.title}</h3>
              {r.contentPreview && <p className="mt-1 line-clamp-2 text-[13px] leading-relaxed text-muted">{r.contentPreview}</p>}
              <div className="mt-auto flex items-center gap-2 pt-3">
                <Badge tone={kindTone[r.kind]}>{r.kind}</Badge>
                <span className="text-[11.5px] text-faint">{shortDate(r.createdAt)}</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (!deleting) return
          remove.mutate(deleting.id, {
            onSuccess: () => {
              toast('Deleted')
              setDeleting(null)
            },
          })
        }}
        title="Delete file"
        description={deleting ? `“${deleting.title}” and its extracted text will be permanently removed.` : ''}
      />
    </div>
  )
}
