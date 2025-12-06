# Bear Tracks Background Workers

Comprehensive guide for running and managing Celery background workers for course data scraping and analysis.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup](#setup)
- [Running Workers](#running-workers)
- [Triggering Tasks](#triggering-tasks)
- [Monitoring](#monitoring)
- [Task Details](#task-details)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Bear Tracks worker system provides asynchronous background job processing for:

- **Course Scraping**: Fetching course data from UAlberta Bear Tracks
- **Reddit Analysis**: Searching r/ualberta for course mentions and reviews
- **AI Sentiment Analysis**: Using Claude to extract structured insights from student reviews
- **Vector Embeddings**: Generating OpenAI embeddings for semantic search
- **Database Persistence**: Storing all processed data in PostgreSQL

**Key Features:**

- ✅ **Idempotent Tasks**: Duplicate scrapes are prevented with distributed locking
- ✅ **Automatic Retries**: Exponential backoff for transient failures
- ✅ **Progress Tracking**: Real-time progress updates via Redis pub/sub
- ✅ **Cost Tracking**: Monitor AI API costs per task
- ✅ **Dead Letter Queue**: Failed tasks are logged and stored for review
- ✅ **Multiple Queues**: Priority-based task routing (scraping, analysis, default)

## 🏗️ Architecture

```
┌─────────────┐
│   FastAPI   │ ──► Trigger scrape via API endpoint
│     API     │     (POST /api/v1/scrape/trigger)
└─────────────┘
       │
       ▼
┌─────────────┐
│    Redis    │ ──► Task queue + Result backend
│   (Broker)  │
└─────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│           Celery Worker Pool                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Worker 1 │  │ Worker 2 │  │ Worker N │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
       │
       ├──► Bear Tracks (HTTPS)
       ├──► Reddit API (PRAW)
       ├──► Claude API (Anthropic)
       ├──► OpenAI API (Embeddings)
       │
       ▼
┌─────────────┐
│ PostgreSQL  │ ──► Store course data, sentiment, embeddings
│  + pgvector │
└─────────────┘
```

**Task Flow:**

```
1. Idempotency Check (Redis lock)
   ↓
2. Fetch Course from Bear Tracks
   ↓
3. Search Reddit for mentions (r/ualberta)
   ↓
4. Analyze sentiment with Claude AI
   ↓
5. Generate embeddings with OpenAI
   ↓
6. Store in PostgreSQL (Course, Sentiment, Embeddings)
   ↓
7. Return results + release lock
```

## 🚀 Setup

### Prerequisites

1. **Redis Server** running on `localhost:6379`
2. **PostgreSQL** with pgvector extension
3. **API Keys**:
   - Reddit API credentials
   - Anthropic Claude API key
   - OpenAI API key

### Step 1: Install Dependencies

```bash
cd apps/api
pip install -r requirements.txt
# or if using pyproject.toml:
pip install -e .
```

**Required packages:**
- `celery==5.3.6` - Task queue
- `redis==5.0.1` - Broker/backend
- `httpx==0.26.0` - HTTP client
- `beautifulsoup4==4.12.3` - HTML parsing
- `praw==7.7.1` - Reddit API
- `anthropic==0.18.1` - Claude AI
- `openai==1.12.0` - OpenAI API
- `structlog==24.1.0` - Structured logging

### Step 2: Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
nano .env  # Edit with your values
```

**Required variables:**

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Reddit API (create app at https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret

# Claude API (get key at https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# OpenAI API (get key at https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-xxxxx
```

### Step 3: Verify Redis is Running

```bash
redis-cli ping
# Should return: PONG
```

If Redis is not running:

```bash
# macOS (Homebrew)
brew services start redis

# Linux (systemd)
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

## 🏃 Running Workers

### Start Worker (Development)

```bash
cd apps/api
python run_worker.py
```

**Expected output:**

```
======================================================================
Starting Bear Tracks Celery Worker
======================================================================
Concurrency: 10
Log Level: info
Redis URL: redis://localhost:6379/0
Queues: default, scraping, analysis, dead_letter
======================================================================

[2024-01-15 10:30:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-01-15 10:30:00,100: INFO/MainProcess] celery@hostname ready.
```

### Worker Configuration Options

Control worker behavior with environment variables:

```bash
# Run with 20 concurrent workers
WORKER_CONCURRENCY=20 python run_worker.py

# Debug mode
WORKER_LOG_LEVEL=debug python run_worker.py

# Production mode
WORKER_LOG_LEVEL=warning WORKER_CONCURRENCY=50 python run_worker.py
```

### Run as Background Service (Production)

Use systemd, supervisor, or Docker to run workers in production.

**Example systemd service** (`/etc/systemd/system/beartracks-worker.service`):

```ini
[Unit]
Description=Bear Tracks Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=beartracks
WorkingDirectory=/opt/beartracks/apps/api
Environment="PATH=/opt/beartracks/venv/bin"
ExecStart=/opt/beartracks/venv/bin/python run_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable beartracks-worker
sudo systemctl start beartracks-worker
sudo systemctl status beartracks-worker
```

## 📤 Triggering Tasks

### Via API Endpoint

**Endpoint:** `POST /api/v1/scrape/trigger`

**Headers:**
```
X-API-Key: your-secret-key
Content-Type: application/json
```

**Request Body:**
```json
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
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Scrape job queued successfully"
}
```

**cURL example:**

```bash
curl -X POST http://localhost:8000/api/v1/scrape/trigger \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "CMPUT",
    "number": 272,
    "term": "Fall 2024",
    "force": false
  }'
```

### Programmatically (Python)

```python
from app.workers.tasks.scrape_course import scrape_course_task

# Queue task asynchronously
result = scrape_course_task.delay("CMPUT", 272, "Fall 2024", force=False)

# Get task ID
print(f"Task ID: {result.id}")

# Check status
print(f"Status: {result.state}")

# Wait for result (blocking)
final_result = result.get(timeout=300)  # 5 minute timeout
print(final_result)
```

### Via Celery CLI

```bash
# Send task directly
celery -A app.workers.celery_app call scrape_course \
  --args='["CMPUT", 272, "Fall 2024"]' \
  --kwargs='{"force": false}'
```

## 📊 Monitoring

### Check Task Status

**Python:**

```python
from celery.result import AsyncResult

task_id = "550e8400-e29b-41d4-a716-446655440000"
result = AsyncResult(task_id)

print(f"Status: {result.state}")
print(f"Info: {result.info}")

if result.successful():
    print(f"Result: {result.result}")
elif result.failed():
    print(f"Error: {result.traceback}")
```

**Redis CLI:**

```bash
# Check task result
redis-cli GET celery-task-meta-<task_id>

# List all task keys
redis-cli KEYS "celery-task-meta-*"

# Monitor scrape locks
redis-cli KEYS "scrape_lock:*"
```

### Monitor Progress in Real-Time

Subscribe to progress updates via Redis pub/sub:

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)
pubsub = r.pubsub()

task_id = "CMPUT_272_Fall_2024"
pubsub.subscribe(f"scrape_progress:{task_id}")

for message in pubsub.listen():
    if message['type'] == 'message':
        progress = json.loads(message['data'])
        print(f"Step {progress['step']}: {progress['status']}")
```

### Celery Flower (Web UI)

Install and run Flower for a web-based monitoring interface:

```bash
pip install flower
celery -A app.workers.celery_app flower --port=5555
```

Open http://localhost:5555 in your browser.

### Worker Stats

```bash
# Show active workers
celery -A app.workers.celery_app inspect active

# Show registered tasks
celery -A app.workers.celery_app inspect registered

# Show queue stats
celery -A app.workers.celery_app inspect stats
```

## 🔍 Task Details

### scrape_course

**Task Name:** `scrape_course`

**Parameters:**
- `subject` (str): Course subject code (e.g., "CMPUT")
- `number` (int): Course number (e.g., 272)
- `term` (str): Academic term (e.g., "Fall 2024")
- `force` (bool): Bypass cache and re-scrape (default: False)

**Returns:**
```python
{
    'task_id': 'CMPUT_272_Fall_2024',
    'subject': 'CMPUT',
    'number': 272,
    'status': 'completed',
    'difficulty_avg': 3.2,
    'workload_hours': 12.5,
    'gpa_estimate': 3.1,
    'reddit_posts_analyzed': 25,
    'cost_usd': 0.0523,
    'duration_seconds': 45.2,
    'completed_at': '2024-01-15T10:35:00.000Z'
}
```

**Retry Policy:**
- Max retries: 3
- Backoff: Exponential (10s, 20s, 40s)
- Max backoff: 600s (10 minutes)
- Jitter: Enabled

**Error Handling:**
- Network errors → Retry
- Rate limits → Exponential backoff
- 404 Not Found → Fail immediately
- Database errors → Rollback + retry
- Max retries exceeded → Send to dead letter queue

### API Costs

Approximate costs per task execution:

| Service | Model | Cost per Task |
|---------|-------|---------------|
| Claude | claude-3-5-sonnet-20241022 | ~$0.04 |
| OpenAI | text-embedding-3-small | ~$0.001 |
| **Total** | | **~$0.041** |

*Costs vary based on text length. Monitor actual costs in task results.*

## 🧪 Testing

### Run Tests

```bash
cd apps/api
pytest app/workers/tasks/test_helpers.py -v
```

### Manual Testing with Mocks

```python
from app.workers.tasks.test_helpers import run_task_synchronously

# Run task with mock data (no API calls)
result = run_task_synchronously("CMPUT", 272, "Fall 2024")

print(result)
# {
#   'status': 'completed',
#   'difficulty_avg': 3.2,
#   'cost_usd': 0.051,
#   ...
# }
```

### Test Real APIs (Use Sparingly)

```python
from app.workers.tasks.scrape_course import scrape_course_task

# Actually scrape and analyze (costs money!)
result = scrape_course_task.delay("CMPUT", 100, "Fall 2024")
print(result.get(timeout=300))
```

## 🔧 Troubleshooting

### Worker Not Starting

**Issue:** `Error: Cannot connect to redis://localhost:6379/0`

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### Tasks Not Executing

**Issue:** Tasks are queued but never execute

**Checklist:**
1. ✅ Worker is running (`python run_worker.py`)
2. ✅ Redis is accessible
3. ✅ Task is sent to correct queue
4. ✅ Worker is listening to that queue

**Debug:**
```bash
# Check if task is in queue
celery -A app.workers.celery_app inspect active_queues

# Purge stuck tasks
celery -A app.workers.celery_app purge
```

### API Key Errors

**Issue:** `401 Unauthorized` or `Invalid API key`

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check values are set
python -c "from app.config import settings; print(settings.reddit_client_id)"

# Re-export environment
export $(cat .env | xargs)
```

### Rate Limiting

**Issue:** `429 Too Many Requests` from Reddit/Claude/OpenAI

**Solution:**
- Reddit: Task will automatically retry after cooldown
- Claude: Exponential backoff is applied
- OpenAI: Reduce worker concurrency

**Reduce rate:**
```bash
# Run with fewer workers
WORKER_CONCURRENCY=2 python run_worker.py
```

### Memory Leaks

**Issue:** Worker memory usage keeps growing

**Solution:**
Workers automatically restart after 100 tasks to prevent memory leaks:

```python
# In run_worker.py:
'--max-tasks-per-child=100'
```

### Database Connection Issues

**Issue:** `OperationalError: could not connect to server`

**Solution:**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

### Stuck Locks

**Issue:** Task reports "already running" but no worker is processing it

**Solution:**
```bash
# Clear all scrape locks
redis-cli KEYS "scrape_lock:*" | xargs redis-cli DEL

# Or clear specific lock
redis-cli DEL "scrape_lock:CMPUT_272_Fall_2024"
```

### View Dead Letter Queue

**Issue:** Need to see failed tasks

**Solution:**
```python
# Check dead_letter queue
from celery import Celery
app = Celery('bear_tracks_worker', broker='redis://localhost:6379/0')

# Inspect dead letter queue
result = app.control.inspect().active_queues()
print(result)
```

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [PRAW (Reddit API)](https://praw.readthedocs.io/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs/)

## 🔗 Related Files

- `app/workers/celery_app.py` - Celery configuration
- `app/workers/tasks/scrape_course.py` - Main task implementation
- `app/workers/tasks/test_helpers.py` - Testing utilities
- `run_worker.py` - Worker startup script
- `app/config.py` - Application settings
- `.env.example` - Environment variable template

---

**Need Help?**

Check the main [README](../../README.md) for general setup or open an issue on GitHub.
