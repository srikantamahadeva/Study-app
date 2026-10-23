// API client for the FastAPI backend.
//
// The browser talks to the FastAPI server on the same origin (Vite proxies
// /api in development; in production FastAPI serves the SPA itself). Session
// auth rides on an HttpOnly cookie, so every request sends credentials. CSRF
// is enforced server-side for mutations via the Origin header, which the
// browser sets automatically on same-origin fetches.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type {
  AnswerResult,
  Card,
  Concept,
  CurriculumTree,
  Deck,
  DueCard,
  Exercise,
  ExerciseDetail,
  LessonDetail,
  MasteryRow,
  Me,
  Note,
  NoteKind,
  ProjectDetail,
  ProjectSummary,
  Question,
  QuizSession,
  Recommendations,
  Resource,
  ResourceKind,
  ReviewGrade,
  ReviewResult,
  ReviewStats,
  SearchResult,
  Submission,
  SubmitResult,
  TutorReply,
  TutorSessionDetail,
  TutorSessionSummary,
  TutorStatus,
  WeeklyWeek,
} from '../../shared/types'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit & { json?: unknown; form?: FormData }): Promise<T> {
  const { json, form, ...rest } = init ?? {}
  const headers: Record<string, string> = { accept: 'application/json' }
  let body: BodyInit | undefined
  if (json !== undefined) {
    headers['content-type'] = 'application/json'
    body = JSON.stringify(json)
  } else if (form !== undefined) {
    body = form // let the browser set the multipart boundary
  }
  const response = await fetch(`/api${path}`, { credentials: 'same-origin', ...rest, headers, body })
  if (!response.ok) {
    let message = response.statusText
    try {
      const payload = (await response.json()) as { detail?: string; error?: string }
      message = payload.detail ?? payload.error ?? message
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, message)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

// ---------------------------------------------------------------- auth

// The auth endpoints serialize snake_case (`display_name`); everything else
// in the API is camelCase. Translate here so the app only ever sees Me.
interface AuthUserRaw {
  id: string
  email: string
  display_name: string
  timezone: string
}

const toMe = (raw: AuthUserRaw): Me => ({ id: raw.id, email: raw.email, displayName: raw.display_name, timezone: raw.timezone })

export const useMe = () => useQuery({ queryKey: ['me'], queryFn: () => request<AuthUserRaw>('/auth/me').then(toMe), retry: false, staleTime: 60_000 })

export function useLogin() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { email: string; password: string }) => request<AuthUserRaw>('/auth/login', { method: 'POST', json: input }).then(toMe),
    onSuccess: () => client.invalidateQueries(),
  })
}

export function useRegister() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { email: string; password: string; displayName: string }) =>
      request<AuthUserRaw>('/auth/register', {
        method: 'POST',
        json: { email: input.email, password: input.password, display_name: input.displayName },
      }).then(toMe),
    onSuccess: () => client.invalidateQueries(),
  })
}

export function useLogout() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: () => request<void>('/auth/logout', { method: 'POST' }),
    onSuccess: () => client.clear(),
  })
}

// ---------------------------------------------------------------- curriculum

export const useCurriculum = () =>
  useQuery({ queryKey: ['curriculum'], queryFn: () => request<CurriculumTree>('/curriculum/') })

export const useLesson = (id: string | undefined) =>
  useQuery({ queryKey: ['lesson', id], queryFn: () => request<LessonDetail>(`/curriculum/lessons/${id}`), enabled: Boolean(id) })

export const useResume = () => useQuery({ queryKey: ['resume'], queryFn: () => request<{ lesson: LessonDetail['lesson'] }>('/curriculum/resume') })

export function useSetLessonProgress() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ lessonId, percent, status }: { lessonId: string; percent: number; status: string }) =>
      request<{ status: string }>(`/curriculum/lessons/${lessonId}/progress`, { method: 'PUT', json: { percent, status } }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['curriculum'] })
      void client.invalidateQueries({ queryKey: ['resume'] })
      void client.invalidateQueries({ queryKey: ['reports'] })
    },
  })
}

export function useAddBookmark() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ lessonId, label, note }: { lessonId: string; label: string; note: string }) =>
      request<{ id: string }>(`/curriculum/lessons/${lessonId}/bookmarks`, { method: 'POST', json: { label, note } }),
    onSuccess: (_r, input) => client.invalidateQueries({ queryKey: ['lesson', input.lessonId] }),
  })
}

export function useDeleteBookmark() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { bookmarkId: string; lessonId: string }) =>
      request<{ ok: boolean }>(`/curriculum/bookmarks/${input.bookmarkId}`, { method: 'DELETE' }),
    onSuccess: (_r, input) => client.invalidateQueries({ queryKey: ['lesson', input.lessonId] }),
  })
}

