import { useEffect, useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Gauge,
  Pause,
  Play,
  Repeat2,
  Volume2,
} from 'lucide-react'
import type { LyricLine } from '../types/lyrics'

export type AudioSource = 'vocals' | 'original'

interface AudioControlsProps {
  audioRef: React.RefObject<HTMLAudioElement | null>
  line: LyricLine
  speed: number
  onSpeedChange: (speed: number) => void
  loopLine: boolean
  onLoopLineChange: (loop: boolean) => void
  source: AudioSource
  onSourceChange: (source: AudioSource) => void
  hasVocals: boolean
  hasOriginal: boolean
  onPrevious: () => void
  onNext: () => void
  onPlayReference?: () => void
}

const SPEEDS = [0.5, 0.75, 1]

export function AudioControls({
  audioRef,
  line,
  speed,
  onSpeedChange,
  loopLine,
  onLoopLineChange,
  source,
  onSourceChange,
  hasVocals,
  hasOriginal,
  onPrevious,
  onNext,
}: AudioControlsProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(line.start)
  const canPlay = hasVocals || hasOriginal

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const onTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
      if (loopLine && audio.currentTime >= line.end) {
        audio.currentTime = line.start
        void audio.play()
      }
    }
    const onPlay = () => setIsPlaying(true)
    const onPause = () => setIsPlaying(false)
    audio.addEventListener('timeupdate', onTimeUpdate)
    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate)
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
    }
  }, [audioRef, line.end, line.start, loopLine])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    audio.playbackRate = speed
    if (audio.currentTime < line.start || audio.currentTime >= line.end) {
      audio.currentTime = line.start
    }
  }, [audioRef, line.end, line.start, speed])

  const togglePlay = async () => {
    const audio = audioRef.current
    if (!audio || !canPlay) return
    if (audio.paused) {
      if (audio.currentTime < line.start || audio.currentTime >= line.end) {
        audio.currentTime = line.start
      }
      await audio.play()
    } else {
      audio.pause()
    }
  }

  const seek = (value: number) => {
    const audio = audioRef.current
    if (!audio) return
    audio.currentTime = value
    setCurrentTime(value)
  }

  return (
    <div className="practice-controls">
      <div className="transport-row">
        <div className="source-control" role="group" aria-label="音频来源">
          <Volume2 aria-hidden="true" size={15} />
          <button
            type="button"
            className={source === 'vocals' ? 'is-active' : ''}
            disabled={!hasVocals}
            onClick={() => onSourceChange('vocals')}
          >
            人声
          </button>
          <button
            type="button"
            className={source === 'original' ? 'is-active' : ''}
            disabled={!hasOriginal}
            onClick={() => onSourceChange('original')}
          >
            原曲
          </button>
        </div>

        <div className="transport-buttons">
          <button type="button" className="icon-button" aria-label="上一句" onClick={onPrevious}>
            <ChevronLeft aria-hidden="true" size={19} />
          </button>
          <button
            type="button"
            className="play-button"
            aria-label={isPlaying ? '暂停' : '播放当前句'}
            disabled={!canPlay}
            onClick={togglePlay}
          >
            {isPlaying ? <Pause aria-hidden="true" size={19} /> : <Play aria-hidden="true" size={19} fill="currentColor" />}
          </button>
          <button type="button" className="icon-button" aria-label="下一句" onClick={onNext}>
            <ChevronRight aria-hidden="true" size={19} />
          </button>
        </div>

        <div className="speed-control" role="group" aria-label="播放速度">
          <Gauge aria-hidden="true" size={15} />
          {SPEEDS.map((option) => (
            <button
              type="button"
              key={option}
              className={speed === option ? 'is-active' : ''}
              aria-pressed={speed === option}
              onClick={() => onSpeedChange(option)}
            >
              {option}×
            </button>
          ))}
        </div>
      </div>

      <div className="line-scrubber">
        <span>{formatTime(Math.max(line.start, currentTime))}</span>
        <input
          type="range"
          min={line.start}
          max={Math.max(line.start + 0.1, line.end)}
          step={0.01}
          value={Math.min(line.end, Math.max(line.start, currentTime))}
          aria-label="当前句播放位置"
          onChange={(event) => seek(Number(event.target.value))}
        />
        <span>{formatTime(line.end)}</span>
        <button
          type="button"
          className={`loop-button ${loopLine ? 'is-active' : ''}`}
          aria-pressed={loopLine}
          onClick={() => onLoopLineChange(!loopLine)}
        >
          <Repeat2 aria-hidden="true" size={15} />
          单句循环
        </button>
      </div>
    </div>
  )
}

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const rest = Math.floor(seconds % 60)
  return `${minutes}:${rest.toString().padStart(2, '0')}`
}
