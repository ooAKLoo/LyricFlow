import { useState, useRef, useEffect } from 'react'
import { convertFileSrc } from '@tauri-apps/api/core'
import { save } from '@tauri-apps/plugin-dialog'
import { writeTextFile } from '@tauri-apps/plugin-fs'
import type { SongResult } from '../types/lyrics'
import { LyricPlayer } from '../components/LyricPlayer'
import { AudioControls } from '../components/AudioControls'
import { AnnotationLayer } from '../components/AnnotationLayer'
import { useAnnotations } from '../hooks/useAnnotations'

interface ResultPageProps {
  result: SongResult
  onBack: () => void
}

export function ResultPage({ result, onBack }: ResultPageProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [activeLineIndex, setActiveLineIndex] = useState(0)
  const { visibleTypes, toggleType, stats } = useAnnotations({ lines: result.lines })

  // Track active line from audio time
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const onTimeUpdate = () => {
      const t = audio.currentTime
      const idx = result.lines.findIndex((l) => t >= l.start && t < l.end)
      if (idx !== -1) setActiveLineIndex(idx)
    }

    audio.addEventListener('timeupdate', onTimeUpdate)
    return () => audio.removeEventListener('timeupdate', onTimeUpdate)
  }, [result.lines])

  const handleLineClick = (lineIndex: number) => {
    const audio = audioRef.current
    const line = result.lines[lineIndex]
    if (audio && line) {
      audio.currentTime = line.start
      audio.play()
      setActiveLineIndex(lineIndex)
    }
  }

  return (
    <div className="h-screen bg-[#f8f8f8] flex flex-col">
      {/* Hidden audio element — use convertFileSrc for local file access */}
      <audio
        ref={audioRef}
        src={result.vocals_path ? convertFileSrc(result.vocals_path) : result.vocals_url}
        preload="auto"
      />

      {/* Header with titlebar drag region */}
      <div className="flex items-center gap-3 px-6 py-4" data-tauri-drag-region>
        <div className="w-[78px]" /> {/* Traffic light spacer */}
        <button
          onClick={onBack}
          className="w-8 h-8 rounded-lg bg-white flex items-center justify-center text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <div className="flex-1">
          <h1 className="text-[13px] font-medium text-neutral-700">
            {result.song_title}
          </h1>
          <p className="text-[10px] text-neutral-400">{result.artist}</p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[9px] font-medium text-neutral-400 uppercase tracking-wide">
            {stats.total} ANNOTATIONS
          </span>
        </div>
      </div>

      {/* Main layout */}
      <div className="flex-1 flex gap-4 px-4 pb-4 min-h-0">
        {/* Lyrics area */}
        <div className="flex-1 bg-white rounded-3xl flex flex-col min-w-0 overflow-hidden">
          <LyricPlayer
            lines={result.lines}
            audioRef={audioRef}
            visibleTypes={visibleTypes}
            activeLineIndex={activeLineIndex}
            onLineClick={handleLineClick}
          />
        </div>

        {/* Sidebar */}
        <div className="w-64 flex-shrink-0 space-y-3">
          {/* Player controls */}
          <AudioControls
            audioRef={audioRef}
            duration={result.duration}
            songTitle={result.song_title}
            artist={result.artist}
          />

          {/* Annotation filters */}
          <AnnotationLayer
            visibleTypes={visibleTypes}
            toggleType={toggleType}
            stats={stats}
          />

          {/* Stats card */}
          <div className="bg-white rounded-xl p-3">
            <div className="text-[9px] font-medium text-neutral-400 uppercase tracking-wide mb-2">
              STATISTICS
            </div>
            <div className="grid grid-cols-2 gap-2">
              <StatItem label="总词数" value={result.stats.total_words} />
              <StatItem label="标注数" value={result.stats.total_annotations} />
              <StatItem label="连读" value={result.stats.total_linking} color="#2563EB" />
              <StatItem label="弱读" value={result.stats.total_weak_forms} color="#888888" />
              <StatItem label="吞音" value={result.stats.total_elision} color="#D32F2F" />
              <StatItem label="行数" value={result.lines.length} />
            </div>
          </div>

          {/* Export */}
          <button
            onClick={async () => {
              const path = await save({
                defaultPath: `${result.song_title || 'annotations'}.json`,
                filters: [{ name: 'JSON', extensions: ['json'] }],
              })
              if (path) {
                await writeTextFile(path, JSON.stringify(result, null, 2))
              }
            }}
            className="w-full py-2.5 rounded-xl bg-neutral-100 hover:bg-neutral-200 text-[10px] font-medium text-neutral-500 transition-colors"
          >
            导出标注 JSON
          </button>
        </div>
      </div>
    </div>
  )
}

function StatItem({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div className="bg-neutral-100 rounded-lg p-2">
      <div className="text-[9px] text-neutral-400">{label}</div>
      <div
        className="text-[13px] font-semibold tabular-nums"
        style={{ color: color || '#404040' }}
      >
        {value}
      </div>
    </div>
  )
}
