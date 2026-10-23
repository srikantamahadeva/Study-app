import { Search as SearchIcon } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import { Badge, Card, EmptyState, Input, PageHeader, Spinner } from '../components/ui'
import { useSearch } from '../lib/api'
import type { SearchResult } from '../../shared/types'

const typeTone: Record<SearchResult['type'], 'accent' | 'neutral' | 'success' | 'info'> = {
  lesson: 'accent',
  note: 'neutral',
  concept: 'info',
  flashcard: 'neutral',
  quiz: 'info',
  project: 'success',
  document: 'neutral',
}

const href = (r: SearchResult) => {
  // The backend returns a best-effort path; fall back to the owning section.
  if (r.type === 'lesson' && r.id) return `/lessons/${r.id}`
  if (r.type === 'project' && r.id) return `/projects/${r.id}`
  if (r.type === 'note') return '/notes'
  if (r.type === 'concept') return '/notes'
  if (r.type === 'flashcard') return '/flashcards'
  if (r.type === 'quiz') return '/quiz'
  if (r.type === 'document') return '/resources'
  return '/'
}

/** Global search across everything in the account. */
export function Search() {
  const [query, setQuery] = useState('')
  const { data, isLoading } = useSearch(query)

  const results = data?.items ?? []

  return (
    <div className="mx-auto flex max-w-[720px] flex-col gap-5">
      <PageHeader title="Search" subtitle="Find lessons, notes, concepts, cards and uploads." />

      <div className="relative">
        <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-faint" />
        <Input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search everything…" className="h-11 pl-9 text-[15px]" />
      </div>

      {isLoading && query.trim() && <Spinner />}

      {query.trim() && !isLoading && results.length === 0 && (
        <EmptyState icon={<SearchIcon />} title="No results" description={`Nothing matched “${query}”. Try a different term.`} />
      )}

      {results.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-[13px] text-muted">
            {data?.total} result{data?.total === 1 ? '' : 's'}
          </p>
          {results.map((r) => (
            <Link key={`${r.type}-${r.id}`} to={href(r)}>
              <Card className="flex flex-col gap-1.5 p-4 transition-shadow hover:shadow-pop">
                <div className="flex items-center gap-2">
                  <Badge tone={typeTone[r.type]}>{r.type}</Badge>
                  <span className="min-w-0 flex-1 truncate text-[14.5px] font-medium">{r.title}</span>
                </div>
                {r.excerpt && <p className="line-clamp-2 text-[13px] leading-relaxed text-muted">{r.excerpt}</p>}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
