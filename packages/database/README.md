# @bear-tracks/database

Prisma database schema and client for the Bear Tracks Course Insight Platform.

## 📋 Table of Contents

- [Database Schema](#database-schema)
- [Setup](#setup)
- [Commands](#commands)
- [Seeding](#seeding)
- [Migrations](#migrations)
- [Troubleshooting](#troubleshooting)

## 🗄️ Database Schema

The database includes the following models:

### Course
Stores course information from the UAlberta catalog.

- `id`: UUID (primary key)
- `subject`: String (e.g., "CMPUT")
- `number`: Integer (e.g., 272)
- `title`: String
- `description`: Text
- `credits`: Float
- `faculty`: String
- `prerequisitesCodes`: String[] (array of course codes)
- `termAvailability`: String[] (e.g., ["Fall", "Winter"])
- `createdAt`: DateTime
- `updatedAt`: DateTime

**Indexes:**
- Unique constraint on `(subject, number)`
- Index on `(faculty, number)`
- Index on `updatedAt`

### CourseSentiment
Stores sentiment analysis and course metrics.

- `id`: UUID (primary key)
- `courseId`: UUID (foreign key to Course, unique)
- `redditThreadIds`: String[]
- `difficultyAvg`: Float? (1-5 scale)
- `workloadAvg`: Float? (hours per week)
- `gpaEstimate`: Float? (0-4.0 scale)
- `professorMentions`: JSON (map of professor names to sentiment scores)
- `warnings`: String[]
- `lastScrapedAt`: DateTime

**Indexes:**
- Unique on `courseId`
- Index on `lastScrapedAt`

### CourseEmbedding
Stores vector embeddings for semantic search (using pgvector).

- `courseId`: UUID (primary key, foreign key to Course)
- `descriptionVector`: vector(1536)
- `reviewsVector`: vector(1536)
- `createdAt`: DateTime

### Prerequisite
Stores course prerequisite relationships.

- `id`: UUID (primary key)
- `courseId`: UUID (foreign key to Course)
- `requiresId`: UUID (foreign key to Course)
- `createdAt`: DateTime

**Indexes:**
- Unique constraint on `(courseId, requiresId)`
- Index on `courseId`
- Index on `requiresId`

## 🚀 Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL connection string:

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/bear_tracks?schema=public"
```

### 3. Ensure PostgreSQL with pgvector is running

**Option A: Using Docker Compose (from root)**
```bash
# From the repository root
docker-compose up -d postgres
```

**Option B: Local PostgreSQL**
```bash
# macOS (using Homebrew)
brew install postgresql@15 pgvector
brew services start postgresql@15

# Create database
createdb bear_tracks

# Enable pgvector extension
psql bear_tracks -c "CREATE EXTENSION vector;"
```

### 4. Run migrations

```bash
npm run migrate
```

This will:
- Enable the pgvector extension
- Create all tables
- Set up indexes and constraints

### 5. Seed the database

```bash
npm run seed
```

This will populate the database with:
- 30 CMPUT courses (Computer Science)
- 25 MATH courses (Mathematics)
- 15 STAT courses (Statistics)
- Realistic sentiment data for each course
- Prerequisite relationships

## 📝 Commands

### Development

| Command | Description |
|---------|-------------|
| `npm run migrate` | Run database migrations (creates/updates schema) |
| `npm run seed` | Seed database with course data |
| `npm run studio` | Open Prisma Studio (visual database editor) |
| `npm run db:generate` | Generate Prisma client (run after schema changes) |
| `npm run db:push` | Push schema changes without migrations (dev only) |
| `npm run db:reset` | **⚠️ Reset database (deletes all data!)** |

### Full Commands

```bash
# Generate Prisma client (after schema.prisma changes)
npm run db:generate

# Push schema to database (development only, no migration files)
npm run db:push

# Create and run a new migration
npm run db:migrate

# Open Prisma Studio (database GUI)
npm run db:studio

# Seed the database
npm run db:seed

# Reset database (WARNING: deletes all data)
npm run db:reset
```

## 🌱 Seeding

The seed script (`src/seed.ts`) populates the database with realistic course data.

### What Gets Seeded

1. **Courses** (70 total):
   - CMPUT 101, 174, 175, 201, 204, 229, 272, 274, 301, 304, 325, 328, 340, 350, 365, 366, 367, 401, 412, 414, 415, 416, 424, 428, 429, 455, 466, 467, 474, 496
   - MATH 100, 101, 102, 114, 115, 125, 127, 134, 136, 144, 146, 154, 156, 201, 209, 214, 215, 225, 227, 228, 241, 253, 281, 311, 322
   - STAT 141, 151, 235, 252, 265, 266, 268, 321, 330, 332, 337, 350, 361, 371, 378

2. **Sentiment Data**:
   - Difficulty ratings (1-5 scale, normally distributed)
   - Workload estimates (5-20 hours/week)
   - GPA estimates (2.3-3.8 scale)
   - Professor mentions with sentiment scores
   - Course warnings (e.g., "heavy math", "lots of coding")

3. **Prerequisites**:
   - Automatically parsed from course descriptions
   - Linked relationships (e.g., CMPUT 101 → 174 → 272)

### Seed Features

- **Idempotent**: Can be run multiple times safely (uses upsert)
- **Realistic data**: Based on actual UAlberta course catalog
- **Error handling**: Continues on individual failures
- **Progress logging**: Shows detailed progress and summary

### Running the Seed

```bash
# Full run (recommended)
npm run seed

# Or using tsx directly
npx tsx src/seed.ts
```

**Expected output:**
```
[2024-01-01T12:00:00.000Z] ℹ️ Starting database seed...
[2024-01-01T12:00:00.100Z] ℹ️ Seeding 70 courses
[2024-01-01T12:00:00.200Z] ✅ Created CMPUT 101: Introduction to Computing
[2024-01-01T12:00:00.250Z] ✅ Created CMPUT 174: Introduction to the Foundations of Computation I
...
[2024-01-01T12:00:10.000Z] ℹ️ Creating prerequisite relationships...
[2024-01-01T12:00:12.000Z] ✅ Created 45 prerequisite relationships

=== Seed Summary ===
[2024-01-01T12:00:12.100Z] ✅ Courses created: 70
[2024-01-01T12:00:12.100Z] ✅ Courses updated: 0
[2024-01-01T12:00:12.100Z] ✅ Sentiments created: 70
[2024-01-01T12:00:12.100Z] ✅ Prerequisites created: 45
[2024-01-01T12:00:12.100Z] ✅ Errors: 0

[2024-01-01T12:00:12.100Z] ✅ Success rate: 70/70 (100.0%)
```

## 🔄 Migrations

### Creating a Migration

When you modify `prisma/schema.prisma`:

```bash
# Create and apply migration
npm run migrate

# You'll be prompted to name the migration
# Example: "add_course_ratings"
```

This will:
1. Generate SQL migration file in `prisma/migrations/`
2. Apply the migration to your database
3. Regenerate Prisma client

### Migration Files

Migrations are stored in `prisma/migrations/`:

```
prisma/migrations/
├── 20240101000000_initial_setup/
│   └── migration.sql
└── migration_lock.toml
```

### Applying Migrations

```bash
# Apply pending migrations
npm run migrate

# In production (without prompts)
npx prisma migrate deploy
```

### Resetting Database

**⚠️ WARNING: This deletes all data!**

```bash
npm run db:reset
```

This will:
1. Drop the database
2. Recreate it
3. Run all migrations
4. Run seed script (if configured)

## 🛠️ Troubleshooting

### "Extension 'vector' does not exist"

The pgvector extension is not installed. Solutions:

**Docker:**
```bash
# Use the ankane/pgvector image (already in docker-compose.yml)
docker-compose up -d postgres
```

**Local PostgreSQL:**
```bash
# macOS
brew install pgvector

# Then enable in database
psql bear_tracks -c "CREATE EXTENSION vector;"
```

### "Database 'bear_tracks' does not exist"

Create the database:

```bash
createdb bear_tracks

# Or using psql
psql -U postgres -c "CREATE DATABASE bear_tracks;"
```

### "P2002: Unique constraint failed"

The seed script is idempotent, but if you're seeing constraint errors:

1. Check your data for duplicates
2. Reset the database: `npm run db:reset`
3. Re-run seed: `npm run seed`

### Connection refused (ECONNREFUSED)

Ensure PostgreSQL is running:

```bash
# Docker
docker-compose up -d postgres

# Local (macOS)
brew services start postgresql@15

# Check connection
psql -U postgres -d bear_tracks -c "SELECT 1;"
```

### Prisma Client not found

Regenerate the Prisma client:

```bash
npm run db:generate
```

### Slow seed performance

The seed script includes small delays to avoid overwhelming the database. For faster seeding:

1. Reduce the delay in `src/seed.ts` (line with `setTimeout`)
2. Use `db:push` instead of migrations for development:
   ```bash
   npm run db:push
   npm run seed
   ```

## 📚 Additional Resources

- [Prisma Documentation](https://www.prisma.io/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Prisma Schema Reference](https://www.prisma.io/docs/reference/api-reference/prisma-schema-reference)

## 🔗 Usage in Other Packages

Import the Prisma client in other packages:

```typescript
import { prisma, Course, CourseSentiment } from '@bear-tracks/database';

// Query courses
const courses = await prisma.course.findMany({
  where: { subject: 'CMPUT' },
  include: { sentiment: true },
});
```

---

Built with ❤️ for students, by students
