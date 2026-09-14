const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path, options) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Request to ${path} failed: ${res.status} ${text}`)
  }
  return res.json()
}

export function createSession(username, email) {
  return request('/sessions', {
    method: 'POST',
    body: JSON.stringify({ username, email }),
  })
}

export function sendOffer(sessionId, localDescription) {
  return request(`/sessions/${sessionId}/webrtc/offer`, {
    method: 'POST',
    body: JSON.stringify({
      sdp: localDescription.sdp,
      type: localDescription.type,
    }),
  })
}

export function endSession(sessionId) {
  return request(`/sessions/${sessionId}/end`, { method: 'POST' })
}

export function getSegments(sessionId) {
  return request(`/sessions/${sessionId}/segments`)
}

export function segmentVideoUrl(sessionId, segmentIndex) {
  return `${API_BASE_URL}/sessions/${sessionId}/segments/${segmentIndex}/video`
}
