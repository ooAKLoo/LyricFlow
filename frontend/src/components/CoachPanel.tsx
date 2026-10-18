import { Activity, AudioLines, CircleGauge, MousePointer2 } from 'lucide-react'
import type { LyricLine } from '../types/lyrics'
import { ANNOTATION_COLORS, ANNOTATION_LABELS } from '../types/lyrics'
import type { SelectedCue } from './PracticeLine'

interface CoachPanelProps {
  line: LyricLine
  selectedCue: SelectedCue | null
  warnings?: string[]
}

export function CoachPanel({ line, selectedCue, warnings = [] }: CoachPanelProps) {
  if (!selectedCue) {
    return (
      <aside className="coach-panel">
        <div className="coach-heading">
          <p className="eyebrow">教练提示</p>
          <h2>这一句怎么唱</h2>
        </div>
        <div className="coach-summary">
          <AudioLines aria-hidden="true" size={18} />
          <p>{line.coach_summary_zh || '点击中间带颜色标记的词，查看口型、气流和节拍提示。'}</p>
        </div>
        {line.beat_hint && (
          <section className="coach-section">
            <span>节拍轮廓</span>
            <p>{line.beat_hint}</p>
          </section>
        )}
        <div className="coach-empty-action">
          <MousePointer2 aria-hidden="true" size={16} />
          选择一个标注开始拆解
        </div>
        {warnings.length > 0 && <WarningList warnings={warnings} />}
      </aside>
    )
  }

  const { annotation, word } = selectedCue
  const meta = ANNOTATION_LABELS[annotation.type]
  const color = ANNOTATION_COLORS[annotation.type]
  const evidenceLabel = annotation.evidence === 'audio_model' ? '原声音频复核' : '语言规则预判'

  return (
    <aside className="coach-panel">
      <div className="coach-heading">
        <p className="eyebrow">当前标注</p>
        <div className="cue-title-row">
          <span className="cue-color" style={{ background: color }} />
          <h2>{meta.zh}</h2>
          <small>{meta.en}</small>
        </div>
      </div>

      <div className="heard-comparison">
        <span>歌词写的是</span>
        <strong>{annotation.source || word.word}</strong>
        <span>实际更接近</span>
        <strong style={{ color }}>{annotation.heard_as || annotation.weak_ipa || word.ipa}</strong>
      </div>

      <section className="coach-section">
        <span>为什么会这样</span>
        <p>{annotation.explanation_zh}</p>
      </section>

      {annotation.mouth_tip_zh && (
        <section className="coach-section coach-tip">
          <Activity aria-hidden="true" size={16} />
          <div>
            <span>嘴怎么动</span>
            <p>{annotation.mouth_tip_zh}</p>
          </div>
        </section>
      )}

      {annotation.rhythm_tip_zh && (
        <section className="coach-section coach-tip">
          <AudioLines aria-hidden="true" size={16} />
          <div>
            <span>怎么落拍</span>
            <p>{annotation.rhythm_tip_zh}</p>
          </div>
        </section>
      )}

      <div className="evidence-row">
        <span><CircleGauge aria-hidden="true" size={14} />可信度</span>
        <strong>{Math.round(annotation.confidence * 100)}%</strong>
      </div>
      <div className="evidence-source">{evidenceLabel}</div>
      {warnings.length > 0 && <WarningList warnings={warnings} />}
    </aside>
  )
}

function WarningList({ warnings }: { warnings: string[] }) {
  return (
    <details className="analysis-warnings">
      <summary>查看 {warnings.length} 条降级说明</summary>
      <ul>{warnings.map((warning, index) => <li key={`${warning}-${index}`}>{warning}</li>)}</ul>
    </details>
  )
}
