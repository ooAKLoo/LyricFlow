import { useEffect } from 'react'
import { UploadPage } from './pages/UploadPage'
import { ProcessingPage } from './pages/ProcessingPage'
import { ResultPage } from './pages/ResultPage'
import { useSidecar } from './hooks/useSidecar'

function App() {
  const { status, progress, result, error, startSidecar, analyze, reset } = useSidecar()

  // Start sidecar on mount
  useEffect(() => {
    startSidecar()
  }, [startSidecar])

  const handleAnalyze = (audioPath: string, lyricsPath?: string) => {
    analyze(audioPath, lyricsPath)
  }

  const handleBack = () => {
    reset()
  }

  // Show result page
  if (status === 'done' && result) {
    return <ResultPage result={result} onBack={handleBack} />
  }

  // Show processing page
  if (status === 'analyzing') {
    return <ProcessingPage progress={progress} />
  }

  // Show error
  if (status === 'error') {
    return (
      <div className="min-h-screen bg-[#f8f8f8] flex items-center justify-center p-6">
        <div className="bg-white rounded-3xl p-8 max-w-md w-full text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-[13px] font-medium text-neutral-700 mb-2">
            处理出错
          </h2>
          <p className="text-[10px] text-neutral-500 mb-4">{error}</p>
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

  // Upload page (idle, starting, or ready)
  return (
    <UploadPage
      onAnalyze={handleAnalyze}
      sidecarReady={status === 'ready'}
    />
  )
}

export default App
