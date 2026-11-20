import { useEffect, useRef, useState } from 'react'
import Sidebar from '../components/Sidebar'

type Message = {
  role: 'user' | 'bot'
  text: string
}

type Status = 'idle' | 'listening' | 'processing' | 'speaking'

const WS_URL = import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/voice`
const SILENCE_THRESHOLD = 0.015
const SILENCE_DURATION_MS = 900      // reduced from 1500ms — cuts perceived latency, small risk of cutting off long mid-sentence pauses
const SAMPLE_RATE = 16000
const BARGE_IN_THRESHOLD = 0.04      // louder than silence — user is actively speaking
const BARGE_IN_HOLD_MS = 300         // must speak for 300ms to trigger barge-in
const SPEECH_START_THRESHOLD = 0.025 // RMS must exceed this to begin recording
const SPEECH_START_HOLD_MS = 350     // must sustain speech for 350ms before recording starts
const MIN_SPEECH_MS = 600            // ignore recordings shorter than 600ms (noise/cough)
const HEARTBEAT_INTERVAL_MS = 10000  // keep the backend's 30s silence timeout from firing during long bot playback

export default function VoiceChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string>('')
  const [textInput, setTextInput] = useState('')

  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const analyserRef = useRef<AnalyserNode | null>(null)
  const vadAudioCtxRef = useRef<AudioContext | null>(null)
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const bargeinIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const currentAudioRef = useRef<HTMLAudioElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const isActiveRef = useRef(false)
  const playbackIdRef = useRef(0)
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    return () => stopSession()
  }, [])

  function stopCurrentAudio() {
    playbackIdRef.current++
    window.speechSynthesis?.cancel()
    if (bargeinIntervalRef.current) { clearInterval(bargeinIntervalRef.current); bargeinIntervalRef.current = null }
    if (currentAudioRef.current) { currentAudioRef.current.pause(); currentAudioRef.current = null }
  }

  function stopListening() {
    if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.onstop = null  // prevent onstop from sending audio
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current = null
    }
    audioChunksRef.current = []
  }

  function startHeartbeat() {
    if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current)
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, HEARTBEAT_INTERVAL_MS)
  }

  function stopHeartbeat() {
    if (heartbeatIntervalRef.current) { clearInterval(heartbeatIntervalRef.current); heartbeatIntervalRef.current = null }
  }

  function stopSession() {
    isActiveRef.current = false
    stopHeartbeat()
    stopCurrentAudio()
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (vadAudioCtxRef.current) { vadAudioCtxRef.current.close(); vadAudioCtxRef.current = null }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStatus('idle')
  }

  async function startSession() {
    // Guard against double-invocation (e.g. rapid double-click) leaving an
    // orphaned prior connection whose later close event would still fire
    // the shared onclose handler and show a spurious "Connection closed."
    if (wsRef.current) return

    setError('')
    setMessages([])

    // Connect WebSocket
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'empty') {
        if (isActiveRef.current) startListening()
        return
      }
      if (data.type === 'error') {
        setError(data.message)
        setStatus('idle')
        return
      }
      if (data.type === 'timeout') {
        isActiveRef.current = false
        setMessages(prev => [...prev, { role: 'bot', text: data.bot_text }])
        setStatus('idle')
        return
      }
      if (data.type === 'response') {
        stopCurrentAudio()
        setMessages(prev => [
          ...prev,
          { role: 'bot', text: data.bot_text },
        ])

        if (data.bot_text) {
          setStatus('speaking')
          const interrupted = data.audio_base64
            ? await playAudioWithBargein(data.audio_base64)
            : await speakWithBargein(data.bot_text)
          if (interrupted) return
        }

        if (isActiveRef.current) startListening()
      }
    }

    ws.onerror = () => setError('WebSocket connection failed. Backend running?')
    ws.onclose = () => {
      stopHeartbeat()
      if (isActiveRef.current) setError('Connection closed.')
      setStatus('idle')
    }

    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => resolve()
      setTimeout(() => reject(new Error('WS timeout')), 60000)
    }).catch(e => { setError(e.message); return })

    startHeartbeat()

    // Mic access + persistent analyser for barge-in detection
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const vadCtx = new AudioContext()
      vadAudioCtxRef.current = vadCtx
      const src = vadCtx.createMediaStreamSource(stream)
      const analyser = vadCtx.createAnalyser()
      analyser.fftSize = 512
      src.connect(analyser)
      analyserRef.current = analyser

      isActiveRef.current = true
      // Tell backend we're ready — it will send the greeting first,
      // and startListening() will be called after the greeting audio ends
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ready' }))
      }
    } catch {
      setError('Microphone access denied.')
    }
  }

  function getRMS(): number {
    const analyser = analyserRef.current
    if (!analyser) return 0
    const data = new Uint8Array(analyser.frequencyBinCount)
    analyser.getByteTimeDomainData(data)
    let sum = 0
    for (let i = 0; i < data.length; i++) {
      const v = (data[i] - 128) / 128
      sum += v * v
    }
    return Math.sqrt(sum / data.length)
  }

  function startListening() {
    if (!isActiveRef.current || !streamRef.current) return
    setStatus('listening')
    audioChunksRef.current = []

    const stream = streamRef.current
    let speechHoldStart: number | null = null
    let recorder: MediaRecorder | null = null
    let recordingStart: number | null = null

    // Phase 1: wait for sustained speech before starting recorder
    const waitForSpeech = () => {
      if (!isActiveRef.current) return
      // If recorder already started, switch to silence detection
      if (recorder && recorder.state === 'recording') {
        checkSilence()
        return
      }
      const rms = getRMS()
      if (rms > SPEECH_START_THRESHOLD) {
        if (speechHoldStart === null) speechHoldStart = Date.now()
        else if (Date.now() - speechHoldStart >= SPEECH_START_HOLD_MS) {
          // Real speech detected — start recording
          recorder = new MediaRecorder(stream)
          mediaRecorderRef.current = recorder
          recordingStart = Date.now()

          recorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunksRef.current.push(e.data)
          }

          recorder.onstop = async () => {
            if (!isActiveRef.current) return
            const duration = recordingStart ? Date.now() - recordingStart : 0
            if (audioChunksRef.current.length === 0 || duration < MIN_SPEECH_MS) {
              // Too short — likely noise, go back to listening
              audioChunksRef.current = []
              startListening()
              return
            }
            setStatus('processing')
            const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
            const arrayBuffer = await blob.arrayBuffer()
            const wavBuffer = await convertToWav(arrayBuffer)
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(wavBuffer)
            }
          }

          recorder.start(100)
          silenceTimerRef.current = setTimeout(checkSilence, 200)
          return
        }
      } else {
        speechHoldStart = null
      }
      silenceTimerRef.current = setTimeout(waitForSpeech, 100)
    }

    // Phase 2: silence detection after speech started
    let silenceStart: number | null = null
    const checkSilence = () => {
      if (!isActiveRef.current || !recorder) return
      const rms = getRMS()
      if (rms < SILENCE_THRESHOLD) {
        if (silenceStart === null) silenceStart = Date.now()
        else if (Date.now() - silenceStart > SILENCE_DURATION_MS) {
          if (recorder.state === 'recording') recorder.stop()
          return
        }
      } else {
        silenceStart = null
      }
      if (recorder.state === 'recording') {
        silenceTimerRef.current = setTimeout(checkSilence, 200)
      }
    }

    silenceTimerRef.current = setTimeout(waitForSpeech, 100)
  }

  async function convertToWav(webmBuffer: ArrayBuffer): Promise<ArrayBuffer> {
    const audioCtx = new OfflineAudioContext(1, SAMPLE_RATE * 10, SAMPLE_RATE)
    const decoded = await audioCtx.decodeAudioData(webmBuffer.slice(0))
    const offlineCtx = new OfflineAudioContext(1, decoded.length, SAMPLE_RATE)
    const src = offlineCtx.createBufferSource()
    src.buffer = decoded
    src.connect(offlineCtx.destination)
    src.start()
    const rendered = await offlineCtx.startRendering()
    return audioBufferToWav(rendered)
  }

  function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
    const numChannels = 1
    const sampleRate = buffer.sampleRate
    const format = 1 // PCM
    const bitDepth = 16
    const samples = buffer.getChannelData(0)
    const dataLength = samples.length * 2
    const bufferLength = 44 + dataLength
    const arrayBuffer = new ArrayBuffer(bufferLength)
    const view = new DataView(arrayBuffer)

    const writeString = (offset: number, str: string) => {
      for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
    }
    writeString(0, 'RIFF')
    view.setUint32(4, 36 + dataLength, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, format, true)
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * numChannels * (bitDepth / 8), true)
    view.setUint16(32, numChannels * (bitDepth / 8), true)
    view.setUint16(34, bitDepth, true)
    writeString(36, 'data')
    view.setUint32(40, dataLength, true)

    let offset = 44
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]))
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
      offset += 2
    }
    return arrayBuffer
  }

  // ElevenLabs audio playback with barge-in
  async function playAudioWithBargein(base64: string): Promise<boolean> {
    const myId = ++playbackIdRef.current
    return new Promise<boolean>((resolve) => {
      const binary = atob(base64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
      const blob = new Blob([bytes], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      currentAudioRef.current = audio

      const cleanup = (interrupted: boolean) => {
        // If a newer playback has started, this one is superseded — do nothing
        if (playbackIdRef.current !== myId) { URL.revokeObjectURL(url); resolve(false); return }
        if (bargeinIntervalRef.current) { clearInterval(bargeinIntervalRef.current); bargeinIntervalRef.current = null }
        URL.revokeObjectURL(url)
        currentAudioRef.current = null
        if (interrupted && isActiveRef.current) startListening()
        resolve(interrupted)
      }

      audio.onended = () => cleanup(false)
      audio.onerror = () => cleanup(false)

      let voiceStart: number | null = null
      bargeinIntervalRef.current = setInterval(() => {
        if (playbackIdRef.current !== myId) { clearInterval(bargeinIntervalRef.current!); bargeinIntervalRef.current = null; resolve(false); return }
        if (!isActiveRef.current) { cleanup(false); return }
        const rms = getRMS()
        if (rms > BARGE_IN_THRESHOLD) {
          if (voiceStart === null) voiceStart = Date.now()
          else if (Date.now() - voiceStart > BARGE_IN_HOLD_MS) {
            audio.pause()
            cleanup(true)
          }
        } else {
          voiceStart = null
        }
      }, 100)

      audio.play().catch(() => cleanup(false))
    })
  }

  // Browser TTS fallback with barge-in
  async function speakWithBargein(text: string): Promise<boolean> {
    const myId = ++playbackIdRef.current
    return new Promise<boolean>((resolve) => {
      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'en-US'
      utterance.rate = 1.0

      const cleanup = (interrupted: boolean) => {
        if (playbackIdRef.current !== myId) { resolve(false); return }
        if (bargeinIntervalRef.current) { clearInterval(bargeinIntervalRef.current); bargeinIntervalRef.current = null }
        if (interrupted && isActiveRef.current) startListening()
        resolve(interrupted)
      }

      utterance.onend = () => cleanup(false)
      utterance.onerror = () => cleanup(false)

      let voiceStart: number | null = null
      bargeinIntervalRef.current = setInterval(() => {
        if (playbackIdRef.current !== myId) { clearInterval(bargeinIntervalRef.current!); bargeinIntervalRef.current = null; resolve(false); return }
        if (!isActiveRef.current) { cleanup(false); return }
        const rms = getRMS()
        if (rms > BARGE_IN_THRESHOLD) {
          if (voiceStart === null) voiceStart = Date.now()
          else if (Date.now() - voiceStart > BARGE_IN_HOLD_MS) {
            window.speechSynthesis.cancel()
            cleanup(true)
          }
        } else {
          voiceStart = null
        }
      }, 100)

      window.speechSynthesis.speak(utterance)
    })
  }

  const statusConfig = {
    idle: { label: 'Ready', color: 'text-gray-400', dot: 'bg-gray-500', pulse: false },
    listening: { label: 'Listening...', color: 'text-green-400', dot: 'bg-green-400', pulse: true },
    processing: { label: 'Processing...', color: 'text-yellow-400', dot: 'bg-yellow-400', pulse: false },
    speaking: { label: 'Speaking...', color: 'text-blue-400', dot: 'bg-blue-400', pulse: true },
  }
  const s = statusConfig[status]

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        {/* Header */}
        <div className="px-8 py-5 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Voice Chat</h1>
            <p className="text-sm text-gray-400 mt-0.5">Real-time AI voice support</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${s.dot} ${s.pulse ? 'animate-pulse' : ''}`} />
            <span className={`text-sm font-medium ${s.color}`}>{s.label}</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-4">
          {messages.length === 0 && status === 'idle' && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-blue-900/20 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <p className="text-gray-400">Start session to begin voice chat</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-lg px-4 py-3 rounded-2xl text-sm ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-gray-800 text-gray-100 rounded-bl-sm'
              }`}>
                <p className={`text-xs mb-1 font-medium ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-500'}`}>
                  {msg.role === 'user' ? 'You' : 'Briha'}
                </p>
                {msg.text}
              </div>
            </div>
          ))}

          {status === 'processing' && (
            <div className="flex justify-start">
              <div className="bg-gray-800 px-4 py-3 rounded-2xl rounded-bl-sm">
                <div className="flex gap-1 items-center">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Error */}
        {error && (
          <div className="mx-8 mb-2 px-4 py-2 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Text Input */}
        {status !== 'idle' && (
          <div className="px-8 pb-3 flex gap-2">
            <input
              type="text"
              value={textInput}
              onChange={e => setTextInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && textInput.trim()) {
                  stopCurrentAudio()
                  stopListening()
                  if (wsRef.current?.readyState === WebSocket.OPEN) {
                    wsRef.current.send(JSON.stringify({ text: textInput.trim() }))
                    setStatus('processing')
                    setTextInput('')
                  }
                }
              }}
              placeholder="Type a message..."
              className="flex-1 bg-gray-800 text-white text-sm rounded-xl px-4 py-2 border border-gray-700 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={() => {
                if (textInput.trim() && wsRef.current?.readyState === WebSocket.OPEN) {
                  stopCurrentAudio()
                  stopListening()
                  wsRef.current.send(JSON.stringify({ text: textInput.trim() }))
                  setStatus('processing')
                  setTextInput('')
                }
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-colors"
            >
              Send
            </button>
          </div>
        )}

        {/* Controls */}
        <div className="px-8 py-5 border-t border-gray-800 flex items-center justify-center gap-4">
          {status === 'idle' ? (
            <button
              onClick={startSession}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-full font-medium transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              Start Session
            </button>
          ) : (
            <>
              {status === 'listening' && (
                <button
                  onClick={() => {
                    stopCurrentAudio()
                    if (mediaRecorderRef.current?.state === 'recording') {
                      mediaRecorderRef.current.stop()
                    }
                  }}
                  className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-full font-medium transition-colors"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M2 12l7-7v4h13v6H9v4z" />
                  </svg>
                  Send
                </button>
              )}
              <button
                onClick={stopSession}
                className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-full font-medium transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
                End Session
              </button>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
