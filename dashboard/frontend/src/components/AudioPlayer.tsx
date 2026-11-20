interface Props {
  callId: number
}

export default function AudioPlayer({ callId }: Props) {
  const audioUrl = `http://localhost:8000/calls/${callId}/audio`

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <p className="text-sm text-gray-400 mb-2">Session Audio</p>
      <audio controls className="w-full" src={audioUrl}>
        Your browser does not support the audio element.
      </audio>
    </div>
  )
}
