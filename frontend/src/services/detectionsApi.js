/**
 * Detections API Service
 *
 * Provides detection query endpoints, counts, recent alerts, and person options.
 *
 * Expected response shape from backend:
 *   GET /detections
 *   → {
 *       items: [
 *         {
 *           id: string,
 *           personId: string,
 *           personName: string,
 *           detectedAt: string (ISO 8601),
 *           confidence: number (0-100),
 *           cameraSource: string,
 *           sceneImageUrl: string,
 *           thumbnailUrl?: string
 *         }
 *       ],
 *       total: number,
 *       page: number,
 *       pageSize: number
 *     }
 *
 *   GET /detections?limit=N&sortBy=detectedAt&sortOrder=desc
 *   → Array<{ id, personName, detectedAt, confidence, cameraSource, sceneImageUrl }>
 *
 *   GET /detections/count
 *   → { count: number }
 *
 *   GET /persons?fields=id,name
 *   → Array<{ id: string, name: string }>
 */

import { USE_MOCK, BASE_URL, request } from './apiClient'

export { USE_MOCK, BASE_URL }

// ── Person options for filters ─────────────────────────────────────
export const MOCK_PERSONS = [
  { id: '1', name: 'Aarav Sharma' },
  { id: '2', name: 'Priya Patel' },
  { id: '3', name: 'Rohan Gupta' },
  { id: '4', name: 'Sneha Reddy' },
  { id: '5', name: 'Vikram Singh' },
  { id: '6', name: 'Kavita Joshi' },
  { id: '7', name: 'Arjun Nair' },
  { id: '8', name: 'Meera Das' }
]

export const CAMERA_SOURCES = [
  'Mobile Stream #1',
  'CCTV 01 - North Entrance',
  'CCTV 02 - Main Concourse',
  'CCTV 03 - South Transit Gate',
  'CCTV 04 - East Platform',
  'Mobile Stream #2'
]

