import type { AnnotationType } from '../types/lyrics'
import { ANNOTATION_COLORS, ANNOTATION_LABELS } from '../types/lyrics'

interface AnnotationLayerProps {
  visibleTypes: Set<AnnotationType>
  toggleType: (type: AnnotationType) => void
  stats: {
    linking: number
    weakForm: number
    elision: number
    total: number
  }
}

export function AnnotationLayer({ visibleTypes, toggleType, stats }: AnnotationLayerProps) {
  const types: { type: AnnotationType; count: number }[] = [
    { type: 'linking', count: stats.linking },
    { type: 'weak_form', count: stats.weakForm },
    { type: 'elision', count: stats.elision },
  ]

  return (
    <div className="bg-white rounded-xl p-3">
      <div className="text-[9px] font-medium text-neutral-400 uppercase tracking-wide mb-2">
        ANNOTATIONS
      </div>

      <div className="space-y-1.5">
        {types.map(({ type, count }) => {
          const label = ANNOTATION_LABELS[type]
          const color = ANNOTATION_COLORS[type]
          const isVisible = visibleTypes.has(type)

          return (
            <button
              key={type}
              onClick={() => toggleType(type)}
              className={`
                w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-colors
                ${isVisible ? 'bg-neutral-100' : 'bg-neutral-50 opacity-50'}
              `}
            >
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: isVisible ? color : '#d4d4d4' }}
              />
              <div className="flex-1 min-w-0">
                <span className="text-[10px] font-medium text-neutral-700">
                  {label.zh}
                </span>
                <span className="text-[9px] text-neutral-400 ml-1">{label.en}</span>
              </div>
              <span className="text-[10px] font-semibold text-neutral-700 tabular-nums">
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-3 pt-2">
        <div className="text-[9px] font-medium text-neutral-400 uppercase tracking-wide mb-1.5">
          LEGEND
        </div>
        <div className="space-y-1 text-[9px] text-neutral-500">
          <div className="flex items-center gap-2">
            <span className="text-[#2563EB]">⌢</span>
            <span>连读弧线</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-neutral-400">(word)</span>
            <span>弱读括号</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[#D32F2F] line-through">t</span>
            <span>吞音删除线</span>
          </div>
        </div>
      </div>
    </div>
  )
}
