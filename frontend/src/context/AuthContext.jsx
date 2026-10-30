import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getAuthToken, setAuthToken, clearAuthToken, registerLogoutHandler } from '../services/apiClient'
import * as authApi from '../services/authApi'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getAuthToken())
  const [user, setUser] = useState(() => {
    const savedToken = getAuthToken()
    const stored = localStorage.getItem('sentinel_user')
    if (savedToken && stored) {
      try {
        return JSON.parse(stored)
      } catch {
        return null
      }
    }
    return null
  })

  const logout = useCallback(() => {
    setUser(null)
    setToken('')
    clearAuthToken()
    localStorage.removeItem('sentinel_user')
  }, [])

  // Auto-logout if any API call encounters 401 Unauthorized
  useEffect(() => {
    registerLogoutHandler(logout)
  }, [logout])

  const login = useCallback(async (email, password) => {
    const res = await authApi.login({ email, password })
    const authToken = res.token || ''
    const userData = {
      name: res.user?.name || email.split('@')[0],
      email: res.user?.email || email,
      role: res.user?.role || 'Operator'
    }

    setAuthToken(authToken)
    setToken(authToken)
    setUser(userData)
    localStorage.setItem('sentinel_user', JSON.stringify(userData))
    return userData
  }, [])

  const signup = useCallback(async (name, email, password) => {
    const res = await authApi.signup({ name, email, password })
    const authToken = res.token || ''
    const userData = {
      name: res.user?.name || name || 'Operator',
      email: res.user?.email || email,
      role: res.user?.role || 'Operator'
    }

    setAuthToken(authToken)
    setToken(authToken)
    setUser(userData)
    localStorage.setItem('sentinel_user', JSON.stringify(userData))
    return userData
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
