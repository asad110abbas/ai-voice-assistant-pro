interface Props {
  avgHours: number
  prevAvgHours?: number
}

export default function ResolutionTimeChart({ avgHours, prevAvgHours }: Props) {
  const trend = prevAvgHours !== undefined ? avgHours - prevAvgHours : 0
  const trendLabel = trend === 0 ? '—' : trend > 0 ? `↑ ${trend.toFixed(1)}h` : `↓ ${Math.abs(trend).toFixed(1)}h`
  const trendColor = trend > 0 ? 'text-red-400' : trend < 0 ? 'text-green-400' : 'text-gray-400'

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-400 mb-4">Avg Resolution Time</h3>
      <div className="flex items-end gap-3">
        <p className="text-4xl font-bold text-white">{avgHours.toFixed(1)}</p>
        <div className="mb-1">
          <p className="text-gray-400 text-sm">hours</p>
          <p className={`text-sm font-medium ${trendColor}`}>{trendLabel}</p>
        </div>
      </div>
    </div>
  )
}
