# Backend Project Structure

## Overview

Complete production-ready FastAPI backend for Email Digest Summarizer with full CRUD operations, OAuth2 authentication, job scheduling, and multi-channel delivery.

## Directory Tree

```
backend/
├── core/                          # Core application setup
│   ├── __init__.py
│   ├── config.py                  # Pydantic Settings for env variables
│   └── database.py                # SQLAlchemy async setup with SQLite
│
├── models/                        # SQLAlchemy ORM models
│   ├── __init__.py
│   └── models.py                  # 4 models: DigestConfig, FilterRule, ChannelConfig, DigestHistory
│
├── schemas/                       # Pydantic request/response models
│   ├── __init__.py
│   └── schemas.py                 # 15+ schemas for CRUD operations
│
├── services/                      # Business logic services
│   ├── __init__.py
│   ├── gmail_service.py           # Gmail API OAuth2 & email fetching
│   ├── llm_service.py             # Claude API summarization
│   ├── channel_service.py         # WhatsApp, Telegram, Discord, Email delivery
│   ├── digest_service.py          # Digest orchestration (fetch → summarize → send)
│   └── scheduler_service.py       # APScheduler with cron triggers
│
├── routes/                        # FastAPI route handlers
│   ├── __init__.py
│   ├── digests.py                 # Digest CRUD (GET, POST, PUT, DELETE)
│   ├── filters.py                 # Filter CRUD
│   ├── channels.py                # Channel CRUD
│   ├── gmail.py                   # Gmail OAuth2 auth URLs & callbacks
│   └── scheduler.py               # Scheduler control & manual runs
│
├── main.py                        # FastAPI app with CORS, lifespan, routers
├── requirements.txt               # All dependencies
├── Dockerfile                     # Multi-stage Python 3.11 image
├── docker-compose.yml             # Local development with env vars
├── start.sh                       # Development startup script
│
├── .env.example                   # Environment template
├── .gitignore                     # Git exclusions
├── README.md                      # Setup & deployment guide
├── API_EXAMPLES.md                # Complete API usage examples
└── STRUCTURE.md                   # This file
```

## Technology Stack

### Web Framework
- **FastAPI 0.104.1** - Modern async Python web framework
- **Uvicorn 0.24.0** - ASGI server

### Database & ORM
- **SQLAlchemy 2.0.23** - Async ORM
- **aiosqlite 0.19.0** - Async SQLite driver

### Job Scheduling
- **APScheduler 3.10.4** - Cron-based job scheduling

### Email & Auth
- **google-api-python-client 1.12.5** - Gmail API
- **google-auth 2.25.2** - Google OAuth2
- **google-auth-oauthlib 1.2.0** - OAuth2 flow

### LLM Integration
- **anthropic 0.21.3** - Claude API

### Messaging Channels
- **twilio 8.10.0** - WhatsApp via Twilio
- **python-telegram-bot 20.3** - Telegram messaging
- **requests 2.31.0** - HTTP for Discord webhooks

### Configuration & Validation
- **pydantic 2.5.0** - Data validation
- **pydantic-settings 2.1.0** - Settings management
- **python-dotenv 1.0.0** - .env file support

### Async Support
- **aiohttp 3.9.1** - Async HTTP client

## File Details

### core/config.py
Loads configuration from environment variables using Pydantic Settings:
- App settings (name, version, debug, log_level)
- Database URL
- Gmail OAuth2 credentials
- Claude API key
- Twilio/Telegram/Discord credentials
- CORS origins
- Scheduler config

### core/database.py
Async SQLAlchemy setup:
- `engine` - Async engine with NullPool (SQLite compatible)
- `async_session_maker` - Session factory
- `get_db()` - Dependency for injecting sessions
- `init_db()` - Create tables on startup
- `close_db()` - Close connections on shutdown

### models/models.py
SQLAlchemy declarative models:
- `DigestConfig` - Digest scheduling & auth
- `FilterRule` - Email filters (sender/keyword)
- `ChannelConfig` - Delivery channels with credentials
- `DigestHistory` - Execution history & results
- Enums: FilterType, ChannelType, DigestStatus

### schemas/schemas.py
Pydantic models for:
- Filter CRUD (Create, Update, Response)
- Channel CRUD (Create, Update, Response)
- Digest CRUD (Create, Update, DetailResponse)
- Digest History
- Gmail auth (URL, callback, status)
- Scheduler (status, manual run, requests)

### services/gmail_service.py
Gmail API wrapper:
- OAuth2 URL generation
- Token exchange & refresh
- Email fetching with Gmail API
- Email parsing (headers, body)
- Mark emails as read
- User profile retrieval
- Query building from filters

### services/llm_service.py
Claude API integration:
- Email summarization
- Digest title generation
- Action item extraction
- Sentiment analysis
- Prompt engineering

### services/channel_service.py
Multi-channel message delivery:
- WhatsApp via Twilio
- Telegram Bot API
- Discord Webhooks
- Email via SMTP
- Message splitting (4000 char limit)
- Config validation
- Display names

### services/digest_service.py
Digest orchestration:
- Complete workflow (fetch → summarize → send)
- Email fetching with filters
- LLM summarization
- Multi-channel delivery
- History recording
- Error handling

### services/scheduler_service.py
APScheduler wrapper:
- Async scheduler initialization
- Cron trigger setup
- Job sync from database
- Manual trigger
- Schedule updates
- Job listing
- Status reporting

### routes/digests.py
Digest CRUD endpoints:
- `GET /digests` - List all
- `POST /digests` - Create new
- `GET /digests/{id}` - Get details
- `PUT /digests/{id}` - Update
- `DELETE /digests/{id}` - Delete

