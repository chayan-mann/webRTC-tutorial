import { useState } from 'react'
import LandingForm from './components/LandingForm.jsx'
import InterviewSession from './components/InterviewSession.jsx'
import EndedScreen from './components/EndedScreen.jsx'
import ErrorScreen from './components/ErrorScreen.jsx'
import { createSession } from './api.js'

export default function App() {
  const [stage, setStage] = useState('landing') // landing | session | ended | error
  const [sessionId, setSessionId] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleStart(username, email) {
    setSubmitting(true)
    setError(null)
    try {
      const { session_id: id } = await createSession(username, email)
      setSessionId(id)
      setStage('session')
    } catch (err) {
      setError(err.message || 'Failed to start session')
    } finally {
      setSubmitting(false)
    }
  }

  function handleEnded() {
    setStage('ended')
  }

  function handleSessionError(message) {
    setError(message)
    setStage('error')
  }

  function handleBackToHome() {
    setSessionId(null)
    setError(null)
    setStage('landing')
  }

  if (stage === 'landing') {
    return <LandingForm onSubmit={handleStart} submitting={submitting} error={error} />
  }

  if (stage === 'session' && sessionId) {
    return (
      <InterviewSession sessionId={sessionId} onEnded={handleEnded} onError={handleSessionError} />
    )
  }

  if (stage === 'ended') {
    return <EndedScreen sessionId={sessionId} onBackToHome={handleBackToHome} />
  }

  return <ErrorScreen message={error} onBackToHome={handleBackToHome} />
}
