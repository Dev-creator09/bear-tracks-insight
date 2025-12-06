# Database Quick Start Guide

Get the Bear Tracks database up and running in 5 minutes.

## Prerequisites

- Node.js >= 20
- PostgreSQL 15+ with pgvector extension
- OR Docker (easier option)

## Option 1: Docker Setup (Recommended)

### 1. Start PostgreSQL with Docker

```bash
# From the repository root
docker-compose up -d postgres

# Wait for PostgreSQL to be ready (about 10 seconds)
docker-compose logs -f postgres
# Look for: "database system is ready to accept connections"
```

### 2. Install dependencies

```bash
# From packages/database
npm install
```

### 3. Set up environment

```bash
cp .env.example .env
# The default DATABASE_URL should work with Docker
```

### 4. Run migrations and seed

```bash
npm run migrate  # Creates tables and indexes
npm run seed     # Populates with 70 courses
```

### 5. Verify setup

```bash
npm run studio   # Opens Prisma Studio at http://localhost:5555
```

You should see 70 courses across CMPUT, MATH, and STAT subjects!

## Option 2: Local PostgreSQL Setup

### 1. Install PostgreSQL and pgvector

**macOS:**
```bash
brew install postgresql@15 pgvector
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-15 postgresql-15-pgvector
sudo systemctl start postgresql
```

### 2. Create database

```bash
createdb bear_tracks
psql bear_tracks -c "CREATE EXTENSION vector;"
```

### 3. Install dependencies and setup

```bash
npm install
cp .env.example .env
npm run migrate
npm run seed
```

## Verify Installation

### Check tables

```bash
psql bear_tracks -c "\dt"
```

You should see:
- courses
- course_sentiments
- course_embeddings
- prerequisites

### Check data

```bash
psql bear_tracks -c "SELECT COUNT(*) FROM courses;"
# Should return: 70

psql bear_tracks -c "SELECT subject, COUNT(*) FROM courses GROUP BY subject;"
# Should show: CMPUT (30), MATH (25), STAT (15)
```

### Query sample data

```bash
psql bear_tracks -c "
  SELECT c.subject, c.number, c.title, s.difficulty_avg, s.workload_avg
  FROM courses c
  LEFT JOIN course_sentiments s ON c.id = s.course_id
  LIMIT 5;
"
```

## Common Commands

```bash
# View data visually
npm run studio

# Reset and reseed (WARNING: deletes all data)
npm run db:reset
npm run seed

# Just reseed (preserves schema)
npm run seed

# Generate Prisma client (after schema changes)
npm run db:generate
```

## Troubleshooting

### "Extension 'vector' does not exist"

**Docker:**
```bash
docker-compose down
docker-compose up -d postgres
```

**Local:**
```bash
brew install pgvector  # macOS
psql bear_tracks -c "CREATE EXTENSION vector;"
```

### "Database 'bear_tracks' does not exist"

```bash
createdb bear_tracks
```

### "Connection refused"

**Docker:**
```bash
docker-compose up -d postgres
docker-compose ps  # Check if postgres is running
```

**Local:**
```bash
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux
```

### Start fresh

```bash
# Drop and recreate everything
npm run db:reset

# Or manually
dropdb bear_tracks
createdb bear_tracks
psql bear_tracks -c "CREATE EXTENSION vector;"
npm run migrate
npm run seed
```

## What's Next?

After successful setup:

1. **Explore the data**: `npm run studio`
2. **Read the schema**: Check `prisma/schema.prisma`
3. **Understand the models**: See the main README.md
4. **Test queries**: Try the Prisma client in your code

## Sample Queries

```typescript
import { prisma } from '@bear-tracks/database';

// Get all CMPUT courses
const cmputCourses = await prisma.course.findMany({
  where: { subject: 'CMPUT' },
  include: { sentiment: true },
});

// Find difficult courses
const difficultCourses = await prisma.course.findMany({
  where: {
    sentiment: {
      difficultyAvg: { gte: 4.0 }
    }
  },
  include: { sentiment: true },
});

// Get course with prerequisites
const courseWithPrereqs = await prisma.course.findFirst({
  where: { subject: 'CMPUT', number: 272 },
  include: {
    prerequisites: {
      include: { requiredCourse: true }
    }
  },
});
```

---

Need help? Check the full README.md or open an issue!