// Generate SVG scene snapshot helper for mock demonstration
export function generateMockSceneSvg(name, confidence, camera, timestamp) {
  const encodedSvg = encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#151221" />
          <stop offset="100%" stop-color="#241c30" />
        </linearGradient>
      </defs>
      <rect width="640" height="360" fill="url(#bg)" />
      <!-- Grid lines -->
      <path d="M 0 90 L 640 90 M 0 180 L 640 180 M 0 270 L 640 270 M 160 0 L 160 360 M 320 0 L 320 360 M 480 0 L 480 360" stroke="#8b5cf6" stroke-opacity="0.12" stroke-width="1" />
      
      <!-- Bounding Box -->
      <rect x="230" y="80" width="180" height="200" fill="none" stroke="#14b8a6" stroke-width="2" stroke-dasharray="8 4" />
      <circle cx="320" cy="140" r="45" fill="#8b5cf6" fill-opacity="0.25" stroke="#ec4899" stroke-width="2" />
      <path d="M 280 230 C 280 190, 360 190, 360 230 Z" fill="#8b5cf6" fill-opacity="0.3" />
      
      <!-- Target corners -->
      <path d="M 220 90 L 220 70 L 240 70" stroke="#14b8a6" stroke-width="3" fill="none" />
      <path d="M 400 70 L 420 70 L 420 90" stroke="#14b8a6" stroke-width="3" fill="none" />
      <path d="M 220 270 L 220 290 L 240 290" stroke="#14b8a6" stroke-width="3" fill="none" />
      <path d="M 400 290 L 420 290 L 420 270" stroke="#14b8a6" stroke-width="3" fill="none" />

      <!-- HUD Tag -->
      <rect x="230" y="52" width="180" height="24" rx="4" fill="#0f0e17" fill-opacity="0.85" stroke="#14b8a6" stroke-width="1"/>
      <text x="238" y="68" fill="#14b8a6" font-family="sans-serif" font-size="12" font-weight="bold">MATCH: ${confidence}%</text>

      <!-- Overlay Footer Info -->
      <rect x="0" y="320" width="640" height="40" fill="#0f0e17" fill-opacity="0.8" />
      <text x="16" y="344" fill="#f1f5f9" font-family="sans-serif" font-size="12" font-weight="600">${camera} | ${name}</text>
      <text x="490" y="344" fill="#94a3b8" font-family="sans-serif" font-size="11">${timestamp}</text>
    </svg>
  `.trim())
  return `data:image/svg+xml;utf8,${encodedSvg}`
}

// ── Generate 48 mock detections spread across the last 30 days ─────
export const MOCK_DETECTIONS = (() => {
  const items = []
  const baseTime = new Date('2026-10-19T18:00:00Z').getTime()

  // Deterministic seed sequence for realistic distribution
  for (let i = 1; i <= 48; i++) {
    const person = MOCK_PERSONS[(i * 3 + 1) % MOCK_PERSONS.length]
    const camera = CAMERA_SOURCES[(i * 2 + 3) % CAMERA_SOURCES.length]

    const hoursAgo = Math.floor((i * 14.5) + (i % 5) * 3)
    const detectedDate = new Date(baseTime - hoursAgo * 3600 * 1000)
    const isoString = detectedDate.toISOString()
    const readableDate = isoString.replace('T', ' ').substring(0, 16)

    const confBase = 72 + ((i * 17) % 27)
    const confidence = Math.min(99, Math.max(71, confBase))

    const hasImage = i % 9 !== 0
    const sceneUrl = hasImage ? generateMockSceneSvg(person.name, confidence, camera, readableDate) : ''

    items.push({
      id: `det-${1000 + i}`,
      personId: person.id,
      personName: person.name,
      detectedAt: isoString,
      confidence,
      cameraSource: camera,
      sceneImageUrl: sceneUrl,
      thumbnailUrl: sceneUrl
    })
  }

  return items.sort((a, b) => new Date(b.detectedAt) - new Date(a.detectedAt))
})()

// ── Internal mock query evaluator ──────────────────────────────────
function filterAndSortMock(params = {}) {
  let list = [...MOCK_DETECTIONS]

  if (params.person && params.person.trim() !== '') {
    const p = params.person.trim().toLowerCase()
    list = list.filter(
      (item) => item.personId === params.person || item.personName.toLowerCase().includes(p)
    )
  }

  if (params.dateFrom && params.dateFrom.trim() !== '') {
    const fromTime = new Date(params.dateFrom + 'T00:00:00').getTime()
    list = list.filter((item) => new Date(item.detectedAt).getTime() >= fromTime)
  }

  if (params.dateTo && params.dateTo.trim() !== '') {
    const toTime = new Date(params.dateTo + 'T23:59:59.999').getTime()
    list = list.filter((item) => new Date(item.detectedAt).getTime() <= toTime)
  }

  if (params.confidenceMin != null && params.confidenceMin !== '') {
    const min = Number(params.confidenceMin)
    list = list.filter((item) => item.confidence >= min)
  }

  if (params.confidenceMax != null && params.confidenceMax !== '') {
    const max = Number(params.confidenceMax)
    list = list.filter((item) => item.confidence <= max)
  }

  const sortBy = params.sortBy || 'detectedAt'
  const sortOrder = params.sortOrder === 'asc' ? 1 : -1

  list.sort((a, b) => {
    if (sortBy === 'confidence') {
      return (a.confidence - b.confidence) * sortOrder
    }
    return (new Date(a.detectedAt).getTime() - new Date(b.detectedAt).getTime()) * sortOrder
  })

  const page = Math.max(1, Number(params.page) || 1)
  const pageSize = Math.max(1, Number(params.pageSize) || 10)
  const total = list.length
  const startIndex = (page - 1) * pageSize
  const items = list.slice(startIndex, startIndex + pageSize)

  return {
    items,
    total,
    page,
    pageSize
  }
}

function buildQueryString(params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== '') {
      qs.append(key, value)
    }
  })
  const str = qs.toString()
  return str ? `?${str}` : ''
}

// ── Public API ─────────────────────────────────────────────────────

/**
 * Fetch paginated, filtered, and sorted detection history.
 * @param {Object} params
 * @returns {Promise<{ items: Array, total: number, page: number, pageSize: number }>}
 */
export async function getDetections(params = {}) {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 450))
    return filterAndSortMock(params)
  }

  // TODO: connect backend endpoint
  const query = buildQueryString(params)
  return request(`/detections${query}`)
}

/**
 * Fetch top recent detection alerts.
 * @param {number} [limit=5]
 * @returns {Promise<Array<{ id, personName, detectedAt, confidence, cameraSource, sceneImageUrl }>>}
 */
export async function getRecentDetections(limit = 5) {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 250))
    return MOCK_DETECTIONS.slice(0, limit)
  }

  // TODO: connect backend endpoint
  return request(`/detections?limit=${limit}&sortBy=detectedAt&sortOrder=desc`)
}

/**
 * Fetch total count of all detections.
 * @returns {Promise<{ count: number }>}
 */
export async function getDetectionsCount() {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150))
    return { count: MOCK_DETECTIONS.length }
  }

  // TODO: connect backend endpoint
  return request('/detections/count')
}

/**
 * Fetch person options for filter dropdown.
 * @returns {Promise<Array<{ id: string, name: string }>>}
 */
export async function getPersonOptions() {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 150))
    return [...MOCK_PERSONS]
  }

  // TODO: connect backend endpoint
  return request('/persons?fields=id,name')
}
