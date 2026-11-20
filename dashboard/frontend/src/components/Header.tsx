import { useState, useEffect } from 'react'
import client from '../api/client'

interface Notification {
  id: number
  type: string
  message: string
  read: boolean
  created_at: string
}

interface Props {
  title: string
}

export default function Header({ title }: Props) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [showDropdown, setShowDropdown] = useState(false)

  const fetchNotifications = async () => {
    try {
      const res = await client.get('/notifications')
      setNotifications(res.data)
    } catch {
      // silently ignore
    }
  }

  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  const markRead = async (id: number) => {
    await client.patch(`/notifications/${id}/read`)
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }

  return (
    <header className="h-16 bg-gray-900 border-b border-gray-700 flex items-center justify-between px-6 fixed top-0 right-0 left-64 z-10">
      <h2 className="text-lg font-semibold text-white">{title}</h2>

      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="relative p-2 text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          {notifications.length > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center text-white">
              {notifications.length}
            </span>
          )}
        </button>

        {showDropdown && (
          <div className="absolute right-0 mt-2 w-80 bg-gray-800 rounded-lg shadow-xl border border-gray-700 z-50">
            <div className="p-3 border-b border-gray-700">
              <p className="text-sm font-medium text-white">Notifications</p>
            </div>
            {notifications.length === 0 ? (
              <p className="p-4 text-sm text-gray-400">No unread notifications</p>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className="p-3 border-b border-gray-700 hover:bg-gray-700 cursor-pointer"
                  onClick={() => markRead(n.id)}
                >
                  <p className="text-sm text-white">{n.message}</p>
                  <p className="text-xs text-gray-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </header>
  )
}
