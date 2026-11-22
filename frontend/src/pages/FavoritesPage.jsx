import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { FaHeart, FaFilter, FaSpotify, FaYoutube, FaTrash, FaMusic } from 'react-icons/fa'
import { getFavorites, removeFavorite } from '../services/api'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

const MOOD_META = {
  happy:        { emoji: '😊', color: '#FFD700' },
  sad:          { emoji: '😢', color: '#6B8DD6' },
  angry:        { emoji: '😤', color: '#FF4444' },
  romantic:     { emoji: '💕', color: '#FF69B4' },
  relaxed:      { emoji: '😌', color: '#90EE90' },
  motivational: { emoji: '💪', color: '#FF8C00' },
  party:        { emoji: '🎉', color: '#9B59B6' },
  study:        { emoji: '📚', color: '#20B2AA' },
}

function FavoriteSongCard({ song, onRemove }) {
  const [removing, setRemoving] = useState(false)
  const meta = MOOD_META[song.mood] || { emoji: '🎵', color: '#1DB954' }

  const handleRemove = async () => {
    setRemoving(true)
    try {
      await removeFavorite(song.id)
      onRemove(song.id)
      toast.success('Removed from favorites')
    } catch {
      toast.error('Failed to remove')
      setRemoving(false)
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      className="bg-spotify-card hover:bg-spotify-hover rounded-xl p-4 transition-all duration-300 group"
    >
      {/* Album Art */}
      <div className="relative mb-3">
        {song.album_image ? (
          <img
            src={song.album_image}
            alt={song.song_name}
            className="w-full aspect-square object-cover rounded-lg"
            loading="lazy"
          />
        ) : (
          <div className="w-full aspect-square rounded-lg bg-spotify-hover flex items-center justify-center">
            <FaMusic className="text-3xl text-spotify-light" />
          </div>
        )}
        {/* Mood badge overlay */}
        {song.mood && (
          <span
            className="absolute top-2 left-2 text-xs px-2 py-0.5 rounded-full font-semibold capitalize"
            style={{ backgroundColor: `${meta.color}30`, color: meta.color, border: `1px solid ${meta.color}50` }}
          >
            {meta.emoji} {song.mood}
          </span>
        )}
        {/* Remove button overlay */}
        <button
          onClick={handleRemove}
          disabled={removing}
          className="absolute top-2 right-2 p-1.5 bg-black/60 rounded-full text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-all duration-200"
          title="Remove from favorites"
        >
          {removing
            ? <span className="w-3 h-3 border border-t-transparent border-red-400 rounded-full animate-spin inline-block" />
            : <FaTrash className="text-xs" />}
        </button>
      </div>

      {/* Info */}
      <div className="mb-3">
        <h3 className="text-white font-semibold text-sm truncate">{song.song_name}</h3>
        <p className="text-spotify-light text-xs truncate mt-0.5">{song.artist}</p>
        {song.album && <p className="text-white/30 text-xs truncate mt-0.5">{song.album}</p>}
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        {song.spotify_url && (
          <a
            href={song.spotify_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-spotify-green/10 hover:bg-spotify-green text-spotify-green hover:text-black text-xs font-semibold transition-all duration-200"
          >
            <FaSpotify />
            <span className="hidden sm:block">Spotify</span>
          </a>
        )}
        {song.youtube_url && (
          <a
            href={song.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-red-500/10 hover:bg-red-500 text-red-400 hover:text-white text-xs font-semibold transition-all duration-200"
          >
            <FaYoutube />
            <span className="hidden sm:block">YouTube</span>
          </a>
        )}
      </div>
    </motion.div>
  )
}

export default function FavoritesPage() {
  const navigate = useNavigate()
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterMood, setFilterMood] = useState('all')

  useEffect(() => {
    fetchFavorites()
  }, [])

  const fetchFavorites = async () => {
    setLoading(true)
    try {
      const data = await getFavorites()
      setFavorites(data)
    } catch {
      toast.error('Failed to load favorites')
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = (id) => {
    setFavorites(f => f.filter(s => s.id !== id))
  }

  // Build unique mood list from favorites
  const availableMoods = ['all', ...new Set(favorites.map(f => f.mood).filter(Boolean))]

  const filtered = filterMood === 'all'
    ? favorites
    : favorites.filter(f => f.mood === filterMood)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="lg" text="Loading your favorites..." />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-8"
      >
        <div>
          <h1 className="text-3xl font-black text-white flex items-center gap-3">
            <FaHeart className="text-red-400" />
            Your Favorites
          </h1>
          <p className="text-spotify-light mt-1 text-sm">
            {favorites.length} saved song{favorites.length !== 1 ? 's' : ''}
          </p>
        </div>
      </motion.div>

      {favorites.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-16 text-center"
        >
          <div className="text-6xl mb-4">🎵</div>
          <h3 className="text-white font-bold text-xl mb-2">No favorites yet</h3>
          <p className="text-spotify-light text-sm mb-6">
            Save songs from your recommendations to build your collection
          </p>
          <button onClick={() => navigate('/recommend')} className="btn-primary">
            Discover Music
          </button>
        </motion.div>
      ) : (
        <>
          {/* Mood filter chips */}
          <div className="flex items-center gap-2 mb-6 flex-wrap">
            <FaFilter className="text-spotify-light text-sm" />
            {availableMoods.map(mood => {
              const meta = MOOD_META[mood]
              const isActive = filterMood === mood
              return (
                <button
                  key={mood}
                  onClick={() => setFilterMood(mood)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold capitalize transition-all duration-200 ${
                    isActive
                      ? 'bg-spotify-green text-black'
                      : 'bg-spotify-hover text-spotify-light hover:bg-spotify-card hover:text-white'
                  }`}
                >
                  {mood === 'all' ? `All (${favorites.length})` : `${meta?.emoji || ''} ${mood} (${favorites.filter(f => f.mood === mood).length})`}
                </button>
              )
            })}
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            {Object.entries(
              favorites.reduce((acc, f) => { if (f.mood) acc[f.mood] = (acc[f.mood] || 0) + 1; return acc }, {})
            ).slice(0, 4).map(([mood, count]) => {
              const meta = MOOD_META[mood] || { emoji: '🎵', color: '#1DB954' }
              return (
                <div
                  key={mood}
                  className="glass-card p-4 text-center cursor-pointer hover:border-white/20 transition-colors"
                  onClick={() => setFilterMood(mood)}
                >
                  <div className="text-2xl mb-1">{meta.emoji}</div>
                  <div className="text-white font-bold text-lg">{count}</div>
                  <div className="text-spotify-light text-xs capitalize">{mood}</div>
                </div>
              )
            })}
          </div>

          {/* Songs grid */}
          <AnimatePresence>
            {filtered.length > 0 ? (
              <motion.div
                layout
                className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
              >
                <AnimatePresence>
                  {filtered.map(song => (
                    <FavoriteSongCard
                      key={song.id}
                      song={song}
                      onRemove={handleRemove}
                    />
                  ))}
                </AnimatePresence>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-card p-12 text-center"
              >
                <p className="text-4xl mb-3">🔍</p>
                <p className="text-white font-semibold">No {filterMood} songs saved</p>
                <p className="text-spotify-light text-sm mt-1">
                  Discover and save songs in this mood category
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  )
}
