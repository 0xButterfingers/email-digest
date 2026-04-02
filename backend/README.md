# Email Digest Summarizer - Backend API

A production-ready FastAPI backend for an email digest summarizer application with scheduled digest creation, multi-channel delivery, and Claude-powered email summarization.

## Features

- Gmail OAuth2 integration for secure email access
- Configurable email filters (by sender or keyword)
- Claude AI-powered email summarization
- Multi-channel message delivery (WhatsApp, Telegram, Discord, Email)
- APScheduler for automated digest scheduling
- SQLite database with async SQLAlchemy
- Comprehensive REST API
- Docker support

## Architecture

### Core Components

- **FastAPI**: Web framework with async support
- **SQLAlchemy**: ORM with async SQLite
- **APScheduler**: Job scheduling with cron triggers
- **Gmail API**: Email retrieval via OAuth2
- **Anthropic SDK**: Claude API for summarization
- **Twilio**: WhatsApp messaging
- **Telegram Bot API**: Telegram messaging
- **Discord Webhooks**: Discord messaging

### Database Models

- **DigestConfig**: Digest settings and schedules
- **FilterRule**: Email filters (sender/keyword)
- **ChannelConfig**: Delivery channel settings
- **DigestHistory**: Execution history and results

## Setup

### Prerequisites

- Python 3.11+
- Gmail API credentials (OAuth2 app)
- Anthropic API key
- (Optional) Twilio, Telegram, Discord credentials

### Installation

1. Clone and enter the directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Configuration

Key environment variables in `.env`:

```env
# Gmail OAuth2 (from Google Cloud Console)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/auth/gmail/callback

# Claude API
ANTHROPIC_API_KEY=sk-ant-v3-...

# Optional: Channel credentials
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TELEGRAM_BOT_TOKEN=
DISCORD_WEBHOOK_URL=

# Database (default: SQLite local)
DATABASE_URL=sqlite+aiosqlite:///./email_digest.db
```

## Running the Application

### Development

```bash
uvicorn main:app --reload
```

API available at: http://localhost:8000
Docs: http://localhost:8000/docs

### Docker

```bash
docker-compose up
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Digests
- `GET /digests` - List all digests
- `POST /digests` - Create new digest
- `GET /digests/{id}` - Get digest details
- `PUT /digests/{id}` - Update digest
- `DELETE /digests/{id}` - Delete digest

### Filters
- `GET /digests/{digest_id}/filters` - List filters
- `POST /digests/{digest_id}/filters` - Add filter
- `PUT /digests/{digest_id}/filters/{filter_id}` - Update filter
- `DELETE /digests/{digest_id}/filters/{filter_id}` - Delete filter

### Channels
- `GET /digests/{digest_id}/channels` - List channels
- `POST /digests/{digest_id}/channels` - Add channel
- `PUT /digests/{digest_id}/channels/{channel_id}` - Update channel
- `DELETE /digests/{digest_id}/channels/{channel_id}` - Delete channel

### Gmail Authentication
- `GET /auth/gmail/{digest_id}/url` - Get OAuth2 auth URL
- `POST /auth/gmail/callback` - Handle OAuth2 callback
- `GET /auth/gmail/{digest_id}/status` - Check auth status
- `POST /auth/gmail/{digest_id}/revoke` - Revoke authentication

### Scheduler
- `GET /scheduler/status` - Get scheduler status
- `POST /scheduler/digest/run` - Manually run digest
- `GET /scheduler/jobs` - List scheduled jobs
- `POST /scheduler/digest/{digest_id}/schedule` - Schedule digest
- `POST /scheduler/digest/{digest_id}/unschedule` - Remove from schedule

### Health
- `GET /health` - Health check
- `GET /` - API info

## Example Usage

### Create a Digest

```bash
curl -X POST http://localhost:8000/digests \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Work Digest",
    "schedule_time": "09:00",
    "is_active": true,
    "filter_rules": [
      {"filter_type": "sender", "value": "boss@company.com"},
      {"filter_type": "keyword", "value": "urgent"}
    ],
    "channel_configs": [
      {
        "channel_type": "telegram",
        "config": {"chat_id": "123456789"},
        "is_primary": true
      }
    ]
  }'
