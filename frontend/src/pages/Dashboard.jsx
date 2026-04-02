import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { digests } from '../api'
import Modal from '../components/Modal'
import StatusBadge from '../components/StatusBadge'
import styles from './Dashboard.module.css'

export default function Dashboard({ showToast }) {
  const [digestList, setDigestList] = useState([])
  const [loading, setLoading] = useState(true)
  const [showNewModal, setShowNewModal] = useState(false)
  const [runningId, setRunningId] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [newDigest, setNewDigest] = useState({
    name: '',
    schedule_time: '09:00',
  })

  useEffect(() => {
    loadDigests()
  }, [])

  async function loadDigests() {
    try {
      setLoading(true)
      const data = await digests.list()
      setDigestList(data)
    } catch (error) {
      showToast(`Error loading digests: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateDigest() {
    if (!newDigest.name.trim()) {
      showToast('Digest name is required', 'warning')
      return
    }

    try {
      await digests.create(newDigest)
      showToast('Digest created successfully', 'success')
      setNewDigest({ name: '', schedule_time: '09:00' })
      setShowNewModal(false)
      loadDigests()
    } catch (error) {
      showToast(`Error creating digest: ${error.message}`, 'error')
    }
  }

  async function handleRunDigest(id) {
    try {
      setRunningId(id)
      await digests.run(id)
      showToast('Digest run started', 'success')
      loadDigests()
    } catch (error) {
      showToast(`Error running digest: ${error.message}`, 'error')
    } finally {
      setRunningId(null)
    }
  }

  async function handleDeleteDigest(id) {
    try {
      await digests.delete(id)
      showToast('Digest deleted successfully', 'success')
      setDeleteConfirm(null)
      loadDigests()
    } catch (error) {
      showToast(`Error deleting digest: ${error.message}`, 'error')
    }
  }

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <div>
          <h1>Dashboard</h1>
          <p>Manage your email digest configurations</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowNewModal(true)}>
          + New Digest
        </button>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="loading"></div>
          <p>Loading digests...</p>
        </div>
      ) : digestList.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <h3>No digests yet</h3>
          <p>Create your first email digest to get started</p>
          <button
            className="btn btn-primary mt-lg"
            onClick={() => setShowNewModal(true)}
          >
            Create First Digest
          </button>
        </div>
      ) : (
        <div className={styles.grid}>
          {digestList.map((digest) => (
            <div key={digest.id} className={`card ${styles.digestCard}`}>
              <div className={styles.cardHeader}>
                <div>
                  <h3>{digest.name}</h3>
                  <p className="text-sm text-secondary">{digest.description}</p>
                </div>
                <StatusBadge status={digest.active} type="status" />
              </div>

              <div className={styles.cardContent}>
                <div className={styles.detail}>
                  <span className="text-muted">Schedule:</span>
                  <span className="text-sm">{digest.schedule_time || '09:00'}</span>
                </div>
                <div className={styles.detail}>
                  <span className="text-muted">Filters:</span>
                  <span className="text-sm">{digest.filter_count || 0}</span>
                </div>
                <div className={styles.detail}>
                  <span className="text-muted">Channels:</span>
                  <span className="text-sm">{digest.channel_count || 0}</span>
                </div>
              </div>

              <div className={styles.cardFooter}>
                <Link to={`/digest/${digest.id}`} className="btn btn-secondary btn-sm">
                  Configure
                </Link>
                <button
                  className="btn btn-success btn-sm"
                  onClick={() => handleRunDigest(digest.id)}
                  disabled={runningId === digest.id}
                >
                  {runningId === digest.id ? (
                    <>
                      <span className="loading"></span> Running
                    </>
                  ) : (
                    '▶ Run Now'
                  )}
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => setDeleteConfirm(digest.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        isOpen={showNewModal}
        onClose={() => setShowNewModal(false)}
        title="Create New Digest"
        actions={
          <>
            <button className="btn btn-secondary" onClick={() => setShowNewModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleCreateDigest}>
              Create
            </button>
          </>
        }
      >
        <div className={styles.formGroup}>
          <label>Digest Name *</label>
          <input
            type="text"
            placeholder="e.g., Daily Marketing Digest"
            value={newDigest.name}
            onChange={(e) => setNewDigest({ ...newDigest, name: e.target.value })}
          />
        </div>
        <div className={styles.formGroup}>
          <label>Default Schedule Time</label>
          <input
            type="time"
            value={newDigest.schedule_time}
            onChange={(e) => setNewDigest({ ...newDigest, schedule_time: e.target.value })}
          />
        </div>
      </Modal>

      <Modal
        isOpen={deleteConfirm !== null}
        onClose={() => setDeleteConfirm(null)}
        title="Delete Digest?"
        actions={
          <>
            <button className="btn btn-secondary" onClick={() => setDeleteConfirm(null)}>
              Cancel
            </button>
            <button
              className="btn btn-danger"
              onClick={() => handleDeleteDigest(deleteConfirm)}
            >
              Delete
            </button>
          </>
        }
      >
        <p>Are you sure you want to delete this digest? This action cannot be undone.</p>
      </Modal>
    </div>
  )
}
