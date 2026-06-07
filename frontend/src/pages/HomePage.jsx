import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FaMusic, FaBrain, FaSpotify, FaYoutube, FaArrowRight } from 'react-icons/fa'
import MoodInput from '../components/ui/MoodInput'
import { useState } from 'react'

const MOODS = [
  { emoji: '😊', label: 'Happy', color: '#FFD700' },
  { emoji: '😢', label: 'Sad', color: '#6B8DD6' },
  { emoji: '😤', label: 'Angry', color: '#FF4444' },
  { emoji: '💕', label: 'Romantic', color: '#FF69B4' },
  { emoji: '😌', label: 'Relaxed', color: '#90EE90' },
  { emoji: '💪', label: 'Motivated', color: '#FF8C00' },
  { emoji: '🎉', label: 'Party', color: '#9B59B6' },
  { emoji: '📚', label: 'Study', color: '#20B2AA' },
]

const FEATURES = [
  { icon: <FaBrain className="text-2xl text-spotify-green" />, title: 'AI Mood Detection', desc: 'NLP-powered emotion analysis from your text using TF-IDF & Logistic Regression.' },
  { icon: <FaSpotify className="text-2xl text-spotify-green" />, title: 'Spotify Integration', desc: "Real-time song recommendations pulled directly from Spotify's vast catalog." },
  { icon: <FaYoutube className="text-2xl text-red-400" />, title: 'YouTube Links', desc: 'Every song comes with a direct YouTube link for instant playback.' },
  { icon: <FaMusic className="text-2xl text-purple-400" />, title: '8 Mood Categories', desc: 'From happy and sad to study and party — music for every emotion.' },
]

export default function HomePage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  const handleMoodSubmit = (text) => {
    navigate('/recommend', { state: { text } })
  }

  return (
    <div className="min-h-screen">
      {/* ── Hero ── */}
      <section className="relative overflow-hidden py-20 px-4">
        {/* Background blobs */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-spotify-green/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-spotify-green/10 border border-spotify-green/30 text-spotify-green text-sm font-medium mb-6">
              <FaBrain className="text-xs" />
              AI-Powered Music Recommendations
            </span>
            <h1 className="text-5xl sm:text-7xl font-black text-white mb-6 leading-tight">
              Music That Matches
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-spotify-green to-emerald-400">
                Your Mood
              </span>
            </h1>
            <p className="text-spotify-light text-lg sm:text-xl max-w-2xl mx-auto mb-12">
              Tell us how you're feeling and our AI will detect your emotion and curate the perfect playlist from Spotify.
            </p>
          </motion.div>

          {/* Mood Input */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <MoodInput onSubmit={handleMoodSubmit} loading={loading} />
          </motion.div>
        </div>
      </section>

      {/* ── Mood Grid ── */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white text-center mb-8">
            Music for Every Emotion
          </h2>
          <div className="grid grid-cols-4 sm:grid-cols-8 gap-3">
            {MOODS.map((mood, i) => (
              <motion.button
                key={mood.label}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.07 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/recommend', { state: { text: `I'm feeling ${mood.label.toLowerCase()} today`, mood: mood.label.toLowerCase() } })}
                className="flex flex-col items-center gap-2 p-3 rounded-xl bg-spotify-card hover:bg-spotify-hover transition-all"
              >
                <span className="text-3xl">{mood.emoji}</span>
                <span className="text-xs text-spotify-light font-medium">{mood.label}</span>
              </motion.button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-white text-center mb-12">How It Works</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass-card p-6 text-center hover:border-spotify-green/30 transition-colors"
              >
                <div className="mb-4 flex justify-center">{f.icon}</div>
                <h3 className="text-white font-semibold mb-2">{f.title}</h3>
                <p className="text-spotify-light text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-4 text-center">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          className="max-w-lg mx-auto glass-card p-10"
        >
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Discover?</h2>
          <p className="text-spotify-light mb-8">Tell us your mood and get your personalized playlist instantly.</p>
          <button onClick={() => navigate('/recommend')} className="btn-primary inline-flex items-center gap-2">
            Get My Playlist <FaArrowRight />
          </button>
        </motion.div>
      </section>
    </div>
  )
}
