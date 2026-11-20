import AudioPlayer from './AudioPlayer'

interface Turn {
  role: string
  content: string
}

interface CallRecord {
  id: number
  start_time: string
  end_time: string
  duration_seconds: number
  language: string
  escalated: boolean
  transcript: Turn[]
  audio_path?: string
}

interface Props {
  record: CallRecord
  onClose: () => void
}

export default function TranscriptModal({ record, onClose }: Props) {
  const langLabel: Record<string, string> = { en: 'EN', ur: 'UR', 'roman-ur': 'Roman UR' }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col border border-gray-700">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div>
            <h3 className="text-lg font-bold text-white">Call Transcript</h3>
            <div className="flex gap-2 mt-1">
              <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded">
                {langLabel[record.language] || record.language}
              </span>
              {record.escalated && (
                <span className="text-xs bg-red-900/50 text-red-400 px-2 py-0.5 rounded">Escalated</span>
              )}
              <span className="text-xs text-gray-400">{Math.round(record.duration_seconds)}s</span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl leading-none">&times;</button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {record.audio_path && (
            <div className="mb-4">
              <AudioPlayer callId={record.id} />
            </div>
          )}

          <div className="space-y-3">
            {(record.transcript || []).map((turn, i) => (
              <div
                key={i}
                className={`flex gap-3 ${turn.role === 'assistant' ? 'flex-row-reverse' : ''}`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                    turn.role === 'user' ? 'bg-gray-700 text-gray-300' : 'bg-blue-900/30 text-blue-400'
                  }`}
                >
                  {turn.role === 'user' ? 'C' : 'B'}
                </div>
                <div
                  className={`max-w-lg px-4 py-3 rounded-2xl text-sm ${
                    turn.role === 'user'
                      ? 'bg-gray-800 text-white'
                      : 'bg-blue-900/10 text-white border border-blue-900/30'
                  }`}
                >
                  <p className="text-xs text-gray-400 mb-1">
                    {turn.role === 'user' ? 'Customer' : 'Bot'}
                  </p>
                  {turn.content}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
