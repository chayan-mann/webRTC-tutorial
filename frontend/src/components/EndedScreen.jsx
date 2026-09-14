import RecordingsList from './RecordingsList.jsx'

export default function EndedScreen({ sessionId, onBackToHome }) {
  return (
    <div className="ended-page">
      <div className="ended-card">
        <button className="back-home-button" onClick={onBackToHome}>
          ← Back to Home
        </button>
        <div className="ended-header">
          <h1>Interview Ended</h1>
          <p>Thanks — your recording has been saved.</p>
          <p className="session-id">Session ID: {sessionId}</p>
        </div>
        <RecordingsList sessionId={sessionId} />
      </div>
    </div>
  )
}
