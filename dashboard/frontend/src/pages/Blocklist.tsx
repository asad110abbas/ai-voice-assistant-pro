import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import client from '../api/client'

interface BlockedIP {
  ip: string
  reason: string
  timestamp: string
}

interface AbuseEntry {
  ip: string
  reason: string
  timestamp: string
}

export default function Blocklist() {
  const [blocklist, setBlocklist] = useState<BlockedIP[]>([])
  const [abuseLog, setAbuseLog] = useState<AbuseEntry[]>([])

  const fetchData = async () => {
    const [blRes, alRes] = await Promise.allSettled([
      client.get('/blocklist'),
      client.get('/abuse-log'),
    ])
    if (blRes.status === 'fulfilled') setBlocklist(blRes.value.data)
    if (alRes.status === 'fulfilled') setAbuseLog(alRes.value.data)
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleUnblock = async (ip: string) => {
    await client.delete(`/blocklist/${encodeURIComponent(ip)}`)
    fetchData()
  }

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col">
        <Header title="Blocklist" />
        <main className="flex-1 overflow-auto p-6 pt-20">
          <h3 className="text-white font-semibold mb-3">Blocked IPs ({blocklist.length})</h3>
          <div className="bg-gray-900 rounded-xl border border-gray-700 overflow-hidden mb-8">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <th className="p-4">IP Address</th>
                  <th className="p-4">Reason</th>
                  <th className="p-4">Blocked At</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody>
                {blocklist.map((entry) => (
                  <tr key={entry.ip} className="border-b border-gray-800">
                    <td className="p-4 text-white font-mono">{entry.ip}</td>
                    <td className="p-4 text-red-400">{entry.reason}</td>
                    <td className="p-4 text-gray-300">{new Date(entry.timestamp).toLocaleString()}</td>
                    <td className="p-4">
                      <button
                        onClick={() => handleUnblock(entry.ip)}
                        className="text-xs bg-green-900/40 text-green-400 hover:bg-green-900/70 px-3 py-1 rounded transition-colors"
                      >
                        Unblock
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3 className="text-white font-semibold mb-3">Abuse Log ({abuseLog.length})</h3>
          <div className="bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <th className="p-4">IP Address</th>
                  <th className="p-4">Reason</th>
                  <th className="p-4">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {abuseLog.map((entry, i) => (
                  <tr key={i} className="border-b border-gray-800">
                    <td className="p-4 text-white font-mono">{entry.ip}</td>
                    <td className="p-4 text-orange-400">{entry.reason}</td>
                    <td className="p-4 text-gray-300">{new Date(entry.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  )
}
