// Types shared between the FastAPI backend contract and the SPA.
// Field names mirror the JSON the server emits (camelCase where the API
// serializes it that way).

export const BRAND = 'Algo Study'

// ---------------------------------------------------------------- auth

export interface Me {
  id: string
  email: string
  displayName: string
  timezone: string
}

// ---------------------------------------------------------------- curriculum

export type LessonContentStatus = 'sample' | 'published'

export interface LessonSummary {
  id: string
  title: string
  position: number
  minutes: number
  contentStatus: LessonContentStatus
  status: 'not_started' | 'in_progress' | 'completed'
  percent: number
}

export interface ModuleNode {
  id: string
  number: number
  title: string
  summary: string
  lessons: LessonSummary[]
}

export interface CourseNode {
  id: string
  title: string
  slug: string
  description: string
  modules: ModuleNode[]
}

export interface CurriculumTree {
  courses: CourseNode[]
  progress: { lessonsTotal: number; lessonsCompleted: number; percent: number }
}

export interface Bookmark {
  id: string
  label: string
  note: string
  createdAt: number
}

export interface LessonDetail {
  lesson: {
    id: string
    title: string
    summary: string
    bodyMarkdown: string
    minutes: number
    contentStatus: LessonContentStatus
    moduleId: string
    moduleTitle: string
  }
  navigation: { prev: LessonSummary | null; next: LessonSummary | null }
  bookmarks: Bookmark[]
}

export interface ResumeLesson {
  lesson: LessonSummary
  courseTitle: string
  moduleTitle: string
}

// ---------------------------------------------------------------- quiz

export type QuestionKind = 'mcq' | 'truefalse' | 'shortanswer' | 'code_reading' | 'debugging' | 'scenario' | 'audit'

export interface Question {
  id: string
  kind: QuestionKind
  prompt: string
  options: string[]
  topics: string[]
  sourceRef: string | null
  lessonId: string | null
  origin: string
}

export interface QuizSession {
  sessionId: string
  questions: Question[]
}

export interface AnswerResult {
  correct: boolean
  explanation: string
  sourceRef: string | null
  acceptedAnswers: string[]
  topicMastery: { topic: string; mastery: number; attempts: number }[]
  reviewCardCreated: boolean
}

export interface MasteryRow {
  topic: string
  mastery: number
  attempts: number
  correct: number
}

export interface Deck {
  id: string
  title: string
  lessonId: string | null
  cardCount: number
  dueCount: number
}

export interface Card {
  id: string
  front: string
  back: string
  dueAt: number | null
  state: string
  repetitions: number
  ease: number | null
}

export interface DueCard {
  cardId: string
  front: string
  back: string
  deckTitle: string
  state: string
}

export type ReviewGrade = 'again' | 'difficult' | 'good' | 'easy'

export interface ReviewResult {
  cardId: string
  nextDueAt: number
  intervalDays: number
  state: string
  ease: number
}

export interface ReviewStats {
  totalCards: number
  dueNow: number
  learned: number
  mature: number
  reviewsLast7Days: number
  last7Days: { day: string; count: number }[]
}

// ---------------------------------------------------------------- notes

export type NoteKind = 'lesson' | 'research' | 'concept' | 'snippet' | 'spec' | 'mistake' | 'bookmark'

export interface Note {
  id: string
  kind: NoteKind
  title: string
  bodyMarkdown: string
  lessonId: string | null
  tags: string[]
  aiDraft: boolean
  isPinned: boolean
  createdAt: number
  updatedAt: number
}

export interface Concept {
  id: string
  term: string
  definition: string
  lessonId: string | null
  tags: string[]
}

// ---------------------------------------------------------------- labs

export interface Exercise {
  id: string
  language: 'pine' | 'python'
  title: string
  requirement: string
  lessonId: string | null
  position: number
}

