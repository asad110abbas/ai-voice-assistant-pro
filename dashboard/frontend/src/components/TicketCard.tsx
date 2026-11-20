interface Ticket {
  id: number
  issue_summary: string
  status: string
  assigned_to?: number
  created_at: string
  assignee?: { name: string }
}

interface Props {
  ticket: Ticket
  onClick: (ticket: Ticket) => void
}

const statusColors: Record<string, string> = {
  open: 'bg-yellow-900/40 text-yellow-400',
  assigned: 'bg-blue-900/40 text-blue-400',
  resolved: 'bg-green-900/40 text-green-400',
}

export default function TicketCard({ ticket, onClick }: Props) {
  return (
    <div
      className="bg-gray-900 rounded-xl p-4 border border-gray-700 hover:border-blue-500/50 cursor-pointer transition-colors"
      onClick={() => onClick(ticket)}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs text-gray-400">#{ticket.id}</span>
        <span className={`text-xs px-2 py-0.5 rounded ${statusColors[ticket.status] || ''}`}>
          {ticket.status}
        </span>
      </div>
      <p className="text-sm text-white leading-snug line-clamp-3">{ticket.issue_summary}</p>
      {ticket.assignee && (
        <p className="text-xs text-gray-400 mt-2">Assigned: {ticket.assignee.name}</p>
      )}
      <p className="text-xs text-gray-500 mt-1">{new Date(ticket.created_at).toLocaleString()}</p>
    </div>
  )
}
