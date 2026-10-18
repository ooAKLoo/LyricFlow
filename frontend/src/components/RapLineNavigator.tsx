import { ListMusic, Mic2 } from 'lucide-react'
import type { LyricLine } from '../types/lyrics'

interface RapLineNavigatorProps {
  lines: LyricLine[]
  selectedIndex: number
  onSelect: (index: number) => void
  showAll: boolean
  onShowAllChange: (showAll: boolean) => void
}

export function RapLineNavigator({
  lines,
  selectedIndex,
  onSelect,
  showAll,
  onShowAllChange,
}: RapLineNavigatorProps) {
  const rapCount = lines.filter((line) => line.is_rap).length
  const visibleLines = lines
    .map((line, index) => ({ line, index }))
    .filter(({ line }) => showAll || line.is_rap || rapCount === 0)

  return (
    <nav className="line-navigator" aria-label="练习句列表">
      <div className="navigator-heading">
        <span className="navigator-icon"><Mic2 aria-hidden="true" size={16} /></span>
        <div>
          <strong>Rap 段落</strong>
          <small>{rapCount || lines.length} 句可练</small>
        </div>
      </div>

      {rapCount > 0 && (
        <div className="navigator-filter" role="group" aria-label="歌词范围">
          <button
            type="button"
            className={!showAll ? 'is-active' : ''}
            aria-pressed={!showAll}
            onClick={() => onShowAllChange(false)}
          >
            只看 Rap
          </button>
          <button
            type="button"
            className={showAll ? 'is-active' : ''}
            aria-pressed={showAll}
            onClick={() => onShowAllChange(true)}
          >
            全部歌词
          </button>
        </div>
      )}

      <div className="line-list">
        {visibleLines.map(({ line, index }) => (
          <button
            type="button"
            key={`${line.start}-${index}`}
            className={`line-list-item ${index === selectedIndex ? 'is-active' : ''}`}
            aria-current={index === selectedIndex ? 'true' : undefined}
            onClick={() => onSelect(index)}
          >
            <span className="line-number">{String(index + 1).padStart(2, '0')}</span>
            <span className="line-list-copy">
              <strong>{line.text}</strong>
              <small>
                {formatTime(line.start)} · {line.is_rap ? 'Rap' : '演唱'}
                {line.difficulty ? ` · 难度 ${line.difficulty}` : ''}
              </small>
            </span>
          </button>
        ))}
      </div>

      <div className="navigator-footer">
        <ListMusic aria-hidden="true" size={14} />
        点击任意一句，从它的起点开始播放
      </div>
    </nav>
  )
}

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const rest = Math.floor(seconds % 60)
  return `${minutes}:${rest.toString().padStart(2, '0')}`
}
