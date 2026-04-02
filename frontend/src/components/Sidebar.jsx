import { Link, useLocation } from 'react-router-dom'
import styles from './Sidebar.module.css'

export default function Sidebar() {
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <aside className={styles.sidebar}>
      <nav className={styles.nav}>
        <Link
          to="/"
          className={`${styles.navLink} ${isActive('/') ? styles.active : ''}`}
        >
          <span>📊</span>
          Dashboard
        </Link>
        <Link
          to="/channels"
          className={`${styles.navLink} ${isActive('/channels') ? styles.active : ''}`}
        >
          <span>📱</span>
          Channels
        </Link>
        <Link
          to="/history"
          className={`${styles.navLink} ${isActive('/history') ? styles.active : ''}`}
        >
          <span>📝</span>
          History
        </Link>
        <Link
          to="/settings"
          className={`${styles.navLink} ${isActive('/settings') ? styles.active : ''}`}
        >
          <span>⚙️</span>
          Settings
        </Link>
      </nav>
    </aside>
  )
}
