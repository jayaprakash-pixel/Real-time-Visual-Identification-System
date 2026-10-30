import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Home from './pages/Home'
import Registration from './pages/Registration'
import Persons from './pages/Persons'
import History from './pages/History'
import Layout from './components/Layout'

export default function App() {
  const { user } = useAuth()
  
  if (!user) {
    return <Login />
  }
  
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/register" element={<Registration />} />
        <Route path="/persons" element={<Persons />} />
        <Route path="/history" element={<History />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
