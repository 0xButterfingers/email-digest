import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { digests, filters, channels, history } from '../api'
import Modal from '../components/Modal'
import ToggleSwitch from '../components/ToggleSwitch'
import StatusBadge from '../components/StatusBadge'
import styles from './DigestDetail.module.css'

const ALL_DAYS = [
  { value: 'mon', label: 'Mon' },
  { value: 'tue', label: 'Tue' },
  { value: 'wed', label: 'Wed' },
  { value: 'thu', label: 'Thu' },
  { value: 'fri', label: 'Fri' },
  { value: 'sat', label: 'Sat' },
  { value: 'sun', label: 'Sun' },
]

const SCAN_HOUR_OPTIONS = [
  { value: 6, label: 'Last 6 hours' },
  { value: 12, label: 'Last 12 hours' },
  { value: 24, label: 'Last 24 hours' },
  { value: 48, label: 'Last 48 hours' },
  { value: 72, label: 'Last 72 hours' },
]

function parseDays(schedule_days) {
  if (!schedule_days) return ['mon', 'tue', 'wed', 'thu', 'fri']
  return schedule_days.split(',').filter(Boolean)
}

function formatDays(daysArray) {
  return ALL_DAYS.map((d) => d.value).filter((d) => daysArray.includes(d)).join(',')
}

function channelDisplayValue(channel) {
  const cfg = channel.config || {}
  if (cfg.chat_id) return `Chat ID: ${cfg.chat_id}`
  if (cfg.phone_number) return cfg.phone_number
  if (cfg.webhook_url) return cfg.webhook_url
  return 'Configured'
}

