import { useState } from 'react'
import { exportCallsCsv, exportTicketsCsv, exportTicketPdf } from '../api/exports'

interface Props {
  type: 'calls' | 'tickets'
  ticketId?: number
}

export default function ExportButton({ type, ticketId }: Props) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleExport = async (format: 'csv' | 'pdf') => {
    setLoading(true)
    setOpen(false)
    try {
      if (type === 'calls') {
        await exportCallsCsv()
      } else if (format === 'csv') {
        await exportTicketsCsv()
      } else if (format === 'pdf' && ticketId) {
        await exportTicketPdf(ticketId)
      }
    } catch (err) {
      console.error('Export failed', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        disabled={loading}
        className="bg-gray-800 text-white text-sm px-4 py-2 rounded-lg border border-gray-600 hover:border-blue-400 transition-colors flex items-center gap-2"
      >
        {loading ? 'Exporting...' : 'Export'}
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="absolute right-0 mt-1 w-40 bg-gray-800 rounded-lg border border-gray-600 shadow-xl z-50">
          <button
            onClick={() => handleExport('csv')}
            className="w-full text-left text-sm text-white px-4 py-2 hover:bg-gray-700 rounded-t-lg"
          >
            Export CSV
          </button>
          {type === 'tickets' && ticketId && (
            <button
              onClick={() => handleExport('pdf')}
              className="w-full text-left text-sm text-white px-4 py-2 hover:bg-gray-700 rounded-b-lg"
            >
              Export PDF
            </button>
          )}
        </div>
      )}
    </div>
  )
}
