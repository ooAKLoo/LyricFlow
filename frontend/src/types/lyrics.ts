export interface PhoneAnnotation {
  phone: string
  start: number
  end: number
}

export interface Annotation {
  type: 'linking' | 'weak_form' | 'elision'
  subtype: string
  symbol: string
  target_word?: string
  explanation_zh: string
  confidence: number
  strong_ipa?: string
  weak_ipa?: string
}

export interface WordData {
  word: string
  start: number
  end: number
  ipa: string
  phones: PhoneAnnotation[]
  annotations: Annotation[]
}

export interface LyricLine {
  text: string
  translation: string
  start: number
  end: number
  words: WordData[]
  is_rap: boolean
}

export interface SongStats {
  total_words: number
  total_linking: number
  total_weak_forms: number
  total_elision: number
  total_annotations: number
}

export interface SongResult {
  song_id: string
  song_title: string
  artist: string
  dialect: string
  duration: number
  lines: LyricLine[]
  audio_url: string
  vocals_url: string
  stats: SongStats
}

export interface TaskStatus {
  task_id: string
  status:
    | 'pending'
    | 'preprocessing'
    | 'lyrics_fetching'
    | 'aligning'
    | 'phonetics'
    | 'detecting'
    | 'completed'
    | 'error'
  progress: number
  current_stage: string
  error_message?: string
  song_id?: string
}

export type AnnotationType = 'linking' | 'weak_form' | 'elision'

export const ANNOTATION_COLORS: Record<AnnotationType, string> = {
  linking: '#2563EB',
  weak_form: '#888888',
  elision: '#D32F2F',
}

export const ANNOTATION_LABELS: Record<AnnotationType, { zh: string; en: string }> = {
  linking: { zh: '连读', en: 'Linking' },
  weak_form: { zh: '弱读', en: 'Weak Form' },
  elision: { zh: '吞音', en: 'Elision' },
}
