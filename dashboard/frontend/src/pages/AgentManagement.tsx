import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import { getAgents, createAgent, updateAgent } from '../api/agents'

interface Agent {
  id: number
  name: string
  email: string
  role: string
  open_ticket_count: number
}

export default function AgentManagement() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [showModal, setShowModal] = useState(false)
  const [editAgent, setEditAgent] = useState<Agent | null>(null)
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'agent' })

  const fetchAgents = async () => {
    try {
      const res = await getAgents()
      setAgents(res.data)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    fetchAgents()
  }, [])

  const openCreate = () => {
    setEditAgent(null)
    setForm({ name: '', email: '', password: '', role: 'agent' })
    setShowModal(true)
  }

  const openEdit = (agent: Agent) => {
    setEditAgent(agent)
    setForm({ name: agent.name, email: agent.email, password: '', role: agent.role })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editAgent) {
      await updateAgent(editAgent.id, { name: form.name, email: form.email, role: form.role })
    } else {
      await createAgent(form)
    }
    setShowModal(false)
    fetchAgents()
  }

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col">
        <Header title="Agent Management" />
        <main className="flex-1 overflow-auto p-6 pt-20">
          <div className="flex justify-end mb-4">
            <button
              onClick={openCreate}
              className="text-white text-sm px-4 py-2 rounded-lg transition-colors"
              style={{ backgroundColor: '#49A8FF' }}
            >
              Add Agent
            </button>
          </div>

          <div className="bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <th className="p-4">Name</th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Role</th>
                  <th className="p-4">Open Tickets</th>
                  <th className="p-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((a) => (
                  <tr key={a.id} className="border-b border-gray-800">
                    <td className="p-4 text-white">{a.name}</td>
                    <td className="p-4 text-gray-300">{a.email}</td>
                    <td className="p-4">
                      <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded">{a.role}</span>
                    </td>
                    <td className="p-4 text-gray-300">{a.open_ticket_count}</td>
                    <td className="p-4">
                      <button
                        onClick={() => openEdit(a)}
                        className="text-xs text-blue-400 hover:underline"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-2xl w-full max-w-md border border-gray-700 p-6">
            <h3 className="text-lg font-bold text-white mb-4">
              {editAgent ? 'Edit Agent' : 'Add Agent'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Name</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none"
                />
              </div>
              {!editAgent && (
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Password</label>
                  <input
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    required
                    className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none"
                  />
                </div>
              )}
              <div>
                <label className="text-xs text-gray-400 block mb-1">Role</label>
                <select
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 outline-none"
                >
                  <option value="agent">Agent</option>
                  <option value="senior_agent">Senior Agent</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  className="flex-1 text-white text-sm py-2 rounded-lg transition-colors"
                  style={{ backgroundColor: '#49A8FF' }}
                >
                  {editAgent ? 'Save Changes' : 'Create Agent'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-gray-800 text-gray-300 text-sm py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
