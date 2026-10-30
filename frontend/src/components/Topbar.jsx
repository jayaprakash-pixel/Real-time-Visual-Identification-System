import { Menu } from 'lucide-react'
import { useSystemStatus } from '../context/SystemStatusContext'

export default function Topbar({ title, subtitle, onMenuClick }) {
  const { systemStatus, statusError } = useSystemStatus()

  // Determine badge styling and label based on system state
  let badgeLabel = 'System Active'
  let badgeColor = 'var(--accent-teal)'
  let badgeBg = 'rgba(20, 184, 166, 0.1)'
  let badgeBorder = 'rgba(20, 184, 166, 0.3)'

  if (statusError || systemStatus.aiService === 'down' || systemStatus.monitoring === 'offline') {
    badgeLabel = 'System Offline'
    badgeColor = 'var(--accent-red)'
    badgeBg = 'rgba(239, 68, 68, 0.1)'
    badgeBorder = 'rgba(239, 68, 68, 0.3)'
  } else if (systemStatus.monitoring === 'idle') {
    badgeLabel = 'System Idle'
    badgeColor = 'var(--accent-pink)'
    badgeBg = 'rgba(236, 72, 153, 0.1)'
    badgeBorder = 'rgba(236, 72, 153, 0.3)'
  }

  return (
    <div className="topbar">
      <div className="topbar-left" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <button
          className="btn btn-ghost"
          onClick={onMenuClick}
          style={{ display: 'none' }}
          id="mobile-menu-btn"
          aria-label="Toggle navigation menu"
        >
          <Menu />
        </button>
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>

      <div className="topbar-right">
        <div
          className="topbar-live-badge"
          style={{
            color: badgeColor,
            background: badgeBg,
            borderColor: badgeBorder
          }}
        >
          <span
            className="live-dot"
            style={{ background: badgeColor }}
          />
          {badgeLabel}
        </div>
      </div>
    </div>
  )
}
