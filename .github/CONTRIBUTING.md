# Contributing to Bear Tracks Course Insight Platform

Thank you for your interest in contributing! This guide will help you understand our development workflow and CI/CD pipeline.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Running CI Locally](#running-ci-locally)
- [Understanding CI Failures](#understanding-ci-failures)
- [Deployment Process](#deployment-process)
- [Evaluation System](#evaluation-system)
- [Secrets Management](#secrets-management)

## Getting Started

### Prerequisites

- Node.js 20.x
- Python 3.11
- PostgreSQL 15+
- Redis 7+
- Docker (for deployment)
- pnpm 8.15.0

### Initial Setup

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/beartracks.git
cd beartracks
```

2. **Install dependencies:**

```bash
# Install pnpm if needed
npm install -g pnpm@8.15.0

# Install Node.js dependencies
pnpm install

# Install Python dependencies
cd apps/api
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov ruff black isort
```

3. **Set up environment variables:**

```bash
# Copy example env file
cp apps/api/.env.example apps/api/.env

# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY
# - OPENAI_API_KEY
# - DATABASE_URL
# - REDIS_URL
```

4. **Set up database:**

```bash
# Start PostgreSQL and Redis with Docker
docker compose up -d postgres redis

# Run migrations
cd apps/api
alembic upgrade head

# Install pgvector extension
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Development Workflow

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new search filter
fix: resolve query parsing bug
docs: update API documentation
chore: update dependencies
test: add unit tests for RAG pipeline
```

### Pull Request Process

1. Create a feature branch from `main` or `develop`
2. Make your changes
3. Run tests locally (see below)
4. Push and create a PR
5. Wait for CI checks to pass
6. Request review from maintainers
7. Address feedback
8. Merge when approved

## Running CI Locally

Before pushing, run these commands to catch issues early:

### API Tests

```bash
cd apps/api

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term

# Run linting
ruff check .
black --check .
isort --check-only .

# Auto-fix formatting
black .
isort .
```

### Web Tests

```bash
cd apps/web

# Run type checking
pnpm tsc --noEmit

# Run tests
pnpm test

# Run linting
pnpm lint

# Auto-fix lint issues
pnpm lint --fix
```

### Monorepo Commands

```bash
# From root directory

# Run all tests
pnpm test

# Run all linting
pnpm lint

# Build all apps
pnpm build
```

## Understanding CI Failures

### Common Failure Scenarios

#### 1. Test Failures

**Symptom:** `test-api` or `test-web` job fails

**Debug steps:**
1. Check the test output in GitHub Actions logs
2. Run the same test locally: `pytest tests/path/to/test.py -v`
3. Check if you need to update test fixtures
4. Ensure all dependencies are installed

#### 2. Lint Failures

**Symptom:** `lint` job fails

**Debug steps:**
1. Check which linter failed (ESLint, ruff, black, isort)
2. Run the linter locally
3. Auto-fix if possible: `black .` or `pnpm lint --fix`
4. Manually fix remaining issues

#### 3. Evaluation Regression

**Symptom:** `eval-harness` job fails due to metrics regression

**Debug steps:**
1. Check the eval output artifact
2. Compare metrics with baseline in `.github/eval-baseline.json`
3. Identify which category regressed
4. Debug using `apps/api/README_EVALS.md` troubleshooting guide
5. If regression is intentional, update baseline (see below)

#### 4. Build Failures

**Symptom:** `build-and-push` job fails

**Debug steps:**
1. Check Docker build logs
2. Test Docker build locally:
   ```bash
   docker build -t test-web ./apps/web
   docker build -t test-api ./apps/api
   ```
3. Verify Dockerfile syntax
4. Check for missing dependencies

#### 5. Deployment Failures

**Symptom:** `deploy-staging` or `deploy-production` fails

**Debug steps:**
1. Check SSH connection: Ensure SSH keys are configured
2. Check Docker registry: Verify images were pushed
3. Check health checks: API must respond within 60 seconds
4. Review smoke test failures
5. Check server logs: SSH into server and check `docker compose logs`

### Retrying Failed Jobs

- Navigate to the GitHub Actions run
- Click "Re-run failed jobs"
- If the failure is intermittent (flaky test), retry up to 3 times
- If it consistently fails, investigate and fix the issue

## Deployment Process

### Environments

1. **Staging** (staging.beartracks.app)
   - Deployed automatically on `main` branch pushes
   - Requires manual approval
   - Used for final testing before production

2. **Production** (beartracks.app)
   - Deployed after staging deployment succeeds
   - Requires manual approval
   - Includes automatic backup before deployment

### Manual Deployment Approval

1. Navigate to GitHub Actions run
2. Click on the deployment job (e.g., `deploy-staging`)
3. Click "Review deployments"
4. Select the environment
5. Click "Approve and deploy"

### Rollback Procedure

If a deployment causes issues:

#### Automatic Rollback

- If smoke tests fail, deployment automatically rolls back
- Previous Docker images are redeployed

#### Manual Rollback

```bash
# SSH into the server
ssh user@production-server

cd /opt/beartracks

# List available image tags
docker images | grep beartracks

# Update docker-compose.yml to use previous tag
# Edit: image: username/beartracks-api:previous-sha

# Restart services
docker compose down
docker compose up -d

# Restore database from backup if needed
docker compose exec -T postgres psql -U postgres bear_tracks < /opt/backups/backup-YYYYMMDD-HHMMSS.sql
```

## Evaluation System

### Running Evaluations

**Locally:**

```bash
cd apps/api
python -m app.evals.eval_runner
```

**Via API:**

```bash
curl -X GET http://localhost:8000/api/v1/evals/run \
  -H "X-API-Key: your-admin-key"
```

**Via GitHub Actions:**

Evaluations run automatically on `main` branch pushes.

### Updating Baseline

When you make intentional improvements to the search system:

1. Run the "Update Evaluation Baseline" workflow:
   - Go to GitHub Actions
   - Select "Update Evaluation Baseline"
   - Click "Run workflow"
   - Enter reason: "Improved re-ranking prompt"
   - Click "Run workflow"

2. Review the auto-created PR:
   - Check the new metrics
   - Verify improvements are as expected
   - Approve and merge

3. **Never update baseline just to make CI pass!**
   - Only update after genuine improvements
   - Document the reason in the PR

### Interpreting Metrics

- **Recall@10**: Fraction of relevant courses in top 10 (target: >0.85)
- **MRR**: Mean reciprocal rank of first relevant (target: >0.70)
- **Precision@10**: Fraction of top 10 that are relevant
- **NDCG@10**: Ranking quality metric (target: >0.75)

See `apps/api/README_EVALS.md` for detailed explanations.

### Adding Test Queries

1. Edit `apps/api/scripts/generate_golden_set.py`
2. Add your query to the appropriate category
3. Label relevant courses
4. Run: `python scripts/generate_golden_set.py`
5. Commit the updated `fixtures/golden-queries.json`

## Secrets Management

### Required GitHub Secrets

Configure these in your repository settings (Settings → Secrets and variables → Actions):

#### Docker Hub

- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_TOKEN`: Docker Hub access token (not password!)

#### SSH Deployment

- `SSH_PRIVATE_KEY`: SSH private key for deployment servers
- `STAGING_USER`: SSH username for staging server
- `STAGING_HOST`: Staging server hostname
- `PRODUCTION_USER`: SSH username for production server
- `PRODUCTION_HOST`: Production server hostname

#### API Keys

- `ANTHROPIC_API_KEY`: Claude API key (production)
- `ANTHROPIC_API_KEY_TEST`: Claude API key (testing, lower rate limits)
- `OPENAI_API_KEY`: OpenAI API key (production)
- `OPENAI_API_KEY_TEST`: OpenAI API key (testing)
- `REDDIT_CLIENT_ID`: Reddit API client ID
- `REDDIT_CLIENT_SECRET`: Reddit API secret

#### Optional

- `SLACK_WEBHOOK_URL`: Slack webhook for deployment notifications
- `CODECOV_TOKEN`: Codecov upload token for coverage reports

### Setting Up Secrets

1. **Generate SSH key for deployment:**

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/beartracks-deploy
# Add public key to deployment servers: ~/.ssh/authorized_keys
# Add private key to GitHub secret: SSH_PRIVATE_KEY
```

2. **Create Docker Hub token:**
   - Go to Docker Hub → Account Settings → Security
   - Click "New Access Token"
   - Name: "GitHub Actions"
   - Copy token and add to GitHub secret: DOCKER_TOKEN

3. **API Keys:**
   - Get from respective service dashboards
   - Use separate keys for test/production to manage rate limits

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```bash
# API
pytest apps/api/tests/unit/

# Web
pnpm test:unit
```

### Integration Tests

Test component interactions:

```bash
# API with database
pytest apps/api/tests/integration/

# Web with API
pnpm test:integration
```

### E2E Tests

Test full user workflows (future):

```bash
pnpm test:e2e
```

## Code Quality Standards

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Docstrings for all public functions
- Max line length: 100 characters
- Use `ruff` for linting
- Use `black` for formatting
- Use `isort` for import sorting

### TypeScript/JavaScript

- Follow [Airbnb Style Guide](https://github.com/airbnb/javascript)
- Use TypeScript strict mode
- ESLint for linting
- Prettier for formatting (via ESLint)

### Documentation

- Update README.md for user-facing changes
- Update API docs for endpoint changes
- Add inline comments for complex logic
- Update CONTRIBUTING.md for process changes

## Getting Help

- **Documentation**: Check `apps/api/README_EVALS.md` for evaluation system
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Slack**: Join our Slack channel (link in README)

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

**Thank you for contributing to Bear Tracks! 🐻**
