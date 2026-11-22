import { motion } from 'framer-motion'

export default function LoadingSpinner({ fullscreen = false, size = 'md', text = '' }) {
  const sizes = { sm: 'w-5 h-5', md: 'w-10 h-10', lg: 'w-16 h-16' }

  const spinner = (
    <div className="flex flex-col items-center gap-4">
      <motion.div
        className={`${sizes[size]} rounded-full border-2 border-spotify-hover border-t-spotify-green`}
        animate={{ rotate: 360 }}
        transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
      />
      {text && <p className="text-spotify-light text-sm">{text}</p>}
    </div>
  )

  if (fullscreen) {
    return (
      <div className="fixed inset-0 bg-spotify-dark flex items-center justify-center z-50">
        {spinner}
      </div>
    )
  }

  return spinner
}
