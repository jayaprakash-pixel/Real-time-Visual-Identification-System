import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getSystemStatus } from '../services/systemApi'

const SystemStatusContext = createContext(null)

export function SystemStatusProvider({ children }) {
  const [systemStatus, setSystemStatus] = useState({
    monitoring: 'active',
    activeCamera: null,
    aiService: 'up'
  })
  const [statusLoading, setStatusLoading] = useState(true)
  const [statusError, setStatusError] = useState(false)
  const [realtimeState, setRealtimeState] = useState('connected') // 'connected' | 'reconnecting' | 'disconnected'

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

  // Poll system status every 10 seconds
  useEffect(() => {
    refreshStatus()
    const interval = setInterval(refreshStatus, 10000)
    return () => clearInterval(interval)
  }, [refreshStatus])

  return (
    <SystemStatusContext.Provider
      value={{
        systemStatus,
        statusLoading,
        statusError,
        realtimeState,
        setRealtimeState,
        refreshStatus
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
