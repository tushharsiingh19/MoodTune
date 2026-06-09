import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import RecommendPage from './pages/RecommendPage'
import HistoryPage from './pages/HistoryPage'
import FavoritesPage from './pages/FavoritesPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import LoadingSpinner from './components/ui/LoadingSpinner'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return <LoadingSpinner fullscreen />
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="recommend" element={<RecommendPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="history" element={
          <ProtectedRoute><HistoryPage /></ProtectedRoute>
        } />
        <Route path="favorites" element={
          <ProtectedRoute><FavoritesPage /></ProtectedRoute>
        } />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
