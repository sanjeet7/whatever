import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authAPI } from '@/lib/api'
import { User } from '@/types'
import toast from 'react-hot-toast'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in on mount
    if (token) {
      // In a real app, you'd validate the token here
      setUser({ 
        id: 1, 
        username: 'user', 
        email: 'user@example.com',
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString()
      })
    }
    setIsLoading(false)
  }, [token])

  const login = async (username: string, password: string) => {
    try {
      const response = await authAPI.login(username, password)
      const { access_token } = response
      
      localStorage.setItem('token', access_token)
      setToken(access_token)
      
      // Set a mock user - in production, you'd fetch user details
      setUser({
        id: 1,
        username,
        email: `${username}@example.com`,
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString()
      })
      
      toast.success('Login successful!')
    } catch (error) {
      toast.error('Login failed. Please check your credentials.')
      throw error
    }
  }

  const register = async (username: string, email: string, password: string) => {
    try {
      const response = await authAPI.register({ username, email, password })
      toast.success('Registration successful! Please login.')
      return response
    } catch (error) {
      toast.error('Registration failed. Please try again.')
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    toast.success('Logged out successfully')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}