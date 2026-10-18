import { useCallback, useEffect, useState } from 'react'
import { resolveResource } from '@tauri-apps/api/path'
import { readTextFile } from '@tauri-apps/plugin-fs'
import { AlertTriangle, AudioLines, RotateCcw } from 'lucide-react'
import { ResultPage } from './pages/ResultPage'
import { demoResult } from './data/demoResult'
import type { SongResult } from './types/lyrics'

type BabyLoadState =
  | { status: 'loading' }
  | { status: 'ready'; result: SongResult }
  | { status: 'error'; message: string }

function App() {
  const demoMode = import.meta.env.DEV && new URLSearchParams(window.location.search).has('demo')
  const [baby, setBaby] = useState<BabyLoadState>({ status: 'loading' })

  const openBaby = useCallback(async () => {
    setBaby({ status: 'loading' })

    try {
      const [resultPath, vocalsPath, originalPath] = await Promise.all([
        resolveResource('baby/result.json'),
        resolveResource('baby/vocals.wav'),
        resolveResource('baby/original.wav'),
      ])
      const parsed = JSON.parse(await readTextFile(resultPath)) as SongResult

      if (!Array.isArray(parsed.lines) || parsed.lines.length === 0) {
        throw new Error('内置拆解结果缺少歌词行')
      }

      setBaby({
        status: 'ready',
        result: {
          ...parsed,
          song_title: 'Baby',
          artist: 'Justin Bieber',
          vocals_path: vocalsPath,
          original_path: originalPath,
        },
      })
    } catch (error) {
      setBaby({
        status: 'error',
        message: error instanceof Error ? error.message : String(error),
      })
    }
  }, [])

  useEffect(() => {
    if (!demoMode) void openBaby()
  }, [demoMode, openBaby])

  if (demoMode) return <ResultPage result={demoResult} autoPlay={false} />

  if (baby.status === 'ready') {
    return <ResultPage result={baby.result} />
  }

  if (baby.status === 'error') {
    return (
      <div className="app-state-page">
        <div className="state-message" role="alert">
          <AlertTriangle aria-hidden="true" size={24} />
          <h2>Baby 没有打开</h2>
          <p>{baby.message}</p>
          <button type="button" onClick={openBaby} className="button button-primary">
            <RotateCcw aria-hidden="true" size={16} />
            重新打开
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="app-state-page" aria-live="polite">
      <div className="state-message baby-loading">
        <span className="brand-mark"><AudioLines aria-hidden="true" size={18} /></span>
        <h2>正在打开 Baby</h2>
        <p>准备 Ludacris 的 Rap 段…</p>
      </div>
    </div>
  )
}

export default App
