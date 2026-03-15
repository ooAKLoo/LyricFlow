import { useState } from 'react'
import type { WordData, Annotation, AnnotationType } from '../types/lyrics'
import { ANNOTATION_COLORS, ANNOTATION_LABELS } from '../types/lyrics'

interface WordSpanProps {
  word: WordData
  active: boolean
  visibleTypes: Set<AnnotationType>
  onClickWord?: (word: WordData) => void
}

export function WordSpan({ word, active, visibleTypes, onClickWord }: WordSpanProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  const visibleAnnotations = word.annotations.filter((a) => visibleTypes.has(a.type))
  const hasAnnotations = visibleAnnotations.length > 0

  const getAnnotationStyle = () => {
    if (!hasAnnotations) return {}

    const primaryAnnotation = visibleAnnotations[0]
    const color = ANNOTATION_COLORS[primaryAnnotation.type]

    if (primaryAnnotation.type === 'weak_form') {
      return { color: '#888888', opacity: 0.7 }
    }
    if (primaryAnnotation.type === 'elision') {
      return { color: '#D32F2F' }
    }
    return { color }
  }

  const hasLinking = visibleAnnotations.some((a) => a.type === 'linking')
  const hasWeakForm = visibleAnnotations.some((a) => a.type === 'weak_form')
  const hasElision = visibleAnnotations.some((a) => a.type === 'elision')

  return (
    <span
      className="relative inline-block cursor-pointer select-none"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onClick={() => onClickWord?.(word)}
    >
      {/* Main word */}
      <span
        className={`
          relative inline-block px-0.5 transition-all duration-150
          ${active ? 'scale-110 font-bold' : ''}
        `}
        style={{
          ...getAnnotationStyle(),
          color: active ? '#2563EB' : getAnnotationStyle().color || '#374151',
        }}
      >
        {/* Weak form brackets */}
        {hasWeakForm && <span className="text-neutral-400">(</span>}

        {/* Elision strikethrough on specific letters */}
        {hasElision ? (
          <span className="line-through decoration-red-500 decoration-2">{word.word}</span>
        ) : (
          word.word
        )}

        {hasWeakForm && <span className="text-neutral-400">)</span>}
      </span>

      {/* Linking arc (displayed after the word, before next word) */}
      {hasLinking && (
        <span className="text-[#2563EB] text-[10px] mx-[-2px] select-none">⌢</span>
      )}

      {/* IPA display below word */}
      {word.ipa && (
        <span className="block text-center text-[9px] text-neutral-400 leading-tight mt-0.5">
          /{word.ipa}/
        </span>
      )}

      {/* Tooltip */}
      {showTooltip && hasAnnotations && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-56">
          <div className="bg-white rounded-xl p-3 text-left" style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
            {visibleAnnotations.map((ann, i) => (
              <AnnotationTooltip key={i} annotation={ann} />
            ))}
          </div>
        </div>
      )}
    </span>
  )
}

function AnnotationTooltip({ annotation }: { annotation: Annotation }) {
  const label = ANNOTATION_LABELS[annotation.type]
  const color = ANNOTATION_COLORS[annotation.type]

  return (
    <div className="mb-2 last:mb-0">
      <div className="flex items-center gap-1.5 mb-1">
        <span
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: color }}
        />
        <span className="text-[10px] font-medium text-neutral-700">
          {label.zh} {label.en}
        </span>
        <span className="text-[9px] text-neutral-400 ml-auto">
          {Math.round(annotation.confidence * 100)}%
        </span>
      </div>
      <p className="text-[10px] text-neutral-500 leading-relaxed">
        {annotation.explanation_zh}
      </p>
      {annotation.strong_ipa && annotation.weak_ipa && (
        <div className="flex gap-2 mt-1">
          <span className="text-[9px] text-neutral-400">
            强读 /{annotation.strong_ipa}/
          </span>
          <span className="text-[9px] text-neutral-500">→</span>
          <span className="text-[9px] font-medium" style={{ color }}>
            弱读 /{annotation.weak_ipa}/
          </span>
        </div>
      )}
    </div>
  )
}
