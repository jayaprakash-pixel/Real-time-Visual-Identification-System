/**
 * Authentication API Service
 *
 * Handles operator login and account creation.
 * Uses shared apiClient configuration and mock switch.
 *
 * Expected backend responses:
 *   POST /auth/login
 *     Request:  { email, password }
 *     Response: { token: string, user: { name: string, email: string, role: string } }
 *
 *   POST /auth/signup
 *     Request:  { name, email, password }
 *     Response: { token: string, user: { name: string, email: string, role: string } }
 */

import { USE_MOCK, request } from './apiClient'

/**
 * Authenticate existing operator.
 * @param {{ email: string, password: string }} credentials
 * @returns {Promise<{ token: string, user: { name: string, email: string, role: string } }>}
 */
export async function login({ email, password }) {
  if (USE_MOCK) {
    // Simulate network delay
    await new Promise((r) => setTimeout(r, 600))

    // Mock validation errors for testing
    if (email === 'wrong@test.com' || password === 'invalid123') {
      const err = new Error('Invalid email or password.')
      err.status = 401
      throw err
    }

    const defaultName = email.split('@')[0]
    const capitalized = defaultName.charAt(0).toUpperCase() + defaultName.slice(1)

    return {
      token: `mock-jwt-token-${Date.now()}`,
      user: {
        name: capitalized,
        email,
        role: 'Operator'
      }
    }
  }

  // TODO: connect backend endpoint
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  })
}

/**
 * Register a new operator account.
 * @param {{ name: string, email: string, password: string }} data
 * @returns {Promise<{ token: string, user: { name: string, email: string, role: string } }>}
 */
export async function signup({ name, email, password }) {
  if (USE_MOCK) {
    // Simulate network delay
    await new Promise((r) => setTimeout(r, 700))

    // Mock duplicate error for testing
    if (email.toLowerCase() === 'exists@test.com') {
      const err = new Error('An account with this email already exists.')
      err.status = 409
      err.field = 'email'
      throw err
    }

    return {
      token: `mock-jwt-token-${Date.now()}`,
      user: {
        name: name || 'Operator',
        email,
        role: 'Operator'
      }
    }
  }

  // TODO: connect backend endpoint
  return request('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ name, email, password })
  })
}
