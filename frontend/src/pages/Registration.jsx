import { useState, useRef } from 'react'
import { Upload, X, CheckCircle, AlertTriangle } from 'lucide-react'
import { registerPerson } from '../services/personsApi'
import '../styles/Home.css'
import '../styles/Registration.css'

export default function Registration() {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: 'Male',
    missingDate: '',
    missingLocation: '',
    description: '',
    photo: null
  })
  const [preview, setPreview] = useState(null)
  const [successMsg, setSuccessMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileRef = useRef(null)

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setErrorMsg('')
  }

  const handlePhoto = (e) => {
    const file = e.target.files[0]
    if (file) {
      const url = URL.createObjectURL(file)
      setFormData({ ...formData, photo: file })
      setPreview(url)
      setErrorMsg('')
    }
  }

  const removePhoto = () => {
    setFormData({ ...formData, photo: null })
    setPreview(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isSubmitting) return

    // Validate required fields
    if (!formData.name || !formData.age || !formData.missingDate || !formData.missingLocation || !formData.photo) {
      setErrorMsg('Please fill out all required fields and upload a photograph.')
      return
    }

    setIsSubmitting(true)
    setErrorMsg('')
    setSuccessMsg('')
    setUploadProgress(0)

    try {
      const payload = new FormData()
      payload.append('name', formData.name)
      payload.append('age', formData.age)
      payload.append('gender', formData.gender)
      payload.append('missingDate', formData.missingDate)
      payload.append('missingLocation', formData.missingLocation)
      payload.append('description', formData.description || '')
      payload.append('photo', formData.photo)

      await registerPerson(payload, (percent) => {
        setUploadProgress(percent)
      })

      setSuccessMsg(
        `Registration successful! ${formData.name}'s profile has been forwarded to the AI Recognition Module.`
      )

      // Reset form on success
      setFormData({
        name: '',
        age: '',
        gender: 'Male',
        missingDate: '',
        missingLocation: '',
        description: '',
        photo: null
      })
      setPreview(null)
      if (fileRef.current) fileRef.current.value = ''

      setTimeout(() => {
        setSuccessMsg('')
      }, 5000)
    } catch (err) {
      setErrorMsg(err.message || 'Failed to register missing person. Please try again.')
    } finally {
      setIsSubmitting(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="form-container">
      {successMsg && (
        <div className="alert-success">
          <CheckCircle size={20} />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="alert-error">
          <AlertTriangle size={20} />
          <span>{errorMsg}</span>
        </div>
      )}

      {isSubmitting && (
        <div className="upload-progress-box">
          <div className="upload-progress-header">
            <span>
              {uploadProgress >= 100
                ? 'Processing photo with AI…'
                : `Uploading photograph & profile… ${uploadProgress}%`}
            </span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="upload-progress-track">
            <div
              className="upload-progress-fill"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group full-width">
            <label>Photograph *</label>
            {preview ? (
              <div className="photo-preview">
                <img src={preview} alt="Preview" />
                <button
                  type="button"
                  onClick={removePhoto}
                  disabled={isSubmitting}
                  aria-label="Remove photograph"
                >
                  <X size={16} />
                </button>
              </div>
            ) : (
              <div
                className="photo-upload"
                onClick={() => !isSubmitting && fileRef.current?.click()}
                style={isSubmitting ? { opacity: 0.6, cursor: 'not-allowed' } : undefined}
              >
                <Upload size={24} />
                <p>Click to upload photograph</p>
                <span className="hint">JPG, PNG up to 5MB. Clear facial photo required for AI recognition.</span>
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/*"
                  onChange={handlePhoto}
                  disabled={isSubmitting}
                  required
                />
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="name">Full Name *</label>
            <input
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter full name"
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="age">Age *</label>
            <input
              id="age"
              name="age"
              type="number"
              min="0"
              value={formData.age}
              onChange={handleChange}
              placeholder="Age"
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="gender">Gender *</label>
            <select
              id="gender"
              name="gender"
              value={formData.gender}
              onChange={handleChange}
              disabled={isSubmitting}
              required
            >
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="missingDate">Missing Date *</label>
            <input
              id="missingDate"
              name="missingDate"
              type="date"
              value={formData.missingDate}
              onChange={handleChange}
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="form-group full-width">
            <label htmlFor="missingLocation">Missing Location *</label>
            <input
              id="missingLocation"
              name="missingLocation"
              value={formData.missingLocation}
              onChange={handleChange}
              placeholder="e.g. Central Station, Mumbai"
              disabled={isSubmitting}
              required
            />
          </div>

          <div className="form-group full-width">
            <label htmlFor="description">Additional Description</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Physical appearance, clothing worn, distinguishing marks, etc."
              disabled={isSubmitting}
            />
          </div>
        </div>

        <div className="form-actions" style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting
              ? (uploadProgress >= 100 ? 'Processing photo…' : `Uploading… ${uploadProgress}%`)
              : 'Register Missing Person'}
          </button>
        </div>
      </form>
    </div>
  )
}