```

### Setup Gmail OAuth2

1. Get auth URL:
```bash
curl http://localhost:8000/auth/gmail/1/url
```

2. User visits returned URL and authorizes

3. Handle callback:
```bash
curl -X POST http://localhost:8000/auth/gmail/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "auth-code-from-google",
    "digest_id": 1
  }'
```

### Run Digest Manually

```bash
curl -X POST http://localhost:8000/scheduler/digest/run \
  -H "Content-Type: application/json" \
  -d '{"digest_id": 1}'
```

## Project Structure

```
backend/
├── core/
│   ├── config.py          # Settings and environment config
│   ├── database.py        # SQLAlchemy async setup
│   └── __init__.py
├── models/
│   ├── models.py          # SQLAlchemy models
│   └── __init__.py
├── schemas/
│   ├── schemas.py         # Pydantic request/response models
│   └── __init__.py
├── services/
│   ├── gmail_service.py   # Gmail API wrapper
│   ├── llm_service.py     # Claude summarization
│   ├── channel_service.py # Multi-channel delivery
│   ├── digest_service.py  # Digest orchestration
│   ├── scheduler_service.py # Job scheduling
│   └── __init__.py
├── routes/
│   ├── digests.py         # Digest CRUD endpoints
│   ├── filters.py         # Filter management endpoints
│   ├── channels.py        # Channel management endpoints
│   ├── gmail.py           # Gmail auth endpoints
│   ├── scheduler.py       # Scheduler endpoints
│   └── __init__.py
├── main.py                # FastAPI app
├── requirements.txt       # Dependencies
├── Dockerfile             # Container image
├── docker-compose.yml     # Local development
└── README.md              # This file
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 201: Created
- 204: No content
- 400: Bad request
- 404: Not found
- 500: Server error
- 503: Service unavailable

All error responses include a `detail` field with the error message.

## Logging

Logging is configured via `LOG_LEVEL` environment variable:
- DEBUG: Verbose output
- INFO: General information
- WARNING: Warnings
- ERROR: Errors only

Logs include timestamps and source module information.

## Database

### Async SQLite Setup

Uses `aiosqlite` for async SQLite support:
- Automatic table creation on startup
- Async session management via dependency injection
- Connection pooling disabled for SQLite compatibility

### Database File

Default location: `./email_digest.db`

To reset database:
```bash
rm email_digest.db
```

## Testing

Run with pytest (when test files are added):
```bash
pip install pytest pytest-asyncio
pytest
```

## Performance Considerations

- SQLite suitable for small to medium deployments
- For production: Consider PostgreSQL with async support
- APScheduler stores jobs in memory (no persistence)
- Message splitting for long messages (4000 char limit)
- Token refresh automatic on Gmail API calls

## Security

- OAuth2 for Gmail authentication
- State tokens for CSRF protection
- Non-root Docker user
- Environment variable configuration
- CORS configurable
- No hardcoded credentials

## Deployment

### Docker Image

Build:
```bash
docker build -t email-digest-backend:1.0.0 .
```

Run:
```bash
docker run -p 8000:8000 \
  -e GMAIL_CLIENT_ID=... \
  -e ANTHROPIC_API_KEY=... \
  email-digest-backend:1.0.0
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Use strong `GMAIL_CLIENT_SECRET`
- [ ] Configure `CORS_ORIGINS` appropriately
- [ ] Use PostgreSQL for production database
- [ ] Set up proper logging/monitoring
- [ ] Use reverse proxy (nginx/caddy)
- [ ] Configure SSL/TLS
- [ ] Set up backups for database
- [ ] Monitor APScheduler jobs

## Troubleshooting

### Gmail authentication fails
- Verify `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET`
- Check `GMAIL_REDIRECT_URI` matches Google Console settings
- Ensure Gmail API is enabled in Google Cloud

### Emails not being fetched
- Verify Gmail OAuth2 tokens are valid
- Check filter rules are correct
- Review logs for API errors

### Digest not sending
- Verify channel configuration is correct
- Check channel credentials
- Review logs for channel errors

### Scheduler not running
- Check scheduler service initialized (startup logs)
- Verify digest is active (`is_active = True`)
- Check APScheduler logs

## Support

For issues and questions, refer to:
- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Gmail API: https://developers.google.com/gmail/api
- Claude API: https://claude.ai/api
- APScheduler: https://apscheduler.readthedocs.io

## License

Proprietary - All rights reserved
