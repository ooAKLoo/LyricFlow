import { useEffect, useMemo, useRef, useState } from 'react'
import { readFile } from '@tauri-apps/plugin-fs'
import {
  AudioLines,
  CheckCircle2,
  Headphones,
  Mic2,
  SlidersHorizontal,
} from 'lucide-react'
import type { SongResult } from '../types/lyrics'
import { useAudioSync } from '../hooks/useAudioSync'
import { RapLineNavigator } from '../components/RapLineNavigator'
import { PracticeLine, type SelectedCue } from '../components/PracticeLine'
import { CoachPanel } from '../components/CoachPanel'
import { AudioControls, type AudioSource } from '../components/AudioControls'
import { PracticeRecorder } from '../components/PracticeRecorder'

interface ResultPageProps {
  result: SongResult
  autoPlay?: boolean
}

type PracticeMode = 'listen' | 'breakdown' | 'perform'

const MODES: Array<{ id: PracticeMode; label: string; icon: typeof Headphones }> = [
  { id: 'listen', label: '听清', icon: Headphones },
  { id: 'breakdown', label: '拆解', icon: SlidersHorizontal },
  { id: 'perform', label: '跟唱', icon: Mic2 },
]

export function ResultPage({ result, autoPlay = true }: ResultPageProps) {
  const firstRapIndex = Math.max(0, result.lines.findIndex((line) => line.is_rap))
  const [selectedLineIndex, setSelectedLineIndex] = useState(firstRapIndex)
  const [manualCue, setManualCue] = useState<{ lineIndex: number; cue: SelectedCue } | null>(null)
  const [showAll, setShowAll] = useState(false)
  const [mode, setMode] = useState<PracticeMode>('breakdown')
  const [speed, setSpeed] = useState(0.75)
  const [loopLine, setLoopLine] = useState(true)
  const [source, setSource] = useState<AudioSource>('vocals')
  const [audioUrls, setAudioUrls] = useState<{ vocals: string; original: string }>({ vocals: '', original: '' })
  const [audioLoadError, setAudioLoadError] = useState('')
  const audioRef = useRef<HTMLAudioElement>(null)
  const sourceResumeRef = useRef<{ time: number; playing: boolean } | null>(null)
  const initialPlaybackRef = useRef(false)

  const selectedLine = result.lines[selectedLineIndex] || result.lines[0]
  const activeUrl = audioUrls[source] || audioUrls.vocals || audioUrls.original
  const { activeWordIndex } = useAudioSync({ words: selectedLine?.words || [], audioRef })
  const selectedCue = useMemo(() => {
    if (manualCue?.lineIndex === selectedLineIndex) return manualCue.cue
    return firstCueForLine(selectedLine)
  }, [manualCue, selectedLine, selectedLineIndex])

  useEffect(() => {
    let disposed = false
    const createdUrls: string[] = []

    const load = async (path: string | undefined, fallbackMime: string) => {
      if (!path) return ''
      const bytes = await readFile(path)
      const url = URL.createObjectURL(new Blob([bytes], { type: mimeForPath(path, fallbackMime) }))
      createdUrls.push(url)
      return url
    }

    void Promise.allSettled([
      load(result.vocals_path, 'audio/wav'),
      load(result.original_path, 'audio/wav'),
    ]).then(([vocalsResult, originalResult]) => {
      if (disposed) return
      const vocals = vocalsResult.status === 'fulfilled' ? vocalsResult.value : ''
      const original = originalResult.status === 'fulfilled' ? originalResult.value : ''
      setAudioUrls({ vocals, original })
      if (!vocals && original) setSource('original')
      if (!vocals && !original) {
        const reason = vocalsResult.status === 'rejected'
          ? vocalsResult.reason
          : originalResult.status === 'rejected'
            ? originalResult.reason
            : '未找到内置音频'
        setAudioLoadError(reason instanceof Error ? reason.message : String(reason))
      }
    })

    return () => {
      disposed = true
      createdUrls.forEach((url) => URL.revokeObjectURL(url))
    }
  }, [result.original_path, result.vocals_path])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio || !activeUrl || initialPlaybackRef.current) return

    const startAtFirstRap = () => {
      audio.currentTime = selectedLine.start
      audio.playbackRate = speed
      initialPlaybackRef.current = true
      if (autoPlay) void audio.play().catch(() => undefined)
    }

    if (audio.readyState >= 1) startAtFirstRap()
    else audio.addEventListener('loadedmetadata', startAtFirstRap, { once: true })

    return () => audio.removeEventListener('loadedmetadata', startAtFirstRap)
  }, [activeUrl, autoPlay, selectedLine.start, speed])

  useEffect(() => {
    const audio = audioRef.current
    const resume = sourceResumeRef.current
    if (!audio || !activeUrl || !resume) return
    sourceResumeRef.current = null
    const restore = () => {
      audio.currentTime = resume.time
      audio.playbackRate = speed
      if (resume.playing) void audio.play()
    }
    if (audio.readyState >= 1) restore()
    else audio.addEventListener('loadedmetadata', restore, { once: true })
    return () => audio.removeEventListener('loadedmetadata', restore)
  }, [activeUrl, speed])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    const updateActiveLine = () => {
      if (loopLine) return
      const index = result.lines.findIndex((line) => audio.currentTime >= line.start && audio.currentTime < line.end)
      if (index >= 0 && index !== selectedLineIndex) setSelectedLineIndex(index)
    }
    audio.addEventListener('timeupdate', updateActiveLine)
    return () => audio.removeEventListener('timeupdate', updateActiveLine)
  }, [loopLine, result.lines, selectedLineIndex])

  const navigableIndices = useMemo(() => {
    const rapCount = result.lines.filter((line) => line.is_rap).length
    return result.lines
      .map((line, index) => ({ line, index }))
      .filter(({ line }) => showAll || line.is_rap || rapCount === 0)
      .map(({ index }) => index)
  }, [result.lines, showAll])

  if (!selectedLine) {
    return <div className="app-state-page"><div className="state-message"><h2>没有可练习的歌词</h2></div></div>
  }

  const selectLine = (index: number, autoplay = false) => {
    setSelectedLineIndex(index)
    const audio = audioRef.current
    if (!audio) return
    const wasPlaying = autoplay || !audio.paused
    audio.currentTime = result.lines[index].start
    if (wasPlaying && activeUrl) void audio.play()
  }

  const moveLine = (direction: -1 | 1) => {
    const currentPosition = navigableIndices.indexOf(selectedLineIndex)
    const safePosition = currentPosition >= 0 ? currentPosition : 0
    const nextPosition = Math.min(
      navigableIndices.length - 1,
      Math.max(0, safePosition + direction),
    )
    selectLine(navigableIndices[nextPosition])
  }

  const switchSource = (nextSource: AudioSource) => {
    if (nextSource === source || !audioUrls[nextSource]) return
    const audio = audioRef.current
    sourceResumeRef.current = {
      time: audio?.currentTime || selectedLine.start,
      playing: Boolean(audio && !audio.paused),
    }
    audio?.pause()
    setSource(nextSource)
  }

  const changeMode = (nextMode: PracticeMode) => {
    setMode(nextMode)
    if (nextMode === 'listen') setSpeed(1)
    if (nextMode === 'breakdown') setSpeed(0.75)
    if (nextMode === 'perform') setSpeed(0.75)
    setLoopLine(nextMode !== 'listen')
  }

  const playReference = () => {
    const audio = audioRef.current
    if (!audio || !activeUrl) return
    audio.currentTime = selectedLine.start
    audio.playbackRate = speed
    void audio.play()
  }

  return (
    <div className="practice-page">
      <audio ref={audioRef} src={activeUrl} preload="metadata" />

      <header className="practice-header" data-tauri-drag-region>
        <span className="brand-mark small"><AudioLines aria-hidden="true" size={16} /></span>
        <div className="track-title">
          <strong>{result.song_title} · Ludacris Rap 专练</strong>
          <span>{result.artist} · 从 2:12 开始</span>
        </div>
        <div className="analysis-status">
          <CheckCircle2 aria-hidden="true" size={15} />
          <span>{result.analysis?.coaching_provider === 'qwen_audio' ? '音频智能分析' : '本地规则分析'}</span>
          {result.analysis?.alignment_quality ? <small>{Math.round(result.analysis.alignment_quality * 100)}% 对齐</small> : null}
        </div>
      </header>

      <main className="practice-layout">
        <RapLineNavigator
          lines={result.lines}
          selectedIndex={selectedLineIndex}
          onSelect={selectLine}
          showAll={showAll}
          onShowAllChange={setShowAll}
        />

        <section className="practice-stage">
          <div className="mode-switcher" role="tablist" aria-label="练习模式">
            {MODES.map(({ id, label, icon: Icon }) => (
              <button
                type="button"
                role="tab"
                key={id}
                aria-selected={mode === id}
                className={mode === id ? 'is-active' : ''}
                onClick={() => changeMode(id)}
              >
                <Icon aria-hidden="true" size={15} />{label}
              </button>
            ))}
          </div>

          <div className="practice-stage-scroll">
            {audioLoadError ? (
              <div className="audio-load-error" role="alert">
                内置音频读取失败：{audioLoadError}
              </div>
            ) : null}
            <PracticeLine
              line={selectedLine}
              lineIndex={selectedLineIndex}
              activeWordIndex={activeWordIndex}
              selectedCue={selectedCue}
              onSelectCue={(cue) => setManualCue({ lineIndex: selectedLineIndex, cue })}
            />

            {mode === 'perform' && (
              <PracticeRecorder
                maxDurationSeconds={Math.max(2, selectedLine.end - selectedLine.start)}
                onPlayReference={playReference}
              />
            )}
          </div>

          <AudioControls
            audioRef={audioRef}
            line={selectedLine}
            speed={speed}
            onSpeedChange={setSpeed}
            loopLine={loopLine}
            onLoopLineChange={setLoopLine}
            source={source}
            onSourceChange={switchSource}
            hasVocals={Boolean(audioUrls.vocals)}
            hasOriginal={Boolean(audioUrls.original)}
            onPrevious={() => moveLine(-1)}
            onNext={() => moveLine(1)}
            onPlayReference={playReference}
          />
        </section>

        <CoachPanel
          line={selectedLine}
          selectedCue={selectedCue}
          warnings={result.analysis?.warnings}
        />
      </main>
    </div>
  )
}

function mimeForPath(path: string, fallback: string) {
  const extension = path.split('.').pop()?.toLowerCase()
  if (extension === 'wav') return 'audio/wav'
  if (extension === 'ogg') return 'audio/ogg'
  if (extension === 'm4a' || extension === 'aac') return 'audio/mp4'
  return fallback
}

function firstCueForLine(line: SongResult['lines'][number] | undefined): SelectedCue | null {
  if (!line) return null
  for (let wordIndex = 0; wordIndex < line.words.length; wordIndex += 1) {
    const annotationIndex = line.words[wordIndex].annotations.findIndex(
      (annotation) => annotation.evidence === 'audio_model',
    )
    const preferredIndex = annotationIndex >= 0 ? annotationIndex : 0
    const annotation = line.words[wordIndex].annotations[preferredIndex]
    if (annotation) {
      return {
        annotation,
        word: line.words[wordIndex],
        wordIndex,
        annotationIndex: preferredIndex,
      }
    }
  }
  return null
}
