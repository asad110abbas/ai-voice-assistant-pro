import { useState, useEffect } from 'react'
import { getNotes, addNote } from '../api/tickets'

interface Note {
  id: number
  content: string
  agent_id: number
  created_at: string
}

interface Props {
  ticketId: number
}

export default function NotesPanel({ ticketId }: Props) {
  const [notes, setNotes] = useState<Note[]>([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchNotes = async () => {
    const res = await getNotes(ticketId)
    setNotes(res.data)
  }

  useEffect(() => {
    fetchNotes()
  }, [ticketId])

  const handleSubmit = async () => {
    if (!content.trim()) return
    setLoading(true)
    try {
      await addNote(ticketId, content)
      setContent('')
      fetchNotes()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-700">
      <h4 className="text-sm font-medium text-white mb-3">Internal Notes</h4>
      <div className="space-y-3 mb-4 max-h-48 overflow-y-auto">
        {notes.map((note) => (
          <div key={note.id} className="bg-gray-800 rounded-lg p-3">
            <p className="text-sm text-white">{note.content}</p>
            <p className="text-xs text-gray-400 mt-1">
              Agent #{note.agent_id} · {new Date(note.created_at).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Add internal note..."
        rows={2}
        className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none resize-none"
      />
      <button
        onClick={handleSubmit}
        disabled={loading || !content.trim()}
        className="mt-2 w-full text-white text-sm py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        style={{ backgroundColor: '#49A8FF' }}
      >
        Add Note
      </button>
    </div>
  )
}
