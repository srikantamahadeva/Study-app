import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router'

import { Shell } from './components/Shell'
import { Spinner, ToastProvider } from './components/ui'
import { ApiError, useMe } from './lib/api'
import { Deck } from './pages/Deck'
import { Flashcards } from './pages/Flashcards'
import { Learn } from './pages/Learn'
import { Library } from './pages/Library'
import { Match } from './pages/Match'
import { Settings } from './pages/Settings'
import { SetupNeeded, SignIn } from './pages/SignIn'
import { StatsPage } from './pages/Stats'

const client = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 15_000 } } })

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
        <Route index element={<Library />} />
        <Route path="decks/:id" element={<Deck />} />
        <Route path="stats" element={<StatsPage />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="decks/:id/flashcards" element={<Flashcards />} />
      <Route path="decks/:id/learn" element={<Learn />} />
      <Route path="decks/:id/match" element={<Match />} />
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
