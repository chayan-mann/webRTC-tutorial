import { useEffect, useState } from 'react'
import { getSegments, segmentVideoUrl } from '../api.js'

function formatDuration(seconds) {
  if (seconds == null) return '--:--'
  const total = Math.round(seconds)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function RecordingsList({ sessionId }) {
  const [segments, setSegments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeIndex, setActiveIndex] = useState(null)

  useEffect(() => {
    let cancelled = false
    getSegments(sessionId)
      .then((data) => {
        if (cancelled) return
        setSegments(data)
        if (data.length > 0) setActiveIndex(data[0].segment_index)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Failed to load recordings')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [sessionId])

  if (loading) return <p>Loading recordings...</p>
  if (error) return <p className="error-text">{error}</p>
  if (segments.length === 0) return <p>No recordings were saved for this session.</p>

  return (
    <div className="recordings">
      <video
        key={activeIndex}
        className="recordings-player"
        src={segmentVideoUrl(sessionId, activeIndex)}
        controls
        autoPlay
      />
      <div className="recordings-grid">
        {segments.map((seg) => (
          <div
            key={seg.segment_index}
            className={`recording-card ${seg.segment_index === activeIndex ? 'active' : ''}`}
          >
            <button
              className="recording-card-play"
              onClick={() => setActiveIndex(seg.segment_index)}
            >
              <span className="recording-card-title">Part {seg.segment_index + 1}</span>
              <span className="recording-card-duration">{formatDuration(seg.duration_seconds)}</span>
            </button>
            <a
              className="recording-card-download"
              href={segmentVideoUrl(sessionId, seg.segment_index)}
              download={`segment_${seg.segment_index + 1}.webm`}
            >
              Download
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}
