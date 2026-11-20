import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const navItems = [
  { path: '/dashboard', label: 'Dashboard' },
  { path: '/voice-chat', label: 'Voice Chat' },
  { path: '/calls', label: 'Call Records' },
  { path: '/tickets', label: 'Tickets' },
]

const adminItems = [
  { path: '/agents', label: 'Agents' },
  { path: '/blocklist', label: 'Blocklist' },
]

export default function Sidebar() {
  const { user, role, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 bg-gray-900 flex flex-col h-screen fixed left-0 top-0">
      <div className="p-6 border-b border-gray-700">
        <h1 className="text-xl font-bold" style={{ color: '#49A8FF' }}>Briha</h1>
        <p className="text-gray-400 text-sm mt-1">Admin Dashboard</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-900/20 text-blue-400 border-l-4 border-blue-400'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}

        {role === 'admin' && (
          <>
            <div className="pt-4 pb-2">
              <p className="text-xs text-gray-500 uppercase tracking-wider px-4">Admin</p>
            </div>
            {adminItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-900/20 text-blue-400 border-l-4 border-blue-400'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-blue-900/30 flex items-center justify-center text-blue-400 text-sm font-bold">
            {user?.agent_id}
          </div>
          <div>
            <p className="text-sm text-white">Agent #{user?.agent_id}</p>
            <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded">{role}</span>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full text-left text-sm text-gray-400 hover:text-red-400 transition-colors"
        >
          Logout
        </button>
      </div>
    </aside>
  )
}
