import { useState, useEffect } from 'react'
import { gmail, scheduler } from '../api'
import ToggleSwitch from '../components/ToggleSwitch'
import StatusBadge from '../components/StatusBadge'
import styles from './Settings.module.css'

export default function Settings({ showToast }) {
  const [gmailStatus, setGmailStatus] = useState(null)
  const [schedulerStatus, setSchedulerStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [authUrl, setAuthUrl] = useState(null)

  useEffect(() => {
    loadSettings()
  }, [])

  async function loadSettings() {
    try {
      setLoading(true)
      const [gStatus, sStatus] = await Promise.all([
        gmail.status(),
        scheduler.status(),
      ])
      setGmailStatus(gStatus)
      setSchedulerStatus(sStatus)
    } catch (error) {
      showToast(`Error loading settings: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function handleGmailAuth() {
    try {
      const data = await gmail.getAuthUrl()
      setAuthUrl(data.auth_url)
      window.location.href = data.auth_url
    } catch (error) {
      showToast(`Error getting auth URL: ${error.message}`, 'error')
    }
  }

  async function handleGmailDisconnect() {
    showToast('Gmail account disconnection not yet implemented', 'info')
  }

  async function handleSchedulerStart() {
    try {
      await scheduler.start()
      showToast('Scheduler started successfully', 'success')
      loadSettings()
    } catch (error) {
      showToast(`Error starting scheduler: ${error.message}`, 'error')
    }
  }

  async function handleSchedulerStop() {
    try {
      await scheduler.stop()
      showToast('Scheduler stopped successfully', 'success')
      loadSettings()
    } catch (error) {
      showToast(`Error stopping scheduler: ${error.message}`, 'error')
    }
  }

  return (
    <div className={styles.settings}>
      <div className={styles.header}>
        <h1>Settings</h1>
        <p>Configure email source and scheduling</p>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="loading"></div>
          <p>Loading settings...</p>
        </div>
      ) : (
        <>
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Gmail Configuration</h2>
            <div className="card">
              <div className={styles.settingBlock}>
                <div className={styles.settingInfo}>
                  <h3>Gmail Connection</h3>
                  <p className="text-secondary">
                    Connect your Gmail account to enable email digest functionality
                  </p>
                </div>
                <div className={styles.settingAction}>
                  {gmailStatus?.is_authenticated ? (
                    <>
                      <StatusBadge status="active" type="status" />
                      <div className={styles.accountInfo}>
                        <p className="text-sm">Connected as:</p>
                        <p className="text-primary">{gmailStatus.user_email || 'Gmail Account'}</p>
                      </div>
                      <button
                        className="btn btn-danger"
                        onClick={handleGmailDisconnect}
                      >
                        Disconnect
                      </button>
                    </>
                  ) : (
                    <>
                      <StatusBadge status="inactive" type="status" />
                      <p className="text-secondary text-sm">
                        Not connected
                      </p>
                      <button
                        className="btn btn-primary"
                        onClick={handleGmailAuth}
                      >
                        Connect Gmail
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Scheduler Control</h2>
            <div className="card">
              <div className={styles.settingBlock}>
                <div className={styles.settingInfo}>
                  <h3>Background Scheduler</h3>
                  <p className="text-secondary">
                    Control the automatic execution of scheduled digests
                  </p>
                </div>
                <div className={styles.settingAction}>
                  {schedulerStatus?.running ? (
                    <>
                      <StatusBadge status="active" type="status" />
                      <div className={styles.statusInfo}>
                        <p className="text-sm">Status: Running</p>
                        {schedulerStatus.last_run && (
                          <p className="text-xs text-muted">
                            Last run: {new Date(schedulerStatus.last_run).toLocaleString()}
                          </p>
                        )}
                      </div>
                      <button
                        className="btn btn-danger"
                        onClick={handleSchedulerStop}
                      >
                        Stop Scheduler
                      </button>
                    </>
                  ) : (
                    <>
                      <StatusBadge status="inactive" type="status" />
                      <p className="text-secondary text-sm">
                        Currently stopped
                      </p>
                      <button
                        className="btn btn-success"
                        onClick={handleSchedulerStart}
                      >
                        Start Scheduler
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>System Information</h2>
            <div className="card">
              <div className={styles.infoGrid}>
                <div className={styles.infoItem}>
                  <span className="text-muted">Backend URL</span>
                  <span className={styles.infoValue}>http://localhost:8000</span>
                </div>
                <div className={styles.infoItem}>
                  <span className="text-muted">Frontend Version</span>
                  <span className={styles.infoValue}>1.0.0</span>
                </div>
                <div className={styles.infoItem}>
                  <span className="text-muted">Environment</span>
                  <span className={styles.infoValue}>{import.meta.env.MODE}</span>
                </div>
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Environment Setup</h2>
            <div className="card">
              <p className="text-secondary mb-lg">
                To set up this application, ensure the following environment variables are configured:
              </p>
              <div className={styles.envList}>
                <div className={styles.envItem}>
                  <code>GMAIL_CLIENT_ID</code>
                  <span>Your Google OAuth client ID</span>
                </div>
                <div className={styles.envItem}>
                  <code>GMAIL_CLIENT_SECRET</code>
                  <span>Your Google OAuth client secret</span>
                </div>
                <div className={styles.envItem}>
                  <code>WHATSAPP_API_KEY</code>
                  <span>WhatsApp Business API key (optional)</span>
                </div>
                <div className={styles.envItem}>
                  <code>TELEGRAM_BOT_TOKEN</code>
                  <span>Telegram bot token (optional)</span>
                </div>
                <div className={styles.envItem}>
                  <code>DISCORD_WEBHOOK_SECRET</code>
                  <span>Discord webhook secret (optional)</span>
                </div>
              </div>
              <p className="text-xs text-muted mt-lg">
                Contact your system administrator for help with environment setup.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
