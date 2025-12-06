# 🐻 Bear Tracks - Course Insight Platform

[![CI/CD Pipeline](https://github.com/yourusername/beartracks/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/yourusername/beartracks/actions)
[![codecov](https://codecov.io/gh/yourusername/beartracks/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/beartracks)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20](https://img.shields.io/badge/node-20.x-green.svg)](https://nodejs.org/)

A modern, full-stack course discovery and analytics platform built with Turborepo, Next.js, and FastAPI. Helps students make informed decisions about their courses through AI-powered sentiment analysis and comprehensive course data.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Development](#development)
- [Project Structure](#project-structure)
- [Available Commands](#available-commands)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)

## ✨ Features

- **Course Discovery**: Browse and search thousands of courses with advanced filtering
- **Sentiment Analysis**: AI-powered analysis of student reviews and feedback
- **Prerequisite Tracking**: Visualize course dependencies and plan your academic path
- **Semantic Search**: Vector-based course search using embeddings
- **Real-time Updates**: Live data synchronization using Redis
- **Responsive Design**: Beautiful UI built with Tailwind CSS and shadcn/ui
- **Type Safety**: End-to-end type safety with TypeScript and Zod schemas

## 🏗️ Architecture

Bear Tracks is built as a **Turborepo monorepo** with the following structure:

```
bear-tracks-monorepo/
├── apps/
│   ├── web/          # Next.js 14 frontend (TypeScript, Tailwind, shadcn/ui)
│   └── api/          # FastAPI backend (Python 3.11, SQLAlchemy)
├── packages/
│   ├── database/     # Prisma schema and migrations
│   └── types/        # Shared Zod schemas and TypeScript types
└── scripts/          # Utility scripts
```

### Architecture Overview

```
┌─────────────────┐
│   Next.js Web   │ ──────┐
│   (Port 3000)   │       │
└─────────────────┘       │
                          ▼
                  ┌───────────────┐
                  │  FastAPI      │
                  │  (Port 8000)  │
                  └───────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    ┌──────────────┐           ┌──────────────┐
    │  PostgreSQL  │           │    Redis     │
    │  + pgvector  │           │  (Cache)     │
    │  (Port 5432) │           │  (Port 6379) │
    └──────────────┘           └──────────────┘
```

## 🛠️ Tech Stack

### Frontend (`apps/web`)
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (Radix UI)
- **Data Tables**: TanStack Table
- **Validation**: Zod
- **Linting**: ESLint (Airbnb TypeScript preset)

### Backend (`apps/api`)
- **Framework**: FastAPI
- **Language**: Python 3.11
- **ORM**: SQLAlchemy (async)
- **Validation**: Pydantic v2
- **Database**: PostgreSQL 15 + pgvector
- **Cache**: Redis 7
- **Code Quality**: Black, Ruff, MyPy

### Shared Packages
- **Database**: Prisma (schema definition)
- **Types**: Zod schemas for API contracts

### Infrastructure
- **Monorepo**: Turborepo
- **Containerization**: Docker & Docker Compose
- **Package Manager**: npm

## 📦 Prerequisites

- **Node.js**: >= 20.0.0
- **Python**: >= 3.11
- **Docker**: >= 24.0.0 (optional, for containerized development)
- **PostgreSQL**: >= 15 (with pgvector extension)
- **Redis**: >= 7

## 🚀 Getting Started

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bear-tracks-monorepo
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   cp apps/api/.env.example apps/api/.env
   cp packages/database/.env.example packages/database/.env
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the applications**
   - Web: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050 (with `--profile tools`)

### Option 2: Local Development

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Set up PostgreSQL and Redis**
   ```bash
   # Install PostgreSQL with pgvector
   # macOS (using Homebrew)
   brew install postgresql@15 pgvector

   # Start PostgreSQL
   brew services start postgresql@15

   # Install Redis
   brew install redis
   brew services start redis
   ```

3. **Create database**
   ```bash
   createdb bear_tracks
   psql bear_tracks -c "CREATE EXTENSION vector;"
   ```

4. **Set up Python environment (API)**
   ```bash
   cd apps/api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cd ../..
   ```

5. **Generate Prisma client**
   ```bash
   npm run db:generate --filter=@bear-tracks/database
   ```

6. **Start development servers**
   ```bash
   # Terminal 1: Start all apps in parallel
   npm run dev

   # Or start individually
   # Terminal 1: Web app
   npm run dev --filter=@bear-tracks/web

   # Terminal 2: API
   cd apps/api
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

## 💻 Development

### Development Commands

```bash
# Install dependencies
npm install

# Run all apps in development mode
npm run dev

# Build all apps
npm run build

# Lint all code
npm run lint

# Format code
npm run format

# Run tests
npm run test

# Clean build artifacts
npm run clean
```

### Working with the Database

```bash
# Generate Prisma client
npm run db:generate --filter=@bear-tracks/database

# Push schema to database (development)
npm run db:push --filter=@bear-tracks/database

# Create migration
npm run db:migrate --filter=@bear-tracks/database

# Open Prisma Studio
npm run db:studio --filter=@bear-tracks/database
```

### Python Development (API)

```bash
cd apps/api

# Activate virtual environment
source venv/bin/activate

# Format code with Black
black app/

# Lint with Ruff
ruff check app/

# Type check with MyPy
mypy app/

# Run tests
pytest

# Run with auto-reload
uvicorn app.main:app --reload
```

## 📁 Project Structure

```
bear-tracks-monorepo/
├── apps/
│   ├── web/                      # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/             # App router pages
│   │   │   ├── components/      # React components
│   │   │   │   ├── ui/         # shadcn/ui components
│   │   │   │   └── ...
│   │   │   └── lib/            # Utilities
│   │   ├── public/             # Static assets
│   │   ├── Dockerfile          # Multi-stage Docker build
│   │   └── package.json
│   │
│   └── api/                     # FastAPI backend
│       ├── app/
│       │   ├── api/
│       │   │   └── routes/     # API endpoints
│       │   ├── models/         # SQLAlchemy models
│       │   ├── schemas/        # Pydantic schemas
│       │   ├── database.py     # DB connection
│       │   ├── config.py       # Settings
│       │   └── main.py         # FastAPI app
│       ├── tests/              # Pytest tests
│       ├── Dockerfile          # Multi-stage Docker build
│       ├── pyproject.toml      # Python config
│       └── requirements.txt
│
├── packages/
│   ├── database/               # Prisma schema
│   │   ├── prisma/
│   │   │   └── schema.prisma  # Database schema
│   │   └── src/
│   │       └── index.ts       # Prisma client export
│   │
│   └── types/                  # Shared types
│       └── src/
│           ├── course.ts      # Course schemas
│           ├── api.ts         # API schemas
│           └── common.ts      # Common types
│
├── scripts/                    # Utility scripts
│   └── init-db.sql            # DB initialization
│
├── .env.example               # Environment template
├── docker-compose.yml         # Docker orchestration
├── turbo.json                 # Turborepo config
├── tsconfig.base.json         # Base TypeScript config
├── .prettierrc                # Prettier config
└── package.json               # Root package.json
```

## 📝 Available Commands

### Root Level

| Command | Description |
|---------|-------------|
| `npm run dev` | Start all apps in development mode |
| `npm run build` | Build all apps for production |
| `npm run lint` | Lint all code |
| `npm run format` | Format code with Prettier |
| `npm run test` | Run all tests |
| `npm run clean` | Clean build artifacts |

### Web App (`apps/web`)

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Next.js dev server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Lint with ESLint |

### API (`apps/api`)

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload` | Start with auto-reload |
| `black app/` | Format code |
| `ruff check app/` | Lint code |
| `mypy app/` | Type check |
| `pytest` | Run tests |

### Database (`packages/database`)

| Command | Description |
|---------|-------------|
| `npm run db:generate` | Generate Prisma client |
| `npm run db:push` | Push schema to database |
| `npm run db:migrate` | Create migration |
| `npm run db:studio` | Open Prisma Studio |

## 🔐 Environment Variables

### Root `.env`

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bear_tracks
REDIS_URL=redis://localhost:6379/0
NEXT_PUBLIC_API_URL=http://localhost:8000
DEBUG=True
NODE_ENV=development
```

### API `.env` (`apps/api/.env`)

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bear_tracks
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
```

## 🗄️ Database Schema

### Core Tables

- **courses**: Course information (code, name, description, credits, department, level)
- **course_sentiments**: Sentiment analysis data (rating, difficulty, workload, sentiment_score)
- **course_embeddings**: Vector embeddings for semantic search (1536-dimensional vectors)
- **prerequisites**: Course prerequisite relationships

### Key Features

- **pgvector Extension**: Enables similarity search using vector embeddings
- **Cascade Deletes**: Maintain referential integrity
- **Indexes**: Optimized for common queries (department, level, rating)

## 📚 API Documentation

### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy"
}
```

### Courses

```http
GET /api/v1/courses
GET /api/v1/courses/{course_id}
POST /api/v1/courses
PATCH /api/v1/courses/{course_id}
DELETE /api/v1/courses/{course_id}
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚢 Deployment

### Production Build

```bash
# Build all apps
npm run build

# Build Docker images
docker-compose build

# Start in production mode
docker-compose up -d
```

### Docker Deployment

The project includes optimized multi-stage Dockerfiles:

- **Web**: Uses Next.js standalone output for minimal image size
- **API**: Uses `uv` for fast dependency installation and runs as non-root user

### Environment Configuration

Ensure all production environment variables are set:
- Update `SECRET_KEY` to a secure random string
- Set `DEBUG=False` in production
- Configure production database and Redis URLs
- Update CORS origins in `apps/api/app/main.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **TypeScript**: Follow Airbnb TypeScript style guide
- **Python**: Use Black for formatting, Ruff for linting
- **Commits**: Use conventional commits format

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Turborepo](https://turbo.build/) - Monorepo build system
- [Next.js](https://nextjs.org/) - React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [shadcn/ui](https://ui.shadcn.com/) - UI component library
- [Prisma](https://www.prisma.io/) - Database toolkit
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search

---

Built with ❤️ for students, by students
