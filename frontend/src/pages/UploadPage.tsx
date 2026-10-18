import { useCallback, useEffect, useState } from 'react'
import { isTauri } from '@tauri-apps/api/core'
import { getCurrentWebview } from '@tauri-apps/api/webview'
import { open } from '@tauri-apps/plugin-dialog'
import { readTextFile } from '@tauri-apps/plugin-fs'
import {
  AudioLines,
  Check,
  ChevronRight,
  CloudCog,
  FileText,
  FolderOpen,
  LoaderCircle,
  Music2,
  ShieldCheck,
  Upload,
  X,
} from 'lucide-react'
import type { ProviderCapabilities } from '../hooks/useSidecar'
import type { SongResult } from '../types/lyrics'

interface UploadPageProps {
  onAnalyze: (
    audioPath: string,
    lyricsPath?: string,
    title?: string,
    artist?: string,
    skipEmbedded?: boolean,
    cloudEnabled?: boolean,
  ) => void
  sidecarReady: boolean
  capabilities: ProviderCapabilities
  onOpenResult: (result: SongResult) => void
}

const AUDIO_EXTENSIONS = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a']
const LYRIC_EXTENSIONS = ['lrc', 'qrc', 'krc', 'txt']

export function UploadPage({ onAnalyze, sidecarReady, capabilities, onOpenResult }: UploadPageProps) {
  const [audioPath, setAudioPath] = useState('')
  const [audioName, setAudioName] = useState('')
  const [lyricsPath, setLyricsPath] = useState('')
  const [lyricsName, setLyricsName] = useState('')
  const [title, setTitle] = useState('')
  const [artist, setArtist] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [skipEmbedded, setSkipEmbedded] = useState(false)
  const [cloudEnabled, setCloudEnabled] = useState(false)
  const [resultError, setResultError] = useState('')

  const cloudReady = capabilities.cloudAsrConfigured && capabilities.audioCoachConfigured

  const applyDroppedPaths = useCallback((paths: string[]) => {
    for (const path of paths) {
      const name = fileNameFromPath(path)
      const extension = name.split('.').pop()?.toLowerCase() || ''
      if (AUDIO_EXTENSIONS.includes(extension)) {
        setAudioPath(path)
        setAudioName(name)
      } else if (LYRIC_EXTENSIONS.includes(extension)) {
        setLyricsPath(path)
        setLyricsName(name)
      }
    }
  }, [])

  useEffect(() => {
    if (!isTauri()) return
    let disposed = false
    let unlisten: (() => void) | undefined

    void getCurrentWebview().onDragDropEvent(({ payload }) => {
      if (payload.type === 'enter' || payload.type === 'over') {
        setIsDragging(true)
      } else if (payload.type === 'drop') {
        setIsDragging(false)
        applyDroppedPaths(payload.paths)
      } else if (payload.type === 'leave') {
        setIsDragging(false)
      }
    }).then((stopListening) => {
      if (disposed) stopListening()
      else unlisten = stopListening
    })

    return () => {
      disposed = true
      unlisten?.()
    }
  }, [applyDroppedPaths])

  const selectAudio = useCallback(async () => {
    const selected = await open({
      multiple: false,
      filters: [{ name: 'Audio', extensions: AUDIO_EXTENSIONS }],
    })
    if (typeof selected === 'string') {
      setAudioPath(selected)
      setAudioName(fileNameFromPath(selected))
    }
  }, [])

  const selectLyrics = useCallback(async () => {
    const selected = await open({
      multiple: false,
      filters: [{ name: 'Lyrics', extensions: LYRIC_EXTENSIONS }],
    })
    if (typeof selected === 'string') {
      setLyricsPath(selected)
      setLyricsName(fileNameFromPath(selected))
    }
  }, [])

  const openResult = useCallback(async () => {
    const selected = await open({
      multiple: false,
      filters: [{ name: 'LyricFlow Result', extensions: ['json'] }],
    })
    if (typeof selected !== 'string') return
    try {
      const parsed = JSON.parse(await readTextFile(selected)) as Partial<SongResult>
      if (!parsed.song_id || !Array.isArray(parsed.lines) || !parsed.stats) {
        throw new Error('invalid result')
      }
      setResultError('')
      onOpenResult(parsed as SongResult)
    } catch {
      setResultError('这不是有效的 LyricFlow 分析结果。')
    }
  }, [onOpenResult])

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    setIsDragging(false)
    applyDroppedPaths(Array.from(event.dataTransfer.files).map((file) => {
      const fileWithPath = file as File & { path?: string }
      return fileWithPath.path || file.name
    }))
  }, [applyDroppedPaths])

  const handleStart = () => {
    if (!audioPath || !sidecarReady) return
    onAnalyze(
      audioPath,
      lyricsPath || undefined,
      title,
      artist,
      skipEmbedded,
      cloudEnabled && cloudReady,
    )
  }

  return (
    <div className="import-page">
      <div className="titlebar-drag-region" data-tauri-drag-region />

      <header className="import-brand" aria-label="LyricFlow">
        <span className="brand-mark"><AudioLines aria-hidden="true" size={18} /></span>
        <span>LyricFlow</span>
        <span className="brand-caption">Rap 语流教练</span>
      </header>

      <main className="import-main">
        <section className="import-intro">
          <p className="eyebrow">从听不清，到跟得上</p>
          <h1>把最难的 Rap 段，<br />拆成你能唱出的每一拍。</h1>
          <p className="import-description">
            导入一首歌，LyricFlow 会定位 Rap 段，并把真实唱法里的连读、弱读、吞音、重音和换气逐句标出来。
          </p>
          <ol className="import-promises" aria-label="分析流程">
            <li><span>01</span>找到 Rap 段与逐词时间</li>
            <li><span>02</span>听证据，而不是只套发音规则</li>
            <li><span>03</span>慢放、循环、录音做 A/B 对照</li>
          </ol>
        </section>

        <section className="import-workspace" aria-labelledby="import-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">新练习</p>
              <h2 id="import-title">选择你的歌曲</h2>
            </div>
            <span className={`engine-state ${sidecarReady ? 'is-ready' : ''}`}>
              {sidecarReady ? <Check aria-hidden="true" size={13} /> : <LoaderCircle aria-hidden="true" size={13} />}
              {sidecarReady ? '引擎就绪' : '正在启动'}
            </span>
          </div>

          <button
            type="button"
            className={`audio-dropzone ${isDragging ? 'is-dragging' : ''} ${audioPath ? 'has-file' : ''}`}
            onDragOver={(event) => { event.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={selectAudio}
          >
            <span className="dropzone-icon">
              {audioPath ? <Music2 aria-hidden="true" size={22} /> : <Upload aria-hidden="true" size={22} />}
            </span>
            <span className="dropzone-copy">
              <strong>{audioName || '拖入音频，或点击选择'}</strong>
              <span>{audioPath ? '点击可更换文件' : 'MP3、WAV、FLAC、AAC、OGG、M4A · 最大 50MB'}</span>
            </span>
            {audioPath && <Check aria-hidden="true" className="dropzone-check" size={18} />}
          </button>

          <div className="lyrics-row">
            <button type="button" className="lyrics-picker" onClick={selectLyrics}>
              <FileText aria-hidden="true" size={17} />
              <span>
                <strong>{lyricsName || '添加歌词文件'}</strong>
                <small>{lyricsName ? '已优先使用这份歌词' : '可选 · 支持 LRC、QRC、KRC、TXT'}</small>
              </span>
              {!lyricsName && <ChevronRight aria-hidden="true" size={16} />}
            </button>
            {lyricsPath && (
              <button
                type="button"
                className="icon-button"
                aria-label="移除歌词文件"
                onClick={() => { setLyricsPath(''); setLyricsName('') }}
              >
                <X aria-hidden="true" size={16} />
              </button>
            )}
          </div>

          <div className="track-metadata" aria-label="歌曲信息">
            <label>
              <span>歌曲名 <small>可选</small></span>
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="例如 Baby"
                autoComplete="off"
              />
            </label>
            <label>
              <span>歌手 <small>可选</small></span>
              <input
                value={artist}
                onChange={(event) => setArtist(event.target.value)}
                placeholder="例如 Justin Bieber"
                autoComplete="off"
              />
            </label>
          </div>

          <div className="analysis-options">
            <button
              type="button"
              className={`analysis-option ${cloudEnabled ? 'is-selected' : ''}`}
              role="switch"
              aria-checked={cloudEnabled}
              disabled={!cloudReady}
              onClick={() => setCloudEnabled((value) => !value)}
            >
              <span className="option-icon"><CloudCog aria-hidden="true" size={18} /></span>
              <span className="option-copy">
                <strong>智能云分析 <em>推荐</em></strong>
                <small>
                  {cloudReady
                    ? '整曲发送至火山 ASR；仅 Rap 小片段发送至千问音频模型。'
                    : '尚未检测到完整服务配置，将使用本地规则分析。'}
                </small>
              </span>
              <span className="switch-track" aria-hidden="true"><span /></span>
            </button>

            <button
              type="button"
              className={`compact-option ${skipEmbedded ? 'is-selected' : ''}`}
              role="switch"
              aria-checked={skipEmbedded}
              onClick={() => setSkipEmbedded((value) => !value)}
            >
              <span>忽略音频内封歌词</span>
              <span className="switch-track" aria-hidden="true"><span /></span>
            </button>
          </div>

          <div className="privacy-note">
            <ShieldCheck aria-hidden="true" size={15} />
            <span>本地模式不会上传文件；云分析只有在你打开开关后才会发送。</span>
          </div>

          <button
            type="button"
            className="button button-primary analyze-button"
            disabled={!audioPath || !sidecarReady}
            onClick={handleStart}
          >
            开始拆解这首歌
            <ChevronRight aria-hidden="true" size={17} />
          </button>
          <button type="button" className="open-result-button" onClick={openResult}>
            <FolderOpen aria-hidden="true" size={15} />打开已有拆解结果
          </button>
          {resultError && <p className="result-file-error" role="alert">{resultError}</p>}
        </section>
      </main>
    </div>
  )
}

function fileNameFromPath(path: string) {
  return path.split('/').pop()?.split('\\').pop() || path
}
