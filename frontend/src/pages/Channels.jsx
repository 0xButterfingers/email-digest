import { useState, useEffect } from 'react'
import { digests, channels } from '../api'
import styles from './Channels.module.css'

export default function ChannelsPage({ showToast }) {
  const [channelsList, setChannelsList] = useState([])
  const [digestsList, setDigestsList] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadChannels()
  }, [])

  async function loadChannels() {
    try {
      setLoading(true)
      const digests_data = await digests.list()
      setDigestsList(digests_data)

      const allChannels = []
      for (const digest of digests_data) {
        const channelsData = await channels.list(digest.id)
        allChannels.push(
          ...channelsData.map((ch) => ({
            ...ch,
            digestName: digest.name,
            digestId: digest.id,
          }))
        )
      }
      setChannelsList(allChannels)
    } catch (error) {
      showToast(`Error loading channels: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const guides = {
    WhatsApp: {
      icon: '💬',
      title: 'WhatsApp Business',
      steps: [
        'Create a WhatsApp Business account',
        'Get your phone number from WhatsApp Manager',
        'Verify the phone number with OTP',
        'Configure the phone number in the channel settings',
      ],
    },
    Telegram: {
      icon: '✈️',
      title: 'Telegram Bot',
      steps: [
        'Create a new bot with BotFather on Telegram',
        'Get your Chat ID by messaging your bot',
        'Copy the Chat ID to the channel settings',
        'Send a test message to verify the connection',
      ],
    },
    Discord: {
      icon: '🎮',
      title: 'Discord Webhook',
      steps: [
        'Go to your Discord server settings',
        'Select Integrations > Webhooks',
        'Create a new webhook and copy the URL',
        'Paste the webhook URL in the channel settings',
      ],
    },
  }

  return (
    <div className={styles.channels}>
      <div className={styles.header}>
        <h1>Channels</h1>
        <p>Manage all email digest delivery channels</p>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="loading"></div>
          <p>Loading channels...</p>
        </div>
      ) : (
        <>
          {channelsList.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>Configured Channels</h2>
              <div className={styles.channelGrid}>
                {channelsList.map((channel) => (
                  <div key={channel.id} className="card">
                    <div className={styles.channelCard}>
                      <div>
                        <h3>{guides[channel.type]?.icon} {channel.type}</h3>
                        <p className="text-secondary text-sm">{channel.digestName}</p>
                        <p className="text-xs text-muted">
                          {channel.config?.phone_number ||
                            channel.config?.chat_id ||
                            channel.config?.webhook_url ||
                            'Configured'}
                        </p>
                        {channel.is_primary && (
                          <span className="badge badge-success mt-md">Primary</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Setup Guides</h2>
            <div className={styles.guidesGrid}>
              {Object.entries(guides).map(([key, guide]) => (
                <div key={key} className="card">
                  <div className={styles.guideCard}>
                    <div className={styles.guideIcon}>{guide.icon}</div>
                    <h3>{guide.title}</h3>
                    <ol className={styles.guideSteps}>
                      {guide.steps.map((step, idx) => (
                        <li key={idx}>{step}</li>
                      ))}
                    </ol>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {channelsList.length === 0 && (
            <div className="empty-state">
              <div className="empty-state-icon">📱</div>
              <h3>No channels configured</h3>
              <p>Add your first channel in the Dashboard by creating a digest</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
