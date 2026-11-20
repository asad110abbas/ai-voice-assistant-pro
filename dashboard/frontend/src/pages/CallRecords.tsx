import { useState, useEffect, useCallback } from 'react'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import FilterBar from '../components/FilterBar'
import TranscriptModal from '../components/TranscriptModal'
import ExportButton from '../components/ExportButton'
import { getCalls } from '../api/calls'

interface CallRecord {
  id: number
  start_time: string
  duration_seconds: number
  language: string
  escalated: boolean
  transcript: Array<{ role: string; content: string }>
  audio_path?: string
  end_time: string
}

export default function CallRecords() {
  const [records, setRecords] = useState<CallRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [selected, setSelected] = useState<CallRecord | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const res = await getCalls({ ...filters, page })
      setRecords(res.data.items)
      setTotal(res.data.total)
    } catch (e) {
      console.error(e)
    }
  }, [filters, page])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1)
  }

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col">
        <Header title="Call Records" />
        <main className="flex-1 overflow-auto p-6 pt-20">
          <div className="flex items-center justify-between mb-4">
            <p className="text-gray-400 text-sm">{total} total calls</p>
            <ExportButton type="calls" />
          </div>

          <FilterBar
            filters={filters}
            onChange={handleFilterChange}
            onClear={() => { setFilters({}); setPage(1) }}
          />

          <div className="mt-4 bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Duration</th>
                  <th className="p-4">Language</th>
                  <th className="p-4">Escalated</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr
                    key={r.id}
                    className="border-b border-gray-800 hover:bg-gray-800/50 cursor-pointer transition-colors"
                    onClick={() => setSelected(r)}
                  >
                    <td className="p-4 text-white">{r.start_time ? new Date(r.start_time).toLocaleString() : '—'}</td>
                    <td className="p-4 text-gray-300">{Math.round(r.duration_seconds)}s</td>
                    <td className="p-4 text-gray-300 uppercase">{r.language}</td>
                    <td className="p-4">
                      {r.escalated ? (
                        <span className="bg-red-900/40 text-red-400 text-xs px-2 py-0.5 rounded">Yes</span>
                      ) : (
                        <span className="bg-gray-800 text-gray-400 text-xs px-2 py-0.5 rounded">No</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex gap-2 mt-4 justify-end">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="text-sm text-gray-400 hover:text-white disabled:opacity-40 px-3 py-1 rounded border border-gray-700"
            >
              Prev
            </button>
            <span className="text-gray-400 text-sm px-3 py-1">Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              className="text-sm text-gray-400 hover:text-white px-3 py-1 rounded border border-gray-700"
            >
              Next
            </button>
          </div>
        </main>
      </div>

      {selected && (
        <TranscriptModal record={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}
