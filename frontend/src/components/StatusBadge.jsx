export default function StatusBadge({ status, type = 'status' }) {
  let statusText = status
  let badgeClass = 'badge-info'

  if (type === 'status') {
    if (status === 'active' || status === true) {
      statusText = 'Active'
      badgeClass = 'badge-success'
    } else if (status === 'inactive' || status === false) {
      statusText = 'Inactive'
      badgeClass = 'badge-secondary'
    }
  } else if (type === 'result') {
    if (status === 'success') {
      badgeClass = 'badge-success'
      statusText = '✓ Success'
    } else if (status === 'failed' || status === 'error') {
      badgeClass = 'badge-danger'
      statusText = '✕ Failed'
    } else if (status === 'pending') {
      badgeClass = 'badge-info'
      statusText = 'Pending'
    }
  }

  return <span className={`badge ${badgeClass}`}>{statusText}</span>
}
