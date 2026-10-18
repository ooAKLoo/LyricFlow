import { AudioWaveform, Headphones, Info } from 'lucide-react'
import type { Annotation, LyricLine, WordData } from '../types/lyrics'
import { ANNOTATION_COLORS, ANNOTATION_LABELS } from '../types/lyrics'

export interface SelectedCue {
  annotation: Annotation
  word: WordData
  wordIndex: number
  annotationIndex: number
}

interface PracticeLineProps {
  line: LyricLine
  lineIndex: number
  activeWordIndex: number
  selectedCue: SelectedCue | null
  onSelectCue: (cue: SelectedCue) => void
}

export function PracticeLine({
  line,
  lineIndex,
  activeWordIndex,
  selectedCue,
  onSelectCue,
}: PracticeLineProps) {
  const cueTypes = Array.from(new Set(
    line.words.flatMap((word) => word.annotations.map((annotation) => annotation.type)),
  ))
  const hasAudioCoaching = Boolean(line.performed_text)

  return (
    <article className="practice-line">
      <header className="practice-line-header">
        <div>
          <p className="eyebrow">第 {lineIndex + 1} 句 · {formatRange(line.start, line.end)}</p>
          <h2>先听清，再跟上</h2>
        </div>
        <span className={`evidence-badge ${hasAudioCoaching ? 'is-verified' : ''}`}>
          {hasAudioCoaching ? <Headphones aria-hidden="true" size={14} /> : <Info aria-hidden="true" size={14} />}
          {hasAudioCoaching ? '音频复核' : '规则预判'}
        </span>
      </header>

      <section className="lyric-layer" aria-labelledby="written-lyric-label">
        <span id="written-lyric-label">书面歌词</span>
        <p>{line.text}</p>
      </section>

      <section className="performance-layer" aria-labelledby="performance-label">
        <div className="layer-label-row">
          <span id="performance-label">实际唱法</span>
          {line.beat_hint && <small>{line.beat_hint}</small>}
        </div>
        <p>{line.performed_text || line.text}</p>
      </section>

      <section className="word-map" aria-label="逐词发音标注">
        {line.words.map((word, wordIndex) => {
          const primaryIndex = preferredAnnotationIndex(word)
          const primary = word.annotations[primaryIndex]
          const isSelected = selectedCue?.wordIndex === wordIndex
          const isActive = activeWordIndex === wordIndex
          return (
            <span className="word-map-item" key={`${word.word}-${wordIndex}`}>
              <button
                type="button"
                className={`word-token ${primary ? `cue-${primary.type}` : ''} ${isSelected ? 'is-selected' : ''} ${isActive ? 'is-playing' : ''}`}
                style={primary ? { '--cue-color': ANNOTATION_COLORS[primary.type] } as React.CSSProperties : undefined}
                aria-label={primary ? `${word.word}，${ANNOTATION_LABELS[primary.type].zh}` : word.word}
                disabled={!primary}
                onClick={() => primary && onSelectCue({
                  annotation: primary,
                  word,
                  wordIndex,
                  annotationIndex: primaryIndex,
                })}
              >
                <strong>{word.word}</strong>
                {word.ipa && <small>/{word.ipa}/</small>}
              </button>
              {primary?.type === 'linking' && <span className="link-mark" aria-hidden="true">‿</span>}
              {word.annotations.length > 1 && (
                <span className="extra-cue-count" title={`另有 ${word.annotations.length - 1} 个标注`}>
                  +{word.annotations.length - 1}
                </span>
              )}
            </span>
          )
        })}
      </section>

      <footer className="cue-legend">
        <AudioWaveform aria-hidden="true" size={14} />
        {cueTypes.length ? cueTypes.map((type) => (
          <span key={type}>
            <i style={{ background: ANNOTATION_COLORS[type] }} />
            {ANNOTATION_LABELS[type].zh}
          </span>
        )) : <span>这一句暂时没有高置信度语流标注</span>}
      </footer>
    </article>
  )
}

function preferredAnnotationIndex(word: WordData) {
  const audioIndex = word.annotations.findIndex((annotation) => annotation.evidence === 'audio_model')
  return audioIndex >= 0 ? audioIndex : 0
}

function formatRange(start: number, end: number) {
  return `${formatTime(start)}–${formatTime(end)}`
}

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const rest = Math.floor(seconds % 60)
  return `${minutes}:${rest.toString().padStart(2, '0')}`
}
