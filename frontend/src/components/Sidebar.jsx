import { useAuth } from '../context/AuthContext'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Shield, LayoutDashboard, LogOut, UserPlus, Users, History
} from 'lucide-react'

export default function Sidebar({ stats, isOpen, onClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { id: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { id: '/register', icon: UserPlus, label: 'Register Person' },
    { id: '/persons', icon: Users, label: 'Missing Persons' },
    { id: '/history', icon: History, label: 'Detection History' }
  ]

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && <div className="modal-overlay" style={{ zIndex: 35 }} onClick={onClose} />}

      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <Shield />
          </div>
          <div>
            <h2>Survelliance</h2>
          </div>
        </div>

        <nav className="sidebar-nav">
          <span className="nav-section-label">Main Menu</span>
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${location.pathname === item.id ? 'active' : ''}`}
              onClick={() => { navigate(item.id); onClose?.() }}
            >
              <item.icon />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-user">
          <div className="sidebar-avatar">
            {user?.name?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div className="sidebar-user-info">
            <div className="name">{user?.name || user?.email || 'User'}</div>
            <div className="role">{user?.role || 'Operator'}</div>
          </div>
          <button className="sidebar-logout" onClick={logout} title="Sign out">
            <LogOut />
          </button>
        </div>
      </aside>
    </>
  )
}
