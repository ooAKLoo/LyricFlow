import { useState, useEffect, useRef, useCallback } from 'react'
import type { WordData } from '../types/lyrics'

interface UseAudioSyncOptions {
  words: WordData[]
  audioRef: React.RefObject<HTMLAudioElement | null>
}

export function useAudioSync({ words, audioRef }: UseAudioSyncOptions) {
  const [activeWordIndex, setActiveWordIndex] = useState(-1)
  const rafRef = useRef<number>(0)

  const sync = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return

    const t = audio.currentTime
    const idx = words.findIndex((w) => t >= w.start && t < w.end)
    if (idx !== -1) {
      setActiveWordIndex(idx)
    }

    rafRef.current = requestAnimationFrame(sync)
  }, [words, audioRef])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const onPlay = () => {
      rafRef.current = requestAnimationFrame(sync)
    }

    const onPause = () => {
      cancelAnimationFrame(rafRef.current)
    }

    const onSeeked = () => {
      const t = audio.currentTime
      const idx = words.findIndex((w) => t >= w.start && t < w.end)
      setActiveWordIndex(idx)
    }

    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    audio.addEventListener('seeked', onSeeked)

    // If already playing
    if (!audio.paused) {
      rafRef.current = requestAnimationFrame(sync)
    }

    return () => {
      cancelAnimationFrame(rafRef.current)
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
      audio.removeEventListener('seeked', onSeeked)
    }
  }, [sync, audioRef, words])

  return { activeWordIndex }
}
