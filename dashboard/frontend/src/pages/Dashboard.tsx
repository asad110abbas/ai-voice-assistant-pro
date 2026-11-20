import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import StatsCard from '../components/StatsCard'
import CallVolumeChart from '../components/Charts/CallVolumeChart'
import ResolutionTimeChart from '../components/Charts/ResolutionTimeChart'
import AgentPerformanceChart from '../components/Charts/AgentPerformanceChart'
import { getStats, getAnalytics, getCallOutcomes, getCostStats } from '../api/dashboard'

interface CostStats {
  total_bot_cost_usd: number
  avg_cost_per_call_usd: number
  total_calls: number
  bot_monthly_cost_usd: number
  agent_monthly_cost_pkr: number
  agent_monthly_cost_usd: number
  agent_cost_per_call_usd: number
  savings_percent: number
}

interface Outcomes {
  bot_handled: number
  agent_transfer: number
  spam: number
  timeout: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<Record<string, number>>({})
  const [callVolume, setCallVolume] = useState([])
  const [resolutionTime, setResolutionTime] = useState({ avg_hours: 0 })
  const [agentPerf, setAgentPerf] = useState([])
  const [outcomes, setOutcomes] = useState<Outcomes>({ bot_handled: 0, agent_transfer: 0, spam: 0, timeout: 0 })
  const [costStats, setCostStats] = useState<CostStats | null>(null)

  const fetchData = async () => {
    const [statsRes, volRes, resRes, perfRes, outRes, costRes] = await Promise.allSettled([
      getStats(),
      getAnalytics('call_volume'),
      getAnalytics('resolution_time'),
      getAnalytics('agent_performance'),
      getCallOutcomes(30),
      getCostStats(30),
    ])
    if (statsRes.status === 'fulfilled') setStats(statsRes.value.data)
    if (volRes.status === 'fulfilled') setCallVolume(volRes.value.data)
    if (resRes.status === 'fulfilled') setResolutionTime(resRes.value.data)
    if (perfRes.status === 'fulfilled') setAgentPerf(perfRes.value.data)
    if (outRes.status === 'fulfilled') setOutcomes(outRes.value.data)
    if (costRes.status === 'fulfilled') setCostStats(costRes.value.data)
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const botPct = costStats && costStats.bot_monthly_cost_usd > 0
    ? Math.min(100, (costStats.bot_monthly_cost_usd / costStats.agent_monthly_cost_usd) * 100)
    : 2

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col">
        <Header title="Dashboard" />
        <main className="flex-1 overflow-auto p-6 pt-20">

          {/* Row 1 — Basic stats */}
          <div className="grid grid-cols-4 gap-4 mb-4">
            <StatsCard title="Calls Today" value={stats.total_calls_today ?? 0} icon="📞" />
            <StatsCard title="Open Tickets" value={stats.open_tickets ?? 0} icon="🎫" color="#F59E0B" />
            <StatsCard title="Resolved Today" value={stats.resolved_today ?? 0} icon="✅" color="#10B981" />
            <StatsCard title="Avg Duration (s)" value={stats.avg_duration_seconds ?? 0} icon="⏱️" color="#8B5CF6" />
          </div>

          {/* Row 2 — Call outcomes */}
          <div className="grid grid-cols-4 gap-4 mb-4">
            <StatsCard title="Bot Handled" value={outcomes.bot_handled} icon="🤖" color="#10B981" />
            <StatsCard title="Agent Transfer" value={outcomes.agent_transfer} icon="🔀" color="#F59E0B" />
            <StatsCard title="Spam / Abusive" value={outcomes.spam} icon="🚫" color="#EF4444" />
            <StatsCard title="Timeout (Empty)" value={outcomes.timeout} icon="⏰" color="#6B7280" />
          </div>

          {/* Row 3 — Charts */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="col-span-2">
              <CallVolumeChart data={callVolume} />
            </div>
            <ResolutionTimeChart avgHours={resolutionTime.avg_hours ?? 0} />
          </div>

          {/* Row 4 — Agent performance */}
          <div className="mb-4">
            <AgentPerformanceChart data={agentPerf} />
          </div>

          {/* Row 5 — Bot vs Agent cost comparison */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
            <h2 className="text-white font-semibold text-lg mb-4">💰 Bot vs Agent Cost (Last 30 Days)</h2>
            <div className="grid grid-cols-3 gap-6 mb-6">
              <div className="bg-gray-800 rounded-lg p-4 border-l-4 border-blue-500">
                <p className="text-gray-400 text-sm">Bot Cost This Month</p>
                <p className="text-white text-2xl font-bold mt-1">
                  ${costStats?.bot_monthly_cost_usd?.toFixed(2) ?? '0.00'}
                </p>
                <p className="text-gray-500 text-xs mt-1">
                  ~${costStats?.avg_cost_per_call_usd?.toFixed(4) ?? '0.0000'} / call
                </p>
              </div>
              <div className="bg-gray-800 rounded-lg p-4 border-l-4 border-amber-500">
                <p className="text-gray-400 text-sm">Agent Monthly Cost</p>
                <p className="text-white text-2xl font-bold mt-1">
                  ${costStats?.agent_monthly_cost_usd?.toFixed(0) ?? '108'}
                </p>
                <p className="text-gray-500 text-xs mt-1">
                  PKR {costStats?.agent_monthly_cost_pkr?.toLocaleString() ?? '30,000'} / month
                </p>
              </div>
              <div className="bg-gray-800 rounded-lg p-4 border-l-4 border-green-500">
                <p className="text-gray-400 text-sm">You're Saving</p>
                <p className="text-green-400 text-2xl font-bold mt-1">
                  {costStats?.savings_percent?.toFixed(1) ?? '94'}%
                </p>
                <p className="text-gray-500 text-xs mt-1">vs hiring a human agent</p>
              </div>
            </div>

            {/* Visual bar comparison */}
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm text-gray-400 mb-1">
                  <span>🤖 Bot</span>
                  <span>${costStats?.bot_monthly_cost_usd?.toFixed(2) ?? '0.00'}/mo</span>
                </div>
                <div className="bg-gray-700 rounded-full h-4">
                  <div
                    className="bg-blue-500 h-4 rounded-full transition-all duration-700"
                    style={{ width: `${Math.max(botPct, 1)}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm text-gray-400 mb-1">
                  <span>👤 Human Agent</span>
                  <span>${costStats?.agent_monthly_cost_usd?.toFixed(0) ?? '108'}/mo</span>
                </div>
                <div className="bg-gray-700 rounded-full h-4">
                  <div className="bg-amber-500 h-4 rounded-full w-full" />
                </div>
              </div>
            </div>
          </div>

        </main>
      </div>
    </div>
  )
}
