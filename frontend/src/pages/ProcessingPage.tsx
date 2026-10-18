import {
  AudioWaveform,
  Captions,
  Check,
  FileCheck2,
  Languages,
  LoaderCircle,
  ScanSearch,
  TimerReset,
} from 'lucide-react'
import type { ComponentType } from 'react'
import type { ProgressInfo } from '../hooks/useSidecar'

interface ProcessingPageProps {
  progress: ProgressInfo
}

const STAGES: Array<{ key: string; label: string; detail: string; icon: ComponentType<{ size?: number }> }> = [
  { key: 'preprocessing', label: '整理音频', detail: '人声、响度与节拍', icon: AudioWaveform },
  { key: 'lyrics', label: '确认歌词', detail: '匹配版本与时间线', icon: Captions },
  { key: 'aligning', label: '逐词对齐', detail: '把每个词放回音频', icon: TimerReset },
  { key: 'phonetics', label: '建立发音层', detail: '标准音与口语变体', icon: Languages },
  { key: 'detecting', label: '听辨语流', detail: '连读、弱读、吞音与重拍', icon: ScanSearch },
  { key: 'output', label: '生成练习', detail: '整理成可跟唱的句子', icon: FileCheck2 },
]

export function ProcessingPage({ progress }: ProcessingPageProps) {
  const currentKey = progress.stage || 'preprocessing'
  const currentIndex = Math.max(0, STAGES.findIndex((stage) => stage.key === currentKey))
  const current = STAGES[currentIndex] || STAGES[0]
  const CurrentIcon = current.icon

  return (
    <div className="processing-page">
      <div className="titlebar-drag-region" data-tauri-drag-region />
      <main className="processing-layout">
        <section className="processing-summary" aria-live="polite">
          <span className="processing-icon"><CurrentIcon size={26} /></span>
          <p className="eyebrow">正在准备你的练习</p>
          <h1>{current.label}</h1>
          <p>{progress.message || current.detail}</p>

          <div className="progress-track" aria-label={`分析进度 ${progress.percent}%`}>
            <span style={{ width: `${Math.max(2, progress.percent)}%` }} />
          </div>
          <div className="progress-meta">
            <span>通常需要几分钟，可以让窗口保持在后台</span>
            <strong>{progress.percent}%</strong>
          </div>
        </section>

        <ol className="processing-steps">
          {STAGES.map((stage, index) => {
            const Icon = stage.icon
            const isDone = index < currentIndex || currentKey === 'done'
            const isCurrent = index === currentIndex && currentKey !== 'done'
            return (
              <li key={stage.key} className={isCurrent ? 'is-current' : isDone ? 'is-done' : ''}>
                <span className="step-status">
                  {isDone ? <Check size={15} /> : isCurrent ? <LoaderCircle size={15} /> : <Icon size={15} />}
                </span>
                <span>
                  <strong>{stage.label}</strong>
                  <small>{stage.detail}</small>
                </span>
              </li>
            )
          })}
        </ol>
      </main>
    </div>
  )
}
