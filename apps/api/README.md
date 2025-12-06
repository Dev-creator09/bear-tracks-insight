# Bear Tracks API

FastAPI-based backend for the Bear Tracks Course Insight Platform.

## 📋 Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Examples](#examples)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## 🎯 Overview

The Bear Tracks API provides endpoints for:
- **Course Discovery**: List and search courses with advanced filtering
- **Sentiment Analysis**: Access course difficulty, workload, and GPA estimates
- **Semantic Search**: AI-powered course search using vector embeddings
- **Prerequisite Trees**: Recursive prerequisite graph traversal
- **Data Scraping**: Admin endpoints for collecting course data

## 🚀 Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

### 5. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## 📚 API Endpoints

### Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "version": "1.0.0",
  "uptimeSeconds": 3600.5
}
```

### List Courses

```http
GET /api/v1/courses?limit=50&subject=CMPUT&min_gpa=3.0
```

**Parameters:**
- `cursor` (optional): Pagination cursor
- `limit` (optional, default: 50, max: 100): Results per page
- `faculty` (optional): Filter by faculty
- `subject` (optional): Filter by subject code
- `min_gpa` (optional): Minimum GPA estimate
- `max_difficulty` (optional): Maximum difficulty rating
- `term` (optional): Filter by term availability

**Response:**
```json
{
  "courses": [
    {
      "id": "uuid",
      "subject": "CMPUT",
      "number": 272,
      "title": "Formal Systems and Logic",
      "description": "Propositional and predicate logic...",
      "credits": 3.0,
      "faculty": "Science",
      "prerequisiteCodes": ["CMPUT 175", "MATH 101"],
      "termAvailability": ["Fall", "Winter"],
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z",
      "sentiment": {
        "id": "uuid",
        "courseId": "uuid",
        "redditThreadIds": ["abc123"],
        "difficultyAvg": 3.5,
        "workloadAvg": 12.0,
        "gpaEstimate": 3.2,
        "professorMentions": {
          "Smith, J.": 4.2
        },
        "warnings": ["heavy math"],
        "lastScrapedAt": "2024-01-01T00:00:00Z"
      }
    }
  ],
  "pagination": {
    "cursor": null,
    "nextCursor": "Science:272:uuid",
    "limit": 50,
    "hasMore": true
  }
}
```

### Get Course Detail

```http
GET /api/v1/courses/{subject}/{number}
```

**Example:**
```http
GET /api/v1/courses/CMPUT/272
```

**Response:**
```json
{
  "id": "uuid",
  "subject": "CMPUT",
  "number": 272,
  "title": "Formal Systems and Logic",
  "description": "...",
  "credits": 3.0,
  "faculty": "Science",
  "prerequisiteCodes": ["CMPUT 175", "MATH 101"],
  "termAvailability": ["Fall", "Winter"],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z",
  "sentiment": { ... },
  "prerequisites": [
    {
      "id": "uuid",
      "course": { ... }
    }
  ],
  "requiredBy": [
    {
      "id": "uuid",
      "course": { ... }
    }
  ]
}
```

### Semantic Search

```http
POST /api/v1/courses/search
Content-Type: application/json

{
  "query": "machine learning courses with good ratings",
  "filters": {
    "subject": "CMPUT",
    "minGpa": 3.0
  },
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "subject": "CMPUT",
      "number": 367,
      "title": "Introduction to Machine Learning",
      "description": "...",
      "relevanceScore": 0.92,
      "reasoning": "High relevance for machine learning query",
      "sentiment": { ... }
    }
  ],
  "query": "machine learning courses with good ratings",
  "totalResults": 5
}
```

### Get Prerequisite Tree

```http
GET /api/v1/prerequisites/{subject}/{number}?depth=5
```

**Example:**
```http
GET /api/v1/prerequisites/CMPUT/301?depth=5
```

**Response:**
```json
{
  "course": { ... },
  "tree": {
    "course": { ... },
    "children": [
      {
        "course": { ... },
        "children": []
      }
    ]
  },
  "depth": 5
}
```

### Trigger Scrape (Admin Only)

```http
POST /api/v1/scrape/trigger
X-API-Key: your-api-key
Content-Type: application/json

{
  "subject": "CMPUT",
  "number": 272,
  "term": "Fall 2024",
  "force": false
}
```

**Response:**
```json
{
  "jobId": "uuid",
  "status": "queued",
  "message": "Scrape job queued for CMPUT 272 (Fall 2024)"
}
```

## 🔐 Authentication

Admin endpoints require API key authentication.

### Setting API Key

Set the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-secret-key" \
  http://localhost:8000/api/v1/scrape/trigger
```

### Generating API Key

API keys should be:
- Cryptographically secure random strings
- At least 32 characters
- Stored securely (not in version control)

```python
import secrets
api_key = secrets.token_urlsafe(32)
```

## 📖 Examples

### cURL Examples

