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

export interface ProviderCapabilities {
  cloudAsrConfigured: boolean
  audioCoachConfigured: boolean
}

interface SidecarMessage {
  type: 'ready' | 'pong' | 'progress' | 'result' | 'error'
  version?: string
  stage?: string
  percent?: number
  message?: string
  data?: SongResult
  traceback?: string
  capabilities?: ProviderCapabilities
}

export function useSidecar() {
  const [status, setStatus] = useState<SidecarStatus>('idle')
  const [progress, setProgress] = useState<ProgressInfo>({ stage: '', percent: 0, message: '' })
  const [result, setResult] = useState<SongResult | null>(null)
  const [error, setError] = useState<string>('')
  const [capabilities, setCapabilities] = useState<ProviderCapabilities>({
    cloudAsrConfigured: false,
    audioCoachConfigured: false,
  })
  const childRef = useRef<Awaited<ReturnType<ReturnType<typeof Command.sidecar>['spawn']>> | null>(null)
  const resolveReady = useRef<(() => void) | null>(null)
  const rejectReady = useRef<((error: Error) => void) | null>(null)
  const statusRef = useRef<SidecarStatus>(status)

  const updateStatus = useCallback((next: SidecarStatus) => {
    statusRef.current = next
    setStatus(next)
  }, [])

  useEffect(() => {
    statusRef.current = status
  }, [status])

  const startSidecar = useCallback(async () => {
    if (childRef.current) return // Already running

    updateStatus('starting')
    let readyTimeout: number | undefined

    try {
      const command = Command.sidecar('binaries/lyricflow-sidecar')
      const waitForReady = new Promise<void>((resolve, reject) => {
        const finishReady = () => {
          if (readyTimeout !== undefined) window.clearTimeout(readyTimeout)
          if (resolveReady.current === finishReady) resolveReady.current = null
          rejectReady.current = null
          resolve()
        }
        const failReady = (error: Error) => {
          if (readyTimeout !== undefined) window.clearTimeout(readyTimeout)
          resolveReady.current = null
          if (rejectReady.current === failReady) rejectReady.current = null
          reject(error)
        }
        resolveReady.current = finishReady
        rejectReady.current = failReady
        readyTimeout = window.setTimeout(() => {
          if (resolveReady.current !== finishReady) return
          failReady(new Error('Sidecar 启动超时'))
        }, 10000)
      })

      command.stdout.on('data', (line: string) => {
        if (!line.trim()) return
        try {
          const msg: SidecarMessage = JSON.parse(line)

          switch (msg.type) {
            case 'ready':
              if (msg.capabilities) setCapabilities(msg.capabilities)
              updateStatus('ready')
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
                updateStatus('done')
              }
              break

            case 'error':
              if (rejectReady.current) {
                rejectReady.current(new Error(msg.message || 'Sidecar 启动失败'))
              } else {
                setError(msg.message || 'Unknown error')
                updateStatus('error')
              }
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
        if (statusRef.current === 'analyzing') {
          updateStatus('error')
          setError('Sidecar process exited unexpectedly')
        }
      })

      const child = await command.spawn()
      childRef.current = child
      await waitForReady
    } catch (err) {
      if (readyTimeout !== undefined) window.clearTimeout(readyTimeout)
      resolveReady.current = null
      rejectReady.current = null
      if (childRef.current) {
        await childRef.current.kill().catch(() => {})
        childRef.current = null
      }
      setError(err instanceof Error ? err.message : 'Failed to start sidecar')
      updateStatus('error')
    }
  }, [updateStatus])

  const analyze = useCallback(async (
    audioPath: string,
    lyricsPath?: string,
    title = '',
    artist = '',
    dialect = 'en-us',
    skipEmbedded = false,
    cloudEnabled = false,
  ) => {
    if (!childRef.current) {
      await startSidecar()
    }

    const child = childRef.current
    if (!child) {
      setError('Sidecar not available')
      updateStatus('error')
      return
    }

    updateStatus('analyzing')
    setProgress({ stage: '', percent: 0, message: 'Starting analysis...' })
    setResult(null)
    setError('')

    const msg = JSON.stringify({
      type: 'analyze',
      audioPath,
      lyricsPath: lyricsPath || null,
      title: title.trim(),
      artist: artist.trim(),
      skipEmbedded,
      cloudEnabled,
      dialect,
    }) + '\n'

    await child.write(msg)
  }, [startSidecar, updateStatus])

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
    updateStatus('idle')
  }, [updateStatus])

  const reset = useCallback(() => {
    updateStatus('ready')
    setProgress({ stage: '', percent: 0, message: '' })
    setResult(null)
    setError('')
  }, [updateStatus])

  const loadResult = useCallback((loadedResult: SongResult) => {
    setResult(loadedResult)
    setError('')
    updateStatus('done')
  }, [updateStatus])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (childRef.current) {
        childRef.current.kill().catch(() => {})
      }
    }
  }, [])

  return { status, progress, result, error, capabilities, startSidecar, analyze, stop, reset, loadResult }
}
