import { useState, useEffect, useCallback, useRef } from 'react'
import {
  History as HistoryIcon,
  RotateCw,
  Filter,
  Camera,
  ImageOff,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  X,
  AlertTriangle,
  Radio
} from 'lucide-react'
import { getDetections, getPersonOptions } from '../services/detectionsApi'
import '../styles/History.css'

// ── Date formatter: "19 Oct 2026, 11:42 AM" ───────────────────────
function formatDateTime(isoString) {
  if (!isoString) return '—'
  const d = new Date(isoString)
  if (isNaN(d.getTime())) return isoString

  const datePart = d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })

  const timePart = d.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })

  return `${datePart}, ${timePart}`
}

// ── Confidence Badge Component ─────────────────────────────────────
export function ConfidenceBadge({ confidence }) {
  const val = Math.round(Number(confidence) || 0)
  let modifier = 'low'
  if (val >= 90) {
    modifier = 'high'
  } else if (val >= 75) {
    modifier = 'medium'
  }

  return (
    <span
      className={`confidence-badge confidence-badge--${modifier}`}
      title={`Match Confidence: ${val}%`}
    >
      {val}%
    </span>
  )
}

// ── Scene Thumbnail with graceful fallback ─────────────────────────
function SceneThumbnail({ src, alt }) {
  const [hasError, setHasError] = useState(false)

  if (!src || hasError) {
    return (
      <div className="thumb-container" aria-label="No thumbnail available">
        <div className="thumb-fallback">
          <ImageOff />
        </div>
      </div>
    )
  }

  return (
    <div className="thumb-container">
      <img
        src={src}
        alt={alt || 'Scene thumbnail'}
        className="thumb-img"
        onError={() => setHasError(true)}
        loading="lazy"
      />
    </div>
  )
}

// ── Scene Modal Component with navigation and focus management ─────
export function SceneModal({
  detection,
  currentIndex,
  totalInView,
  hasPrev,
  hasNext,
  onPrev,
  onNext,
  onClose,
  triggerRef
}) {
  const [imgError, setImgError] = useState(false)
  const modalContainerRef = useRef(null)
  const closeBtnRef = useRef(null)

  // Focus management: initial focus inside modal, return focus to trigger on unmount
  useEffect(() => {
    closeBtnRef.current?.focus()
    const previousActiveElement = triggerRef?.current

    return () => {
      previousActiveElement?.focus?.()
    }
  }, [triggerRef])

  // Keyboard navigation: Esc to close, ArrowLeft for prev, ArrowRight for next
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      } else if (e.key === 'ArrowLeft' && hasPrev) {
        e.preventDefault()
        onPrev()
      } else if (e.key === 'ArrowRight' && hasNext) {
        e.preventDefault()
        onNext()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [hasPrev, hasNext, onPrev, onNext, onClose])

  if (!detection) return null

  return (
    <div
      className="scene-modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-detection-title"
    >
      <div
        className="scene-modal-container"
        ref={modalContainerRef}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="scene-modal-header">
          <div className="scene-modal-title">
            <h3 id="modal-detection-title">Detection Verification</h3>
            <span className="scene-modal-counter">
              {currentIndex + 1} of {totalInView}
            </span>
          </div>

          <div className="scene-modal-actions">
            <button
              type="button"
              className="modal-nav-btn"
              onClick={onPrev}
              disabled={!hasPrev}
              aria-label="Previous detection (Left Arrow)"
              title="Previous detection (Left Arrow)"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              type="button"
              className="modal-nav-btn"
              onClick={onNext}
              disabled={!hasNext}
              aria-label="Next detection (Right Arrow)"
              title="Next detection (Right Arrow)"
            >
              <ChevronRight size={18} />
            </button>
            <button
              type="button"
              className="modal-close-btn"
              ref={closeBtnRef}
              onClick={onClose}
              aria-label="Close dialog (Escape)"
              title="Close (Escape)"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="scene-modal-body">
          <div className="scene-image-area">
            {detection.sceneImageUrl && !imgError ? (
              <img
                src={detection.sceneImageUrl}
                alt={`Surveillance scene capturing ${detection.personName}`}
                className="scene-full-image"
                onError={() => setImgError(true)}
              />
            ) : (
              <div className="scene-fallback">
                <Camera />
                <p>Scene snapshot unavailable</p>
              </div>
            )}
          </div>

          <div className="scene-details-panel">
            <div className="detail-item">
              <span className="detail-label">Subject Match</span>
              <span className="detail-value detail-value--name">
                {detection.personName}
              </span>
            </div>

            <div className="detail-item">
              <span className="detail-label">Confidence Score</span>
              <div>
                <ConfidenceBadge confidence={detection.confidence} />
              </div>
            </div>

            <div className="detail-item">
              <span className="detail-label">Camera Feed</span>
              <span className="detail-value">{detection.cameraSource}</span>
            </div>

            <div className="detail-item">
              <span className="detail-label">Timestamp</span>
              <span className="detail-value">
                {formatDateTime(detection.detectedAt)}
              </span>
            </div>

            <div className="detail-item">
              <span className="detail-label">Reference ID</span>
              <span className="detail-value" style={{ fontFamily: 'monospace', fontSize: '0.8125rem' }}>
                {detection.id}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Skeleton rows for loading state ────────────────────────────────
function SkeletonRows({ count = 10 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <tr key={i} className="skeleton-row" aria-hidden="true">
          <td>
            <div className="skeleton-shimmer skeleton-shimmer--thumb" />
          </td>
          <td>
            <div className="skeleton-shimmer skeleton-shimmer--md" />
          </td>
          <td>
            <div className="skeleton-shimmer skeleton-shimmer--lg" />
          </td>
          <td>
            <div className="skeleton-shimmer skeleton-shimmer--sm" />
          </td>
          <td>
            <div className="skeleton-shimmer skeleton-shimmer--md" />
          </td>
        </tr>
      ))}
    </>
  )
}