// ---------------------------------------------------------------- quiz

export const useQuestions = () => useQuery({ queryKey: ['questions'], queryFn: () => request<{ items: Question[] }>('/quiz/questions') })

export function useStartQuiz() {
  return useMutation({
    mutationFn: (input: { lessonId?: string; limit: number }) => request<QuizSession>('/quiz/start', { method: 'POST', json: input }),
  })
}

export function useAnswerQuestion() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { sessionId: string; questionId: string; givenIndex?: number; givenAnswer?: string }) =>
      request<AnswerResult>('/quiz/answer', { method: 'POST', json: input }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['mastery'] })
      void client.invalidateQueries({ queryKey: ['due'] })
      void client.invalidateQueries({ queryKey: ['reports'] })
    },
  })
}

export const useMastery = () => useQuery({ queryKey: ['mastery'], queryFn: () => request<{ items: MasteryRow[]; weakest: MasteryRow[] }>('/quiz/mastery') })

export const useDueCards = () => useQuery({ queryKey: ['due'], queryFn: () => request<{ items: DueCard[]; dueCount: number }>('/quiz/due') })

export const useReviewStats = () => useQuery({ queryKey: ['reviewStats'], queryFn: () => request<ReviewStats>('/quiz/review/stats') })

export function useReviewCard() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ cardId, grade }: { cardId: string; grade: ReviewGrade }) => request<ReviewResult>('/quiz/review', { method: 'POST', json: { cardId, grade } }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['due'] })
      void client.invalidateQueries({ queryKey: ['reviewStats'] })
      void client.invalidateQueries({ queryKey: ['reports'] })
    },
  })
}

export const useDecks = () => useQuery({ queryKey: ['decks'], queryFn: () => request<{ items: Deck[] }>('/quiz/decks') })

export const useDeck = (id: string | undefined) =>
  useQuery({
    queryKey: ['deck', id],
    queryFn: () => request<{ deck: { id: string; title: string }; cards: Card[]; dueNow: number }>(`/quiz/decks/${id}`),
    enabled: Boolean(id),
  })

export function useCreateDeck() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (title: string) => request<{ id: string; title: string }>('/quiz/decks', { method: 'POST', json: { title } }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['decks'] }),
  })
}

export function useAddCard(deckId: string) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { front: string; back: string }) => request<{ id: string }>(`/quiz/decks/${deckId}/cards`, { method: 'POST', json: input }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['deck', deckId] })
      void client.invalidateQueries({ queryKey: ['decks'] })
    },
  })
}

// ---------------------------------------------------------------- notes

export const useNotes = (kind?: NoteKind) =>
  useQuery({ queryKey: ['notes', kind ?? 'all'], queryFn: () => request<{ items: Note[] }>(`/notes${kind ? `?kind=${kind}` : ''}`) })

export function useCreateNote() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { title: string; bodyMarkdown: string; kind: NoteKind; tags?: string[] }) =>
      request<Note>('/notes', { method: 'POST', json: input }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['notes'] }),
  })
}

export function useUpdateNote() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { id: string; title?: string; bodyMarkdown?: string; tags?: string[]; isPinned?: boolean; confirmOverwrite?: boolean }) => {
      const { id, ...body } = input
      return request<Note>(`/notes/${id}`, { method: 'PATCH', json: body })
    },
    onSuccess: () => client.invalidateQueries({ queryKey: ['notes'] }),
  })
}

export function useDeleteNote() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => request<{ ok: boolean }>(`/notes/${id}`, { method: 'DELETE' }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['notes'] }),
  })
}

export const useConcepts = () => useQuery({ queryKey: ['concepts'], queryFn: () => request<{ items: Concept[] }>('/notes/concepts') })

export function useCreateConcept() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { term: string; definition: string; tags?: string[] }) => request<Concept>('/notes/concepts', { method: 'POST', json: input }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['concepts'] }),
  })
}

export function useDeleteConcept() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => request<{ ok: boolean }>(`/notes/concepts/${id}`, { method: 'DELETE' }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['concepts'] }),
  })
}

// ---------------------------------------------------------------- labs

export const useExercises = (language?: string) =>
  useQuery({
    queryKey: ['exercises', language ?? 'all'],
    queryFn: () => request<{ items: Exercise[] }>(`/labs/exercises${language ? `?language=${language}` : ''}`),
  })

export const useExercise = (id: string | undefined) =>
  useQuery({ queryKey: ['exercise', id], queryFn: () => request<ExerciseDetail>(`/labs/exercises/${id}`), enabled: Boolean(id) })