**Get courses:**
```bash
curl http://localhost:8000/api/v1/courses?subject=CMPUT&limit=10
```

**Get course detail:**
```bash
curl http://localhost:8000/api/v1/courses/CMPUT/272
```

**Search courses:**
```bash
curl -X POST http://localhost:8000/api/v1/courses/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "easy intro courses",
    "filters": {"maxDifficulty": 3.0},
    "limit": 10
  }'
```

**Get prerequisite tree:**
```bash
curl http://localhost:8000/api/v1/prerequisites/CMPUT/301?depth=3
```

**Trigger scrape (admin):**
```bash
curl -X POST http://localhost:8000/api/v1/scrape/trigger \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "subject": "CMPUT",
    "number": 272,
    "term": "Fall 2024",
    "force": false
  }'
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000"

# Get courses
response = requests.get(
    f"{BASE_URL}/api/v1/courses",
    params={"subject": "CMPUT", "limit": 10}
)
courses = response.json()

# Get course detail
response = requests.get(f"{BASE_URL}/api/v1/courses/CMPUT/272")
course = response.json()

# Search courses
response = requests.post(
    f"{BASE_URL}/api/v1/courses/search",
    json={
        "query": "machine learning",
        "filters": {"minGpa": 3.0},
        "limit": 10
    }
)
results = response.json()

# Get prerequisite tree
response = requests.get(
    f"{BASE_URL}/api/v1/prerequisites/CMPUT/301",
    params={"depth": 5}
)
tree = response.json()
```

### JavaScript/TypeScript Examples

```typescript
// Using the provided API client
import { createBearTracksClient } from '@bear-tracks/types';

const client = createBearTracksClient({
  baseUrl: 'http://localhost:8000',
});

// Get courses
const { courses, nextCursor } = await client.getCourses({
  subject: 'CMPUT',
  limit: 10,
});

// Search courses
const results = await client.searchCourses({
  query: 'machine learning',
  filters: { minGpa: 3.0 },
  limit: 10,
});
```

## 🚨 Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": { ... },
  "path": "/api/v1/courses",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

### Validation Errors

Validation errors include detailed field-level errors:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "errors": [
    {
      "field": "number",
      "message": "must be >= 100",
      "code": "value_error.number.not_ge"
    }
  ]
}
```

## ⏱️ Rate Limiting

Rate limits are enforced per API key (admin endpoints) or IP address (public endpoints).

| Endpoint Type | Limit |
|--------------|-------|
| Public | 100 requests/minute |
| Search | 20 requests/minute |
| Admin | 10 requests/minute |

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

### Handling Rate Limits

When rate limited, the API returns:

```json
{
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded",
  "details": {
    "retryAfter": 60,
    "limit": 100,
    "window": "minute"
  }
}
```

## 🔧 Development

### Code Formatting

```bash
black app/
```

### Linting

```bash
ruff check app/
```

### Type Checking

```bash
mypy app/
```

### Testing

```bash
pytest
pytest --cov=app --cov-report=term-missing
```

### Running with Auto-Reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Monitoring

### Request Tracing

All requests include:
- **X-Request-ID**: Unique request identifier
- **X-Response-Time**: Processing time in seconds

Example response headers:
```
X-Request-ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
X-Response-Time: 0.045s
```

### Health Monitoring

Monitor the `/api/v1/health` endpoint for:
- Database connectivity
- Redis connectivity
- Application uptime

## 🔄 Background Workers

The Bear Tracks API uses Celery for asynchronous background job processing. Workers handle:

- **Course Scraping**: Fetching data from UAlberta Bear Tracks
- **Reddit Analysis**: Searching and analyzing r/ualberta posts
- **AI Processing**: Sentiment analysis with Claude, embeddings with OpenAI
- **Database Updates**: Persisting processed data

### Quick Start

1. **Ensure Redis is running:**
   ```bash
   redis-cli ping  # Should return PONG
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Add your API keys: REDDIT_CLIENT_ID, ANTHROPIC_API_KEY, OPENAI_API_KEY
   ```

3. **Start the worker:**
   ```bash
   python run_worker.py
   ```

4. **Trigger a scrape job:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/scrape/trigger \
     -H "X-API-Key: your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"subject": "CMPUT", "number": 272, "term": "Fall 2024"}'
   ```

### Documentation

For comprehensive worker documentation including:
- Architecture and task flow
- Monitoring and debugging
- Error handling and retries
- Testing with mock data
- Production deployment

**See: [README_WORKERS.md](README_WORKERS.md)**

## 🔗 Related Documentation

- [Background Workers Guide](README_WORKERS.md) ⭐ **NEW**
- [OpenAPI Specification](app/openapi.yaml)
- [Pydantic Models](app/schemas/)
- [Database Models](app/models/)
- [API Client Documentation](../../packages/types/README.md)

---

Built with ❤️ using FastAPI
