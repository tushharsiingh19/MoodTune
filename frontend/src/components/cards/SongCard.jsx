import { useState } from 'react'
import { motion } from 'framer-motion'
import { FaSpotify, FaYoutube, FaHeart, FaRegHeart, FaPlay } from 'react-icons/fa'
import { addFavorite, removeFavorite } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'

export default function SongCard({ song, mood, isFavorited = false, onFavoriteToggle, index = 0 }) {
  const { isAuthenticated } = useAuth()
  const [favorited, setFavorited] = useState(isFavorited)
  const [favoriteId, setFavoriteId] = useState(song.id || null)
  const [loading, setLoading] = useState(false)

  const handleFavorite = async (e) => {
    e.stopPropagation()
    if (!isAuthenticated) {
      toast.error('Please log in to save favorites')
      return
    }
    setLoading(true)
    try {
      if (favorited && favoriteId) {
        await removeFavorite(favoriteId)
        setFavorited(false)
        setFavoriteId(null)
        toast.success('Removed from favorites')
        onFavoriteToggle?.()
      } else {
        const saved = await addFavorite({
          song_name: song.song_name,
          artist: song.artist,
          album: song.album,
          album_image: song.album_image,
          spotify_url: song.spotify_url,
          youtube_url: song.youtube_url,
          youtube_thumbnail: song.youtube_thumbnail,
          popularity: song.popularity,
          mood,
        })
        setFavorited(true)
        setFavoriteId(saved.id)
        toast.success('Added to favorites! ❤️')
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Something went wrong'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.4 }}
      className="song-card"
    >
      {/* Album Art */}
      <div className="relative mb-4">
        {song.album_image ? (
          <img
            src={song.album_image}
            alt={song.album || song.song_name}
            className="w-full aspect-square object-cover rounded-lg"
            loading="lazy"
          />
        ) : (
          <div className="w-full aspect-square rounded-lg bg-spotify-hover flex items-center justify-center">
            <FaPlay className="text-3xl text-spotify-light" />
          </div>
        )}
        {/* Hover play overlay */}
        <div className="absolute inset-0 bg-black/40 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <div className="w-12 h-12 bg-spotify-green rounded-full flex items-center justify-center shadow-lg transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
            <FaPlay className="text-black ml-1" />
          </div>
        </div>
      </div>

      {/* Song Info */}
      <div className="flex-1 min-w-0 mb-3">
        <h3 className="text-white font-semibold text-sm truncate">{song.song_name}</h3>
        <p className="text-spotify-light text-xs truncate mt-0.5">{song.artist}</p>
        {song.popularity && (
          <div className="flex items-center gap-1 mt-1">
            <div className="h-1 flex-1 bg-spotify-hover rounded-full overflow-hidden">
              <div
                className="h-full bg-spotify-green rounded-full"
                style={{ width: `${song.popularity}%` }}
              />
            </div>
            <span className="text-xs text-spotify-light">{song.popularity}</span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2">
        {song.spotify_url && (
          <a
            href={song.spotify_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-spotify-green/10 hover:bg-spotify-green text-spotify-green hover:text-black text-xs font-semibold transition-all duration-200"
          >
            <FaSpotify className="text-base" />
            <span className="hidden sm:block">Spotify</span>
          </a>
        )}
        {song.youtube_url && (
          <a
            href={song.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-red-500/10 hover:bg-red-500 text-red-400 hover:text-white text-xs font-semibold transition-all duration-200"
          >
            <FaYoutube className="text-base" />
            <span className="hidden sm:block">YouTube</span>
          </a>
        )}
        <button
          onClick={handleFavorite}
          disabled={loading}
          className={`p-2 rounded-lg transition-all duration-200 ${
            favorited
              ? 'text-red-400 bg-red-500/10 hover:bg-red-500/20'
              : 'text-spotify-light hover:text-red-400 hover:bg-red-500/10'
          }`}
        >
          {favorited ? <FaHeart /> : <FaRegHeart />}
        </button>
      </div>
    </motion.div>
  )
}
