import type { ProgressInfo } from '../hooks/useSidecar'

interface ProcessingPageProps {
  progress: ProgressInfo
}

const STAGE_LABELS: Record<string, { label: string; icon: string }> = {
  preprocessing: { label: '音频预处理（人声分离、降噪）', icon: '🎵' },
  lyrics: { label: '检测内封歌词 / 获取歌词', icon: '📝' },
  aligning: { label: '逐词时间对齐', icon: '🔗' },
  phonetics: { label: '音标转换', icon: '🔤' },
  detecting: { label: '发音现象检测', icon: '🔍' },
  output: { label: '生成标注结果', icon: '📊' },
  done: { label: '处理完成', icon: '✅' },
}

const STAGE_ORDER = ['preprocessing', 'lyrics', 'aligning', 'phonetics', 'detecting', 'output']

export function ProcessingPage({ progress }: ProcessingPageProps) {
  const currentStage = progress.stage || 'preprocessing'
  const stageInfo = STAGE_LABELS[currentStage] || { label: progress.message || '处理中...', icon: '⏳' }

  return (
    <div className="min-h-screen bg-[#f8f8f8] flex items-center justify-center p-6">
      {/* macOS titlebar drag region */}
      <div
        className="fixed top-0 left-0 right-0 h-[52px] z-50"
        data-tauri-drag-region
      />

      <div className="w-full max-w-md">
        <div className="bg-white rounded-3xl p-8 text-center">
          <div className="text-4xl mb-4 animate-bounce">{stageInfo.icon}</div>

          <h2 className="text-[13px] font-medium text-neutral-700 mb-1">
            正在分析您的歌曲
          </h2>
          <p className="text-[10px] text-neutral-400 mb-6">
            {progress.message || stageInfo.label}
          </p>

          {/* Progress bar */}
          <div className="w-full bg-neutral-100 rounded-full h-1.5 mb-2">
            <div
              className="h-1.5 rounded-full bg-neutral-800 transition-all duration-500"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          <span className="text-[9px] text-neutral-400 tabular-nums">
            {progress.percent}%
          </span>

          {/* Stage indicators */}
          <div className="mt-6 space-y-2">
            {STAGE_ORDER.map((key) => {
              const info = STAGE_LABELS[key]
              const currentIdx = STAGE_ORDER.indexOf(currentStage)
              const thisIdx = STAGE_ORDER.indexOf(key)

              const isDone = thisIdx < currentIdx || currentStage === 'done'
              const isCurrent = key === currentStage

              return (
                <div
                  key={key}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                    isCurrent ? 'bg-[#EFF6FF]' : ''
                  }`}
                >
                  <span className="text-[10px] w-3 text-center">
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
