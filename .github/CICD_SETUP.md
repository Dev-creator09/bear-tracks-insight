# CI/CD Pipeline Setup Guide

This guide walks you through setting up the complete CI/CD pipeline for Bear Tracks.

## Table of Contents

- [Quick Start](#quick-start)
- [GitHub Secrets Configuration](#github-secrets-configuration)
- [Server Setup](#server-setup)
- [First Deployment](#first-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Quick Start

### Prerequisites

- GitHub repository for your project
- Docker Hub account
- Staging and production servers (Ubuntu 22.04 recommended)
- Domain names configured (staging.beartracks.app, beartracks.app)

### Initial Setup Steps

1. **Fork/Clone Repository**
2. **Configure GitHub Secrets** (see below)
3. **Set Up Deployment Servers** (see below)
4. **Push to main branch** (triggers CI/CD)

## GitHub Secrets Configuration

Navigate to your repository → Settings → Secrets and variables → Actions → New repository secret

### Docker Hub Secrets

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `DOCKER_USERNAME` | Docker Hub username | Your Docker Hub account username |
| `DOCKER_TOKEN` | Docker Hub access token | Docker Hub → Account Settings → Security → New Access Token |

**Creating Docker Hub Token:**
```bash
# 1. Go to: https://hub.docker.com/settings/security
# 2. Click "New Access Token"
# 3. Description: "GitHub Actions"
# 4. Permissions: Read, Write, Delete
# 5. Copy the token (you won't see it again!)
# 6. Add to GitHub secrets as DOCKER_TOKEN
```

### SSH Deployment Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SSH_PRIVATE_KEY` | SSH private key for deployments | Contents of ~/.ssh/beartracks-deploy |
| `STAGING_USER` | SSH username for staging | `deploy` |
| `STAGING_HOST` | Staging server hostname | `staging.beartracks.app` |
| `PRODUCTION_USER` | SSH username for production | `deploy` |
| `PRODUCTION_HOST` | Production server hostname | `beartracks.app` |

**Creating SSH Key:**
```bash
# 1. Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/beartracks-deploy -N ""

# 2. Copy public key to servers
ssh-copy-id -i ~/.ssh/beartracks-deploy.pub deploy@staging.beartracks.app
ssh-copy-id -i ~/.ssh/beartracks-deploy.pub deploy@beartracks.app

# 3. Test connection
ssh -i ~/.ssh/beartracks-deploy deploy@staging.beartracks.app

# 4. Add private key to GitHub
cat ~/.ssh/beartracks-deploy
# Copy entire output (including BEGIN and END lines) to GitHub secret: SSH_PRIVATE_KEY
```

### API Key Secrets

| Secret Name | Description | Where to Get |
|-------------|-------------|--------------|
| `ANTHROPIC_API_KEY` | Claude API key (production) | https://console.anthropic.com/settings/keys |
| `ANTHROPIC_API_KEY_TEST` | Claude API key (testing) | Same, use separate key with lower limits |
| `OPENAI_API_KEY` | OpenAI API key (production) | https://platform.openai.com/api-keys |
| `OPENAI_API_KEY_TEST` | OpenAI API key (testing) | Same, use separate key |
| `REDDIT_CLIENT_ID` | Reddit API client ID | https://www.reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | Reddit API secret | Same |

**Creating Reddit API Credentials:**
```bash
# 1. Go to: https://www.reddit.com/prefs/apps
# 2. Click "create another app..." at bottom
# 3. Name: "BearTracks Bot"
# 4. Type: "script"
# 5. Description: "Course sentiment analysis"
# 6. About URL: Your site URL
# 7. Redirect URI: http://localhost:8000
# 8. Copy client_id and client_secret to GitHub secrets
```

### Optional Secrets

| Secret Name | Description | Where to Get |
|-------------|-------------|--------------|
| `SLACK_WEBHOOK_URL` | Slack notifications | Slack App → Incoming Webhooks |
| `CODECOV_TOKEN` | Code coverage reports | https://codecov.io/gh/yourusername/beartracks |

## Server Setup

### Server Requirements

- Ubuntu 22.04 LTS (or newer)
- 2+ CPU cores
- 4+ GB RAM
- 50+ GB disk space
- Docker and Docker Compose installed
- Domain name pointing to server

### Server Preparation (Both Staging and Production)

Run these commands on each server:

```bash
# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Create deployment directory
sudo mkdir -p /opt/beartracks
sudo chown $USER:$USER /opt/beartracks
cd /opt/beartracks

# 5. Create backup directory
sudo mkdir -p /opt/backups
sudo chown $USER:$USER /opt/backups

# 6. Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: bear_tracks
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "127.0.0.1:6379:6379"
    restart: unless-stopped

  api:
    image: ${DOCKER_USERNAME}/beartracks-api:latest
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/bear_tracks
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      REDDIT_CLIENT_ID: ${REDDIT_CLIENT_ID}
      REDDIT_CLIENT_SECRET: ${REDDIT_CLIENT_SECRET}
      ADMIN_API_KEY: ${ADMIN_API_KEY}
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  web:
    image: ${DOCKER_USERNAME}/beartracks-web:latest
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      - api
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
      - api
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# 7. Create .env file
cat > .env << 'EOF'
# Replace these values!
DOCKER_USERNAME=your-docker-username
POSTGRES_PASSWORD=change-this-secure-password
SECRET_KEY=change-this-long-random-secret
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
REDDIT_CLIENT_ID=your-id
REDDIT_CLIENT_SECRET=your-secret
ADMIN_API_KEY=your-admin-key
API_URL=https://api.beartracks.app
EOF

# 8. Install Nginx and Certbot for SSL
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 9. Get SSL certificates
sudo certbot --nginx -d staging.beartracks.app
# For production: sudo certbot --nginx -d beartracks.app -d api.beartracks.app

# 10. Create nginx.conf (simplified version)
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name staging.beartracks.app;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name staging.beartracks.app;

        ssl_certificate /etc/letsencrypt/live/staging.beartracks.app/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/staging.beartracks.app/privkey.pem;

        location / {
            proxy_pass http://web:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api/ {
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF
```

### Install pgvector Extension

```bash
# On the server
docker compose exec postgres psql -U postgres -d bear_tracks -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## First Deployment

### 1. Push Code to GitHub

```bash
git add .
git commit -m "feat: initial CI/CD setup"
git push origin main
```

### 2. Watch GitHub Actions

1. Go to GitHub → Actions tab
2. Watch the CI/CD Pipeline workflow
3. Jobs will run in order:
   - ✅ test-api
   - ✅ test-web
   - ✅ lint
   - ✅ eval-harness (on main branch only)
   - ✅ build-and-push (on main branch only)
   - ⏸️ deploy-staging (requires approval)

### 3. Approve Staging Deployment

1. Click on the running workflow
2. Click "deploy-staging" job
3. Click "Review deployments"
4. Check "staging"
5. Click "Approve and deploy"
6. Wait for deployment to complete
7. Check: https://staging.beartracks.app

### 4. Approve Production Deployment

1. Click "deploy-production" job
2. Click "Review deployments"
3. Check "production"
4. Click "Approve and deploy"
5. Wait for deployment to complete
6. Check: https://beartracks.app

## Monitoring and Maintenance

### Viewing Logs

```bash
# On server
cd /opt/beartracks

# View all logs
docker compose logs -f

# View specific service
docker compose logs -f api
docker compose logs -f web
```

### Health Checks

```bash
# API health
curl https://beartracks.app/api/v1/health

# Expected response:
# {"status":"healthy","database":"ok","redis":"ok"}
```

### Manual Deployment

If you need to deploy manually:

```bash
# On server
cd /opt/beartracks

# Pull latest images
docker compose pull

# Restart services
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head
```

### Database Backups

Backups are created automatically before production deployments.

**Manual backup:**
```bash
# On server
BACKUP_FILE="backup-$(date +%Y%m%d-%H%M%S).sql"
docker compose exec -T postgres pg_dump -U postgres bear_tracks > /opt/backups/$BACKUP_FILE
```

**Restore from backup:**
```bash
# On server
docker compose exec -T postgres psql -U postgres bear_tracks < /opt/backups/backup-20241206-120000.sql
```

### Monitoring Disk Space

```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up old images
docker system prune -a
```

## Troubleshooting

### Common Issues

#### 1. SSH Permission Denied

```bash
# Check SSH key permissions
chmod 600 ~/.ssh/beartracks-deploy

# Verify key is added to server
ssh -i ~/.ssh/beartracks-deploy deploy@staging.beartracks.app
```

#### 2. Docker Pull Rate Limit

If you hit Docker Hub rate limits:

```bash
# On server, login to Docker Hub
docker login -u your-username

# Retry deployment
```

#### 3. Health Check Failures

```bash
# On server
cd /opt/beartracks

# Check logs
docker compose logs -f api

# Restart services
docker compose restart api

# Check database connection
docker compose exec api alembic current
```

#### 4. SSL Certificate Issues

```bash
# Renew certificates
sudo certbot renew

# Restart nginx
docker compose restart nginx
```

## Updating Configuration

### Update Environment Variables

```bash
# On server
cd /opt/beartracks
nano .env

# Restart services
docker compose up -d
```

### Update docker-compose.yml

```bash
# On server
cd /opt/beartracks
nano docker-compose.yml

# Restart services
docker compose up -d
```

## Security Best Practices

1. **Keep secrets secure**: Never commit secrets to Git
2. **Use strong passwords**: Use password managers
3. **Rotate keys regularly**: Change API keys every 90 days
4. **Monitor access logs**: Check for unauthorized access
5. **Keep systems updated**: Run `apt-get update` regularly
6. **Enable firewall**: Use `ufw` to restrict access
7. **Use HTTPS only**: Never serve over HTTP

## Next Steps

1. Set up monitoring (Grafana, Prometheus)
2. Configure log aggregation (ELK stack)
3. Set up alerts (PagerDuty, Slack)
4. Enable automated backups
5. Configure CDN (Cloudflare)
6. Add load balancing for production

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/docs/)

---

**Need help?** Open an issue or check [CONTRIBUTING.md](.github/CONTRIBUTING.md)
