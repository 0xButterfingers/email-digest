import styles from './Modal.module.css'

export default function Modal({ isOpen, onClose, title, children, actions }) {
  if (!isOpen) return null

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>{title}</h2>
          <button className={styles.closeButton} onClick={onClose}>
            ✕
          </button>
        </div>
        <div className={styles.modalBody}>{children}</div>
        {actions && <div className={styles.modalFooter}>{actions}</div>}
      </div>
    </div>
  )
}
