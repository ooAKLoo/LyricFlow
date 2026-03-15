import { useState, useRef, useCallback } from 'react'

interface UploadPageProps {
  onTaskCreated: (taskId: string) => void
}

export function UploadPage({ onTaskCreated }: UploadPageProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [title, setTitle] = useState('')
  const [artist, setArtist] = useState('')
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [lyricsFile, setLyricsFile] = useState<File | null>(null)
  const [error, setError] = useState('')

  const audioInputRef = useRef<HTMLInputElement>(null)
  const lyricsInputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    for (const file of files) {
      const ext = file.name.split('.').pop()?.toLowerCase() || ''
      if (['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'].includes(ext)) {
        setAudioFile(file)
        // Try to extract title/artist from filename
        const name = file.name.replace(/\.[^.]+$/, '')
        if (name.includes(' - ')) {
          const [a, t] = name.split(' - ')
          setArtist(a.trim())
          setTitle(t.trim())
        } else {
          setTitle(name)
        }
      } else if (['lrc', 'qrc', 'krc', 'txt'].includes(ext)) {
        setLyricsFile(file)
      }
    }
  }, [])

  const handleUpload = async () => {
    if (!audioFile) {
      setError('Please select an audio file')
      return
    }

    setIsUploading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('audio', audioFile)
      if (lyricsFile) formData.append('lyrics', lyricsFile)
      if (title) formData.append('title', title)
      if (artist) formData.append('artist', artist)
      formData.append('dialect', 'en-us')

      const resp = await fetch('/api/v1/songs/upload', {
        method: 'POST',
        body: formData,
      })

      if (!resp.ok) {
        const data = await resp.json()
        throw new Error(data.detail || 'Upload failed')
      }

      const data = await resp.json()
      onTaskCreated(data.task_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f8f8f8] flex items-center justify-center p-6">
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
            onClick={() => audioInputRef.current?.click()}
            className={`
              rounded-2xl p-8 text-center cursor-pointer transition-colors
              ${isDragging ? 'bg-[#EFF6FF]' : 'bg-neutral-100 hover:bg-neutral-50'}
            `}
          >
            <input
              ref={audioInputRef}
              type="file"
              accept=".mp3,.wav,.flac,.aac,.ogg,.m4a"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) {
                  setAudioFile(file)
                  const name = file.name.replace(/\.[^.]+$/, '')
                  if (name.includes(' - ')) {
                    const [a, t] = name.split(' - ')
                    setArtist(a.trim())
                    setTitle(t.trim())
                  } else if (!title) {
                    setTitle(name)
                  }
                }
              }}
            />

            {audioFile ? (
              <div>
                <div className="w-10 h-10 rounded-xl bg-[#EFF6FF] flex items-center justify-center mx-auto mb-3">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2">
                    <path d="M9 18V5l12-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="18" cy="16" r="3" />
                  </svg>
                </div>
                <p className="text-[11px] font-medium text-neutral-700">{audioFile.name}</p>
                <p className="text-[9px] text-neutral-400 mt-1">
                  {(audioFile.size / 1024 / 1024).toFixed(1)} MB · 系统会自动检测内封歌词
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
                  支持 MP3, WAV, FLAC, AAC, OGG (最大 50MB)
                </p>
              </div>
            )}
          </div>

          {/* Lyrics file (optional) */}
          <div
            onClick={() => lyricsInputRef.current?.click()}
            className="rounded-xl bg-neutral-100 hover:bg-neutral-50 p-3 cursor-pointer transition-colors"
          >
            <input
              ref={lyricsInputRef}
              type="file"
              accept=".lrc,.qrc,.krc,.txt"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) setLyricsFile(file)
              }}
            />
            <div className="flex items-center gap-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <span className="text-[10px] text-neutral-500">
                {lyricsFile ? lyricsFile.name : '手动添加歌词文件（可选，系统优先使用内封歌词）'}
              </span>
            </div>
          </div>

          {/* Song info */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[9px] font-medium text-neutral-400 uppercase tracking-wide mb-1 block">
                TITLE
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Song title"
                className="w-full bg-neutral-100 rounded-lg px-3 py-2 text-[11px] text-neutral-700 placeholder:text-neutral-300 outline-none focus:bg-neutral-50"
              />
            </div>
            <div>
              <label className="text-[9px] font-medium text-neutral-400 uppercase tracking-wide mb-1 block">
                ARTIST
              </label>
              <input
                type="text"
                value={artist}
                onChange={(e) => setArtist(e.target.value)}
                placeholder="Artist name"
                className="w-full bg-neutral-100 rounded-lg px-3 py-2 text-[11px] text-neutral-700 placeholder:text-neutral-300 outline-none focus:bg-neutral-50"
              />
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-[10px] text-red-500">{error}</p>
          )}

          {/* Upload button */}
          <button
            onClick={handleUpload}
            disabled={!audioFile || isUploading}
            className={`
              w-full py-3 rounded-xl text-[11px] font-medium transition-colors
              ${audioFile && !isUploading
                ? 'bg-neutral-800 text-white hover:bg-neutral-700'
                : 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
              }
            `}
          >
            {isUploading ? '上传中...' : '开始分析'}
          </button>
        </div>
      </div>
    </div>
  )
}
