import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Shield, Mail, Lock, Eye, EyeOff, AlertTriangle, ShieldCheck, User } from 'lucide-react'
import '../styles/Login.css'

export default function Login() {
  const { login, signup } = useAuth()
  const [isLogin, setIsLogin] = useState(true)

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [errorField, setErrorField] = useState('')

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setError('')
    if (errorField === e.target.name) {
      setErrorField('')
    }
  }

  const validateForm = () => {
    if (!formData.email || !formData.password) {
      return 'Please fill in all required fields.'
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      setErrorField('email')
      return 'Please enter a valid email address.'
    }

    if (formData.password.length < 8) {
      setErrorField('password')
      return 'Password must be at least 8 characters long.'
    }

    if (!isLogin) {
      if (!formData.name) {
        setErrorField('name')
        return 'Please enter your full name.'
      }
      if (formData.password !== formData.confirmPassword) {
        setErrorField('confirmPassword')
        return 'Passwords do not match.'
      }
    }

    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (loading) return

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setLoading(true)
    setError('')
    setErrorField('')

    try {
      if (isLogin) {
        await login(formData.email, formData.password)
      } else {
        await signup(formData.name, formData.email, formData.password)
      }
    } catch (err) {
      if (err.field) {
        setErrorField(err.field)
      }
      if (err.status === 401) {
        setError('Invalid email or password.')
      } else if (err.status === 409) {
        setError(err.message || 'An account with this email already exists.')
      } else if (err.status === 0 || err.message?.includes('Cannot reach server')) {
        setError('Cannot reach server. Please try again.')
      } else {
        setError(err.message || 'An error occurred. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const toggleMode = () => {
    setIsLogin(!isLogin)
    setError('')
    setErrorField('')
    setFormData({ name: '', email: '', password: '', confirmPassword: '' })
  }

  return (
    <div className="login-page">
      <div className="login-bg-grid" />

      <div className="login-card">
        {/* Brand */}
        <div className="login-brand">
          <div className="login-logo">
            <Shield />
          </div>
          <h1>Survelliance</h1>
          <p>{isLogin ? 'Sign in to Command Center' : 'Create Operator Account'}</p>
        </div>

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="login-error">
              <AlertTriangle />
              <span>{error}</span>
            </div>
          )}

          {!isLogin && (
            <div className="input-group">
              <label htmlFor="name">Full Name</label>
              <div className="input-wrapper">
                <User />
                <input
                  id="name"
                  name="name"
                  type="text"
                  placeholder="Enter your full name"
                  value={formData.name}
                  onChange={handleChange}
                  disabled={loading}
                  style={errorField === 'name' ? { borderColor: 'var(--accent-red)' } : undefined}
                  required={!isLogin}
                />
              </div>
            </div>
          )}

          <div className="input-group">
            <label htmlFor="email">Email Address</label>
            <div className="input-wrapper">
              <Mail />
              <input
                id="email"
                name="email"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleChange}
                autoComplete="email"
                disabled={loading}
                style={errorField === 'email' ? { borderColor: 'var(--accent-red)' } : undefined}
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <Lock />
              <input
                id="password"
                name="password"
                type={showPass ? 'text' : 'password'}
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                autoComplete={isLogin ? 'current-password' : 'new-password'}
                disabled={loading}
                style={errorField === 'password' ? { borderColor: 'var(--accent-red)' } : undefined}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPass(!showPass)}
                disabled={loading}
                aria-label={showPass ? 'Hide password' : 'Show password'}
              >
                {showPass ? <EyeOff /> : <Eye />}
              </button>
            </div>
          </div>

          {!isLogin && (
            <div className="input-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <div className="input-wrapper">
                <Lock />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showPass ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  autoComplete="new-password"
                  disabled={loading}
                  style={errorField === 'confirmPassword' ? { borderColor: 'var(--accent-red)' } : undefined}
                  required={!isLogin}
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            className="login-btn"
            disabled={loading}
          >
            {loading ? (
              <span className="login-btn-loading">
                <span className="spinner" />
                {isLogin ? 'Authenticating…' : 'Creating Account…'}
              </span>
            ) : (
              isLogin ? 'Sign In' : 'Create Account'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button type="button" className="toggle-mode-btn" onClick={toggleMode} disabled={loading}>
              {isLogin ? 'Create Account' : 'Sign In'}
            </button>
          </p>
        </div>

        <div className="security-badge">
          <ShieldCheck />
          <span>256-bit encrypted · Authorized personnel only</span>
        </div>
      </div>
    </div>
  )
}
