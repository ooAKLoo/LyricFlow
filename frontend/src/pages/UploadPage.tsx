import { useState, useCallback } from 'react'
import { open } from '@tauri-apps/plugin-dialog'

interface UploadPageProps {
  onAnalyze: (audioPath: string, lyricsPath?: string) => void
  sidecarReady: boolean
}

export function UploadPage({ onAnalyze, sidecarReady }: UploadPageProps) {
  const [audioPath, setAudioPath] = useState('')
  const [audioName, setAudioName] = useState('')
  const [lyricsPath, setLyricsPath] = useState('')
  const [lyricsName, setLyricsName] = useState('')
  const [isDragging, setIsDragging] = useState(false)

  const selectAudio = useCallback(async () => {
    const selected = await open({
      multiple: false,
      filters: [{
        name: 'Audio',
        extensions: ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'],
      }],
    })
    if (selected) {
      const path = typeof selected === 'string' ? selected : selected
      setAudioPath(path)
      setAudioName(path.split('/').pop()?.split('\\').pop() || path)
    }
  }, [])

  const selectLyrics = useCallback(async () => {
    const selected = await open({
      multiple: false,
      filters: [{
        name: 'Lyrics',
        extensions: ['lrc', 'qrc', 'krc', 'txt'],
      }],
    })
    if (selected) {
      const path = typeof selected === 'string' ? selected : selected
      setLyricsPath(path)
      setLyricsName(path.split('/').pop()?.split('\\').pop() || path)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    // Tauri supports drag-and-drop file paths
    const files = Array.from(e.dataTransfer.files)
    for (const file of files) {
      const ext = file.name.split('.').pop()?.toLowerCase() || ''
      // @ts-expect-error Tauri exposes .path on dropped files
      const filePath: string = file.path || file.name
      if (['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'].includes(ext)) {
        setAudioPath(filePath)
        setAudioName(file.name)
      } else if (['lrc', 'qrc', 'krc', 'txt'].includes(ext)) {
        setLyricsPath(filePath)
        setLyricsName(file.name)
      }
    }
  }, [])

  const handleStart = () => {
    if (!audioPath) return
    onAnalyze(audioPath, lyricsPath || undefined)
  }

  return (
    <div className="min-h-screen bg-[#f8f8f8] flex items-center justify-center p-6">
      {/* macOS titlebar drag region */}
      <div
        className="fixed top-0 left-0 right-0 h-[52px] z-50"
        data-tauri-drag-region
      />

      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-[20px] font-semibold text-neutral-700 tracking-tight">
            LyricFlow
          </h1>
          <p className="text-[11px] text-neutral-400 mt-1">
            英语歌曲发音智能标注
          </p>
        </div>

        <div className="bg-white rounded-3xl p-6 space-y-4">
          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={selectAudio}
            className={`
              rounded-2xl p-8 text-center cursor-pointer transition-colors
              ${isDragging ? 'bg-[#EFF6FF]' : 'bg-neutral-100 hover:bg-neutral-50'}
            `}
          >
            {audioPath ? (
              <div>
                <div className="w-10 h-10 rounded-xl bg-[#EFF6FF] flex items-center justify-center mx-auto mb-3">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
                    <path d="M9 18V5l12-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="18" cy="16" r="3" />
                  </svg>
                </div>
                <p className="text-[11px] font-medium text-neutral-700">{audioName}</p>
                <p className="text-[9px] text-neutral-400 mt-1">
                  系统会自动检测内封歌词
                </p>
              </div>
            ) : (
              <div>
                <div className="w-10 h-10 rounded-xl bg-neutral-200 flex items-center justify-center mx-auto mb-3">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                </div>
                <p className="text-[11px] text-neutral-500">
                  拖拽音频文件到此处，或点击选择
                </p>
                <p className="text-[9px] text-neutral-400 mt-1">
                  支持 MP3, WAV, FLAC, AAC, OGG, M4A
                </p>
              </div>
            )}
          </div>

          {/* Lyrics file (optional) */}
          <div
            onClick={selectLyrics}
            className="rounded-xl bg-neutral-100 hover:bg-neutral-50 p-3 cursor-pointer transition-colors"
          >
            <div className="flex items-center gap-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <span className="text-[10px] text-neutral-500">
                {lyricsName || '手动添加歌词文件（可选，系统优先使用内封歌词）'}
              </span>
              {lyricsPath && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setLyricsPath('')
                    setLyricsName('')
                  }}
                  className="ml-auto text-[9px] text-neutral-400 hover:text-neutral-600"
                >
                  移除
                </button>
              )}
            </div>
          </div>

          {/* Sidecar status */}
          {!sidecarReady && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-100">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-[9px] text-neutral-400">正在初始化分析引擎...</span>
            </div>
          )}

          {/* Start button */}
          <button
            onClick={handleStart}
            disabled={!audioPath || !sidecarReady}
            className={`
              w-full py-3 rounded-xl text-[11px] font-medium transition-colors
              ${audioPath && sidecarReady
                ? 'bg-neutral-800 text-white hover:bg-neutral-700'
                : 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
              }
            `}
          >
            开始分析
          </button>
        </div>
      </div>
    </div>
  )
}
