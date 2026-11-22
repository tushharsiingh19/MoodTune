import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FaBrain, FaArrowRight } from 'react-icons/fa'
import LoadingSpinner from './LoadingSpinner'

const PLACEHOLDER_EXAMPLES = [
  "I'm feeling so happy today, everything is going well!",
  "I'm heartbroken after the breakup...",
  "Pumped up for my workout session 💪",
  "Need something to help me focus and study",
  "It's a chill Sunday morning, time to relax",
  "I'm excited about starting my new internship!",
]

export default function MoodInput({ onSubmit, loading }) {
  const [text, setText] = useState('')
  const placeholder = PLACEHOLDER_EXAMPLES[Math.floor(Math.random() * PLACEHOLDER_EXAMPLES.length)]

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (text.trim().length < 2) return
    onSubmit(text.trim())
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmit()
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="glass-card p-6">
        <label className="block text-sm text-spotify-light mb-3 font-medium">
          How are you feeling right now? Tell me in your own words...
        </label>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={4}
          disabled={loading}
          className="input-field resize-none mb-4 text-sm leading-relaxed"
          maxLength={1000}
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-spotify-light">{text.length}/1000 · Ctrl+Enter to analyze</span>
          <motion.button
            onClick={handleSubmit}
            disabled={loading || text.trim().length < 2}
            whileTap={{ scale: 0.97 }}
            className="btn-primary flex items-center gap-2 !py-2.5 !px-6"
          >
            {loading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <>
                <FaBrain />
                <span>Analyze Mood</span>
                <FaArrowRight className="text-xs" />
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Quick mood chips */}
      <AnimatePresence>
        {!loading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-wrap gap-2 mt-4 justify-center"
          >
            {['😊 Happy', '😢 Sad', '💪 Motivated', '📚 Study', '🎉 Party', '😌 Chill'].map(chip => (
              <button
                key={chip}
                onClick={() => setText(`I'm feeling ${chip.split(' ')[1].toLowerCase()} today`)}
                className="text-xs px-3 py-1.5 rounded-full bg-spotify-hover hover:bg-spotify-green hover:text-black text-spotify-light transition-all duration-200"
              >
                {chip}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
