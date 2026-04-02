# Email Digest Summarizer

A full-stack app that monitors your Gmail for emails from specific senders or matching keywords, summarizes them using Claude AI, and delivers the digest to WhatsApp, Telegram, or Discord on a schedule.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gmail API credentials (OAuth2)
- Anthropic API key
- At least one delivery channel configured (WhatsApp/Telegram/Discord)

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your API keys (see Setup Guides below)
```

### 2. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

### 4. Connect Gmail
1. Go to **Settings** in the app
2. Click **Connect Gmail**
3. Complete the OAuth2 flow

### 5. Create a digest
1. Go to **Dashboard** → **New Digest**
2. Add filter rules (sender emails and/or keywords)
3. Add a delivery channel (WhatsApp, Telegram, or Discord)
4. Set your preferred schedule time
5. Click **Run Now** to test

---

## Setup Guides

### Gmail API (required)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable Gmail API
3. Create OAuth2 credentials (Web application type)
4. Set redirect URI to `http://localhost:8000/api/gmail/callback`
5. Copy Client ID and Client Secret to `.env`

### WhatsApp (via Twilio)
1. Sign up at [Twilio](https://www.twilio.com/)
2. Enable WhatsApp Sandbox in the Twilio console
3. Follow sandbox instructions to join (send "join <keyword>" to the Twilio number)
4. Copy Account SID, Auth Token to `.env`
5. In the app, add a WhatsApp channel with your phone number (format: `whatsapp:+1234567890`)

### Telegram
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token to `.env`
4. Start a chat with your bot, then get your chat ID from `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. In the app, add a Telegram channel with your chat ID

### Discord
1. In your Discord server, go to channel Settings → Integrations → Webhooks
2. Create a new webhook and copy the URL to `.env`
3. In the app, add a Discord channel with the webhook URL

---

## Docker Deployment

```bash
cp .env.example .env
# Edit .env with your credentials
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Architecture

```
email-digest/
├── backend/           # Python FastAPI
│   ├── core/          # Config, database
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── routes/        # API endpoints
│   ├── services/      # Business logic
│   └── main.py        # App entry point
├── frontend/          # React + Vite
│   └── src/
│       ├── pages/     # Dashboard, DigestDetail, Channels, History, Settings
│       ├── components/# Modal, Toast, ToggleSwitch, StatusBadge, Sidebar
│       └── api.js     # API client
├── docker-compose.yml
├── .env.example
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/digests | List all digests |
| POST | /api/digests | Create new digest |
| GET | /api/digests/:id | Get digest details |
| PUT | /api/digests/:id | Update digest |
| DELETE | /api/digests/:id | Delete digest |
| POST | /api/digests/:id/run | Run digest manually |
| GET/POST | /api/digests/:id/filters | List/create filters |
| DELETE | /api/filters/:id | Delete filter |
| GET/POST | /api/digests/:id/channels | List/create channels |
| PUT/DELETE | /api/channels/:id | Update/delete channel |
| GET | /api/digests/:id/history | Get run history |
| GET | /api/gmail/auth-url | Get Gmail OAuth URL |
| GET | /api/gmail/status | Check Gmail connection |
| GET | /api/scheduler/status | Scheduler status |
| POST | /api/scheduler/start | Start scheduler |
| POST | /api/scheduler/stop | Stop scheduler |