### routes/filters.py
Filter management:
- `GET /digests/{id}/filters` - List
- `POST /digests/{id}/filters` - Create
- `PUT /digests/{id}/filters/{id}` - Update
- `DELETE /digests/{id}/filters/{id}` - Delete

### routes/channels.py
Channel management:
- `GET /digests/{id}/channels` - List
- `POST /digests/{id}/channels` - Create with validation
- `PUT /digests/{id}/channels/{id}` - Update
- `DELETE /digests/{id}/channels/{id}` - Delete

### routes/gmail.py
Gmail OAuth2:
- `GET /auth/gmail/{id}/url` - Auth URL with CSRF
- `POST /auth/gmail/callback` - Token exchange
- `GET /auth/gmail/{id}/status` - Auth status
- `POST /auth/gmail/{id}/revoke` - Revoke auth

### routes/scheduler.py
Scheduler control:
- `GET /scheduler/status` - Overall status
- `POST /scheduler/digest/run` - Manual trigger
- `GET /scheduler/jobs` - List all jobs
- `POST /scheduler/digest/{id}/schedule` - Schedule at time
- `POST /scheduler/digest/{id}/unschedule` - Remove from schedule

### main.py
FastAPI application:
- CORS middleware
- Lifespan context (startup/shutdown)
- Database initialization
- Scheduler initialization
- Router registration
- Health check endpoints
- Interactive API docs

### Dockerfile
Production Docker image:
- Python 3.11-slim base
- Non-root user (appuser)
- Health check
- Exposed port 8000
- Uvicorn startup

### docker-compose.yml
Local development setup:
- Service definition
- Environment variables
- Volume mounts
- Port mapping
- Health checks
- Networks

### start.sh
Development startup:
- Creates virtual environment
- Installs dependencies
- Validates .env
- Starts uvicorn with reload

## Database Schema

### DigestConfig
```sql
CREATE TABLE digest_configs (
  id INTEGER PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  schedule_time VARCHAR(5) NOT NULL,  -- HH:MM
  user_id VARCHAR(255) NOT NULL,
  gmail_access_token TEXT,
  gmail_refresh_token TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### FilterRule
```sql
CREATE TABLE filter_rules (
  id INTEGER PRIMARY KEY,
  digest_id INTEGER NOT NULL FOREIGN KEY,
  filter_type ENUM('sender', 'keyword'),
  value VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### ChannelConfig
```sql
CREATE TABLE channel_configs (
  id INTEGER PRIMARY KEY,
  digest_id INTEGER NOT NULL FOREIGN KEY,
  channel_type ENUM('whatsapp', 'telegram', 'discord', 'email'),
  config JSON,
  is_primary BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### DigestHistory
```sql
CREATE TABLE digest_history (
  id INTEGER PRIMARY KEY,
  digest_id INTEGER NOT NULL FOREIGN KEY,
  status ENUM('success', 'failed', 'pending'),
  email_count INTEGER DEFAULT 0,
  summary TEXT,
  error_message TEXT,
  sent_at DATETIME,
  channel_used ENUM('whatsapp', 'telegram', 'discord', 'email'),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling

All endpoints include:
- Try-catch blocks
- Logging at ERROR level
- HTTPException with status codes
- Descriptive error messages
- Transaction rollback on failures

Status codes:
- 200/201 - Success
- 204 - No content (delete)
- 400 - Bad request (validation)
- 404 - Not found
- 500 - Server error
- 503 - Service unavailable (scheduler not ready)

## Logging

Configured via environment:
- LOG_LEVEL: DEBUG, INFO, WARNING, ERROR
- Format: `timestamp - module - level - message`
- All services log operations and errors

## Security

- OAuth2 for Gmail (no password)
- State tokens for CSRF protection
- Environment variables for credentials
- No hardcoded secrets
- Non-root Docker user
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy)
- CORS configurable
- Type hints throughout

## Performance

- Async/await for I/O operations
- Connection pooling (database)
- Message batching via splitting
- Lazy loading of relationships
- Efficient query building
- APScheduler with grace period

## Testing

Structure supports:
- Unit tests (services)
- Integration tests (routes + database)
- E2E tests (complete workflows)

Example with pytest:
```bash
pip install pytest pytest-asyncio httpx
pytest tests/
```

## Deployment

### Development
```bash
./start.sh
```

### Docker
```bash
docker-compose up
```

### Production
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

Or with container orchestration (Kubernetes, ECS, etc.)

## Configuration Management

Environment variables in `.env`:
- Database connection
- Third-party API keys
- Service credentials
- Server settings
- Feature flags

Example in docker-compose.yml shows all options.

## Monitoring & Observability

Ready for:
- Structured logging (via Pydantic models)
- Metrics collection (APScheduler events)
- Error tracking (Sentry integration)
- Distributed tracing (OpenTelemetry)
- Health checks (FastAPI endpoints)

## Documentation

- README.md - Setup & deployment
- API_EXAMPLES.md - Complete usage examples
- STRUCTURE.md - This file
- Inline docstrings - All functions
- Type hints - All parameters
- Interactive docs - /docs endpoint

## Dependencies Management

Keep up to date:
```bash
pip list --outdated
pip install --upgrade pip setuptools
```

Production requirements.txt pinned to versions for reproducibility.

## Future Enhancements

Potential additions:
- Database transactions
- Caching layer (Redis)
- Rate limiting
- API authentication (JWT/API keys)
- Webhook for digest results
- Digest templates
- Multiple Gmail accounts per digest
- Batch operations
- WebSocket support
- Message queuing (Celery)
- Full-text search
- Advanced analytics