// ── Pagination Controls Component ──────────────────────────────────
function Pagination({ page, pageSize, total, onPageChange, onPageSizeChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  // Generate numbered pages with ellipsis
  const getPageNumbers = () => {
    const pages = []
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      if (page > 3) pages.push('ellipsis-start')

      const start = Math.max(2, page - 1)
      const end = Math.min(totalPages - 1, page + 1)
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }

      if (page < totalPages - 2) pages.push('ellipsis-end')
      pages.push(totalPages)
    }
    return pages
  }

  return (
    <div className="history-pagination">
      <div className="pagination-size">
        <label htmlFor="history-page-size">Rows per page:</label>
        <select
          id="history-page-size"
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
        </select>
      </div>

      <nav className="pagination-controls" aria-label="Detection pagination">
        <button
          type="button"
          className="pagination-btn"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Go to previous page"
        >
          <ChevronLeft size={16} />
        </button>

        {getPageNumbers().map((item, idx) => {
          if (typeof item === 'string') {
            return (
              <span key={`ellipsis-${idx}`} className="pagination-ellipsis" aria-hidden="true">
                …
              </span>
            )
          }

          const isActive = item === page
          return (
            <button
              key={item}
              type="button"
              className={`pagination-btn ${isActive ? 'active' : ''}`}
              onClick={() => onPageChange(item)}
              aria-label={`Page ${item}`}
              aria-current={isActive ? 'page' : undefined}
            >
              {item}
            </button>
          )
        })}

        <button
          type="button"
          className="pagination-btn"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Go to next page"
        >
          <ChevronRight size={16} />
        </button>
      </nav>
    </div>
  )
}

// ════════════════════════════════════════════════════
// Main Page: History Component
// ════════════════════════════════════════════════════
const DEFAULT_FILTERS = {
  person: '',
  dateFrom: '',
  dateTo: '',
  confidenceMin: ''
}

