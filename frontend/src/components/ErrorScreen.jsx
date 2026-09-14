export default function ErrorScreen({ message, onBackToHome }) {
  return (
    <div className="ended-page">
      <div className="ended-card ended-card-narrow">
        <button className="back-home-button" onClick={onBackToHome}>
          ← Back to Home
        </button>
        <div className="ended-header">
          <h1>Something went wrong</h1>
          <p className="error-text">{message}</p>
        </div>
      </div>
    </div>
  )
}
