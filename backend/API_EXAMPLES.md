# Email Digest API - Complete Examples

This document provides comprehensive examples for all API endpoints.

## Base URL
```
http://localhost:8000
```

## Table of Contents
1. [Digest Management](#digest-management)
2. [Filter Management](#filter-management)
3. [Channel Management](#channel-management)
4. [Gmail Authentication](#gmail-authentication)
5. [Scheduler Control](#scheduler-control)
6. [Health & Status](#health--status)

---

## Digest Management

### List All Digests

**Request:**
```bash
curl http://localhost:8000/digests
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Daily Work Digest",
    "is_active": true,
    "schedule_time": "09:00",
    "user_id": "user@example.com",
    "created_at": "2024-03-01T10:00:00",
    "updated_at": "2024-03-01T10:00:00"
  }
]
```

### Create a Digest

**Request:**
```bash
curl -X POST http://localhost:8000/digests \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Work Digest",
    "schedule_time": "09:00",
    "is_active": true,
    "filter_rules": [
      {
        "filter_type": "sender",
        "value": "boss@company.com"
      },
      {
        "filter_type": "keyword",
        "value": "urgent"
      }
    ],
    "channel_configs": [
      {
        "channel_type": "telegram",
        "config": {
          "chat_id": "123456789"
        },
        "is_primary": true
      }
    ]
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "Daily Work Digest",
  "is_active": true,
  "schedule_time": "09:00",
  "user_id": "default",
  "created_at": "2024-03-01T10:00:00",
  "updated_at": "2024-03-01T10:00:00"
}
```

### Get Digest Details

**Request:**
```bash
curl http://localhost:8000/digests/1
```

**Response:**
```json
{
  "id": 1,
  "name": "Daily Work Digest",
  "is_active": true,
  "schedule_time": "09:00",
  "user_id": "user@example.com",
  "created_at": "2024-03-01T10:00:00",
  "updated_at": "2024-03-01T10:00:00",
  "filter_rules": [
    {
      "id": 1,
      "digest_id": 1,
      "filter_type": "sender",
      "value": "boss@company.com",
      "created_at": "2024-03-01T10:00:00"
    }
  ],
  "channel_configs": [
    {
      "id": 1,
      "digest_id": 1,
      "channel_type": "telegram",
      "config": {
        "chat_id": "123456789"
      },
      "is_primary": true,
      "created_at": "2024-03-01T10:00:00"
    }
  ]
}
```

### Update Digest

**Request:**
```bash
curl -X PUT http://localhost:8000/digests/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Work Digest",
    "schedule_time": "10:00",
    "is_active": true
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "Updated Work Digest",
  "is_active": true,
  "schedule_time": "10:00",
  "user_id": "user@example.com",
  "created_at": "2024-03-01T10:00:00",
  "updated_at": "2024-03-01T10:30:00"
}
```

### Delete Digest

**Request:**
```bash
curl -X DELETE http://localhost:8000/digests/1
```

**Response:**
```
204 No Content
```

---

## Filter Management

### List Filters for Digest

**Request:**
```bash
curl http://localhost:8000/digests/1/filters
```

**Response:**
```json
[
  {
    "id": 1,
    "digest_id": 1,
    "filter_type": "sender",
    "value": "boss@company.com",
    "created_at": "2024-03-01T10:00:00"
  },
  {
    "id": 2,
    "digest_id": 1,
    "filter_type": "keyword",
    "value": "urgent",
    "created_at": "2024-03-01T10:00:00"
  }
]
```

### Add Filter

**Request:**
```bash
curl -X POST http://localhost:8000/digests/1/filters \
  -H "Content-Type: application/json" \
  -d '{
    "filter_type": "keyword",
    "value": "meeting"
  }'
```

**Response:**
```json
{
  "id": 3,
  "digest_id": 1,
  "filter_type": "keyword",
  "value": "meeting",
  "created_at": "2024-03-01T10:15:00"
}
```

### Update Filter

**Request:**
```bash
curl -X PUT http://localhost:8000/digests/1/filters/3 \
  -H "Content-Type: application/json" \
  -d '{
    "value": "important meeting"
  }'
```

**Response:**
```json
{
  "id": 3,
  "digest_id": 1,
  "filter_type": "keyword",
  "value": "important meeting",
  "created_at": "2024-03-01T10:15:00"
}
```

### Delete Filter

**Request:**
```bash
curl -X DELETE http://localhost:8000/digests/1/filters/3
```

**Response:**
```
204 No Content
```

---

## Channel Management

### List Channels for Digest

**Request:**
```bash
curl http://localhost:8000/digests/1/channels
```

**Response:**
```json
[
  {
    "id": 1,
    "digest_id": 1,
    "channel_type": "telegram",
    "config": {
      "chat_id": "123456789"
    },
    "is_primary": true,
    "created_at": "2024-03-01T10:00:00"
  }
]
```

### Add Channel (WhatsApp)

**Request:**
```bash
curl -X POST http://localhost:8000/digests/1/channels \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "whatsapp",
    "config": {
      "phone_number": "+11234567890"
    },
    "is_primary": false
  }'
```

**Response:**
```json
{
  "id": 2,
  "digest_id": 1,
  "channel_type": "whatsapp",
  "config": {
    "phone_number": "+11234567890"
  },
  "is_primary": false,
  "created_at": "2024-03-01T10:15:00"
}
```

### Add Channel (Discord)

**Request:**
```bash
curl -X POST http://localhost:8000/digests/1/channels \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "discord",
    "config": {
      "webhook_url": "https://discordapp.com/api/webhooks/123/abc"
    },
    "is_primary": false
  }'
```

### Add Channel (Email)

**Request:**
```bash
curl -X POST http://localhost:8000/digests/1/channels \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "email",
    "config": {
      "email": "user@example.com"
    },
    "is_primary": false
  }'
```

### Update Channel

**Request:**
```bash
curl -X PUT http://localhost:8000/digests/1/channels/1 \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "chat_id": "987654321"
    },
    "is_primary": false
  }'
```

**Response:**
```json
{
  "id": 1,
  "digest_id": 1,
  "channel_type": "telegram",
  "config": {
    "chat_id": "987654321"
  },
  "is_primary": false,
  "created_at": "2024-03-01T10:00:00"
}
```

### Delete Channel

**Request:**
```bash
curl -X DELETE http://localhost:8000/digests/1/channels/1
```

**Response:**
```
204 No Content
```

---

## Gmail Authentication

### Get Gmail Auth URL

**Request:**
```bash
curl http://localhost:8000/auth/gmail/1/url
```

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "digest_id": 1
}
```

### Handle OAuth2 Callback

After user authorizes on Gmail, exchange the code:

**Request:**
```bash
curl -X POST http://localhost:8000/auth/gmail/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "4/0AX4XfWh...",
    "digest_id": 1
  }'
```

**Response:**
```json
{
  "digest_id": 1,
  "is_authenticated": true,
  "user_email": "user@gmail.com"
}
```

### Check Gmail Auth Status

**Request:**
```bash
curl http://localhost:8000/auth/gmail/1/status
```

**Response:**
```json
{
  "digest_id": 1,
  "is_authenticated": true,
  "user_email": "user@gmail.com"
}
```

### Revoke Gmail Authorization

**Request:**
```bash
curl -X POST http://localhost:8000/auth/gmail/1/revoke
```

**Response:**
```json
{
  "status": "success",
  "message": "Gmail authorization revoked",
  "digest_id": 1
}
```

---

## Scheduler Control

### Get Scheduler Status

**Request:**
```bash
curl http://localhost:8000/scheduler/status
```

**Response:**
```json
{
  "is_running": true,
  "jobs_count": 2,
  "active_digests": 2
}
```

### List All Scheduled Jobs

**Request:**
```bash
curl http://localhost:8000/scheduler/jobs
```

**Response:**
```json
{
  "jobs": {
    "digest_1": {
      "id": "digest_1",
      "name": "Daily Work Digest",
      "trigger": "cron[hour='9', minute='0', ...]",
      "next_run_time": "2024-03-02T09:00:00+00:00"
    }
  },
  "count": 1
}
```

### Run Digest Now

**Request:**
```bash
curl -X POST http://localhost:8000/scheduler/digest/run \
  -H "Content-Type: application/json" \
  -d '{
    "digest_id": 1
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Digest 1 triggered successfully",
  "history_id": 42
}
```

### Schedule Digest at Specific Time

**Request:**
```bash
curl -X POST "http://localhost:8000/scheduler/digest/1/schedule?schedule_time=09%3A30"
```

**Response:**
```json
{
  "success": true,
  "message": "Digest 1 scheduled at 09:30",
  "digest_id": 1,
  "schedule_time": "09:30"
}
```

### Remove Digest from Scheduler

**Request:**
```bash
curl -X POST http://localhost:8000/scheduler/digest/1/unschedule
```

**Response:**
```json
{
  "success": true,
  "message": "Digest 1 removed from scheduler",
  "digest_id": 1
}
```

---

## Health & Status

### Health Check

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "app_name": "Email Digest Summarizer",
  "version": "1.0.0"
}
```

### API Info

**Request:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "Email Digest Summarizer API",
  "version": "1.0.0",
  "docs": "/docs",
  "openapi": "/openapi.json"
}
```

---

## Error Examples

### 404 Not Found

**Request:**
```bash
curl http://localhost:8000/digests/999
```

**Response:**
```json
{
  "detail": "Digest not found"
}
```

### 400 Bad Request

**Request:**
```bash
curl -X POST http://localhost:8000/digests \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test",
    "schedule_time": "invalid"
  }'
```

**Response:**
```json
{
  "detail": "Invalid schedule time format. Use HH:MM"
}
```

### 500 Internal Server Error

**Response:**
```json
{
  "detail": "Failed to create digest"
}
```

---

## Pagination

List endpoints support pagination:

**Request:**
```bash
curl "http://localhost:8000/digests?skip=0&limit=10"
```

Parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100)

---

## Advanced Examples

### Complete Workflow

1. Create digest:
```bash
DIGEST_ID=$(curl -s -X POST http://localhost:8000/digests \
  -H "Content-Type: application/json" \
  -d '{"name":"My Digest","schedule_time":"09:00"}' | jq '.id')
echo "Created digest: $DIGEST_ID"
```

2. Add filters:
```bash
curl -X POST http://localhost:8000/digests/$DIGEST_ID/filters \
  -H "Content-Type: application/json" \
  -d '{"filter_type":"keyword","value":"important"}'
```

3. Add channel:
```bash
curl -X POST http://localhost:8000/digests/$DIGEST_ID/channels \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type":"telegram",
    "config":{"chat_id":"123456789"},
    "is_primary":true
  }'
```

4. Setup Gmail:
```bash
AUTH_URL=$(curl -s http://localhost:8000/auth/gmail/$DIGEST_ID/url | jq -r '.auth_url')
echo "Visit: $AUTH_URL"
```

5. Run digest:
```bash
curl -X POST http://localhost:8000/scheduler/digest/run \
  -H "Content-Type: application/json" \
  -d "{\"digest_id\":$DIGEST_ID}"
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production, consider:
- FastAPI slowapi extension
- API Gateway rate limiting
- Nginx rate limiting

---

## Authentication

Currently using digest ID in URLs. For production, consider:
- JWT tokens
- API keys
- OAuth2 user authentication

---

## Interactive Documentation

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
OpenAPI Schema: http://localhost:8000/openapi.json
