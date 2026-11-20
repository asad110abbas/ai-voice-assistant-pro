import { useState, useEffect, useCallback } from 'react'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import FilterBar from '../components/FilterBar'
import TicketCard from '../components/TicketCard'
import NotesPanel from '../components/NotesPanel'
import ExportButton from '../components/ExportButton'
import AudioPlayer from '../components/AudioPlayer'
import { getTickets, updateTicket, assignTicket } from '../api/tickets'
import { getAgents } from '../api/agents'
import { useAuth } from '../auth/AuthContext'

interface Ticket {
  id: number
  issue_summary: string
  status: string
  assigned_to?: number
  call_record_id?: number
  conversation?: Array<{ role: string; content: string }>
  resolution_note?: string
  created_at: string
  assignee?: { name: string }
}

export default function Tickets() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [view, setView] = useState<'kanban' | 'table'>('kanban')
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [selected, setSelected] = useState<Ticket | null>(null)
  const [agents, setAgents] = useState<Array<{ id: number; name: string }>>([])
  const [resolveNote, setResolveNote] = useState('')
  const [showResolveModal, setShowResolveModal] = useState(false)
  const { role } = useAuth()

  const fetchData = useCallback(async () => {
    try {
      const res = await getTickets({ ...filters })
      setTickets(res.data.items)
    } catch (e) {
      console.error(e)
    }
  }, [filters])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  useEffect(() => {
    if (role === 'admin' || role === 'senior_agent') {
      getAgents().then((res) => setAgents(res.data)).catch(() => {})
    }
  }, [role])

  const byStatus = (status: string) => tickets.filter((t) => t.status === status)

  const handleAssign = async (ticketId: number, agentId: number) => {
    await assignTicket(ticketId, agentId)
    fetchData()
  }

  const handleResolve = async () => {
    if (!selected || !resolveNote.trim()) return
    await updateTicket(selected.id, { status: 'resolved', resolution_note: resolveNote })
    setShowResolveModal(false)
    setResolveNote('')
    setSelected(null)
    fetchData()
  }

  const columns = [
    { key: 'open', label: 'Open', borderColor: '#F59E0B' },
    { key: 'assigned', label: 'Assigned', borderColor: '#49A8FF' },
    { key: 'resolved', label: 'Resolved', borderColor: '#10B981' },
  ]

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col">
        <Header title="Escalation Tickets" />
        <main className="flex-1 overflow-auto p-6 pt-20">
          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-2">
              <button
                onClick={() => setView('kanban')}
                className={`text-sm px-4 py-2 rounded-lg transition-colors ${view === 'kanban' ? 'text-white' : 'text-gray-400 border border-gray-700 hover:text-white'}`}
                style={view === 'kanban' ? { backgroundColor: '#49A8FF' } : {}}
              >
                Kanban
              </button>
              <button
                onClick={() => setView('table')}
                className={`text-sm px-4 py-2 rounded-lg transition-colors ${view === 'table' ? 'text-white' : 'text-gray-400 border border-gray-700 hover:text-white'}`}
                style={view === 'table' ? { backgroundColor: '#49A8FF' } : {}}
              >
                Table
              </button>
            </div>
            <ExportButton type="tickets" />
          </div>

          {view === 'table' && (
            <FilterBar
              filters={filters}
              onChange={(k, v) => setFilters((p) => ({ ...p, [k]: v }))}
              onClear={() => setFilters({})}
              statusOptions={['open', 'assigned', 'resolved']}
            />
          )}

          {view === 'kanban' ? (
            <div className="grid grid-cols-3 gap-4 mt-4">
              {columns.map((col) => (
                <div
                  key={col.key}
                  className="bg-gray-900 rounded-xl p-4"
                  style={{ borderTop: `4px solid ${col.borderColor}` }}
                >
                  <h3 className="text-sm font-medium text-white mb-3">
                    {col.label} ({byStatus(col.key).length})
                  </h3>
                  <div className="space-y-3">
                    {byStatus(col.key).map((t) => (
                      <TicketCard key={t.id} ticket={t} onClick={setSelected} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-4 bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700 text-gray-400 text-left">
                    <th className="p-4">#</th>
                    <th className="p-4">Issue</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Assigned</th>
                    <th className="p-4">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((t) => (
                    <tr
                      key={t.id}
                      className="border-b border-gray-800 hover:bg-gray-800/50 cursor-pointer"
                      onClick={() => setSelected(t)}
                    >
                      <td className="p-4 text-gray-400">#{t.id}</td>
                      <td className="p-4 text-white max-w-xs truncate">{t.issue_summary}</td>
                      <td className="p-4">
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          t.status === 'open' ? 'bg-yellow-900/40 text-yellow-400' :
                          t.status === 'assigned' ? 'bg-blue-900/40 text-blue-400' :
                          'bg-green-900/40 text-green-400'
                        }`}>{t.status}</span>
                      </td>
                      <td className="p-4 text-gray-300">{t.assignee?.name || '—'}</td>
                      <td className="p-4 text-gray-300">{new Date(t.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </main>
      </div>

      {selected && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto border border-gray-700">
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <h3 className="text-lg font-bold text-white">Ticket #{selected.id}</h3>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-white text-2xl">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-white">{selected.issue_summary}</p>

              {selected.call_record_id && <AudioPlayer callId={selected.call_record_id} />}

              {(role === 'admin' || role === 'senior_agent') && agents.length > 0 && (
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Assign to Agent</label>
                  <select
                    onChange={(e) => handleAssign(selected.id, parseInt(e.target.value))}
                    className="bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600"
                    defaultValue=""
                  >
                    <option value="">Select agent...</option>
                    {agents.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {selected.status !== 'resolved' && (
                <button
                  onClick={() => setShowResolveModal(true)}
                  className="bg-green-700 hover:bg-green-600 text-white text-sm px-4 py-2 rounded-lg transition-colors"
                >
                  Resolve Ticket
                </button>
              )}

              <NotesPanel ticketId={selected.id} />
              <ExportButton type="tickets" ticketId={selected.id} />
            </div>
          </div>
        </div>
      )}

      {showResolveModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[60] p-4">
          <div className="bg-gray-900 rounded-2xl w-full max-w-md border border-gray-700 p-6">
            <h3 className="text-lg font-bold text-white mb-4">Resolve Ticket</h3>
            <textarea
              value={resolveNote}
              onChange={(e) => setResolveNote(e.target.value)}
              placeholder="Enter resolution note (required)..."
              rows={4}
              className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none resize-none mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={handleResolve}
                disabled={!resolveNote.trim()}
                className="flex-1 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm py-2 rounded-lg transition-colors"
              >
                Confirm Resolve
              </button>
              <button
                onClick={() => setShowResolveModal(false)}
                className="flex-1 bg-gray-800 text-gray-300 text-sm py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
