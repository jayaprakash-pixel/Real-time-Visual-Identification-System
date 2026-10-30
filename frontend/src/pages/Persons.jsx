import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users, Search, Grid3X3, List, Trash2, X, Calendar,
  MapPin, UserCircle, AlertTriangle, RefreshCw, UserPlus,
  CheckCircle, XCircle, ImageOff, Filter
} from 'lucide-react'
import { getPersons, deletePerson } from '../services/personsApi'
import '../styles/Persons.css'

// ── Toast component ────────────────────────────────
function Toast({ type, message, onDismiss }) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 4000)
    return () => clearTimeout(timer)
  }, [onDismiss])

  return (
    <div className={`persons-toast persons-toast--${type}`} role="alert">
      {type === 'success' ? <CheckCircle /> : <XCircle />}
      {message}
    </div>
  )
}

// ── Confirm dialog ─────────────────────────────────
function ConfirmDialog({ personName, loading, onConfirm, onCancel }) {
  const cancelRef = useRef(null)

  // Focus-trap and Esc key
  useEffect(() => {
    cancelRef.current?.focus()

    const handleKey = (e) => {
      if (e.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onCancel])

  return (
    <div
      className="confirm-overlay"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-label={`Confirm delete ${personName}`}
    >
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <h3>Delete Record</h3>
        <p>
          Are you sure you want to permanently delete the record for{' '}
          <strong>{personName}</strong>? This action cannot be undone.
        </p>
        <div className="confirm-actions">
          <button
            className="btn-cancel"
            ref={cancelRef}
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            className="btn-danger"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Image preview modal ────────────────────────────
function ImagePreview({ src, alt, onClose }) {
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

  return (
    <div
      className="image-preview-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Image preview"
    >
      <div className="image-preview-content" onClick={(e) => e.stopPropagation()}>
        <img src={src} alt={alt} />
        <button
          className="image-preview-close"
          onClick={onClose}
          aria-label="Close image preview"
        >
          <X size={18} />
        </button>
      </div>
    </div>
  )
}

// ── Person photo with fallback ─────────────────────
function PersonPhoto({ url, name, className, fallbackClass, onClick }) {
  const [failed, setFailed] = useState(false)

  if (!url || failed) {
    return (
      <div className={fallbackClass}>
        <UserCircle />
        <span>No photo</span>
      </div>
    )
  }

  return (
    <img
      src={url}
      alt={`Photo of ${name}`}
      className={className}
      onError={() => setFailed(true)}
      onClick={onClick}
    />
  )
}

// ── Skeleton loaders ───────────────────────────────
function SkeletonCards() {
  return (
    <div className="skeleton-grid" aria-busy="true" aria-label="Loading persons">
      {Array.from({ length: 6 }).map((_, i) => (
        <div className="skeleton-card" key={i}>
          <div className="skeleton-photo" />
          <div className="skeleton-body">
            <div className="skeleton-line skeleton-line--medium" />
            <div className="skeleton-line skeleton-line--short" />
            <div className="skeleton-line skeleton-line--full" />
          </div>
        </div>
      ))}
    </div>
  )
}

function SkeletonTable() {
  return (
    <div className="persons-table-wrapper" aria-busy="true" aria-label="Loading persons">
      {Array.from({ length: 6 }).map((_, i) => (
        <div className="skeleton-table-row" key={i}>
          <div className="skeleton-table-photo" />
          <div className="skeleton-table-lines">
            <div className="skeleton-line" />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Helper: gender badge class ─────────────────────
function genderBadgeClass(gender) {
  switch (gender) {
    case 'Male':   return 'gender-badge gender-badge--male'
    case 'Female': return 'gender-badge gender-badge--female'
    default:       return 'gender-badge gender-badge--other'
  }
}

// ── Format date for display ────────────────────────
function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

// ════════════════════════════════════════════════════
// Main page component
// ════════════════════════════════════════════════════
const EMPTY_FILTERS = { search: '', gender: '', ageMin: '', ageMax: '', dateFrom: '', dateTo: '' }

export default function Persons() {
  const navigate = useNavigate()

  // Data
  const [persons, setPersons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [debouncedSearch, setDebouncedSearch] = useState('')

  // UI
  const [view, setView] = useState('grid') // 'grid' | 'table'
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [previewImage, setPreviewImage] = useState(null)
  const [toast, setToast] = useState(null)

  // ── Debounce search ────────────────────────────
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(filters.search)
    }, 300)
    return () => clearTimeout(timer)
  }, [filters.search])

  // ── Fetch data ─────────────────────────────────
  const fetchPersons = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = { ...filters, search: debouncedSearch }
      const data = await getPersons(params)
      setPersons(data)
    } catch (err) {
      setError(err.message || 'Failed to load missing persons.')
    } finally {
      setLoading(false)
    }
  }, [filters.gender, filters.ageMin, filters.ageMax, filters.dateFrom, filters.dateTo, debouncedSearch])

  useEffect(() => {
    fetchPersons()
  }, [fetchPersons])

  // ── Filter helpers ─────────────────────────────
  const hasActiveFilters = Object.entries(filters).some(
    ([, v]) => v !== ''
  )

  const updateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS)
  }

  // ── Delete flow ────────────────────────────────
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    setDeleteLoading(true)
    try {
      await deletePerson(deleteTarget.id)
      setPersons((prev) => prev.filter((p) => p.id !== deleteTarget.id))
      setToast({ type: 'success', message: `${deleteTarget.name}'s record deleted.` })
    } catch (err) {
      setToast({ type: 'error', message: err.message || 'Failed to delete record.' })
    } finally {
      setDeleteLoading(false)
      setDeleteTarget(null)
    }
  }

  // ── Render ─────────────────────────────────────
  return (
    <>
      {/* Toast */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onDismiss={() => setToast(null)}
        />
      )}

      {/* Confirm dialog */}
      {deleteTarget && (
        <ConfirmDialog
          personName={deleteTarget.name}
          loading={deleteLoading}
          onConfirm={handleDeleteConfirm}
          onCancel={() => !deleteLoading && setDeleteTarget(null)}
        />
      )}

      {/* Image preview */}
      {previewImage && (
        <ImagePreview
          src={previewImage.src}
          alt={previewImage.alt}
          onClose={() => setPreviewImage(null)}
        />
      )}

      {/* Header */}
      <div className="persons-header">
        <div className="persons-header-left">
          <div className="persons-count">
            {!loading && !error && (
              <>
                Showing <strong>{persons.length}</strong>{' '}
                {persons.length === 1 ? 'person' : 'persons'}
              </>
            )}
          </div>
        </div>

        <div className="view-toggle" role="group" aria-label="View mode">
          <button
            className={`view-toggle-btn ${view === 'grid' ? 'active' : ''}`}
            onClick={() => setView('grid')}
            aria-label="Grid view"
            aria-pressed={view === 'grid'}
          >
            <Grid3X3 />
            Cards
          </button>
          <button
            className={`view-toggle-btn ${view === 'table' ? 'active' : ''}`}
            onClick={() => setView('table')}
            aria-label="Table view"
            aria-pressed={view === 'table'}
          >
            <List />
            Table
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="persons-filters" role="search" aria-label="Filter missing persons">
        <div className="filter-group filter-search">
          <label htmlFor="filter-search">Search by name</label>
          <input
            id="filter-search"
            type="text"
            placeholder="Search…"
            value={filters.search}
            onChange={(e) => updateFilter('search', e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="filter-gender">Gender</label>
          <select
            id="filter-gender"
            value={filters.gender}
            onChange={(e) => updateFilter('gender', e.target.value)}
          >
            <option value="">All</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div className="filter-group filter-age">
          <label>Age range</label>
          <div className="filter-age-inputs">
            <input
              type="number"
              min="0"
              placeholder="Min"
              value={filters.ageMin}
              onChange={(e) => updateFilter('ageMin', e.target.value)}
              aria-label="Minimum age"
            />
            <input
              type="number"
              min="0"
              placeholder="Max"
              value={filters.ageMax}
              onChange={(e) => updateFilter('ageMax', e.target.value)}
              aria-label="Maximum age"
            />
          </div>
        </div>

        <div className="filter-group filter-date">
          <label htmlFor="filter-date-from">Date from</label>
          <input
            id="filter-date-from"
            type="date"
            value={filters.dateFrom}
            onChange={(e) => updateFilter('dateFrom', e.target.value)}
          />
        </div>

        <div className="filter-group filter-date">
          <label htmlFor="filter-date-to">Date to</label>
          <input
            id="filter-date-to"
            type="date"
            value={filters.dateTo}
            onChange={(e) => updateFilter('dateTo', e.target.value)}
          />
        </div>

        {hasActiveFilters && (
          <button
            className="filter-clear-btn"
            onClick={clearFilters}
            aria-label="Clear all filters"
          >
            <Filter size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
            Clear filters
          </button>
        )}
      </div>

      {/* Content */}
      {loading ? (
        view === 'grid' ? <SkeletonCards /> : <SkeletonTable />
      ) : error ? (
        <div className="persons-state">
          <AlertTriangle />
          <h3>Something went wrong</h3>
          <p>{error}</p>
          <button className="btn-outline" onClick={fetchPersons}>
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      ) : persons.length === 0 ? (
        <div className="persons-state">
          <Users />
          <h3>{hasActiveFilters ? 'No results match your filters' : 'No missing persons registered yet'}</h3>
          <p>
            {hasActiveFilters
              ? 'Try adjusting your search criteria or clear the filters.'
              : 'Once operators register missing individuals, they will appear here.'}
          </p>
          {hasActiveFilters ? (
            <button className="btn-outline" onClick={clearFilters}>
              Clear filters
            </button>
          ) : (
            <button className="btn btn-primary" onClick={() => navigate('/register')}>
              <UserPlus size={16} />
              Register a person
            </button>
          )}
        </div>
      ) : view === 'grid' ? (
        /* ── Grid view ────────────────── */
        <div className="persons-grid">
          {persons.map((person) => (
            <div className="person-card" key={person.id}>
              <div
                className="person-card-photo"
                onClick={() =>
                  person.photoUrl &&
                  setPreviewImage({ src: person.photoUrl, alt: person.name })
                }
                role={person.photoUrl ? 'button' : undefined}
                aria-label={person.photoUrl ? `View photo of ${person.name}` : undefined}
                tabIndex={person.photoUrl ? 0 : undefined}
                onKeyDown={(e) => {
                  if (person.photoUrl && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault()
                    setPreviewImage({ src: person.photoUrl, alt: person.name })
                  }
                }}
              >
                <PersonPhoto
                  url={person.photoUrl}
                  name={person.name}
                  className=""
                  fallbackClass="person-card-photo-fallback"
                />
              </div>

              <div className="person-card-body">
                <div className="person-card-name">{person.name}</div>

                <div className="person-card-meta">
                  <span>Age {person.age}</span>
                  <span className={genderBadgeClass(person.gender)}>{person.gender}</span>
                </div>

                <div className="person-card-detail">
                  <Calendar />
                  {formatDate(person.missingDate)}
                </div>

                <div className="person-card-detail">
                  <MapPin />
                  {person.missingLocation}
                </div>

                {person.description && (
                  <p className="person-card-desc">{person.description}</p>
                )}
              </div>

              <div className="person-card-footer">
                <button
                  className="btn-delete"
                  onClick={() => setDeleteTarget(person)}
                  aria-label={`Delete ${person.name}`}
                >
                  <Trash2 />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* ── Table view ───────────────── */
        <div className="persons-table-wrapper">
          <table className="persons-table">
            <thead>
              <tr>
                <th>Photo</th>
                <th>Name</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Missing Date</th>
                <th>Location</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {persons.map((person) => (
                <tr key={person.id}>
                  <td>
                    {person.photoUrl ? (
                      <img
                        src={person.photoUrl}
                        alt={`Photo of ${person.name}`}
                        className="table-photo"
                        onError={(e) => {
                          e.target.style.display = 'none'
                          e.target.nextElementSibling &&
                            (e.target.nextElementSibling.style.display = 'flex')
                        }}
                        onClick={() =>
                          setPreviewImage({ src: person.photoUrl, alt: person.name })
                        }
                      />
                    ) : null}
                    <div
                      className="table-photo-fallback"
                      style={{ display: person.photoUrl ? 'none' : 'flex' }}
                    >
                      <ImageOff />
                    </div>
                  </td>
                  <td className="table-name">{person.name}</td>
                  <td>{person.age}</td>
                  <td>
                    <span className={genderBadgeClass(person.gender)}>{person.gender}</span>
                  </td>
                  <td>{formatDate(person.missingDate)}</td>
                  <td>{person.missingLocation}</td>
                  <td>
                    <button
                      className="btn-delete"
                      onClick={() => setDeleteTarget(person)}
                      aria-label={`Delete ${person.name}`}
                    >
                      <Trash2 />
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