export const useExerciseSolution = (id: string | undefined) =>
  useQuery({ queryKey: ['solution', id], queryFn: () => request<{ solution: string; explanation: string }>(`/labs/exercises/${id}/solution`), enabled: Boolean(id) })

export function useSubmitExercise() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { exerciseId: string; code: string; testResults?: { passed: boolean }[] }) =>
      request<SubmitResult>('/labs/submit', { method: 'POST', json: { ...input, testResults: input.testResults ?? [] } }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['submissions'] }),
  })
}

export const useSubmissions = () => useQuery({ queryKey: ['submissions'], queryFn: () => request<{ items: Submission[] }>('/labs/submissions') })

// ---------------------------------------------------------------- projects

export const useProjects = () => useQuery({ queryKey: ['projects'], queryFn: () => request<{ items: ProjectSummary[] }>('/projects') })

export const useProject = (id: string | undefined) =>
  useQuery({ queryKey: ['project', id], queryFn: () => request<ProjectDetail>(`/projects/${id}`), enabled: Boolean(id) })

export function useSetProjectStatus() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => request<{ ok: boolean }>(`/projects/${id}/status`, { method: 'PATCH', json: { status } }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useToggleMilestone() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ milestoneId, done }: { milestoneId: string; done: boolean }) =>
      request<{ ok: boolean; done: boolean }>(`/projects/milestones/${milestoneId}?done=${done}`, { method: 'PATCH' }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['projects'] })
      void client.invalidateQueries({ queryKey: ['project'] })
    },
  })
}

// ---------------------------------------------------------------- tutor

export const useTutorStatus = () => useQuery({ queryKey: ['tutorStatus'], queryFn: () => request<TutorStatus>('/tutor/status'), staleTime: 300_000 })

export const useTutorSessions = () => useQuery({ queryKey: ['tutorSessions'], queryFn: () => request<{ items: TutorSessionSummary[] }>('/tutor/sessions') })

export const useTutorSession = (id: string | undefined) =>
  useQuery({ queryKey: ['tutorSession', id], queryFn: () => request<TutorSessionDetail>(`/tutor/sessions/${id}`), enabled: Boolean(id) })

export function useTutorAsk() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (input: { question: string; sessionId?: string; lessonId?: string }) => request<{ sessionId: string; reply: TutorReply }>('/tutor/ask', { method: 'POST', json: input }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['tutorSessions'] }),
  })
}

export function useTutorChat() {
  return useMutation({
    mutationFn: (input: { sessionId: string; message: string }) => request<{ reply: TutorReply }>('/tutor/chat', { method: 'POST', json: input }),
  })
}

export function useDeleteTutorSession() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => request<{ ok: boolean }>(`/tutor/sessions/${id}`, { method: 'DELETE' }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['tutorSessions'] }),
  })
}

// ---------------------------------------------------------------- resources

export const useResources = (kind?: ResourceKind) =>
  useQuery({ queryKey: ['resources', kind ?? 'all'], queryFn: () => request<{ items: Resource[] }>(`/resources${kind ? `?kind=${kind}` : ''}`) })

export function useUploadResource() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData()
      form.set('file', file)
      form.set('title', file.name)
      return request<{ id: string; fileId: string; title: string; kind: string; indexed: boolean; chunks: number }>('/resources/upload', {
        method: 'POST',
        form,
      })
    },
    onSuccess: () => client.invalidateQueries({ queryKey: ['resources'] }),
  })
}

export function useDeleteResource() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => request<{ ok: boolean }>(`/resources/${id}`, { method: 'DELETE' }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['resources'] }),
  })
}

// ---------------------------------------------------------------- search

export const useSearch = (q: string) =>
  useQuery({
    queryKey: ['search', q],
    queryFn: () => request<{ items: SearchResult[]; total: number }>(`/search?q=${encodeURIComponent(q)}`),
    enabled: q.trim().length > 0,
  })

// ---------------------------------------------------------------- reports

export const useOverview = () => useQuery({ queryKey: ['reports', 'overview'], queryFn: () => request<import('../../shared/types').Overview>('/reports/overview') })

export const useWeekly = (weeks = 4) =>
  useQuery({ queryKey: ['reports', 'weekly', weeks], queryFn: () => request<{ weeks: WeeklyWeek[] }>(`/reports/weekly?weeks=${weeks}`) })

export const useRecommendations = () =>
  useQuery({ queryKey: ['reports', 'recommendations'], queryFn: () => request<Recommendations>('/reports/recommendations') })

export const useExportMarkdown = () =>
  useQuery({ queryKey: ['reports', 'export'], queryFn: () => request<{ markdown: string }>('/reports/export.md') })
