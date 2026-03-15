import { useState, useCallback } from 'react'
import { UploadPage } from './pages/UploadPage'
import { ProcessingPage } from './pages/ProcessingPage'
import { ResultPage } from './pages/ResultPage'
import type { SongResult } from './types/lyrics'

type AppState =
  | { page: 'upload' }
  | { page: 'processing'; taskId: string }
  | { page: 'result'; result: SongResult }
  | { page: 'error'; message: string }

function App() {
  const [state, setState] = useState<AppState>({ page: 'upload' })

  const handleTaskCreated = useCallback((taskId: string) => {
    setState({ page: 'processing', taskId })
  }, [])

  const handleProcessingComplete = useCallback(async (songId: string) => {
    try {
      const resp = await fetch(`/api/v1/songs/${songId}/lyrics`)
      if (!resp.ok) throw new Error('Failed to load results')
      const result: SongResult = await resp.json()
      setState({ page: 'result', result })
    } catch (err) {
      setState({
        page: 'error',
        message: err instanceof Error ? err.message : 'Failed to load results',
      })
    }
  }, [])

  const handleError = useCallback((message: string) => {
    setState({ page: 'error', message })
  }, [])

  const handleBack = useCallback(() => {
    setState({ page: 'upload' })
  }, [])

  switch (state.page) {
    case 'upload':
      return <UploadPage onTaskCreated={handleTaskCreated} />

    case 'processing':
      return (
        <ProcessingPage
          taskId={state.taskId}
          onComplete={handleProcessingComplete}
          onError={handleError}
        />
      )

    case 'result':
      return <ResultPage result={state.result} onBack={handleBack} />

    case 'error':
      return (
        <div className="min-h-screen bg-[#f8f8f8] flex items-center justify-center p-6">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-[13px] font-medium text-neutral-700 mb-2">
              处理出错
            </h2>
            <p className="text-[10px] text-neutral-500 mb-4">{state.message}</p>
            <button
              onClick={handleBack}
              className="px-6 py-2.5 rounded-xl bg-neutral-800 text-white text-[10px] font-medium hover:bg-neutral-700 transition-colors"
            >
              返回重试
            </button>
          </div>
        </div>
      )
  }
}

export default App
