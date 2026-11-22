import { motion } from 'framer-motion'

const MOOD_GRADIENTS = {
  happy:       'from-yellow-500/20 to-orange-500/20',
  sad:         'from-blue-500/20 to-indigo-600/20',
  angry:       'from-red-500/20 to-rose-600/20',
  romantic:    'from-pink-500/20 to-rose-400/20',
  relaxed:     'from-green-500/20 to-teal-500/20',
  motivational:'from-orange-500/20 to-amber-400/20',
  party:       'from-purple-500/20 to-violet-600/20',
  study:       'from-teal-500/20 to-cyan-500/20',
}

export default function MoodCard({ mood, confidence, emoji, description, color }) {
  const gradient = MOOD_GRADIENTS[mood] || 'from-white/10 to-white/5'
  const confidencePct = Math.round(confidence * 100)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, type: 'spring' }}
      className={`glass-card bg-gradient-to-br ${gradient} p-6 text-center`}
    >
      {/* Emoji */}
      <motion.div
        animate={{ scale: [1, 1.15, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
        className="text-6xl mb-3"
      >
        {emoji}
      </motion.div>

      {/* Mood label */}
      <h2 className="text-3xl font-bold text-white capitalize mb-1">{mood}</h2>
      <p className="text-spotify-light text-sm mb-4">{description}</p>

      {/* Confidence meter */}
      <div className="mt-4">
        <div className="flex justify-between text-xs text-spotify-light mb-1">
          <span>Confidence</span>
          <span className="font-bold" style={{ color }}>{confidencePct}%</span>
        </div>
        <div className="confidence-bar">
          <motion.div
            className="confidence-fill"
            style={{ backgroundColor: color }}
            initial={{ width: 0 }}
            animate={{ width: `${confidencePct}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </div>
      </div>
    </motion.div>
  )
}
