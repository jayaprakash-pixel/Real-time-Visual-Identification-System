import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import '../styles/Home.css'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  
  // Determine title and subtitle dynamically based on path
  const routeMeta = {
    '/':         { title: 'Command Center',              subtitle: 'Real-time surveillance overview' },
    '/register': { title: 'Missing Person Registration', subtitle: 'Register a new missing individual' },
    '/persons':  { title: 'Missing Persons',             subtitle: 'View and manage registered missing persons' },
    '/history':  { title: 'Detection History',           subtitle: 'Review previous match detections' }
  }
  const { title, subtitle } = routeMeta[location.pathname] || routeMeta['/']

  return (
    <div className="home-layout">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="main-content">
        <Topbar
          title={title}
          subtitle={subtitle}
          search=""
          setSearch={() => {}}
          onMenuClick={() => setSidebarOpen(true)}
        />

        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
