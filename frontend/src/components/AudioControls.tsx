import { useState, useEffect } from 'react'

interface AudioControlsProps {
  audioRef: React.RefObject<HTMLAudioElement | null>
  duration: number
  songTitle: string
  artist: string
  onLoopLine?: (lineIndex: number | null) => void
}

const SPEED_OPTIONS = [0.5, 0.75, 1.0, 1.25]

export function AudioControls({
  audioRef,
  duration,
  songTitle,
  artist,
}: AudioControlsProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [speed, setSpeed] = useState(1.0)
  const [useVocals, setUseVocals] = useState(true)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const onTimeUpdate = () => setCurrentTime(audio.currentTime)
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
  }, [audioRef])

  const togglePlay = () => {
    const audio = audioRef.current
    if (!audio) return
    if (audio.paused) {
      audio.play()
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

  const changeSpeed = () => {
    const audio = audioRef.current
    if (!audio) return
    const idx = SPEED_OPTIONS.indexOf(speed)
    const nextSpeed = SPEED_OPTIONS[(idx + 1) % SPEED_OPTIONS.length]
    audio.playbackRate = nextSpeed
    setSpeed(nextSpeed)
  }

  const formatTime = (t: number) => {
    const m = Math.floor(t / 60)
    const s = Math.floor(t % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="bg-white rounded-3xl p-4">
      {/* Song info */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-[13px] font-medium text-neutral-700">{songTitle}</h3>
          <p className="text-[10px] text-neutral-400">{artist}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {/* Vocals toggle */}
          <button
            onClick={() => setUseVocals(!useVocals)}
            className={`
              px-2.5 py-1.5 rounded-lg text-[10px] font-medium whitespace-nowrap transition-colors
              ${useVocals ? 'bg-neutral-800 text-white' : 'bg-neutral-100 text-neutral-500 hover:bg-neutral-200'}
            `}
          >
            人声
          </button>
          {/* Speed control */}
          <button
            onClick={changeSpeed}
            className="px-2.5 py-1.5 rounded-lg text-[10px] font-medium bg-neutral-100 text-neutral-500 hover:bg-neutral-200 tabular-nums"
          >
            {speed}x
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-2">
        <input
          type="range"
          min={0}
          max={duration || 100}
          step={0.1}
          value={currentTime}
          onChange={(e) => seek(Number(e.target.value))}
          className="w-full h-1 bg-neutral-200 rounded-full appearance-none cursor-pointer accent-neutral-800"
        />
        <div className="flex justify-between mt-1">
          <span className="text-[9px] text-neutral-400 tabular-nums">
            {formatTime(currentTime)}
          </span>
          <span className="text-[9px] text-neutral-400 tabular-nums">
            {formatTime(duration)}
          </span>
        </div>
      </div>

      {/* Play controls */}
      <div className="flex items-center justify-center gap-4">
        {/* Rewind 5s */}
        <button
          onClick={() => seek(Math.max(0, currentTime - 5))}
          className="w-8 h-8 rounded-lg bg-neutral-100 hover:bg-neutral-200 flex items-center justify-center text-neutral-400 hover:text-neutral-600 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M1 4v6h6M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
        </button>

        {/* Play/Pause */}
        <button
          onClick={togglePlay}
          className="w-10 h-10 rounded-xl bg-neutral-800 text-white flex items-center justify-center hover:bg-neutral-700 transition-colors"
        >
          {isPlaying ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        {/* Forward 5s */}
        <button
          onClick={() => seek(Math.min(duration, currentTime + 5))}
          className="w-8 h-8 rounded-lg bg-neutral-100 hover:bg-neutral-200 flex items-center justify-center text-neutral-400 hover:text-neutral-600 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 4v6h-6M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>
      </div>
    </div>
  )
}
