/**
 * System API Service
 *
 * Provides live surveillance stream URL and monitoring health check.
 *
 * Expected response shape:
 *   GET /system/status
 *   → {
 *       monitoring: "active" | "idle" | "offline",
 *       activeCamera: string | null,
 *       aiService: "up" | "down"
 *     }
 */

import { USE_MOCK, request } from './apiClient'

// Live MJPEG camera feed endpoint from environment
export const STREAM_URL = import.meta.env.VITE_STREAM_URL || ''

/**
 * Fetch current system and surveillance status.
 * @returns {Promise<{ monitoring: "active" | "idle" | "offline", activeCamera: string | null, aiService: "up" | "down" }>}
 */
export async function getSystemStatus() {
  if (USE_MOCK) {
    // Simulate short network latency
    await new Promise((r) => setTimeout(r, 150))
    return {
      monitoring: 'active',
      activeCamera: 'CCTV 01 - North Entrance',
      aiService: 'up'
    }
  }

  // TODO: connect backend endpoint
  return request('/system/status')
}
