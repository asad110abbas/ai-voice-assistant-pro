interface Props {
  filters: Record<string, string>
  onChange: (key: string, value: string) => void
  onClear: () => void
  statusOptions?: string[]
}

export default function FilterBar({ filters, onChange, onClear, statusOptions }: Props) {
  return (
    <div className="flex flex-wrap gap-3 items-end bg-gray-900 p-4 rounded-xl border border-gray-700">
      <div>
        <label className="text-xs text-gray-400 block mb-1">Date From</label>
        <input
          type="date"
          value={filters.date_from || ''}
          onChange={(e) => onChange('date_from', e.target.value)}
          className="bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none"
        />
      </div>

      <div>
        <label className="text-xs text-gray-400 block mb-1">Date To</label>
        <input
          type="date"
          value={filters.date_to || ''}
          onChange={(e) => onChange('date_to', e.target.value)}
          className="bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none"
        />
      </div>

      {statusOptions && (
        <div>
          <label className="text-xs text-gray-400 block mb-1">Status</label>
          <select
            value={filters.status || ''}
            onChange={(e) => onChange('status', e.target.value)}
            className="bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none"
          >
            <option value="">All</option>
            {statusOptions.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label className="text-xs text-gray-400 block mb-1">Search</label>
        <input
          type="text"
          placeholder="Keyword..."
          value={filters.keyword || ''}
          onChange={(e) => onChange('keyword', e.target.value)}
          className="bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none w-48"
        />
      </div>

      <button
        onClick={onClear}
        className="text-sm text-gray-400 hover:text-white px-3 py-2 rounded-lg border border-gray-600 hover:border-gray-400 transition-colors"
      >
        Clear
      </button>
    </div>
  )
}
