import { useState, useRef, useCallback, useEffect } from 'react'
import { Command } from '@tauri-apps/plugin-shell'
import type { SongResult } from '../types/lyrics'

export type SidecarStatus =
  | 'idle'
  | 'starting'
  | 'ready'
  | 'analyzing'
  | 'done'
  | 'error'

export interface ProgressInfo {
  stage: string
  percent: number
  message: string
}

interface SidecarMessage {
  type: 'ready' | 'pong' | 'progress' | 'result' | 'error'
  version?: string
  stage?: string
  percent?: number
  message?: string
  data?: SongResult
  traceback?: string
}

export function useSidecar() {
  const [status, setStatus] = useState<SidecarStatus>('idle')
  const [progress, setProgress] = useState<ProgressInfo>({ stage: '', percent: 0, message: '' })
  const [result, setResult] = useState<SongResult | null>(null)
  const [error, setError] = useState<string>('')
  const childRef = useRef<Awaited<ReturnType<ReturnType<typeof Command.sidecar>['spawn']>> | null>(null)
  const resolveReady = useRef<(() => void) | null>(null)

  const startSidecar = useCallback(async () => {
    if (childRef.current) return // Already running

    setStatus('starting')

    try {
      const command = Command.sidecar('binaries/lyricflow-sidecar')

      command.stdout.on('data', (line: string) => {
        if (!line.trim()) return
        try {
          const msg: SidecarMessage = JSON.parse(line)

          switch (msg.type) {
            case 'ready':
              setStatus('ready')
              resolveReady.current?.()
              break

            case 'pong':
              break

            case 'progress':
              setProgress({
                stage: msg.stage || '',
                percent: msg.percent || 0,
                message: msg.message || '',
              })
              break

            case 'result':
              if (msg.data) {
                setResult(msg.data)
                setStatus('done')
              }
              break

            case 'error':
              setError(msg.message || 'Unknown error')
              setStatus('error')
              break
          }
        } catch {
          // Non-JSON output, ignore
        }
      })

      command.stderr.on('data', (line: string) => {
        console.error('[sidecar stderr]', line)
      })

      command.on('close', () => {
        childRef.current = null
        if (status === 'analyzing') {
          setStatus('error')
          setError('Sidecar process exited unexpectedly')
        }
      })

      const child = await command.spawn()
      childRef.current = child

      // Wait for ready signal
      await new Promise<void>((resolve) => {
        resolveReady.current = resolve
        // Timeout after 10s
        setTimeout(() => {
          if (resolveReady.current === resolve) {
            resolve()
            setStatus('ready')
          }
        }, 10000)
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start sidecar')
      setStatus('error')
    }
  }, [])

  const analyze = useCallback(async (audioPath: string, lyricsPath?: string, dialect = 'en-us') => {
    if (!childRef.current) {
      await startSidecar()
    }

    const child = childRef.current
    if (!child) {
      setError('Sidecar not available')
      setStatus('error')
      return
    }

    setStatus('analyzing')
    setProgress({ stage: '', percent: 0, message: 'Starting analysis...' })
    setResult(null)
    setError('')

    const msg = JSON.stringify({
      type: 'analyze',
      audioPath,
      lyricsPath: lyricsPath || null,
      dialect,
    }) + '\n'

    await child.write(msg)
  }, [startSidecar])

  const stop = useCallback(async () => {
    if (childRef.current) {
      try {
        await childRef.current.write(JSON.stringify({ type: 'quit' }) + '\n')
      } catch {
        // Process may already be dead
      }
      await childRef.current.kill()
      childRef.current = null
    }
    setStatus('idle')
  }, [])

  const reset = useCallback(() => {
    setStatus('ready')
    setProgress({ stage: '', percent: 0, message: '' })
    setResult(null)
    setError('')
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (childRef.current) {
        childRef.current.kill().catch(() => {})
      }
    }
  }, [])

  return { status, progress, result, error, startSidecar, analyze, stop, reset }
}
