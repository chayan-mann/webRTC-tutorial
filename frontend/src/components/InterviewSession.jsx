import { useEffect, useRef, useState } from 'react'
import { sendOffer, endSession } from '../api.js'
import AiSticker from './AiSticker.jsx'
import EndInterviewButton from './EndInterviewButton.jsx'

const ICE_SERVERS = [{ urls: 'stun:stun.l.google.com:19302' }]

function waitForIceGatheringComplete(pc) {
  if (pc.iceGatheringState === 'complete') return Promise.resolve()
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      pc.removeEventListener('icegatheringstatechange', check)
      resolve()
    }, 5000)
    function check() {
      if (pc.iceGatheringState === 'complete') {
        clearTimeout(timeout)
        pc.removeEventListener('icegatheringstatechange', check)
        resolve()
      }
    }
    pc.addEventListener('icegatheringstatechange', check)
  })
}

function formatElapsed(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  const mm = m.toString().padStart(2, '0')
  const ss = s.toString().padStart(2, '0')
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`
}

export default function InterviewSession({ sessionId, onEnded, onError }) {
  const videoRef = useRef(null)
  const pcRef = useRef(null)
  const streamRef = useRef(null)
  const endingRef = useRef(false)
  const [connected, setConnected] = useState(false)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function setup() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            frameRate: { ideal: 30 },
          },
          audio: true,
        })
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }

        const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS })
        pcRef.current = pc
        stream.getTracks().forEach((track) => pc.addTrack(track, stream))

        pc.addEventListener('connectionstatechange', () => {
          if (pc.connectionState === 'connected') setConnected(true)
        })

        const offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await waitForIceGatheringComplete(pc)

        const answer = await sendOffer(sessionId, pc.localDescription)
        if (cancelled) return
        await pc.setRemoteDescription(answer)
      } catch (err) {
        if (!cancelled) onError(err.message || 'Failed to start recording session')
      }
    }

    setup()

    function handleBeforeUnload() {
      endSession(sessionId).catch(() => {})
    }
    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      cancelled = true
      window.removeEventListener('beforeunload', handleBeforeUnload)
      cleanupLocalResources()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  useEffect(() => {
    if (!connected) return
    const startedAt = Date.now()
    const interval = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [connected])

  function cleanupLocalResources() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (pcRef.current) {
      pcRef.current.close()
      pcRef.current = null
    }
  }

  async function handleEnd() {
    if (endingRef.current) return
    endingRef.current = true
    cleanupLocalResources()
    try {
      await endSession(sessionId)
    } catch (err) {
      // backend also finalizes on connection-state teardown, so surfacing
      // this is best-effort only
      console.error(err)
    }
    onEnded()
  }

  return (
    <div className="interview-stage">
      <video ref={videoRef} className="interview-video" autoPlay muted playsInline />
      {!connected && (
        <div className="connecting-overlay">
          <p>Connecting...</p>
        </div>
      )}
      {connected && (
        <div className="recording-timer">
          <span className="recording-dot" />
          {formatElapsed(elapsedSeconds)}
        </div>
      )}
      <EndInterviewButton onEnd={handleEnd} />
      <AiSticker />
    </div>
  )
}
