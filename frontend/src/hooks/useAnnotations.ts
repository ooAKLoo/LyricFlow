import { useState, useMemo } from 'react'
import type { LyricLine, AnnotationType } from '../types/lyrics'

interface UseAnnotationsOptions {
  lines: LyricLine[]
}

export function useAnnotations({ lines }: UseAnnotationsOptions) {
  const [visibleTypes, setVisibleTypes] = useState<Set<AnnotationType>>(
    new Set(['linking', 'weak_form', 'elision'])
  )

  const toggleType = (type: AnnotationType) => {
    setVisibleTypes((prev) => {
      const next = new Set(prev)
      if (next.has(type)) {
        next.delete(type)
      } else {
        next.add(type)
      }
      return next
    })
  }

  const stats = useMemo(() => {
    let linking = 0
    let weakForm = 0
    let elision = 0

    for (const line of lines) {
      for (const word of line.words) {
        for (const ann of word.annotations) {
          if (ann.type === 'linking') linking++
          else if (ann.type === 'weak_form') weakForm++
          else if (ann.type === 'elision') elision++
        }
      }
    }

    return { linking, weakForm, elision, total: linking + weakForm + elision }
  }, [lines])

  return { visibleTypes, toggleType, stats }
}
