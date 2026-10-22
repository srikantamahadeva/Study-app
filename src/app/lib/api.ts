import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { Card, Deck, Me, Session, SessionResult, Stats, StudyMode } from '../../shared/types'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
  ) {
    super(message)
  }
}

export async function api<T>(path: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  const { json, ...rest } = init ?? {}
  const response = await fetch(`/api${path}`, {
    credentials: 'same-origin',
    ...rest,
    headers: { accept: 'application/json', ...(json !== undefined ? { 'content-type': 'application/json' } : {}), ...(rest.headers ?? {}) },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  })
  if (!response.ok) {
    let message = response.statusText
    let code: string | undefined
    try {
      const body = (await response.json()) as { error?: string; message?: string }
      message = body.message ?? body.error ?? message
      code = body.error
    } catch {
      /* no body */
    }
    throw new ApiError(response.status, message, code)
  }
  return (await response.json()) as T
}

export const useMe = () => useQuery({ queryKey: ['me'], queryFn: () => api<Me>('/me'), retry: false, staleTime: 60_000 })
export const useDecks = () => useQuery({ queryKey: ['decks'], queryFn: () => api<{ items: Deck[] }>('/decks') })
export const useDeck = (id: string | undefined) =>
  useQuery({
    queryKey: ['deck', id],
    queryFn: () => api<{ deck: Deck; cards: Card[]; sessions: Session[] }>(`/decks/${id}`),
    enabled: Boolean(id),
  })
export const useStats = () => useQuery({ queryKey: ['stats'], queryFn: () => api<Stats>('/stats') })

export function useInvalidate() {
  const client = useQueryClient()
  return (...keys: string[]) => Promise.all(keys.map((key) => client.invalidateQueries({ queryKey: [key] })))
}

export function useApiMutation<TInput, TResult>(run: (input: TInput) => Promise<TResult>, invalidates: string[], options?: { onSuccess?: (result: TResult, input: TInput) => void }) {
  const invalidate = useInvalidate()
  return useMutation({
    mutationFn: run,
    onSuccess: async (result, input) => {
      await invalidate(...invalidates)
      options?.onSuccess?.(result, input)
    },
  })
}

export function recordSession(deckId: string, mode: StudyMode, results: SessionResult[], durationMs: number) {
  return api<{ session: { id: string; score: number; total: number; accuracy: number } }>(`/decks/${deckId}/sessions`, {
    method: 'POST',
    json: { mode, results, durationMs },
  })
}

export async function uploadCardImage(deckId: string, cardId: string, file: File) {
  const form = new FormData()
  form.set('file', file)
  await api(`/decks/${deckId}/cards/${cardId}/image`, { method: 'PUT', body: form })
}
