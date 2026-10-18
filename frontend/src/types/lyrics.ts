export interface PhoneAnnotation {
  phone: string
  start: number
  end: number
}

export interface Annotation {
  type: AnnotationType
  subtype: string
  symbol: string
  target_word?: string
  explanation_zh: string
  confidence: number
  strong_ipa?: string
  weak_ipa?: string
  source?: string
  heard_as?: string
  mouth_tip_zh?: string
  rhythm_tip_zh?: string
  end_word_index?: number
  evidence?: 'audio_model' | 'timing' | 'rule' | string
}

export interface WordData {
  word: string
  start: number
  end: number
  ipa: string
  phones: PhoneAnnotation[]
  annotations: Annotation[]
  asr_word?: string
  asr_confidence?: number | null
  timing_source?: 'asr_match' | 'interpolated' | 'existing' | 'unknown' | string
}

export interface LyricLine {
  text: string
  translation: string
  start: number
  end: number
  words: WordData[]
  is_rap: boolean
  performed_text?: string
  coach_summary_zh?: string
  difficulty?: number
  beat_hint?: string
  analysis_source?: string
}

export interface SongStats {
  total_words: number
  total_linking: number
  total_weak_forms: number
  total_elision: number
  total_stress?: number
  total_other?: number
  total_annotations: number
}

export interface AnalysisMeta {
  alignment_source: string
  alignment_quality: number
  coaching_provider: string
  cloud_enabled: boolean
  warnings: string[]
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
  vocals_path?: string
  original_path?: string
  stats: SongStats
  analysis?: AnalysisMeta
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

export type AnnotationType =
  | 'linking'
  | 'weak_form'
  | 'elision'
  | 'flap'
  | 'assimilation'
  | 'stress'
  | 'breath'

export const ANNOTATION_COLORS: Record<AnnotationType, string> = {
  linking: '#2563EB',
  weak_form: '#888888',
  elision: '#D32F2F',
  flap: '#8B5CF6',
  assimilation: '#0F766E',
  stress: '#C2410C',
  breath: '#64748B',
}

export const ANNOTATION_LABELS: Record<AnnotationType, { zh: string; en: string }> = {
  linking: { zh: '连读', en: 'Linking' },
  weak_form: { zh: '弱读', en: 'Weak Form' },
  elision: { zh: '吞音', en: 'Elision' },
  flap: { zh: '闪音', en: 'Flap' },
  assimilation: { zh: '同化', en: 'Assimilation' },
  stress: { zh: '重音', en: 'Stress' },
  breath: { zh: '换气', en: 'Breath' },
}
