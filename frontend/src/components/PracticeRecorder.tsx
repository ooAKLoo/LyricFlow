import { useEffect, useRef, useState } from 'react'
import { Mic, Pause, Play, RotateCcw, Square } from 'lucide-react'

interface PracticeRecorderProps {
  maxDurationSeconds: number
  onPlayReference: () => void
}

type RecorderState = 'idle' | 'recording' | 'ready' | 'error'

export function PracticeRecorder({ maxDurationSeconds, onPlayReference }: PracticeRecorderProps) {
  const [state, setState] = useState<RecorderState>('idle')
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState('')
  const [isPlaying, setIsPlaying] = useState(false)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const recordingUrlRef = useRef('')
  const playbackRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    if (state !== 'recording') return
    const startedAt = Date.now()
    const timer = window.setInterval(() => {
      const next = (Date.now() - startedAt) / 1000
      setElapsed(next)
      if (next >= maxDurationSeconds + 2) recorderRef.current?.stop()
    }, 100)
    return () => window.clearInterval(timer)
  }, [maxDurationSeconds, state])

  useEffect(() => () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current)
  }, [])

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError('当前系统不支持应用内录音。')
      setState('error')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const recorder = new MediaRecorder(stream)
      recorderRef.current = recorder
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop())
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current)
        recordingUrlRef.current = URL.createObjectURL(blob)
        if (playbackRef.current) playbackRef.current.src = recordingUrlRef.current
        setState('ready')
      }
      recorder.start()
      setElapsed(0)
      setError('')
      setState('recording')
    } catch {
      setError('没有获得麦克风权限，请在系统设置中允许 LyricFlow 使用麦克风。')
      setState('error')
    }
  }

  const toggleRecordingPlayback = async () => {
    const audio = playbackRef.current
    if (!audio) return
    if (audio.paused) await audio.play()
    else audio.pause()
  }

  const reset = () => {
    playbackRef.current?.pause()
    if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current)
    recordingUrlRef.current = ''
    setElapsed(0)
    setState('idle')
    setError('')
  }

  return (
    <section className="recorder" aria-labelledby="recorder-title">
      <audio
        ref={playbackRef}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
      />
      <div>
        <p className="eyebrow">跟唱对比</p>
        <h3 id="recorder-title">录下这一句，再和原声交替听</h3>
      </div>

      <div className="recorder-actions">
        <button type="button" className="button button-secondary" onClick={onPlayReference}>
          <Play aria-hidden="true" size={16} />听原声
        </button>
        {state === 'recording' ? (
          <button type="button" className="button record-button is-recording" onClick={() => recorderRef.current?.stop()}>
            <Square aria-hidden="true" size={15} fill="currentColor" />
            停止 · {elapsed.toFixed(1)}s
          </button>
        ) : state === 'ready' ? (
          <>
            <button type="button" className="button record-button" onClick={toggleRecordingPlayback}>
              {isPlaying ? <Pause aria-hidden="true" size={16} /> : <Play aria-hidden="true" size={16} />}
              {isPlaying ? '暂停我的录音' : '听我的录音'}
            </button>
            <button type="button" className="icon-button" aria-label="重新录制" onClick={reset}>
              <RotateCcw aria-hidden="true" size={16} />
            </button>
          </>
        ) : (
          <button type="button" className="button record-button" onClick={startRecording}>
            <Mic aria-hidden="true" size={16} />开始录音
          </button>
        )}
      </div>
      {error && <p className="recorder-error" role="alert">{error}</p>}
      <p className="recorder-privacy">录音只保留在当前页面，关闭或重新录制后即释放。</p>
    </section>
  )
}
