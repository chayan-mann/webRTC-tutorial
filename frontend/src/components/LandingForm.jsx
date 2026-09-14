import { useState } from 'react'

export default function LandingForm({ onSubmit, submitting, error }) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit(username.trim(), email.trim())
  }

  return (
    <div className="landing">
      <form className="landing-form" onSubmit={handleSubmit}>
        <div className="landing-icon">🎥</div>
        <h1>Start Your Interview</h1>
        <p className="landing-subtitle">
          Enter your details below to begin. We'll ask for camera access on the next step.
        </p>

        <label className="field-label" htmlFor="username">
          Username
        </label>
        <input
          id="username"
          type="text"
          placeholder="Enter your username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <label className="field-label" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <button type="submit" disabled={submitting}>
          {submitting ? 'Starting...' : 'Start Session'}
        </button>
        {error && <span className="error-text">{error}</span>}
      </form>
    </div>
  )
}
