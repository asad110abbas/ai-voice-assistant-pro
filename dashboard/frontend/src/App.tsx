import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import CallRecords from './pages/CallRecords'
import Tickets from './pages/Tickets'
import AgentManagement from './pages/AgentManagement'
import Blocklist from './pages/Blocklist'
import VoiceChat from './pages/VoiceChat'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/calls" element={<ProtectedRoute><CallRecords /></ProtectedRoute>} />
          <Route path="/tickets" element={<ProtectedRoute><Tickets /></ProtectedRoute>} />
          <Route path="/agents" element={<ProtectedRoute requiredRole="admin"><AgentManagement /></ProtectedRoute>} />
          <Route path="/blocklist" element={<ProtectedRoute requiredRole="admin"><Blocklist /></ProtectedRoute>} />
          <Route path="/voice-chat" element={<ProtectedRoute><VoiceChat /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
