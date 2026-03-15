import { useRef, useMemo, useEffect } from 'react'
import type { LyricLine, AnnotationType } from '../types/lyrics'
import { useAudioSync } from '../hooks/useAudioSync'
import { WordSpan } from './WordSpan'

interface LyricPlayerProps {
  lines: LyricLine[]
  audioRef: React.RefObject<HTMLAudioElement | null>
  visibleTypes: Set<AnnotationType>
  activeLineIndex: number
  onLineClick?: (lineIndex: number) => void
}

export function LyricPlayer({
  lines,
  audioRef,
  visibleTypes,
  activeLineIndex,
  onLineClick,
}: LyricPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Flatten all words for sync tracking
  const allWords = useMemo(() => {
    return lines.flatMap((line) => line.words)
  }, [lines])

  const { activeWordIndex } = useAudioSync({ words: allWords, audioRef })

  // Calculate which word index belongs to which line
  const lineWordRanges = useMemo(() => {
    const ranges: { start: number; end: number }[] = []
    let offset = 0
    for (const line of lines) {
      ranges.push({ start: offset, end: offset + line.words.length })
      offset += line.words.length
    }
    return ranges
  }, [lines])

  // Auto-scroll to active line
  useEffect(() => {
    if (activeLineIndex >= 0 && containerRef.current) {
      const lineEl = containerRef.current.querySelector(
        `[data-line-index="${activeLineIndex}"]`
      )
      if (lineEl) {
        lineEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  }, [activeLineIndex])

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-6 py-8 space-y-6"
    >
      {lines.map((line, lineIdx) => {
        const range = lineWordRanges[lineIdx]
        const isActiveLine =
          activeWordIndex >= range.start && activeWordIndex < range.end

        return (
          <div
            key={lineIdx}
            data-line-index={lineIdx}
            className={`
              rounded-2xl p-4 transition-all duration-300 cursor-pointer
              ${isActiveLine ? 'bg-[#EFF6FF]' : 'bg-neutral-100 hover:bg-neutral-50'}
              ${line.is_rap ? 'border-l-2 border-[#7C3AED]' : ''}
            `}
            onClick={() => onLineClick?.(lineIdx)}
          >
            {/* Words with annotations */}
            <div className="flex flex-wrap items-end gap-x-1 gap-y-3 text-[15px] leading-relaxed">
              {line.words.map((word, wordIdx) => {
                const globalIdx = range.start + wordIdx
                return (
                  <WordSpan
                    key={wordIdx}
                    word={word}
                    active={globalIdx === activeWordIndex}
                    visibleTypes={visibleTypes}
                  />
                )
              })}
            </div>

            {/* Translation */}
            {line.translation && (
              <p className="text-[11px] text-neutral-400 mt-2">
                {line.translation}
              </p>
            )}

            {/* Rap indicator */}
            {line.is_rap && (
              <span className="inline-block mt-2 text-[8px] font-medium text-[#7C3AED] bg-[#FAF5FF] px-2 py-0.5 rounded-lg">
                RAP
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
