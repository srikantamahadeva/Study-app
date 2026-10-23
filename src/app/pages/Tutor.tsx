import { BookOpen, Info, MessageSquare, Send, TriangleAlert } from 'lucide-react'
import { useState } from 'react'

import { Markdown } from '../components/Markdown'
import { Badge, Button, Card, PageHeader, Spinner } from '../components/ui'
import { useTutorAsk, useTutorStatus } from '../lib/api'
import { cx } from '../lib/cx'
import type { TutorReply } from '../../shared/types'

interface ChatTurn {
  question: string
  reply?: TutorReply
}

/** AI tutor. Answers are grounded in your uploaded material and lessons, with citations. */
export function Tutor() {
  const { data: status, isLoading } = useTutorStatus()
  const ask = useTutorAsk()
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [input, setInput] = useState('')

  if (isLoading) return <Spinner />

  // Not configured: explain clearly and never fake an answer.
  if (status && !status.configured) {
    return (
      <div className="mx-auto flex max-w-[640px] flex-col gap-5">
        <PageHeader title="AI tutor" subtitle="Ask questions about your lessons and uploads." />
        <Card className="flex flex-col items-start gap-3 border-l-2 border-warning/50 p-6">
          <div className="grid size-11 place-items-center rounded-tile bg-warning-soft text-warning">
            <TriangleAlert className="size-5" />
          </div>
          <h2 className="text-[16px] font-semibold">The tutor is not configured</h2>
          <p className="text-[14px] leading-relaxed text-muted">
            No AI provider key is set, so the tutor cannot answer yet. Add an OpenAI-compatible API key to the server environment, then reload.
            Until then, everything else — lessons, quizzes, flashcards, labs and reports — works as normal.
          </p>
          <Badge tone="warning">No key configured</Badge>
        </Card>
      </div>
    )
  }

  function send() {
    const question = input.trim()
    if (!question || ask.isPending) return
    setInput('')
    const placeholder: ChatTurn = { question }
    setTurns((t) => [...t, placeholder])
    ask.mutate(
      { question },
      {
        onSuccess: (res) => {
          setTurns((t) => [...t.slice(0, -1), { question, reply: res.reply }])
        },
        onError: () => {
          // Drop the optimistic turn on failure so we never show a fake reply.
          setTurns((t) => t.slice(0, -1))
          setInput(question)
        },
      },
    )
  }

  return (
    <div className="mx-auto flex max-w-[680px] flex-col gap-5">
      <PageHeader title="AI tutor" subtitle={status?.model ? `Grounded in your material · ${status.model}` : 'Grounded in your material'} />

      {turns.length === 0 ? (
        <Card className="flex flex-col items-center gap-3 p-10 text-center">
          <div className="grid size-14 place-items-center rounded-card bg-accent-soft text-accent">
            <MessageSquare className="size-7" />
          </div>
          <p className="text-[15px] text-muted">Ask anything about your lessons and uploaded documents.</p>
          <p className="flex items-center gap-1.5 text-[13px] text-faint">
            <Info className="size-3.5" />
            Answers cite their source and flag anything not covered by your material.
          </p>
        </Card>
      ) : (
        <div className="flex flex-col gap-4">
          {turns.map((turn, i) => (
            <div key={i} className="flex flex-col gap-3">
              <div className="self-end rounded-2xl rounded-br-[6px] bg-accent px-4 py-2.5 text-[14px] leading-relaxed text-white">{turn.question}</div>
              {turn.reply ? (
                <Card className="p-5">
                  <Markdown source={turn.reply.content} className="text-[14px] leading-relaxed" />
                  {turn.reply.includesExternalKnowledge && (
                    <p className="mt-3 flex items-center gap-1.5 border-t border-line pt-3 text-[12.5px] text-warning">
                      <TriangleAlert className="size-3.5" />
                      Includes external knowledge, not from your material.
                    </p>
                  )}
                  {turn.reply.citations.length > 0 && (
                    <div className="mt-3 border-t border-line pt-3">
                      <p className="flex items-center gap-1.5 text-[12px] font-semibold uppercase tracking-wide text-muted">
                        <BookOpen className="size-3.5" />
                        Sources
                      </p>
                      <ul className="mt-2 flex flex-col gap-1.5">
                        {turn.reply.citations.map((c, ci) => (
                          <li key={ci} className="rounded-tile bg-surface-2 p-2.5">
                            <p className="text-[13px] font-medium">{c.lesson}</p>
                            {c.locator && <p className="text-[12px] text-muted">{c.locator}</p>}
                            <p className="mt-1 line-clamp-2 text-[12.5px] leading-relaxed text-faint">{c.excerpt}</p>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Card>
              ) : (
                <div className="flex items-center gap-2 self-start rounded-2xl rounded-bl-[6px] bg-surface-2 px-4 py-3 text-[13.5px] text-muted">
                  <Spinner className="size-4" />
                  Thinking…
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className={cx('sticky bottom-4 flex items-end gap-2')}>
        <Card className="flex flex-1 items-end gap-2 p-2.5">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send()
              }
            }}
            rows={1}
            placeholder="Ask a question…"
            className="max-h-40 min-h-[40px] flex-1 resize-none bg-transparent px-1 py-1.5 text-[14px] leading-relaxed outline-none placeholder:text-faint"
          />
          <Button variant="primary" size="icon" aria-label="Send" loading={ask.isPending} disabled={!input.trim()} onClick={send}>
            <Send className="size-4" />
          </Button>
        </Card>
      </div>
    </div>
  )
}
