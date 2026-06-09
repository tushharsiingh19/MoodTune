import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { FaMusic, FaChevronDown, FaSearch } from 'react-icons/fa'
import { getSongsByMood, getCatalogStats } from '../services/api'
import SongCard from '../components/cards/SongCard'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

const MOOD_META = {
  happy:        { emoji: '😊', color: '#FFD700', label: 'Happy',        desc: 'Upbeat feel-good pop & dance' },
  sad:          { emoji: '😢', color: '#6B8DD6', label: 'Sad',          desc: 'Emotional acoustic & indie' },
  angry:        { emoji: '😤', color: '#FF4444', label: 'Angry',        desc: 'Rock, metal & intense hip-hop' },
  romantic:     { emoji: '💕', color: '#FF69B4', label: 'Romantic',     desc: 'Love songs, soul & R&B ballads' },
  relaxed:      { emoji: '😌', color: '#90EE90', label: 'Relaxed',      desc: 'Ambient, lo-fi & acoustic chill' },
  motivational: { emoji: '💪', color: '#FF8C00', label: 'Motivational', desc: 'Workout anthems & power tracks' },
  party:        { emoji: '🎉', color: '#9B59B6', label: 'Party',        desc: 'EDM, dance & club classics' },
  study:        { emoji: '📚', color: '#20B2AA', label: 'Study',        desc: 'Classical, lo-fi & focus music' },
}

const PAGE_SIZE = 20

export default function CatalogPage() {
  const navigate        = useNavigate()
  const [activeMood, setActiveMood]   = useState('happy')
  const [songs, setSongs]             = useState([])
  const [loading, setLoading]         = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [skip, setSkip]               = useState(0)
  const [hasMore, setHasMore]         = useState(true)
  const [stats, setStats]             = useState({})
  const [search, setSearch]           = useState('')

  // Fetch catalog stats on mount
  useEffect(() => {
    getCatalogStats()
      .then(data => setStats(data.moods || {}))
      .catch(() => {})
  }, [])

  // Fetch songs whenever mood changes
  useEffect(() => {
    fetchSongs(activeMood, 0, true)
  }, [activeMood])

  const fetchSongs = useCallback(async (mood, newSkip, reset = false) => {
    if (reset) {
      setLoading(true)
      setSongs([])
      setSkip(0)
      setHasMore(true)
    } else {
      setLoadingMore(true)
    }

    try {
      const data = await getSongsByMood(mood, PAGE_SIZE, newSkip)
      if (reset) {
        setSongs(data)
      } else {
        setSongs(prev => [...prev, ...data])
      }
      setSkip(newSkip + data.length)
      setHasMore(data.length === PAGE_SIZE)
    } catch (err) {
      toast.error('Failed to load songs. Is the backend running?')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [])

  const handleLoadMore = () => {
    fetchSongs(activeMood, skip, false)
  }

  // Client-side search filter
  const filtered = search.trim()
    ? songs.filter(s =>
        s.song_name.toLowerCase().includes(search.toLowerCase()) ||
        s.artist.toLowerCase().includes(search.toLowerCase())
      )
    : songs

  const meta = MOOD_META[activeMood]

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <h1 className="text-4xl font-black text-white mb-2">
          Song <span className="text-spotify-green">Catalog</span>
        </h1>
        <p className="text-spotify-light">
          Browse {Object.values(stats).reduce((a, b) => a + b, 0) || '320+'} curated songs across 8 moods
        </p>
      </motion.div>

      {/* Mood Tabs */}
      <div className="flex flex-wrap gap-2 justify-center mb-8">
        {Object.entries(MOOD_META).map(([mood, m]) => (
          <motion.button
            key={mood}
            whileTap={{ scale: 0.95 }}
            onClick={() => { setActiveMood(mood); setSearch('') }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-semibold transition-all duration-200 ${
              activeMood === mood
                ? 'text-black scale-105 shadow-lg'
                : 'bg-spotify-card text-spotify-light hover:bg-spotify-hover hover:text-white'
            }`}
            style={activeMood === mood ? { backgroundColor: m.color } : {}}
          >
            <span>{m.emoji}</span>
            <span>{m.label}</span>
            {stats[mood] && (
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                activeMood === mood ? 'bg-black/20 text-black' : 'bg-white/10 text-white/50'
              }`}>
                {stats[mood]}
              </span>
            )}
          </motion.button>
        ))}
      </div>

      {/* Active mood banner */}
      <motion.div
        key={activeMood}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-5 mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        style={{ borderColor: `${meta.color}40` }}
      >
        <div className="flex items-center gap-3">
          <span className="text-4xl">{meta.emoji}</span>
          <div>
            <h2 className="text-white font-bold text-lg">{meta.label}</h2>
            <p className="text-spotify-light text-sm">{meta.desc}</p>
          </div>
        </div>

        {/* Search within mood */}
        <div className="relative w-full sm:w-64">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-spotify-light text-xs" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search songs or artists..."
            className="input-field pl-9 py-2 text-sm"
          />
        </div>
      </motion.div>

      {/* Song Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-24">
          <LoadingSpinner size="lg" text={`Loading ${meta.label.toLowerCase()} songs...`} />
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <div className="text-5xl mb-4">🎵</div>
          {search ? (
            <>
              <p className="text-white font-semibold">No results for "{search}"</p>
              <p className="text-spotify-light text-sm mt-1">Try a different search term</p>
              <button onClick={() => setSearch('')} className="btn-secondary mt-4 !py-2 !px-4 text-sm">
                Clear Search
              </button>
            </>
          ) : (
            <>
              <p className="text-white font-semibold">No songs in catalog yet</p>
              <p className="text-spotify-light text-sm mt-2 mb-4">
              Empty vibes... The song catalog is still being filled with mood-tagged tracks. Check back soon or contribute your own!
              </p>
             
            </>
          )}
        </div>
      ) : (
        <>
          <div className="text-xs text-spotify-light mb-4">
            Showing {filtered.length} song{filtered.length !== 1 ? 's' : ''}
            {search && ` matching "${search}"`}
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={activeMood}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
            >
              {filtered.map((song, i) => (
                <SongCard
                  key={`${song.song_name}-${song.artist}-${i}`}
                  song={song}
                  mood={activeMood}
                  index={i}
                />
              ))}
            </motion.div>
          </AnimatePresence>

          {/* Load More */}
          {!search && hasMore && (
            <div className="flex justify-center mt-10">
              <motion.button
                onClick={handleLoadMore}
                disabled={loadingMore}
                whileTap={{ scale: 0.97 }}
                className="btn-secondary flex items-center gap-2"
              >
                {loadingMore ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <>
                    <FaChevronDown />
                    Load More Songs
                  </>
                )}
              </motion.button>
            </div>
          )}

          {!hasMore && !search && (
            <p className="text-center text-spotify-light text-sm mt-8">
              All {filtered.length} {meta.label.toLowerCase()} songs loaded ✓
            </p>
          )}
        </>
      )}

      {/* CTA to recommend */}
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        className="glass-card p-8 text-center mt-12"
      >
        <p className="text-white font-semibold mb-1">Want personalized picks?</p>
        <p className="text-spotify-light text-sm mb-4">
          Let the AI analyze your mood and hand-pick songs just for you
        </p>
        <button onClick={() => navigate('/recommend')} className="btn-primary">
          Analyze My Mood
        </button>
      </motion.div>
    </div>
  )
}
