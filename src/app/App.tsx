import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router'

import { Shell } from './components/Shell'
import { Spinner, ToastProvider } from './components/ui'
import { ApiError, useMe } from './lib/api'
import { Curriculum } from './pages/Curriculum'
import { Deck, Flashcards } from './pages/Flashcards'
import { Exercise, Labs } from './pages/Labs'
import { Lesson } from './pages/Lesson'
import { Notes } from './pages/Notes'
import { Project, Projects } from './pages/Projects'
import { Quiz, Review } from './pages/Quiz'
import { Reports } from './pages/Reports'
import { Resources } from './pages/Resources'
import { Search } from './pages/Search'
import { SetupNeeded, SignIn } from './pages/SignIn'
import { Tutor } from './pages/Tutor'

const client = new QueryClient({
  defaultOptions: { queries: { retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2, refetchOnWindowFocus: false, staleTime: 15_000 } },
})

function Gate() {
  const me = useMe()
  if (me.isLoading) {
    return (
      <div className="grid min-h-screen place-items-center">
        <Spinner />
      </div>
    )
  }
  if (me.error instanceof ApiError && me.error.status === 401) return <SignIn />
  if (me.error) return <SetupNeeded message={me.error.message} />

  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Curriculum />} />
        <Route path="lessons/:id" element={<Lesson />} />
        <Route path="notes" element={<Notes />} />
        <Route path="flashcards" element={<Flashcards />} />
        <Route path="decks/:id" element={<Deck />} />
        <Route path="quiz" element={<Quiz />} />
        <Route path="review" element={<Review />} />
        <Route path="labs" element={<Labs />} />
        <Route path="labs/:id" element={<Exercise />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id" element={<Project />} />
        <Route path="resources" element={<Resources />} />
        <Route path="reports" element={<Reports />} />
        <Route path="tutor" element={<Tutor />} />
        <Route path="search" element={<Search />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export function App() {
  return (
    <QueryClientProvider client={client}>
      <ToastProvider>
        <BrowserRouter>
          <Gate />
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  )
}
