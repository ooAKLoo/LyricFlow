import { useEffect, useRef, useState } from 'react'
import type { WordData } from '../types/lyrics'

interface UseAudioSyncOptions {
  words: WordData[]
  audioRef: React.RefObject<HTMLAudioElement | null>
}

export function useAudioSync({ words, audioRef }: UseAudioSyncOptions) {
  const [activeWordIndex, setActiveWordIndex] = useState(-1)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const updateActiveWord = () => {
      const time = audio.currentTime
      const index = words.findIndex((word) => time >= word.start && time < word.end)
      setActiveWordIndex(index)
    }
    const sync = () => {
      updateActiveWord()
      rafRef.current = requestAnimationFrame(sync)
    }
    const onPlay = () => {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = requestAnimationFrame(sync)
    }
    const onPause = () => cancelAnimationFrame(rafRef.current)

    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    audio.addEventListener('seeked', updateActiveWord)
    if (!audio.paused) rafRef.current = requestAnimationFrame(sync)

    return () => {
      cancelAnimationFrame(rafRef.current)
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
      audio.removeEventListener('seeked', updateActiveWord)
    }
  }, [audioRef, words])

  return { activeWordIndex }
}
