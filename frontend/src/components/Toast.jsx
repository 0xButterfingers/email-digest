import styles from './Toast.module.css'

export default function Toast({ message, type = 'info' }) {
  return (
    <div className={`${styles.toast} ${styles[type]}`}>
      <span className={styles.icon}>
        {type === 'success' && '✓'}
        {type === 'error' && '✕'}
        {type === 'warning' && '⚠'}
        {type === 'info' && 'ℹ'}
      </span>
      <span>{message}</span>
    </div>
  )
}
