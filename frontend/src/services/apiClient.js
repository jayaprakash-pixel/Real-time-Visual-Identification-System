/**
 * Shared API Client
 *
 * Provides centralized network request handling, auth token management,
 * normalized error throwing, and progress-tracking uploads.
 */

// ── Global Configuration ───────────────────────────────────────────
/**
 * Global mock toggle. Set to `false` when connecting to a real backend.
 */
export const USE_MOCK = true

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// Storage key for the authentication JWT / session token
const TOKEN_KEY = 'sentinel_token'

// ── Auth Token Helpers ─────────────────────────────────────────────
export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY)
}

// ── 401 Unauthorized Callback ──────────────────────────────────────
let unauthorizedCallback = null

/**
 * Register a callback triggered when any request returns 401 Unauthorized.
 * Typically registered by AuthContext to synchronize logout state.
 */
export function registerLogoutHandler(callback) {
  unauthorizedCallback = callback
}

function handle401() {
  clearAuthToken()
  if (typeof unauthorizedCallback === 'function') {
    unauthorizedCallback()
  }
}

// ── Normalized Request Wrapper ─────────────────────────────────────
/**
 * Perform an HTTP request with automatic auth header injection, JSON parsing,
 * and normalized error structure: { status, message, field? }
 *
 * @param {string} path - URL or path relative to BASE_URL
 * @param {RequestInit} [options={}] - Fetch configuration
 * @returns {Promise<any>}
 */
export async function request(path, options = {}) {
  const url = path.startsWith('http://') || path.startsWith('https://')
    ? path
    : `${BASE_URL}${path}`

  const headers = new Headers(options.headers || {})

  // Attach auth bearer token if available
  const token = getAuthToken()
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  // Set Content-Type: application/json if sending a JSON body and not already set
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }

  let res
  try {
    res = await fetch(url, {
      ...options,
      headers
    })
  } catch (netErr) {
    // Network failure (offline, DNS failure, CORS block, server down)
    const error = new Error('Cannot reach server. Please try again.')
    error.status = 0
    error.original = netErr
    throw error
  }

  // Parse response body
  let data = null
  const contentType = res.headers.get('content-type') || ''
  if (res.status !== 204) {
    if (contentType.includes('application/json')) {
      try {
        data = await res.json()
      } catch {
        data = null
      }
    } else {
      try {
        data = await res.text()
      } catch {
        data = null
      }
    }
  }

  // If response is not 2xx, throw normalized error
  if (!res.ok) {
    const error = new Error(
      (data && (data.message || data.error)) ||
      `Request failed with status ${res.status}`
    )
    error.status = res.status
    if (data && data.field) {
      error.field = data.field
    }

    if (res.status === 401) {
      handle401()
    }

    throw error
  }

  return data
}

// ── Multipart Upload with Progress ─────────────────────────────────
/**
 * Upload multipart FormData via XMLHttpRequest to track upload progress (0-100%).
 *
 * @param {string} path - Upload endpoint relative to BASE_URL
 * @param {FormData} formData - Data payload with file
 * @param {(percent: number) => void} [onProgress] - Callback for progress (0 to 100)
 * @returns {Promise<any>}
 */
export function uploadWithProgress(path, formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const url = path.startsWith('http://') || path.startsWith('https://')
      ? path
      : `${BASE_URL}${path}`

    xhr.open('POST', url)

    // Attach auth token if available
    const token = getAuthToken()
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    }

    if (xhr.upload && typeof onProgress === 'function') {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.min(100, Math.round((e.loaded / e.total) * 100))
          onProgress(percent)
        }
      })
    }

    xhr.onload = () => {
      let data = null
      try {
        data = xhr.responseText ? JSON.parse(xhr.responseText) : null
      } catch {
        data = xhr.responseText
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data)
      } else {
        const error = new Error(
          (data && (data.message || data.error)) ||
          `Upload failed with status ${xhr.status}`
        )
        error.status = xhr.status
        if (data && data.field) {
          error.field = data.field
        }

        if (xhr.status === 401) {
          handle401()
        }

        reject(error)
      }
    }

    xhr.onerror = () => {
      const error = new Error('Cannot reach server. Please try again.')
      error.status = 0
      reject(error)
    }

    xhr.send(formData)
  })
}
