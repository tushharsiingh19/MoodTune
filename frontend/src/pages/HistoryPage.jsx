import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { FaHistory, FaTrash, FaRedo, FaChartBar, FaCalendarAlt } from 'react-icons/fa'
import { getHistory, deleteHistoryItem, clearHistory } from '../services/api'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

const MOOD_META = {
  happy:        { emoji: '😊', color: '#FFD700', bg: 'bg-yellow-500/10 border-yellow-500/20' },
  sad:          { emoji: '😢', color: '#6B8DD6', bg: 'bg-blue-500/10 border-blue-500/20' },
  angry:        { emoji: '😤', color: '#FF4444', bg: 'bg-red-500/10 border-red-500/20' },
  romantic:     { emoji: '💕', color: '#FF69B4', bg: 'bg-pink-500/10 border-pink-500/20' },
  relaxed:      { emoji: '😌', color: '#90EE90', bg: 'bg-green-500/10 border-green-500/20' },
  motivational: { emoji: '💪', color: '#FF8C00', bg: 'bg-orange-500/10 border-orange-500/20' },
  party:        { emoji: '🎉', color: '#9B59B6', bg: 'bg-purple-500/10 border-purple-500/20' },
  study:        { emoji: '📚', color: '#20B2AA', bg: 'bg-teal-500/10 border-teal-500/20' },
}

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function MoodStats({ history }) {
  const counts = history.reduce((acc, h) => {
    acc[h.mood] = (acc[h.mood] || 0) + 1
    return acc
  }, {})
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])
  const max = sorted[0]?.[1] || 1

  return (
    <div className="glass-card p-6 mb-6">
      <h2 className="text-white font-bold mb-4 flex items-center gap-2">
        <FaChartBar className="text-spotify-green" /> Mood Analytics
      </h2>
      <div className="space-y-3">
        {sorted.map(([mood, count]) => {
          const meta = MOOD_META[mood] || { emoji: '🎵', color: '#1DB954' }
          return (
            <div key={mood} className="flex items-center gap-3">
              <span className="text-lg w-6">{meta.emoji}</span>
              <span className="text-sm text-spotify-light capitalize w-24">{mood}</span>
              <div className="flex-1 h-2 bg-spotify-hover rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: meta.color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${(count / max) * 100}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                />
              </div>
              <span className="text-xs text-spotify-light w-6 text-right">{count}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState(null)
  const [clearConfirm, setClearConfirm] = useState(false)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const data = await getHistory()
      setHistory(data)
    } catch {
      toast.error('Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    setDeletingId(id)
    try {
      await deleteHistoryItem(id)
      setHistory(h => h.filter(item => item.id !== id))
      toast.success('Entry deleted')
    } catch {
      toast.error('Failed to delete entry')
    } finally {
      setDeletingId(null)
    }
  }

  const handleClearAll = async () => {
    if (!clearConfirm) { setClearConfirm(true); return }
    try {
      await clearHistory()
      setHistory([])
      setClearConfirm(false)
      toast.success('History cleared')
    } catch {
      toast.error('Failed to clear history')
    }
  }

  const handleReplay = (item) => {
    navigate('/recommend', { state: { text: item.text, mood: item.mood } })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="lg" text="Loading your history..." />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-8"
      >
        <div>
          <h1 className="text-3xl font-black text-white flex items-center gap-3">
            <FaHistory className="text-spotify-green" />
            Mood History
          </h1>
          <p className="text-spotify-light mt-1 text-sm">{history.length} entries recorded</p>
        </div>

        {history.length > 0 && (
          <button
            onClick={handleClearAll}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              clearConfirm
                ? 'bg-red-500 text-white hover:bg-red-600'
                : 'text-red-400 hover:bg-red-500/10 border border-red-500/30'
            }`}
          >
            <FaTrash className="text-xs" />
            {clearConfirm ? 'Confirm Clear All' : 'Clear All'}
          </button>
        )}
      </motion.div>

      {history.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-16 text-center"
        >
          <div className="text-6xl mb-4">📭</div>
          <h3 className="text-white font-bold text-xl mb-2">No history yet</h3>
          <p className="text-spotify-light text-sm mb-6">
            Analyze your mood to start building your history
          </p>
          <button onClick={() => navigate('/recommend')} className="btn-primary">
            Analyze My Mood
          </button>
        </motion.div>
      ) : (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Analytics sidebar */}
          <div className="lg:col-span-1">
            <MoodStats history={history} />

            {/* Summary card */}
            <div className="glass-card p-5 text-center">
              <FaCalendarAlt className="text-spotify-green text-2xl mx-auto mb-2" />
              <p className="text-3xl font-black text-white">{history.length}</p>
              <p className="text-spotify-light text-xs mt-1">Total Mood Checks</p>
            </div>
          </div>

          {/* History list */}
          <div className="lg:col-span-2 space-y-3">
            <AnimatePresence>
              {history.map((item, i) => {
                const meta = MOOD_META[item.mood] || { emoji: '🎵', color: '#1DB954', bg: 'bg-white/5 border-white/10' }
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20, height: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className={`border rounded-xl p-4 ${meta.bg} hover:brightness-110 transition-all`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        <span className="text-2xl mt-0.5 flex-shrink-0">{meta.emoji}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm leading-relaxed line-clamp-2 italic">
                            "{item.text}"
                          </p>
                          <div className="flex items-center gap-3 mt-2 flex-wrap">
                            <span
                              className="text-xs font-bold capitalize px-2 py-0.5 rounded-full"
                              style={{ color: meta.color, backgroundColor: `${meta.color}20` }}
                            >
                              {item.mood}
                            </span>
                            {item.confidence && (
                              <span className="text-xs text-spotify-light">
                                {Math.round(item.confidence * 100)}% confidence
                              </span>
                            )}
                            <span className="text-xs text-spotify-light flex items-center gap-1">
                              <FaCalendarAlt className="text-xs" />
                              {formatDate(item.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={() => handleReplay(item)}
                          title="Replay this mood"
                          className="p-2 rounded-lg text-spotify-light hover:text-spotify-green hover:bg-spotify-green/10 transition-all text-sm"
                        >
                          <FaRedo />
                        </button>
                        <button
                          onClick={() => handleDelete(item.id)}
                          disabled={deletingId === item.id}
                          title="Delete entry"
                          className="p-2 rounded-lg text-spotify-light hover:text-red-400 hover:bg-red-500/10 transition-all text-sm"
                        >
                          {deletingId === item.id
                            ? <span className="w-3 h-3 border border-t-transparent border-red-400 rounded-full animate-spin inline-block" />
                            : <FaTrash />}
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  )
}
