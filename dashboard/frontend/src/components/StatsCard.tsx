interface Props {
  title: string
  value: string | number
  icon: string
  color?: string
}

export default function StatsCard({ title, value, icon, color = '#49A8FF' }: Props) {
  return (
    <div
      className="bg-gray-900 rounded-xl p-6 border border-gray-700"
      style={{ borderLeftColor: color, borderLeftWidth: 4 }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  )
}
