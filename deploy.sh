#!/bin/bash
# =============================================================================
# Email Digest Summarizer — Droplet Deploy Script
# Run as root on a fresh Ubuntu 22.04 / 24.04 Droplet
# =============================================================================
set -e

echo "==> [1/5] Installing Docker & Docker Compose..."
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "==> [2/5] Cloning repository..."
cd /opt
git clone https://github.com/YOUR_GITHUB_USERNAME/email-digest.git app
cd app

echo "==> [3/5] Writing .env..."
# --- EDIT BELOW with your real values ---
DROPLET_IP=$(curl -s ifconfig.me)

cat > .env <<EOF
APP_NAME=Email Digest Summarizer
APP_VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO

DATABASE_URL=sqlite+aiosqlite:///./data/email_digest.db

GMAIL_CLIENT_ID=YOUR_GMAIL_CLIENT_ID.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=YOUR_GMAIL_CLIENT_SECRET
GMAIL_REDIRECT_URI=http://${DROPLET_IP}/api/auth/gmail/callback

ANTHROPIC_API_KEY=REPLACE_WITH_YOUR_ANTHROPIC_KEY

TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890

DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/...

CORS_ORIGINS=["http://${DROPLET_IP}","http://localhost:8000"]

SCHEDULER_TIMEZONE=Asia/Singapore
SCHEDULER_POOL_SIZE=10
EOF

echo "    .env written (Droplet IP: ${DROPLET_IP})"

echo "==> [4/5] Building and starting containers..."
docker compose up --build -d

echo "==> [5/5] Checking health..."
sleep 10
docker compose ps
curl -sf http://localhost/api/health && echo "  Backend healthy!" || echo "  WARNING: health check failed — check logs with: docker compose logs backend"

echo ""
echo "========================================"
echo " Deployment complete!"
echo " App:  http://${DROPLET_IP}"
echo " Logs: docker compose logs -f"
echo "========================================"
echo ""
echo "NEXT STEP: Re-authorize Gmail OAuth with the new redirect URI:"
echo "  http://${DROPLET_IP}/api/auth/gmail/callback"
echo "  (Add this URI to your Google Cloud Console → OAuth credentials)"
