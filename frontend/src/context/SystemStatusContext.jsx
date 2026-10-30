import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getSystemStatus } from '../services/systemApi'
import { subscribeToAlerts } from '../services/realtime'
import { useAuth } from './AuthContext'

const SystemStatusContext = createContext(null)

const MAX_POPUPS = 3

export function SystemStatusProvider({ children }) {
  const { user } = useAuth()
  const [systemStatus, setSystemStatus] = useState({
    monitoring: 'active',
    activeCamera: null,
    aiService: 'up'
  })
  const [statusLoading, setStatusLoading] = useState(true)
  const [statusError, setStatusError] = useState(false)
  const [realtimeState, setRealtimeState] = useState('connected') // 'connected' | 'reconnecting' | 'disconnected'
  const [alerts, setAlerts] = useState([]) // live matches waiting for the operator to dismiss them

  const refreshStatus = useCallback(async () => {
    try {
      const data = await getSystemStatus()
      if (data) {
        setSystemStatus(data)
        setStatusError(false)
      }
    } catch (err) {
      console.warn('[SystemStatus] Failed to poll status:', err)
      setStatusError(true)
    } finally {
      setStatusLoading(false)
    }
  }, [])

  // Poll system status every 10 seconds, only while an operator is logged in
  // (the real server answers 401 otherwise, which also triggers a logout)
  useEffect(() => {
    if (!user) return undefined
    refreshStatus()
    const interval = setInterval(refreshStatus, 10000)
    return () => clearInterval(interval)
  }, [refreshStatus, user])

  // Live alerts: one socket for the whole session while an operator is logged in
  useEffect(() => {
    if (!user) return undefined
    return subscribeToAlerts(
      (alert) => setAlerts((prev) => [alert, ...prev.filter((a) => a.id !== alert.id)].slice(0, MAX_POPUPS)),
      setRealtimeState
    )
  }, [user])

  const dismissAlert = useCallback((id) => setAlerts((prev) => prev.filter((a) => a.id !== id)), [])

  return (
    <SystemStatusContext.Provider
      value={{
        systemStatus,
        statusLoading,
        statusError,
        realtimeState,
        setRealtimeState,
        refreshStatus,
        alerts,
        dismissAlert
      }}
    >
      {children}
    </SystemStatusContext.Provider>
  )
}

export function useSystemStatus() {
  const ctx = useContext(SystemStatusContext)
  if (!ctx) {
    throw new Error('useSystemStatus must be used within a SystemStatusProvider')
  }
  return ctx
}
