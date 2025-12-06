# Bear Tracks Database Design Document

Complete database schema and implementation details for the Course Insight Platform.

## Table of Contents

1. [Overview](#overview)
2. [Schema Design](#schema-design)
3. [Relationships](#relationships)
4. [Indexes and Performance](#indexes-and-performance)
5. [Data Population](#data-population)
6. [File Structure](#file-structure)
7. [Usage Examples](#usage-examples)

## Overview

The Bear Tracks database is designed to store and efficiently query course information, sentiment analysis data, and prerequisite relationships for University of Alberta courses. It uses PostgreSQL with the pgvector extension for semantic search capabilities.

### Key Features

- **UUID Primary Keys**: Better for distributed systems and security
- **Vector Search**: Semantic course discovery using pgvector
- **Normalized Schema**: Efficient storage with proper relationships
- **Comprehensive Indexing**: Optimized for common query patterns
- **Type Safety**: Full TypeScript support via Prisma

## Schema Design

### 1. Course Model

The core entity representing a university course.

```prisma
model Course {
  id                 String   @id @default(uuid())
  subject            String   // "CMPUT", "MATH", "STAT"
  number             Int      // 272, 301, etc.
  title              String
  description        String   @db.Text
  credits            Float    // 3.0, 4.5, etc.
  faculty            String   // "Science", "Engineering", "Arts"
  prerequisitesCodes String[] // ["CMPUT 201", "MATH 101"]
  termAvailability   String[] // ["Fall", "Winter"]
  updatedAt          DateTime @updatedAt
  createdAt          DateTime @default(now())

  sentiment      CourseSentiment?
  embedding      CourseEmbedding?
  prerequisites  Prerequisite[]   @relation("CoursePrerequisites")
  requiredBy     Prerequisite[]   @relation("RequiredBy")

  @@unique([subject, number])
  @@index([faculty, number])
  @@index([updatedAt])
}
```

**Design Decisions:**

- **UUID ID**: Prevents enumeration attacks, better for distributed systems
- **Separate subject/number**: Enables filtering by department (e.g., all CMPUT courses)
- **prerequisitesCodes**: Denormalized for quick display, normalized via Prerequisite table
- **termAvailability**: Array for flexible term offerings
- **Unique constraint**: Prevents duplicate courses (subject + number)

### 2. CourseSentiment Model

Stores aggregated sentiment and metrics for courses.

```prisma
model CourseSentiment {
  id                 String   @id @default(uuid())
  courseId           String   @unique
  course             Course   @relation(fields: [courseId], references: [id])

  redditThreadIds    String[]          // Links to source data
  difficultyAvg      Float?            // 1.0 - 5.0 scale
  workloadAvg        Float?            // Hours per week
  gpaEstimate        Float?            // 0.0 - 4.0 scale
  professorMentions  Json?             // {"Smith, J.": 4.2, "Doe, A.": 3.8}
  warnings           String[]          // ["heavy math", "time-consuming"]
  lastScrapedAt      DateTime

  @@index([lastScrapedAt])
}
```

**Design Decisions:**

- **One-to-one with Course**: Each course has at most one sentiment record
- **Nullable metrics**: Allows partial data (e.g., only difficulty rated)
- **JSON for professors**: Flexible structure for variable number of professors
- **lastScrapedAt index**: Efficiently find stale data for re-scraping
- **Array fields**: PostgreSQL arrays for multi-valued attributes

### 3. CourseEmbedding Model

Stores vector embeddings for semantic search.

```prisma
model CourseEmbedding {
  courseId          String   @id
  course            Course   @relation(fields: [courseId], references: [id])

  descriptionVector Unsupported("vector(1536)")  // Course description embedding
  reviewsVector     Unsupported("vector(1536)")  // Reviews/sentiment embedding
  createdAt         DateTime
}
```

**Design Decisions:**

- **Two vectors**: Separate embeddings for description vs. reviews
- **1536 dimensions**: OpenAI ada-002 embedding size
- **pgvector type**: Enables cosine similarity search
- **courseId as PK**: One-to-one relationship with Course

### 4. Prerequisite Model

Represents course prerequisite relationships.

```prisma
model Prerequisite {
  id             String   @id @default(uuid())
  courseId       String   // The course that has prerequisites
  requiresId     String   // The prerequisite course
  course         Course   @relation("CoursePrerequisites", ...)
  requiredCourse Course   @relation("RequiredBy", ...)
  createdAt      DateTime

  @@unique([courseId, requiresId])
  @@index([courseId])
  @@index([requiresId])
}
```

**Design Decisions:**

- **Junction table**: Many-to-many relationship between courses
- **Named relations**: Distinguishes "has prerequisite" from "is prerequisite for"
- **Unique constraint**: Prevents duplicate prerequisite links
- **Dual indexes**: Fast queries in both directions

## Relationships

### Entity-Relationship Diagram

```
┌─────────────┐
│   Course    │
│             │
│ id (PK)     │◄─────┐
│ subject     │      │
│ number      │      │
│ title       │      │
│ ...         │      │
└─────────────┘      │
       │             │
       │ 1           │
       │             │
       │ 1           │ N
       ▼             │
┌─────────────┐      │
│CourseSenti..│      │
│             │      │
│ id (PK)     │      │
│ courseId(FK)│──────┘
│ difficulty  │
│ workload    │
│ ...         │
└─────────────┘

       │
       │ 1
       │
       │ 1
       ▼
┌─────────────┐
│CourseEmbed..│
│             │
│ courseId(PK)│
│ descVector  │
│ reviewsVec  │
└─────────────┘

┌─────────────┐      ┌─────────────┐
│   Course    │      │Prerequisite │
│             │◄─────│             │
│ id (PK)     │ N    │ id (PK)     │
│             │      │ courseId(FK)│
│             │      │ requiresId  │
│             │      │  (FK)       │
└─────────────┘      └─────────────┘
       ▲                    │
       │                    │
       └────────────────────┘
              N
```

### Relationship Patterns

1. **Course ↔ CourseSentiment**: One-to-one (optional)
   - Each course may have sentiment data
   - Sentiment always belongs to exactly one course

2. **Course ↔ CourseEmbedding**: One-to-one (optional)
   - Each course may have embeddings
   - Embedding always belongs to exactly one course

3. **Course ↔ Prerequisite**: Many-to-many (self-referential)
   - A course can have multiple prerequisites
   - A course can be prerequisite for multiple other courses

## Indexes and Performance

### Index Strategy

```sql
-- Course indexes
CREATE UNIQUE INDEX ON courses (subject, number);  -- Unique constraint
CREATE INDEX idx_faculty_number ON courses (faculty, number);
CREATE INDEX idx_updated_at ON courses (updatedAt);

-- CourseSentiment indexes
CREATE UNIQUE INDEX ON course_sentiments (course_id);  -- One-to-one
CREATE INDEX idx_last_scraped ON course_sentiments (lastScrapedAt);

-- Prerequisite indexes
CREATE INDEX idx_prereq_course ON prerequisites (course_id);
CREATE INDEX idx_prereq_requires ON prerequisites (requires_id);
CREATE UNIQUE INDEX ON prerequisites (course_id, requires_id);

-- Vector indexes (created by pgvector)
CREATE INDEX ON course_embeddings USING ivfflat (descriptionVector);
CREATE INDEX ON course_embeddings USING ivfflat (reviewsVector);
```

### Query Optimization

**Common Query Patterns:**

1. **List courses by subject**
   ```sql
   SELECT * FROM courses WHERE subject = 'CMPUT';
   -- Uses: unique_course index (partial match)
   ```

2. **Find courses by faculty and level**
   ```sql
   SELECT * FROM courses WHERE faculty = 'Science' AND number >= 300;
   -- Uses: idx_faculty_number index
   ```

3. **Find stale sentiment data**
   ```sql
   SELECT * FROM course_sentiments
   WHERE lastScrapedAt < NOW() - INTERVAL '7 days';
   -- Uses: idx_last_scraped index
   ```

4. **Get course with all related data**
   ```sql
   SELECT c.*, s.*, ce.*
   FROM courses c
   LEFT JOIN course_sentiments s ON c.id = s.course_id
   LEFT JOIN course_embeddings ce ON c.id = ce.course_id
   WHERE c.subject = 'CMPUT' AND c.number = 272;
   -- Uses: unique_course index
   ```

5. **Find similar courses (vector search)**
   ```sql
   SELECT c.*, ce.descriptionVector <=> $1::vector AS distance
   FROM courses c
   JOIN course_embeddings ce ON c.id = ce.course_id
   ORDER BY distance
   LIMIT 10;
   -- Uses: ivfflat vector index
   ```

## Data Population

### Seed Script Architecture

```
src/seed.ts
├── Import course data from data/courses.ts
├── For each course:
│   ├── Parse prerequisites from description
│   ├── Determine faculty from subject
│   ├── Set term availability
│   ├── Upsert course record
│   ├── Generate sentiment data
│   └── Upsert sentiment record
└── Create prerequisite relationships
```

### Sentiment Generation Algorithm

```typescript
// Difficulty: normally distributed, adjusted by level
const difficultyMean = isIntro ? 2.5 : isAdvanced ? 3.8 : 3.2;
const difficulty = generateNormalRandom(difficultyMean, 0.6, 1.5, 4.5);

// Workload: normally distributed, higher for advanced courses
const workloadMean = isIntro ? 10 : isAdvanced ? 15 : 12;
const workload = generateNormalRandom(workloadMean, 3, 5, 20);

// GPA: normally distributed, slightly higher for intro courses
const gpaMean = isIntro ? 3.2 : isAdvanced ? 2.9 : 3.0;
const gpa = generateNormalRandom(gpaMean, 0.4, 2.3, 3.8);
```

### Prerequisite Parsing

```typescript
// Extract course codes using regex
const courseCodePattern = /\b([A-Z]{2,5})\s+(\d{3})\b/g;
const prerequisites = description.matchAll(courseCodePattern);

// Example:
// "Prerequisite: CMPUT 175 and MATH 101"
// Extracts: ["CMPUT 175", "MATH 101"]
```

## File Structure

```
packages/database/
├── prisma/
│   ├── schema.prisma              # Prisma schema definition
│   └── migrations/
│       ├── migration_lock.toml    # Migration lock file
│       └── 20240101000000_initial_setup/
│           └── migration.sql      # Initial migration
├── src/
│   ├── index.ts                   # Prisma client export
│   ├── seed.ts                    # Main seed script
│   ├── data/
│   │   └── courses.ts             # Course data definitions
│   └── utils/
│       └── helpers.ts             # Utility functions
├── package.json                   # Scripts and dependencies
├── .env.example                   # Environment template
├── README.md                      # Full documentation
└── QUICK_START.md                 # Quick setup guide
```

## Usage Examples

### Basic Queries

```typescript
import { prisma, Course } from '@bear-tracks/database';

// Get all CMPUT courses with sentiment
const courses = await prisma.course.findMany({
  where: { subject: 'CMPUT' },
  include: { sentiment: true },
  orderBy: { number: 'asc' },
});

// Find difficult courses
const difficultCourses = await prisma.course.findMany({
  where: {
    sentiment: {
      difficultyAvg: { gte: 4.0 },
    },
  },
  include: { sentiment: true },
});

// Get course with prerequisites
const course = await prisma.course.findUnique({
  where: { unique_course: { subject: 'CMPUT', number: 272 } },
  include: {
    sentiment: true,
    prerequisites: {
      include: { requiredCourse: true },
    },
  },
});
```

### Advanced Queries

```typescript
// Find courses by multiple subjects
const courses = await prisma.course.findMany({
  where: {
    subject: { in: ['CMPUT', 'MATH', 'STAT'] },
    number: { gte: 300 },
  },
});

// Find courses with good GPA and low workload
const easyCourses = await prisma.course.findMany({
  where: {
    sentiment: {
      gpaEstimate: { gte: 3.5 },
      workloadAvg: { lte: 10 },
    },
  },
  include: { sentiment: true },
});

// Get prerequisite chain
async function getPrerequisiteChain(courseId: string) {
  const prerequisites = await prisma.prerequisite.findMany({
    where: { courseId },
    include: { requiredCourse: true },
  });

  const chains = [];
  for (const prereq of prerequisites) {
    const subchain = await getPrerequisiteChain(prereq.requiresId);
    chains.push([prereq.requiredCourse, ...subchain]);
  }
  return chains;
}

// Vector similarity search (requires raw SQL)
const similarCourses = await prisma.$queryRaw`
  SELECT c.*,
         ce.descriptionVector <=> ${embedding}::vector AS similarity
  FROM courses c
  JOIN course_embeddings ce ON c.id = ce.course_id
  ORDER BY similarity
  LIMIT 10
`;
```

### Aggregations

```typescript
// Average difficulty by faculty
const avgDifficulty = await prisma.course.groupBy({
  by: ['faculty'],
  _avg: {
    sentiment: {
      difficultyAvg: true,
    },
  },
});

// Count courses by subject
const counts = await prisma.course.groupBy({
  by: ['subject'],
  _count: true,
  orderBy: { _count: { subject: 'desc' } },
});
```

## Performance Considerations

### Best Practices

1. **Use select to limit fields**
   ```typescript
   const courses = await prisma.course.findMany({
     select: { id: true, subject: true, number: true, title: true },
   });
   ```

2. **Batch operations when possible**
   ```typescript
   await prisma.course.createMany({
     data: courses,
     skipDuplicates: true,
   });
   ```

3. **Use transactions for consistency**
   ```typescript
   await prisma.$transaction([
     prisma.course.create({ data: courseData }),
     prisma.courseSentiment.create({ data: sentimentData }),
   ]);
   ```

4. **Pagination for large datasets**
   ```typescript
   const courses = await prisma.course.findMany({
     skip: page * pageSize,
     take: pageSize,
   });
   ```

### Scaling Considerations

- **Read replicas**: Use for heavy read workloads
- **Connection pooling**: Use PgBouncer for many connections
- **Vector index tuning**: Adjust `lists` parameter for ivfflat index
- **Materialized views**: For complex aggregations
- **Partitioning**: For very large course datasets

---

**Document Version**: 1.0
**Last Updated**: 2024-01-01
**Schema Version**: 20240101000000_initial_setup
