import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'

interface AgentStat {
  name: string
  tickets_handled: number
  avg_resolution_hours: number
  open_tickets: number
}

interface Props {
  data: AgentStat[]
}

export default function AgentPerformanceChart({ data }: Props) {
  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-400 mb-4">Agent Performance</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis type="number" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
          <YAxis type="category" dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 11 }} width={80} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }}
          />
          <Legend />
          <Bar dataKey="tickets_handled" name="Handled" fill="#49A8FF" radius={[0, 4, 4, 0]} />
          <Bar dataKey="open_tickets" name="Open" fill="#F59E0B" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