export default function History() {
  // Data state
  const [detections, setDetections] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [personOptions, setPersonOptions] = useState([])

  // Query & control state
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [sortBy, setSortBy] = useState('detectedAt') // 'detectedAt' | 'confidence'
  const [sortOrder, setSortOrder] = useState('desc') // 'asc' | 'desc'

  // Modal inspection state
  const [modalIndex, setModalIndex] = useState(null)
  const selectedRowRef = useRef(null)

  // Load person options once on mount
  useEffect(() => {
    let isMounted = true
    getPersonOptions()
      .then((opts) => {
        if (isMounted) setPersonOptions(opts || [])
      })
      .catch((err) => {
        console.error('Failed to load person options:', err)
      })
    return () => {
      isMounted = false
    }
  }, [])

  // ── Fetch detections ──────────────────────────────────────────
  const fetchDetections = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getDetections({
        page,
        pageSize,
        person: filters.person,
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        confidenceMin: filters.confidenceMin,
        sortBy,
        sortOrder
      })

      setDetections(res.items || [])
      setTotal(res.total || 0)
    } catch (err) {
      setError(err.message || 'Failed to retrieve detection history.')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, filters, sortBy, sortOrder])

  useEffect(() => {
    fetchDetections()
  }, [fetchDetections])

  // ── Filter mutations (resets to page 1) ────────────────────────
  const updateFilter = (field, value) => {
    setFilters((prev) => ({ ...prev, [field]: value }))
    setPage(1)
  }

  const clearFilters = () => {
    setFilters(DEFAULT_FILTERS)
    setPage(1)
  }

  const hasActiveFilters = Object.values(filters).some((val) => val !== '')

  // ── Sorting handler ───────────────────────────────────────────
  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
    setPage(1)
  }

  // ── Result count calculation ──────────────────────────────────
  const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1
  const endItem = Math.min(total, page * pageSize)

  // ── Modal navigation ──────────────────────────────────────────
  const activeDetection = modalIndex !== null ? detections[modalIndex] : null
  const hasPrev = modalIndex !== null && modalIndex > 0
  const hasNext = modalIndex !== null && modalIndex < detections.length - 1

  return (
    <>
      {/* ── Page Header ────────────────────────────── */}
      <div className="history-header">
        <div className="history-header-left">
          <div className="history-count">
            {!loading && !error && (
              <>
                Showing <strong>{startItem}–{endItem}</strong> of{' '}
                <strong>{total}</strong> detections
              </>
            )}
          </div>
        </div>

        <div className="history-header-actions">
          <button
            type="button"
            className={`btn-refresh ${loading ? 'spinning' : ''}`}
            onClick={fetchDetections}
            disabled={loading}
            aria-label="Refresh detections"
          >
            <RotateCw size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* ── Filter Bar ─────────────────────────────── */}
      <div
        className="history-filters"
        role="search"
        aria-label="Filter detection records"
      >
        <div className="filter-group filter-person">
          <label htmlFor="history-person-select">Person</label>
          <select
            id="history-person-select"
            value={filters.person}
            onChange={(e) => updateFilter('person', e.target.value)}
          >
            <option value="">All Persons</option>
            {personOptions.map((opt) => (
              <option key={opt.id} value={opt.name}>
                {opt.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group filter-date">
          <label htmlFor="history-date-from">Date From</label>
          <input
            id="history-date-from"
            type="date"
            value={filters.dateFrom}
            onChange={(e) => updateFilter('dateFrom', e.target.value)}
          />
        </div>

        <div className="filter-group filter-date">
          <label htmlFor="history-date-to">Date To</label>
          <input
            id="history-date-to"
            type="date"
            value={filters.dateTo}
            onChange={(e) => updateFilter('dateTo', e.target.value)}
          />
        </div>

        <div className="filter-group filter-confidence">
          <label htmlFor="history-confidence-min">Min Confidence</label>
          <select
            id="history-confidence-min"
            value={filters.confidenceMin}
            onChange={(e) => updateFilter('confidenceMin', e.target.value)}
          >
            <option value="">Any Confidence</option>
            <option value="70">70% and above</option>
            <option value="80">80% and above</option>
            <option value="90">90% and above</option>
          </select>
        </div>

        {hasActiveFilters && (
          <button
            type="button"
            className="filter-clear-btn"
            onClick={clearFilters}
            aria-label="Clear all active filters"
          >
            <Filter size={14} />
            <span>Clear filters</span>
          </button>
        )}
      </div>

      {/* ── Main Content Area ──────────────────────── */}
      {error ? (
        <div className="history-state" role="alert">
          <AlertTriangle />
          <h3>Unable to Load Detections</h3>
          <p>{error}</p>
          <button
            type="button"
            className="btn-state-action"
            onClick={fetchDetections}
          >
            <RotateCw size={14} />
            Retry
          </button>
        </div>
      ) : !loading && detections.length === 0 ? (
        <div className="history-state">
          <HistoryIcon />
          {hasActiveFilters ? (
            <>
              <h3>No detections match your filters</h3>
              <p>
                Try widening your date range, lowering the confidence threshold,
                or resetting your search filters.
              </p>
              <button
                type="button"
                className="btn-state-action"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            </>
          ) : (
            <>
              <h3>No detections recorded yet</h3>
              <p>
                Live camera streams are scanning for registered missing individuals.
                When verified facial matches occur, detection snapshots will appear here.
              </p>
            </>
          )}
        </div>
      ) : (
        <div className="history-table-card">
          <div className="history-table-wrapper">
            <table className="history-table">
              <thead>
                <tr>
                  <th scope="col" style={{ width: '80px' }}>
                    Scene
                  </th>
                  <th scope="col">Person</th>
                  <th
                    scope="col"
                    className={`sortable ${sortBy === 'detectedAt' ? 'sorted-active' : ''}`}
                    onClick={() => handleSort('detectedAt')}
                    aria-sort={
                      sortBy === 'detectedAt'
                        ? sortOrder === 'asc'
                          ? 'ascending'
                          : 'descending'
                        : 'none'
                    }
                  >
                    <span className="th-content">
                      Detection Time
                      {sortBy === 'detectedAt' ? (
                        sortOrder === 'asc' ? (
                          <ArrowUp className="th-sort-icon" />
                        ) : (
                          <ArrowDown className="th-sort-icon" />
                        )
                      ) : (
                        <ArrowUpDown className="th-sort-icon" />
                      )}
                    </span>
                  </th>
                  <th
                    scope="col"
                    className={`sortable ${sortBy === 'confidence' ? 'sorted-active' : ''}`}
                    onClick={() => handleSort('confidence')}
                    aria-sort={
                      sortBy === 'confidence'
                        ? sortOrder === 'asc'
                          ? 'ascending'
                          : 'descending'
                        : 'none'
                    }
                  >
                    <span className="th-content">
                      Confidence
                      {sortBy === 'confidence' ? (
                        sortOrder === 'asc' ? (
                          <ArrowUp className="th-sort-icon" />
                        ) : (
                          <ArrowDown className="th-sort-icon" />
                        )
                      ) : (
                        <ArrowUpDown className="th-sort-icon" />
                      )}
                    </span>
                  </th>
                  <th scope="col">Camera Source</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <SkeletonRows count={pageSize} />
                ) : (
                  detections.map((item, idx) => (
                    <tr
                      key={item.id}
                      tabIndex={0}
                      onClick={(e) => {
                        selectedRowRef.current = e.currentTarget
                        setModalIndex(idx)
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          selectedRowRef.current = e.currentTarget
                          setModalIndex(idx)
                        }
                      }}
                      aria-label={`View detection of ${item.personName} with ${item.confidence}% confidence`}
                    >
                      <td>
                        <SceneThumbnail
                          src={item.thumbnailUrl || item.sceneImageUrl}
                          alt={`Scene preview for ${item.personName}`}
                        />
                      </td>
                      <td className="table-person-name">{item.personName}</td>
                      <td>{formatDateTime(item.detectedAt)}</td>
                      <td>
                        <ConfidenceBadge confidence={item.confidence} />
                      </td>
                      <td>
                        <span className="table-camera">
                          <Radio size={14} />
                          {item.cameraSource}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* ── Pagination Footer ── */}
          {!loading && total > 0 && (
            <Pagination
              page={page}
              pageSize={pageSize}
              total={total}
              onPageChange={(newPage) => setPage(newPage)}
              onPageSizeChange={(newSize) => {
                setPageSize(newSize)
                setPage(1)
              }}
            />
          )}
        </div>
      )}

      {/* ── Scene Modal ────────────────────────────── */}
      {modalIndex !== null && activeDetection && (
        <SceneModal
          key={activeDetection.id}
          detection={activeDetection}
          currentIndex={modalIndex}
          totalInView={detections.length}
          hasPrev={hasPrev}
          hasNext={hasNext}
          onPrev={() => setModalIndex((idx) => Math.max(0, idx - 1))}
          onNext={() =>
            setModalIndex((idx) => Math.min(detections.length - 1, idx + 1))
          }
          onClose={() => setModalIndex(null)}
          triggerRef={selectedRowRef}
        />
      )}
    </>
  )
}
