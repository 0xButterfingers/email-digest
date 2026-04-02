import { useState, useEffect } from 'react'
import { digests, history } from '../api'
import StatusBadge from '../components/StatusBadge'
import styles from './History.module.css'

export default function HistoryPage({ showToast }) {
  const [historyList, setHistoryList] = useState([])
  const [digestsList, setDigestsList] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDigest, setSelectedDigest] = useState(null)
  const [expandedRun, setExpandedRun] = useState(null)

  useEffect(() => {
    loadHistory()
  }, [selectedDigest])

  async function loadHistory() {
    try {
      setLoading(true)
      const digestData = await digests.list()
      setDigestsList(digestData)

      if (selectedDigest) {
        const historyData = await history.list(selectedDigest)
        setHistoryList(historyData)
      } else if (digestData.length > 0) {
        const historyData = await history.list(digestData[0].id)
        setHistoryList(historyData)
        setSelectedDigest(digestData[0].id)
      }
    } catch (error) {
      showToast(`Error loading history: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A'
    if (seconds < 60) return `${seconds}s`
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  }

  return (
    <div className={styles.history}>
      <div className={styles.header}>
        <h1>History</h1>
        <p>View past digest runs and their results</p>
      </div>

      <div className={styles.filterSection}>
        <label>Filter by Digest:</label>
        <select
          value={selectedDigest || ''}
          onChange={(e) => setSelectedDigest(e.target.value)}
        >
          {digestsList.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="loading"></div>
          <p>Loading history...</p>
        </div>
      ) : historyList.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <h3>No runs yet</h3>
          <p>No digest runs have been executed for this configuration</p>
        </div>
      ) : (
        <div className={styles.historyList}>
          {historyList.map((run) => (
            <div key={run.id} className={`card ${styles.runCard}`}>
              <div
                className={styles.runHeader}
                onClick={() =>
                  setExpandedRun(expandedRun === run.id ? null : run.id)
                }
              >
                <div className={styles.runInfo}>
                  <StatusBadge status={run.status} type="result" />
                  <div className={styles.runMeta}>
                    <div className={styles.runTime}>{formatDate(run.timestamp)}</div>
                    <div className={styles.runDuration}>
                      Duration: {formatDuration(run.duration)}
                    </div>
                  </div>
                </div>
                <button className={styles.expandButton}>
                  {expandedRun === run.id ? '−' : '+'}
                </button>
              </div>

              {expandedRun === run.id && (
                <div className={styles.runDetails}>
                  <div className={styles.detail}>
                    <span className="text-muted">Status:</span>
                    <StatusBadge status={run.status} type="result" />
                  </div>
                  <div className={styles.detail}>
                    <span className="text-muted">Emails Processed:</span>
                    <span>{run.emails_processed || 0}</span>
                  </div>
                  <div className={styles.detail}>
                    <span className="text-muted">Emails Sent:</span>
                    <span>{run.emails_sent || 0}</span>
                  </div>
                  {run.error && (
                    <div className={styles.detail}>
                      <span className="text-danger">Error:</span>
                      <span className="text-danger">{run.error}</span>
                    </div>
                  )}
                  {run.summary && (
                    <div className={styles.detail}>
                      <span className="text-muted">Summary:</span>
                      <span className={styles.summary}>{run.summary}</span>
                    </div>
                  )}
                  <div className={styles.detail}>
                    <span className="text-muted">Channels:</span>
                    <span>{run.channels_count || 0}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
