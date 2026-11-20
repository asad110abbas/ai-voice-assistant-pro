import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'

interface Props {
  children: React.ReactNode
  requiredRole?: string
}

export default function ProtectedRoute({ children, requiredRole }: Props) {
  const { user, role } = useAuth()

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (requiredRole && role !== requiredRole) {
    return (
      <div className="flex items-center justify-center h-screen text-red-400 text-xl">
        403 — Access Denied
      </div>
    )
  }

  return <>{children}</>
}
