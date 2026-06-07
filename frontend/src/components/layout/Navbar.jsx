import { Link, NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FaMusic, FaHeart, FaHistory, FaSignOutAlt, FaUser } from 'react-icons/fa'
import { useAuth } from '../../context/AuthContext'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const navLinkClass = ({ isActive }) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
      isActive
        ? 'text-spotify-green bg-spotify-green/10'
        : 'text-spotify-light hover:text-white hover:bg-spotify-hover'
    }`

  return (
    <motion.nav
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-50 bg-spotify-black/80 backdrop-blur-xl border-b border-white/10"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-spotify-green rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
              <FaMusic className="text-black text-sm" />
            </div>
            <span className="text-white font-bold text-lg hidden sm:block">
              Mood<span className="text-spotify-green">Tunes</span> AI
            </span>
          </Link>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              Home
            </NavLink>
            <NavLink to="/recommend" className={navLinkClass}>
              Discover
            </NavLink>
            {isAuthenticated && (
              <>
                <NavLink to="/favorites" className={navLinkClass}>
                  <FaHeart className="text-xs" />
                  <span className="hidden sm:block">Favorites</span>
                </NavLink>
                <NavLink to="/history" className={navLinkClass}>
                  <FaHistory className="text-xs" />
                  <span className="hidden sm:block">History</span>
                </NavLink>
              </>
            )}
          </div>

          {/* Auth actions */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="hidden sm:flex items-center gap-2 text-sm text-spotify-light">
                  <div className="w-7 h-7 bg-spotify-green rounded-full flex items-center justify-center">
                    <FaUser className="text-black text-xs" />
                  </div>
                  <span>{user?.name}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-spotify-light hover:text-white hover:bg-spotify-hover transition-all"
                >
                  <FaSignOutAlt />
                  <span className="hidden sm:block">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login" className="btn-secondary !py-2 !px-4 text-sm">
                  Log In
                </Link>
                <Link to="/register" className="btn-primary !py-2 !px-4 text-sm">
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.nav>
  )
}
