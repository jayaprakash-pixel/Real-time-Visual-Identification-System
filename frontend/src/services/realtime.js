/**
 * Real-time Alerts Service
 *
 * Provides a live subscription channel for detection alerts emitted
 * by the AI Vision surveillance module.
 *
 * Supported transport:
 *   - WebSocket (default)
 *   - Server-Sent Events (SSE fallback pattern documented below)
 *   - In-memory mock simulation (emits realistic detection every ~20 seconds)
 *
 * Expected alert payload from backend:
 *   {
 *     id: string,
 *     personId: string,
 *     personName: string,
 *     detectedAt: string (ISO),
 *     confidence: number (0-100),
 *     cameraSource: string,
 *     sceneImageUrl: string,
 *     thumbnailUrl?: string
 *   }
 */

import { USE_MOCK, getAuthToken } from './apiClient'
import { MOCK_PERSONS, CAMERA_SOURCES, generateMockSceneSvg } from './detectionsApi'

export const REALTIME_URL = import.meta.env.VITE_REALTIME_URL || ''

/**
 * Subscribe to real-time detection alerts with auto-reconnect.
 *
 * @param {(alert: Object) => void} onAlert - Callback invoked on each incoming detection
 * @param {(status: "connected" | "reconnecting" | "disconnected") => void} [onStatusChange] - Status callback
 * @returns {() => void} unsubscribe function
 */
export function subscribeToAlerts(onAlert, onStatusChange) {
  if (USE_MOCK) {
    if (typeof onStatusChange === 'function') {
      onStatusChange('connected')
    }

    let mockCounter = 0

    // Emit a fake detection match every ~20 seconds
    const intervalId = setInterval(() => {
      mockCounter++
      const person = MOCK_PERSONS[mockCounter % MOCK_PERSONS.length]
      const camera = CAMERA_SOURCES[(mockCounter * 3) % CAMERA_SOURCES.length]
      const now = new Date()
      const iso = now.toISOString()
      const readable = iso.replace('T', ' ').substring(0, 16)
      const confidence = Math.min(99, 78 + ((mockCounter * 7) % 21))

      const alertPayload = {
        id: `live-alert-${Date.now()}`,
        personId: person.id,
        personName: person.name,
        detectedAt: iso,
        confidence,
        cameraSource: camera,
        sceneImageUrl: generateMockSceneSvg(person.name, confidence, camera, readable),
        thumbnailUrl: generateMockSceneSvg(person.name, confidence, camera, readable)
      }

      if (typeof onAlert === 'function') {
        onAlert(alertPayload)
      }
    }, 20000)

    return () => {
      clearInterval(intervalId)
      if (typeof onStatusChange === 'function') {
        onStatusChange('disconnected')
      }
    }
  }

  // ───────────────────────────────────────────────────────────────────
  // REAL BACKEND CONNECTION (WebSocket with Auto-Reconnect)
  //
  // NOTE ON SWITCHING TO SERVER-SENT EVENTS (SSE):
  // If your backend serves SSE instead of WebSockets, replace this section:
  //   const sseUrl = `${REALTIME_URL}?token=${encodeURIComponent(getAuthToken())}`
  //   const eventSource = new EventSource(sseUrl)
  //   eventSource.onopen = () => onStatusChange?.('connected')
  //   eventSource.onmessage = (e) => onAlert(JSON.parse(e.data))
  //   eventSource.onerror = () => onStatusChange?.('reconnecting')
  //   return () => eventSource.close()
  // ───────────────────────────────────────────────────────────────────

  // TODO: connect backend endpoint
  let ws = null
  let isClosedManually = false
  let reconnectTimeout = null
  let backoffDelay = 1000 // starts at 1s, doubles up to 16s

  function connect() {
    if (isClosedManually) return

    try {
      const token = getAuthToken()
      const url = token
        ? `${REALTIME_URL}${REALTIME_URL.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`
        : REALTIME_URL

      ws = new WebSocket(url)

      ws.onopen = () => {
        backoffDelay = 1000
        if (typeof onStatusChange === 'function') {
          onStatusChange('connected')
        }
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data && typeof onAlert === 'function') {
            onAlert(data)
          }
        } catch (err) {
          console.warn('[Realtime] Failed to parse alert message:', err)
        }
      }

      ws.onerror = () => {
        if (typeof onStatusChange === 'function') {
          onStatusChange('reconnecting')
        }
      }

      ws.onclose = () => {
        if (!isClosedManually) {
          if (typeof onStatusChange === 'function') {
            onStatusChange('reconnecting')
          }
          reconnectTimeout = setTimeout(() => {
            backoffDelay = Math.min(16000, backoffDelay * 2)
            connect()
          }, backoffDelay)
        } else {
          if (typeof onStatusChange === 'function') {
            onStatusChange('disconnected')
          }
        }
      }
    } catch (err) {
      console.warn('[Realtime] WebSocket connection error:', err)
      if (typeof onStatusChange === 'function') {
        onStatusChange('reconnecting')
      }
    }
  }

  connect()

  return () => {
    isClosedManually = true
    if (reconnectTimeout) clearTimeout(reconnectTimeout)
    if (ws) {
      ws.close()
      ws = null
    }
    if (typeof onStatusChange === 'function') {
      onStatusChange('disconnected')
    }
  }
}
