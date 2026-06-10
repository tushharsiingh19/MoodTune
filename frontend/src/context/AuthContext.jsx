import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [token, setToken]     = useState(() => localStorage.getItem('mt_token'))
  const [loading, setLoading] = useState(true)

  // Verify token on mount
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      api.get('/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          // Token invalid or expired — clear it
          localStorage.removeItem('mt_token')
          delete api.defaults.headers.common['Authorization']
          setToken(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    const { access_token, user: userData } = res.data
    localStorage.setItem('mt_token', access_token)
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    setToken(access_token)
    setUser(userData)
    return userData
  }, [])

  const register = useCallback(async (name, email, password) => {
    const res = await api.post('/auth/register', { name, email, password })
    const { access_token, user: userData } = res.data
    localStorage.setItem('mt_token', access_token)
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    setToken(access_token)
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('mt_token')
    delete api.defaults.headers.common['Authorization']
    setToken(null)
    setUser(null)
    toast.success('Logged out successfully')
  }, [])

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      register,
      logout,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
