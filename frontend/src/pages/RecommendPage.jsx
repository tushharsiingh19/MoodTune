import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { FaRedo, FaMusic } from 'react-icons/fa'
import MoodInput from '../components/ui/MoodInput'
import MoodCard from '../components/cards/MoodCard'
import SongCard from '../components/cards/SongCard'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { getRecommendations } from '../services/api'
import toast from 'react-hot-toast'

export default function RecommendPage() {
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [inputText, setInputText] = useState('')

  // Auto-analyze if navigated with state (from HomePage quick mood chips)
  useEffect(() => {
    if (location.state?.text) {
      const { text, mood } = location.state
      setInputText(text)
      analyze(text, mood || null)
      // Clear location state so refresh doesn't re-trigger
      window.history.replaceState({}, '')
    }
  }, [])

  const analyze = async (text, mood = null) => {
    setLoading(true)
    setResult(null)
    try {
      const data = await getRecommendations(text, mood)
      setResult(data)
      setInputText(text)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to analyze mood. Is the backend running?'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (text) => analyze(text)
  const handleReset = () => { setResult(null); setInputText('') }

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <h1 className="text-4xl font-black text-white mb-2">
          Discover Your <span className="text-spotify-green">Mood Playlist</span>
        </h1>
        <p className="text-spotify-light">Type how you're feeling and get instant AI-powered recommendations</p>
      </motion.div>

      {/* Input — always visible */}
      <div className="mb-10">
        <MoodInput onSubmit={handleSubmit} loading={loading} />
      </div>

      {/* Loading State */}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-6 py-20"
          >
            <LoadingSpinner size="lg" />
            <div className="text-center">
              <p className="text-white font-semibold text-lg">Analyzing your mood...</p>
              <p className="text-spotify-light text-sm mt-1">Running NLP pipeline & fetching songs</p>
            </div>
            {/* Waveform animation */}
            <div className="flex items-end gap-1 h-10">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="wave-bar w-2 bg-spotify-green rounded-full"
                  style={{ height: '40px', animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* User input recap */}
            {inputText && (
              <div className="glass-card p-4 mb-6 flex items-start gap-3">
                <span className="text-spotify-green mt-0.5">💬</span>
                <p className="text-spotify-light text-sm italic">"{inputText}"</p>
              </div>
            )}

            {/* Mood Card + Reset row */}
            <div className="flex flex-col sm:flex-row items-start gap-4 mb-8">
              <div className="w-full sm:w-72 flex-shrink-0">
                <MoodCard
                  mood={result.mood}
                  confidence={result.confidence}
                  emoji={result.emoji}
                  description={result.description}
                  color={result.color}
                />
              </div>

              {/* Stats sidebar */}
              <div className="flex-1 grid grid-cols-2 gap-4">
                <div className="glass-card p-5 text-center">
                  <p className="text-3xl font-black text-spotify-green">
                    {result.songs?.length || 0}
                  </p>
                  <p className="text-xs text-spotify-light mt-1">Songs Found</p>
                </div>
                <div className="glass-card p-5 text-center">
                  <p className="text-3xl font-black text-white capitalize">{result.mood}</p>
                  <p className="text-xs text-spotify-light mt-1">Detected Mood</p>
                </div>
                <div className="glass-card p-5 text-center col-span-2">
                  <p className="text-2xl font-black text-yellow-400">
                    {Math.round(result.confidence * 100)}%
                  </p>
                  <p className="text-xs text-spotify-light mt-1">Confidence Score</p>
                  <div className="confidence-bar mt-2">
                    <motion.div
                      className="confidence-fill"
                      style={{ backgroundColor: result.color }}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.round(result.confidence * 100)}%` }}
                      transition={{ duration: 1.2, ease: 'easeOut' }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Songs Grid */}
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <FaMusic className="text-spotify-green" />
                Recommended Songs
              </h2>
              <button
                onClick={handleReset}
                className="flex items-center gap-2 text-sm text-spotify-light hover:text-white transition-colors"
              >
                <FaRedo className="text-xs" /> Try Again
              </button>
            </div>

            {result.songs?.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {result.songs.map((song, i) => (
                  <SongCard
                    key={`${song.song_name}-${i}`}
                    song={song}
                    mood={result.mood}
                    index={i}
                  />
                ))}
              </div>
            ) : (
              <div className="glass-card p-12 text-center">
                <p className="text-4xl mb-3">🎵</p>
                <p className="text-white font-semibold">No songs found</p>
                <p className="text-spotify-light text-sm mt-1">
                  Check your Spotify API credentials in the backend .env file
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}
      {!result && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="text-6xl mb-4">🎧</div>
          <p className="text-spotify-light">Enter your feelings above to get started</p>
        </motion.div>
      )}
    </div>
  )
}
