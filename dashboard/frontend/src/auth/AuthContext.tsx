import React, { createContext, useContext, useState, useEffect } from 'react'
import { jwtDecode } from 'jwt-decode'
import { login as apiLogin } from '../api/auth'

interface User {
  agent_id: number
  role: string
}

interface AuthContextType {
  user: User | null
  role: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      try {
        const decoded = jwtDecode<User>(token)
        setUser(decoded)
      } catch {
        localStorage.removeItem('token')
      }
    }
  }, [])

  const login = async (email: string, password: string) => {
    const res = await apiLogin(email, password)
    const { access_token } = res.data
    localStorage.setItem('token', access_token)
    const decoded = jwtDecode<User>(access_token)
    setUser(decoded)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, role: user?.role ?? null, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
