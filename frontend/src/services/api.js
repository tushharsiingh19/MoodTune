import axios from 'axios'

const api = axios.create({
  baseURL: 'https://moodtune-5fws.onrender.com/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// Attach token from localStorage on each request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('mt_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 globally - clear auth
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('mt_token')
      delete api.defaults.headers.common['Authorization']
      // Only redirect if not already on auth page
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api

// ── Mood & Music ─────────────────────────────
export const predictMood = (text) =>
  api.post('/predict-mood', { text }).then(r => r.data)

export const getRecommendations = (text, mood = null) =>
  api.post('/recommend', { text, mood }).then(r => r.data)

// ── Auth ──────────────────────────────────────
export const loginUser = (email, password) =>
  api.post('/auth/login', { email, password }).then(r => r.data)

export const registerUser = (name, email, password) =>
  api.post('/auth/register', { name, email, password }).then(r => r.data)

export const getMe = () =>
  api.get('/auth/me').then(r => r.data)

// ── History ───────────────────────────────────
export const getHistory = () =>
  api.get('/history').then(r => r.data)

export const deleteHistoryItem = (id) =>
  api.delete(`/history/${id}`)

export const clearHistory = () =>
  api.delete('/history')

// ── Favorites ─────────────────────────────────
export const getFavorites = () =>
  api.get('/favorites').then(r => r.data)

export const addFavorite = (song) =>
  api.post('/favorites', song).then(r => r.data)

export const removeFavorite = (id) =>
  api.delete(`/favorites/${id}`)

// ── Song Catalog (new) ────────────────────────────────────────
export const getSongsByMood = (mood, limit = 20, skip = 0) =>
  api.get(`/songs/${mood}`, { params: { limit, skip } }).then(r => r.data)

export const getCatalogStats = () =>
  api.get('/catalog/stats').then(r => r.data)
