import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Video,
  Users,
  Activity,
  Radio,
  Camera,
  RotateCw
} from 'lucide-react'
import { getPersonsCount } from '../services/personsApi'
import { getDetectionsCount } from '../services/detectionsApi'
import { STREAM_URL } from '../services/systemApi'
import { serverUrl } from '../services/apiClient'
import { useSystemStatus } from '../context/SystemStatusContext'
import '../styles/Home.css'
import '../styles/Dashboard.css'

export default function Home() {
  const { systemStatus, realtimeState, alerts } = useSystemStatus()

  // ── Stat Card States ─────────────────────────────────────────────
  const [personsCount, setPersonsCount] = useState(null)
  const [personsLoading, setPersonsLoading] = useState(true)
  const [personsError, setPersonsError] = useState(false)

  const [detectionsCount, setDetectionsCount] = useState(null)
  const [detectionsCountLoading, setDetectionsCountLoading] = useState(true)
  const [detectionsCountError, setDetectionsCountError] = useState(false)

  // ── Surveillance Stream States ───────────────────────────────────
  const [streamError, setStreamError] = useState(false)
  const [streamCacheBuster, setStreamCacheBuster] = useState(0)
  const streamImgRef = useRef(null)

  // The server hands out a stream URL with a short-lived token. Pick it once (the 10 s status poll
  // must not restart the video) and take a fresh one on reconnect.
  const freshStreamUrl = () => serverUrl(systemStatus.streamUrl) || STREAM_URL
  const streamUrl = useRef('')
  if (!streamUrl.current) streamUrl.current = freshStreamUrl()
  const streamSrc = streamUrl.current

  // Fetch counts on mount
  const loadCounts = useCallback(async () => {
    setPersonsLoading(true)
    setPersonsError(false)
    try {
      const data = await getPersonsCount()
      setPersonsCount(data.count)
    } catch (err) {
      console.warn('[Dashboard] Error fetching persons count:', err)
      setPersonsError(true)
    } finally {
      setPersonsLoading(false)
    }

    setDetectionsCountLoading(true)
    setDetectionsCountError(false)
    try {
      const data = await getDetectionsCount()
      setDetectionsCount(data.count)
    } catch (err) {
      console.warn('[Dashboard] Error fetching detections count:', err)
      setDetectionsCountError(true)
    } finally {
      setDetectionsCountLoading(false)
    }
  }, [])

  // reload on mount and whenever a live alert arrives, so Total Detections stays current
  useEffect(() => {
    loadCounts()
  }, [loadCounts, alerts.length])

  // Clean up surveillance stream image memory on unmount
  useEffect(() => {
    const imgEl = streamImgRef.current
    return () => {
      if (imgEl) {
        imgEl.src = ''
      }
    }
  }, [])

  const handleReconnectStream = () => {
    streamUrl.current = freshStreamUrl()
    setStreamError(false)
    setStreamCacheBuster(Date.now())
  }

  // A dropped stream (camera restart, expired token) retries on its own every 3 s
  useEffect(() => {
    if (!streamError) return undefined
    const t = setTimeout(handleReconnectStream, 3000)
    return () => clearTimeout(t)
  })

  return (
    <>
      {/* ── Realtime Connection Indicator ──────────── */}
      <div className="dashboard-conn-status">
        <span className={`conn-dot ${realtimeState}`} />
        <span>
          Realtime Link: {realtimeState === 'connected' ? 'Live' : realtimeState === 'reconnecting' ? 'Reconnecting…' : 'Disconnected'}
        </span>
      </div>

      {/* ── 1. Stat Cards Row ──────────────────────── */}
      <div className="stats-grid">
        {/* Card 1: Registered Persons */}
        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-primary">
            <Users />
          </div>
          <div className="stat-info">
            <span className="stat-label">Registered Persons</span>
            {personsLoading ? (
              <div className="stat-skeleton-shimmer" />
            ) : personsError ? (
              <span className="stat-value">--</span>
            ) : (
              <span className="stat-value">{personsCount}</span>
            )}
          </div>
        </div>

        {/* Card 2: Total Detections */}
        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-teal">
            <Activity />
          </div>
          <div className="stat-info">
            <span className="stat-label">Total Detections</span>
            {detectionsCountLoading ? (
              <div className="stat-skeleton-shimmer" />
            ) : detectionsCountError ? (
              <span className="stat-value">--</span>
            ) : (
              <span className="stat-value">{detectionsCount}</span>
            )}
          </div>
        </div>

        {/* Card 3: Monitoring Status */}
        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-pink">
            <Radio />
          </div>
          <div className="stat-info">
            <span className="stat-label">Monitoring Status</span>
            <div className="stat-status-badge">
              <span className={`status-dot ${systemStatus.monitoring || 'active'}`} />
              <span style={{ fontSize: '1.125rem' }}>
                {systemStatus.monitoring === 'active'
                  ? 'Active'
                  : systemStatus.monitoring === 'idle'
                  ? 'Idle'
                  : 'Offline'}
              </span>
            </div>
          </div>
        </div>

        {/* Card 4: Active Camera */}
        <div className="stat-card">
          <div className="stat-icon-wrapper stat-icon-amber">
            <Camera />
          </div>
          <div className="stat-info">
            <span className="stat-label">Active Camera</span>
            <span
              className="stat-value"
              style={{ fontSize: '1rem', fontWeight: 600 }}
              title={systemStatus.activeCamera || 'None'}
            >
              {systemStatus.activeCamera || 'None'}
            </span>
          </div>
        </div>
      </div>

      {/* ── 2. Live Surveillance Feed Panel ───────── */}
      <div className="section-header">
        <h2>Live Surveillance Feed</h2>
      </div>

      <div className="stream-panel-container">
        {streamSrc && !streamError ? (
          <div className="stream-media-wrapper">
            <div className="stream-badge-live">
              <span className="live-dot" />
              LIVE
            </div>
            <img
              ref={streamImgRef}
              src={
                streamCacheBuster
                  ? `${streamSrc}${streamSrc.includes('?') ? '&' : '?'}cb=${streamCacheBuster}`
                  
: streamSrc
              }
              alt="Live surveillance camera stream"
              onError={() => setStreamError(true)}
            />
            <div className="stream-overlay-controls">
              <button
                type="button"
                className="stream-ctrl-btn"
                onClick={handleReconnectStream}
                title="Refresh video stream"
              >
                <RotateCw size={14} />
                <span>Reload</span>
              </button>
            </div>
          </div>
        ) : streamSrc && streamError ? (
          <div className="stream-placeholder">
            <Video size={48} />
            <p>Stream unavailable</p>
            <span>Unable to receive video feed from camera server</span>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleReconnectStream}
              style={{ fontSize: '0.8125rem', padding: 'var(--sp-2) var(--sp-4)' }}
            >
              <RotateCw size={14} />
              Reconnect Stream
            </button>
          </div>
        ) : (
          <div className="stream-placeholder">
            <Video size={48} />
            <p>Waiting for camera feed connection...</p>
            <span>Connect the mobile streaming module or configure VITE_STREAM_URL to begin AI scanning</span>
          </div>
        )}
      </div>
    </>
  )
}