export default function DigestDetail({ showToast }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const [digest, setDigest] = useState(null)
  const [filterList, setFilterList] = useState([])
  const [channelList, setChannelList] = useState([])
  const [historyList, setHistoryList] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [running, setRunning] = useState(false)
  const [showFilterModal, setShowFilterModal] = useState(false)
  const [showChannelModal, setShowChannelModal] = useState(false)
  const [newFilter, setNewFilter] = useState({ filter_type: 'sender', value: '' })
  const [newChannel, setNewChannel] = useState({
    type: 'Telegram',
    phone_number: '',
    chat_id: '',
    webhook_url: '',
    is_primary: false,
  })

  useEffect(() => {
    loadData()
  }, [id])

  async function loadData() {
    try {
      setLoading(true)
      const [digestData, filterData, channelData, historyData] = await Promise.all([
        digests.get(id),
        filters.list(id),
        channels.list(id),
        history.list(id),
      ])
      setDigest(digestData)
      setFilterList(filterData)
      setChannelList(channelData)
      setHistoryList(Array.isArray(historyData) ? historyData.slice(0, 5) : [])
    } catch (error) {
      showToast(`Error loading digest: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  function toggleDay(day) {
    const current = parseDays(digest.schedule_days)
    const next = current.includes(day) ? current.filter((d) => d !== day) : [...current, day]
    setDigest({ ...digest, schedule_days: formatDays(next) })
  }

  async function handleSaveDigest() {
    const days = parseDays(digest.schedule_days)
    if (days.length === 0) {
      showToast('Select at least one schedule day', 'warning')
      return
    }
    try {
      setSaving(true)
      await digests.update(id, {
        name: digest.name,
        schedule_time: digest.schedule_time,
        schedule_days: formatDays(days),
        scan_hours: digest.scan_hours,
        is_active: digest.is_active,
      })
      showToast('Digest saved successfully', 'success')
      loadData()
    } catch (error) {
      showToast(`Error saving digest: ${error.message}`, 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleAddFilter() {
    if (!newFilter.value.trim()) {
      showToast('Filter value is required', 'warning')
      return
    }
    try {
      await filters.create(id, newFilter)
      showToast('Filter added', 'success')
      setNewFilter({ filter_type: 'sender', value: '' })
      setShowFilterModal(false)
      loadData()
    } catch (error) {
      showToast(`Error adding filter: ${error.message}`, 'error')
    }
  }

  async function handleDeleteFilter(filterId) {
    try {
      await filters.delete(id, filterId)
      showToast('Filter deleted', 'success')
      loadData()
    } catch (error) {
      showToast(`Error deleting filter: ${error.message}`, 'error')
    }
  }

  async function handleAddChannel() {
    const type = newChannel.type
    if (type === 'WhatsApp' && !newChannel.phone_number.trim()) {
      showToast('Phone number is required for WhatsApp', 'warning')
      return
    }
    if (type === 'Telegram' && !newChannel.chat_id.trim()) {
      showToast('Chat ID is required for Telegram', 'warning')
      return
    }
    if (type === 'Discord' && !newChannel.webhook_url.trim()) {
      showToast('Webhook URL is required for Discord', 'warning')
      return
    }
    try {
      const config = {}
      if (type === 'WhatsApp') config.phone_number = newChannel.phone_number
      if (type === 'Telegram') config.chat_id = newChannel.chat_id
      if (type === 'Discord') config.webhook_url = newChannel.webhook_url
      await channels.create(id, {
        channel_type: type.toLowerCase(),
        config,
        is_primary: newChannel.is_primary,
      })
      showToast('Channel added', 'success')
      setNewChannel({ type: 'Telegram', phone_number: '', chat_id: '', webhook_url: '', is_primary: false })
      setShowChannelModal(false)
      loadData()
    } catch (error) {
      showToast(`Error adding channel: ${error.message}`, 'error')
    }
  }

  async function handleDeleteChannel(channelId) {
    try {
      await channels.delete(id, channelId)
      showToast('Channel deleted', 'success')
      loadData()
    } catch (error) {
      showToast(`Error deleting channel: ${error.message}`, 'error')
    }
  }

  async function handleSetPrimary(channelId) {
    try {
      await channels.update(id, channelId, { is_primary: true })
      showToast('Primary channel updated', 'success')
      loadData()
    } catch (error) {
      showToast(`Error updating channel: ${error.message}`, 'error')
    }
  }

  async function handleRunDigest() {
    try {
      setRunning(true)
      const result = await digests.run(id)
      showToast(result.message || 'Digest run complete', result.success ? 'success' : 'error')
      setTimeout(() => loadData(), 1500)
    } catch (error) {
      showToast(`Error running digest: ${error.message}`, 'error')
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="empty-state">
        <div className="loading"></div>
        <p>Loading digest details...</p>
      </div>
    )
  }

  if (!digest) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🚫</div>
        <h3>Digest not found</h3>
        <button className="btn btn-primary mt-lg" onClick={() => navigate('/')}>
          Back to Dashboard
        </button>
      </div>
    )
  }

  const selectedDays = parseDays(digest.schedule_days)

  return (
    <div className={styles.detail}>
      <div className={styles.header}>
        <button className="btn btn-secondary" onClick={() => navigate('/')}>
          ← Back
        </button>
        <h1>{digest.name}</h1>
        <span className={`badge ${digest.is_active ? 'badge-success' : 'badge-secondary'}`}>
          {digest.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>

      <div className={styles.content}>
        {/* ── Configuration ─────────────────────────────── */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Configuration</h2>
          <div className="card">
            <div className={styles.formGroup}>
              <label>Digest Name</label>
              <input
                type="text"
                value={digest.name}
                onChange={(e) => setDigest({ ...digest, name: e.target.value })}
              />
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label>Schedule Time (SGT)</label>
                <input
                  type="time"
                  value={digest.schedule_time}
                  onChange={(e) => setDigest({ ...digest, schedule_time: e.target.value })}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Email Scan Window</label>
                <select
                  value={digest.scan_hours ?? 48}
                  onChange={(e) => setDigest({ ...digest, scan_hours: parseInt(e.target.value) })}
                >
                  {SCAN_HOUR_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className={styles.formGroup}>
              <label>Schedule Days</label>
              <div className={styles.dayPicker}>
                {ALL_DAYS.map(({ value, label }) => (
                  <button
                    key={value}
                    type="button"
                    className={`${styles.dayBtn} ${selectedDays.includes(value) ? styles.dayBtnActive : ''}`}
                    onClick={() => toggleDay(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {selectedDays.length === 0 && (
                <p className={styles.fieldHint} style={{ color: 'var(--color-danger)' }}>
                  At least one day must be selected
                </p>
              )}
            </div>

            <div className={styles.formGroup}>
              <ToggleSwitch
                checked={digest.is_active}
                onChange={(val) => setDigest({ ...digest, is_active: val })}
                label="Active"
              />
            </div>

            <div className={styles.actions}>
              <button className="btn btn-primary" onClick={handleSaveDigest} disabled={saving}>
                {saving ? 'Saving...' : 'Save Configuration'}
              </button>
              <button className="btn btn-success" onClick={handleRunDigest} disabled={running}>
                {running ? 'Running...' : '▶ Run Now'}
              </button>
            </div>
          </div>
        </div>

        {/* ── Filters ───────────────────────────────────── */}
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Email Filters</h2>
            <p className="text-secondary">Emails matching any filter will be included</p>
          </div>
          <div className="card">
            {filterList.length === 0 ? (
              <div className="empty-state">
                <p>No filters configured — all recent emails will be scanned</p>
              </div>
            ) : (
              <div className={styles.list}>
                {filterList.map((filter) => (
                  <div key={filter.id} className={styles.listItem}>
                    <div>
                      <span
                        className={`badge ${filter.filter_type === 'sender' ? 'badge-info' : 'badge-secondary'}`}
                      >
                        {filter.filter_type}
                      </span>
                      <span>{filter.value}</span>
                    </div>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDeleteFilter(filter.id)}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
            <button
              className="btn btn-secondary mt-lg"
              onClick={() => setShowFilterModal(true)}
              style={{ width: '100%' }}
            >
              + Add Filter
            </button>
          </div>
        </div>

        {/* ── Channels ──────────────────────────────────── */}
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Delivery Channels</h2>
            <p className="text-secondary">Digest will be sent to all configured channels</p>
          </div>
          <div className="card">
            {channelList.length === 0 ? (
              <div className="empty-state">
                <p>No channels configured</p>
              </div>
            ) : (
              <div className={styles.list}>
                {channelList.map((channel) => (
                  <div key={channel.id} className={styles.listItem}>
                    <div className={styles.channelInfo}>
                      <span className={`badge badge-info ${styles.channelTypeBadge}`}>
                        {channel.channel_type}
                      </span>
                      <div>
                        <div className={styles.channelValue}>{channelDisplayValue(channel)}</div>
                        <div className={styles.channelMeta}>
                          <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                            Connected
                          </span>
                          {channel.is_primary && (
                            <span className="badge badge-secondary" style={{ fontSize: '0.7rem' }}>
                              Primary
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className={styles.channelActions}>
                      {!channel.is_primary && (
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleSetPrimary(channel.id)}
                        >
                          Set Primary
                        </button>
                      )}
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteChannel(channel.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <button
              className="btn btn-secondary mt-lg"
              onClick={() => setShowChannelModal(true)}
              style={{ width: '100%' }}
            >
              + Add Channel
            </button>
          </div>
        </div>

        {/* ── History ───────────────────────────────────── */}
        {historyList.length > 0 && (
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Recent Runs</h2>
            <div className="card">
              <div className={styles.list}>
                {historyList.map((run) => (
                  <div key={run.id} className={styles.listItem}>
                    <div>
                      <StatusBadge status={run.status} type="result" />
                      <div>
                        <div className="text-sm">{new Date(run.timestamp).toLocaleString()}</div>
                        <div className="text-sm text-secondary">
                          {run.emails_processed} email{run.emails_processed !== 1 ? 's' : ''} processed
                        </div>
                      </div>
                    </div>
                    {run.error && <span className="text-danger text-sm">{run.error}</span>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Add Filter Modal ──────────────────────────── */}
      <Modal
        isOpen={showFilterModal}
        onClose={() => setShowFilterModal(false)}
        title="Add Filter"
        actions={
          <>
            <button className="btn btn-secondary" onClick={() => setShowFilterModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleAddFilter}>
              Add
            </button>
          </>
        }
      >
        <div className={styles.formGroup}>
          <label>Filter Type</label>
          <select
            value={newFilter.filter_type}
            onChange={(e) => setNewFilter({ ...newFilter, filter_type: e.target.value })}
          >
            <option value="sender">Sender (email address)</option>
            <option value="keyword">Keyword</option>
          </select>
        </div>
        <div className={styles.formGroup}>
          <label>Value</label>
          <input
            type="text"
            placeholder={newFilter.filter_type === 'sender' ? 'reports@bank.com' : 'market update'}
            value={newFilter.value}
            onChange={(e) => setNewFilter({ ...newFilter, value: e.target.value })}
            onKeyDown={(e) => e.key === 'Enter' && handleAddFilter()}
            autoFocus
          />
        </div>
      </Modal>

      {/* ── Add Channel Modal ─────────────────────────── */}
      <Modal
        isOpen={showChannelModal}
        onClose={() => setShowChannelModal(false)}
        title="Add Channel"
        actions={
          <>
            <button className="btn btn-secondary" onClick={() => setShowChannelModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleAddChannel}>
              Add
            </button>
          </>
        }
      >
        <div className={styles.formGroup}>
          <label>Channel Type</label>
          <select
            value={newChannel.type}
            onChange={(e) => setNewChannel({ ...newChannel, type: e.target.value })}
          >
            <option>Telegram</option>
            <option>WhatsApp</option>
            <option>Discord</option>
          </select>
        </div>
        {newChannel.type === 'Telegram' && (
          <div className={styles.formGroup}>
            <label>Chat ID</label>
            <input
              type="text"
              placeholder="e.g. 913269211"
              value={newChannel.chat_id}
              onChange={(e) => setNewChannel({ ...newChannel, chat_id: e.target.value })}
            />
            <p className={styles.fieldHint}>
              Message your bot, then check getUpdates to find your Chat ID
            </p>
          </div>
        )}
        {newChannel.type === 'WhatsApp' && (
          <div className={styles.formGroup}>
            <label>Phone Number</label>
            <input
              type="tel"
              placeholder="+6512345678"
              value={newChannel.phone_number}
              onChange={(e) => setNewChannel({ ...newChannel, phone_number: e.target.value })}
            />
          </div>
        )}
        {newChannel.type === 'Discord' && (
          <div className={styles.formGroup}>
            <label>Webhook URL</label>
            <input
              type="url"
              placeholder="https://discord.com/api/webhooks/..."
              value={newChannel.webhook_url}
              onChange={(e) => setNewChannel({ ...newChannel, webhook_url: e.target.value })}
            />
          </div>
        )}
        <div className={styles.formGroup}>
          <ToggleSwitch
            checked={newChannel.is_primary}
            onChange={(val) => setNewChannel({ ...newChannel, is_primary: val })}
            label="Set as Primary Channel"
          />
        </div>
      </Modal>
    </div>
  )
}