export interface ExerciseDetail {
  id: string
  language: 'pine' | 'python'
  title: string
  requirement: string
  starterCode: string
  explanation: string
  checks: { kind: string; pattern: string; message: string; level: 'error' | 'warn' | 'info' }[]
  expectedBehavior: string
}

export interface StaticCheck {
  message: string
  level: 'error' | 'warn' | 'info'
  passed: boolean
}

export interface SubmitResult {
  passed: boolean
  result: {
    staticChecks: StaticCheck[]
    staticPassed: boolean
    clientTests: { passed: boolean }[]
    clientPassed: boolean | null
    note: string
  }
  submissionId: string
}

export interface Submission {
  id: string
  exerciseId: string
  passed: boolean
  createdAt: number
}

// ---------------------------------------------------------------- projects

export type ProjectStatus = 'not_started' | 'in_progress' | 'done'

export interface ProjectSummary {
  id: string
  key: string
  title: string
  objectives: string[]
  prerequisites: string[]
  status: ProjectStatus
  origin: string
  milestoneCount: number | null
  milestonesDone: number
  updatedAt: number
}

export interface Milestone {
  id: string
  title: string
  detail: string
  position: number
  done: boolean
  doneAt: number | null
}

export interface ProjectDetail {
  project: ProjectSummary & {
    steps: string[]
    requiredFiles: string[]
    exampleInputs: string[]
    expectedOutputs: string[]
    acceptanceTests: string[]
    failureScenarios: string[]
    securityChecks: string[]
    completionCriteria: string
    finalAssessment: string
  }
  milestones: Milestone[]
}

// ---------------------------------------------------------------- tutor

export interface TutorStatus {
  configured: boolean
  model: string | null
}

export interface TutorSessionSummary {
  id: string
  title: string
  lessonId: string | null
  updatedAt: number
}

export interface TutorMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations: { lesson: string; locator: string; excerpt: string }[]
  includesExternalKnowledge: boolean
  createdAt: number
}

export interface TutorSessionDetail {
  session: { id: string; title: string; lessonId: string | null }
  messages: TutorMessage[]
}

export interface TutorReply {
  id: string
  role: 'assistant'
  content: string
  citations: { lesson: string; locator: string; excerpt: string }[]
  includesExternalKnowledge: boolean
  createdAt: number
}

// ---------------------------------------------------------------- resources

export type ResourceKind = 'pdf' | 'image' | 'code' | 'note' | 'other'

export interface Resource {
  id: string
  kind: ResourceKind
  title: string
  url: string | null
  fileId: string | null
  mimeType: string | null
  tags: string[]
  lessonId: string | null
  contentPreview: string
  hasFile: boolean
  createdAt: number
}

// ---------------------------------------------------------------- search

export interface SearchResult {
  type: 'lesson' | 'note' | 'concept' | 'flashcard' | 'quiz' | 'project' | 'document'
  id: string
  title: string
  excerpt: string
  score: number
  href: string
}

// ---------------------------------------------------------------- reports

export interface Overview {
  progress: { lessonsTotal: number; lessonsCompleted: number; percent: number }
  streak: { current: number; longest: number }
  study: {
    sessions: number
    sessionsThisWeek: number
    minutesThisWeek: number
    byDay: { day: string; seconds: number }[]
  }
  quiz: { attempts: number; accuracy: number | null; accuracy7d: number | null }
  revisions: { dueNow: number; totalCards: number; reviewsLast7Days: number }
  weakestTopics: { topic: string; mastery: number; attempts: number }[]
  nextLesson: { id: string; title: string; percent: number } | null
}

export interface WeeklyWeek {
  weekStart: string
  sessions: number
  minutes: number
  quizAttempts: number
  quizAccuracy: number | null
  reviews: number
}

export interface Recommendations {
  dueReviews: number
  weakTopics: { topic: string; mastery: number; attempts: number }[]
  inProgressLessons: { lessonId: string; percent: number; updatedAt: number }[]
}
