import styles from './ToggleSwitch.module.css'

export default function ToggleSwitch({ checked, onChange, label, disabled = false }) {
  return (
    <label className={styles.toggleLabel}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className={styles.toggleInput}
      />
      <span className={styles.toggleSwitch}></span>
      {label && <span className={styles.toggleText}>{label}</span>}
    </label>
  )
}
