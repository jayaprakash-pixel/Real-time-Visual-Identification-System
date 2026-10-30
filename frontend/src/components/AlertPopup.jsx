import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Siren, X, Bell } from 'lucide-react'
import { useSystemStatus } from '../context/SystemStatusContext'
import '../styles/Alerts.css'

// A short two-tone alarm as a WAV blob: no audio file to ship, and an <audio> element is allowed
// to play once the operator has clicked anywhere (they have, to log in).
function makeAlarmUrl() {
  const rate = 22050, seconds = 1.2, n = Math.floor(rate * seconds)
  const buf = new ArrayBuffer(44 + n * 2)
  const v = new DataView(buf)
  const str = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)))
  str(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); str(8, 'WAVE'); str(12, 'fmt ')
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true)
  v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true)
  str(36, 'data'); v.setUint32(40, n * 2, true)
  for (let i = 0; i < n; i++) {
    const freq = Math.floor(i / (rate * 0.2)) % 2 ? 880 : 1320 // alternate every 0.2 s
    const fade = Math.min(1, (n - i) / (rate * 0.1))
    v.setInt16(44 + i * 2, Math.sin((2 * Math.PI * freq * i) / rate) * 0.5 * fade * 32767, true)
  }
  return URL.createObjectURL(new Blob([buf], { type: 'audio/wav' }))
}

export default function AlertPopup() {
  const { alerts, dismissAlert } = useSystemStatus()
  const audioRef = useRef(null)
  const seen = useRef(new Set())
  const [permission, setPermission] = useState(() => ('Notification' in window ? Notification.permission : 'denied'))

  useEffect(() => {
    const url = makeAlarmUrl()
    audioRef.current = new Audio(url)
    return () => URL.revokeObjectURL(url)
  }, [])

  // Sound + desktop notification once per new alert (not on every re-render)
  useEffect(() => {
    alerts.forEach((a) => {
      if (seen.current.has(a.id)) return
      seen.current.add(a.id)
      audioRef.current?.play().catch(() => {}) // blocked autoplay must never break the popup
      if (permission === 'granted') {
        new Notification(`MATCH: ${a.personName}`, { body: `${a.confidence}% · ${a.cameraSource}`, tag: a.id })
      }
    })
  }, [alerts, permission])

  if (!alerts.length && permission !== 'default') return null

  return (
    <div className="alert-stack" aria-live="assertive">
      {permission === 'default' && (
        <button type="button" className="alert-enable" onClick={() => Notification.requestPermission().then(setPermission)}>
          <Bell size={14} /> Enable desktop alerts
        </button>
      )}
      {alerts.map((a) => (
        <div key={a.id} className="alert-card" role="alert">
          <img src={a.thumbnailUrl || a.sceneImageUrl} alt={`Scene where ${a.personName} was detected`} />
          <div className="alert-body">
            <strong><Siren size={16} /> MATCH FOUND</strong>
            <span className="alert-name">{a.personName}</span>
            <span>{a.confidence}% confidence · {a.cameraSource}</span>
            <span>{new Date(a.detectedAt).toLocaleTimeString()}</span>
            <Link to="/history" onClick={() => dismissAlert(a.id)}>View in history</Link>
          </div>
          <button type="button" className="alert-close" aria-label="Dismiss alert" onClick={() => dismissAlert(a.id)}>
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  )
}
