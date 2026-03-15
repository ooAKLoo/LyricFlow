import { useState, useEffect, useRef } from 'react'
import type { TaskStatus } from '../types/lyrics'

interface ProcessingPageProps {
  taskId: string
  onComplete: (songId: string) => void
  onError: (message: string) => void
}

const STAGE_LABELS: Record<string, { label: string; icon: string }> = {
  pending: { label: '排队等待中...', icon: '⏳' },
  preprocessing: { label: '音频预处理（人声分离、降噪）', icon: '🎵' },
  lyrics_fetching: { label: '检测内封歌词 / 获取歌词', icon: '📝' },
  aligning: { label: '逐词时间对齐', icon: '🔗' },
  phonetics: { label: '音标转换', icon: '🔤' },
  detecting: { label: '发音现象检测', icon: '🔍' },
  completed: { label: '处理完成', icon: '✅' },
}

export function ProcessingPage({ taskId, onComplete, onError }: ProcessingPageProps) {
  const [status, setStatus] = useState<TaskStatus | null>(null)
  const intervalRef = useRef<number>(0)

  useEffect(() => {
    const poll = async () => {
      try {
        const resp = await fetch(`/api/v1/tasks/${taskId}`)
        if (!resp.ok) throw new Error('Failed to fetch status')

        const data: TaskStatus = await resp.json()
        setStatus(data)

        if (data.status === 'completed' && data.song_id) {
          clearInterval(intervalRef.current)
          onComplete(data.song_id)
        } else if (data.status === 'error') {
          clearInterval(intervalRef.current)
          onError(data.error_message || 'Processing failed')
        }
      } catch {
        // Silently retry
      }
    }

    poll() // Initial poll
    intervalRef.current = window.setInterval(poll, 2000)

    return () => clearInterval(intervalRef.current)
  }, [taskId, onComplete, onError])

  const progress = status?.progress || 0
  const stage = status?.status || 'pending'
  const stageInfo = STAGE_LABELS[stage] || STAGE_LABELS.pending

  return (
    <div className="min-h-screen bg-[#f8f8f8] flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-3xl p-8 text-center">
          {/* Animated icon */}
          <div className="text-4xl mb-4 animate-bounce">{stageInfo.icon}</div>

          <h2 className="text-[13px] font-medium text-neutral-700 mb-1">
            正在分析您的歌曲
          </h2>
          <p className="text-[10px] text-neutral-400 mb-6">{stageInfo.label}</p>

          {/* Progress bar */}
          <div className="w-full bg-neutral-100 rounded-full h-1.5 mb-2">
            <div
              className="h-1.5 rounded-full bg-neutral-800 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-[9px] text-neutral-400 tabular-nums">{progress}%</span>

          {/* Stage progress indicators */}
          <div className="mt-6 space-y-2">
            {Object.entries(STAGE_LABELS).map(([key, info]) => {
              if (key === 'pending' || key === 'completed') return null
              const stageOrder = ['preprocessing', 'lyrics_fetching', 'aligning', 'phonetics', 'detecting']
              const currentIdx = stageOrder.indexOf(stage)
              const thisIdx = stageOrder.indexOf(key)

              const isDone = thisIdx < currentIdx || stage === 'completed'
              const isCurrent = key === stage

              return (
                <div
                  key={key}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                    isCurrent ? 'bg-[#EFF6FF]' : ''
                  }`}
                >
                  <span className="text-[10px]">
                    {isDone ? '✓' : isCurrent ? '→' : '○'}
                  </span>
                  <span
                    className={`text-[10px] ${
                      isDone
                        ? 'text-neutral-400'
                        : isCurrent
                          ? 'text-[#2563EB] font-medium'
                          : 'text-neutral-300'
                    }`}
                  >
                    {info.label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
