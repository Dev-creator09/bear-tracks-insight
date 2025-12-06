# @bear-tracks/types

Shared Zod schemas, TypeScript types, and API client for the Bear Tracks Course Insight Platform.

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Development](#development)
- [Schemas](#schemas)
- [API Client](#api-client)
- [Examples](#examples)
- [Error Handling](#error-handling)
- [Type Safety](#type-safety)

## 🎯 Overview

This package provides:
- **Zod Schemas**: Runtime validation for all API data
- **TypeScript Types**: Full type safety across the stack
- **API Client**: Type-safe HTTP client for backend communication
- **Contract Validation**: Ensures frontend/backend compatibility

## 📦 Installation

```bash
npm install @bear-tracks/types
```

## 🔧 Development

### Building the Package

The package is written in TypeScript and needs to be compiled before use.

```bash
# Build once
npm run build

# Watch mode (rebuilds on file changes)
npm run dev

# Type check only (no output)
npm run typecheck

# Clean build artifacts
npm run clean
```

### Project Structure

```
packages/types/
├── src/
│   ├── index.ts          # Main entry point (exports all)
│   ├── schemas.ts        # Zod schemas and types
│   ├── client.ts         # API client implementation
│   ├── course.ts         # Legacy course schemas
│   ├── api.ts            # Legacy API schemas
│   └── common.ts         # Legacy common schemas
├── dist/                 # Compiled output (generated)
│   ├── index.js
│   ├── index.d.ts
│   └── ...
├── tsconfig.json         # TypeScript configuration
└── package.json
```

### TypeScript Configuration

The package is compiled with:
- **Target**: ES2020
- **Module**: CommonJS
- **Strict mode**: Enabled
- **Declaration files**: Generated (.d.ts)
- **Source maps**: Generated

### Using in Development

When developing locally in the monorepo, the package will be automatically linked via npm workspaces.

```bash
# From the repository root
npm install

# Build the types package
npm run build --filter=@bear-tracks/types

# Or build all packages
npm run build
```

## 📚 Schemas

All schemas are defined using Zod and automatically generate TypeScript types.

### Course Schemas

```typescript
import { CourseSchema, Course } from '@bear-tracks/types';

// Validate course data
const courseData = CourseSchema.parse({
  id: 'uuid',
  subject: 'CMPUT',
  number: 272,
  title: 'Formal Systems',
  description: 'Logic and proofs',
  credits: 3.0,
  faculty: 'Science',
  prerequisiteCodes: ['CMPUT 175'],
  termAvailability: ['Fall', 'Winter'],
  createdAt: new Date(),
  updatedAt: new Date(),
});

// Type-safe course object
const course: Course = courseData;
```

### Sentiment Schemas

```typescript
import { CourseSentimentSchema, CourseSentiment } from '@bear-tracks/types';

const sentiment: CourseSentiment = {
  id: 'uuid',
  courseId: 'course-uuid',
  redditThreadIds: ['abc123'],
  difficultyAvg: 3.5,
  workloadAvg: 12.0,
  gpaEstimate: 3.2,
  professorMentions: {
    'Smith, J.': 4.2,
    'Doe, A.': 3.8,
  },
  warnings: ['heavy math', 'lots of coding'],
  lastScrapedAt: new Date(),
};
```

### Search Schemas

```typescript
import { SearchQuerySchema, SearchQuery } from '@bear-tracks/types';

const query: SearchQuery = {
  query: 'machine learning courses',
  filters: {
    subject: 'CMPUT',
    minGpa: 3.0,
    maxDifficulty: 3.5,
  },
  limit: 10,
};
```

## 🌐 API Client

Type-safe HTTP client with automatic validation and error handling.

### Basic Usage

```typescript
import { createBearTracksClient } from '@bear-tracks/types';

// Create client instance
const client = createBearTracksClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key', // Optional, for admin endpoints
  timeout: 30000,
  retries: 3,
});
```

### Get Courses

```typescript
// List courses with pagination and filters
const { courses, nextCursor, hasMore } = await client.getCourses({
  limit: 50,
  faculty: 'Science',
  subject: 'CMPUT',
  minGpa: 3.0,
});

console.log(`Found ${courses.length} courses`);
console.log(`Has more: ${hasMore}`);

// Get next page
if (hasMore && nextCursor) {
  const nextPage = await client.getCourses({
    cursor: nextCursor,
    limit: 50,
  });
}
```

### Get Course Detail

```typescript
// Get detailed course information
const courseDetail = await client.getCourseDetail('CMPUT', 272);

console.log(`Course: ${courseDetail.subject} ${courseDetail.number}`);
console.log(`Title: ${courseDetail.title}`);
console.log(`Difficulty: ${courseDetail.sentiment?.difficultyAvg || 'N/A'}`);
console.log(`Prerequisites: ${courseDetail.prerequisites.length}`);
console.log(`Required by: ${courseDetail.requiredBy.length}`);
```

### Semantic Search

```typescript
// Search for courses
const results = await client.searchCourses({
  query: 'machine learning with good ratings',
  filters: {
    faculty: 'Science',
    minGpa: 3.5,
  },
  limit: 10,
});

for (const result of results) {
  console.log(`${result.subject} ${result.number}: ${result.title}`);
  console.log(`Relevance: ${(result.relevanceScore * 100).toFixed(1)}%`);
  console.log(`Reasoning: ${result.reasoning}`);
}
```

### Get Prerequisite Tree

```typescript
// Get prerequisite tree
const tree = await client.getPrerequisiteTree('CMPUT', 301, 5);

// Recursive tree structure
function printTree(node: PrerequisiteNode, indent = 0) {
  console.log(' '.repeat(indent) + `${node.course.subject} ${node.course.number}`);
  for (const child of node.children) {
    printTree(child, indent + 2);
  }
}

printTree(tree);
```

### Admin: Trigger Scrape

```typescript
// Trigger scrape job (requires API key)
const job = await client.triggerScrape({
  subject: 'CMPUT',
  number: 272,
  term: 'Fall 2024',
  force: false,
});

console.log(`Job ID: ${job.jobId}`);
console.log(`Status: ${job.status}`);
```

### Health Check

```typescript
// Check API health
const health = await client.healthCheck();

console.log(`Status: ${health.status}`);
console.log(`Database: ${health.database}`);
console.log(`Redis: ${health.redis}`);
```

## 🚨 Error Handling

The client provides specific error types for different scenarios.

### Error Types

```typescript
import {
  BearTracksApiClient,
  BearTracksApiError,
  ValidationError,
  NotFoundError,
  UnauthorizedError,
  RateLimitError,
} from '@bear-tracks/types';

const client = createBearTracksClient({ baseUrl: 'http://localhost:8000' });

try {
  const course = await client.getCourseDetail('CMPUT', 999);
} catch (error) {
  if (error instanceof NotFoundError) {
    console.error('Course not found');
  } else if (error instanceof ValidationError) {
    console.error('Invalid request:', error.details);
  } else if (error instanceof UnauthorizedError) {
    console.error('Authentication required');
  } else if (error instanceof RateLimitError) {
    console.error('Rate limit exceeded');
  } else if (error instanceof BearTracksApiError) {
    console.error(`API error: ${error.code} - ${error.message}`);
  }
}
```

### Global Error Handler

```typescript
const client = createBearTracksClient({
  baseUrl: 'http://localhost:8000',
  onError: (error) => {
    console.error(`[API Error] ${error.code}: ${error.message}`);
    // Log to monitoring service
  },
});
```

## 🔒 Type Safety

All API responses are validated at runtime and typed.

### Validation Example

```typescript
import { CourseWithSentimentSchema } from '@bear-tracks/types';

// Runtime validation ensures data matches schema
async function fetchCourses(url: string) {
  const response = await fetch(url);
  const data = await response.json();

  // Validate response
  const courses = data.courses.map((course: unknown) =>
    CourseWithSentimentSchema.parse(course)
  );

  // Now TypeScript knows exact types
  for (const course of courses) {
    console.log(course.title); // ✅ Type-safe
    console.log(course.invalidField); // ❌ TypeScript error
  }
}
```

### Type Inference

```typescript
import type { Course, CourseSentiment } from '@bear-tracks/types';

// Function with typed parameters
function analyzeCourse(course: Course, sentiment: CourseSentiment | null) {
  if (sentiment) {
    const difficulty = sentiment.difficultyAvg ?? 0;
    const workload = sentiment.workloadAvg ?? 0;

    return {
      course: `${course.subject} ${course.number}`,
      difficulty,
      workload,
      recommended: difficulty < 3.5 && workload < 12,
    };
  }

  return null;
}
```

## 📖 Examples

### Cursor-Based Pagination

```typescript
async function fetchAllCourses(client: BearTracksApiClient) {
  const allCourses = [];
  let cursor: string | null = null;

  do {
    const { courses, nextCursor, hasMore } = await client.getCourses({
      cursor: cursor || undefined,
      limit: 100,
    });

    allCourses.push(...courses);
    cursor = hasMore ? nextCursor : null;

    console.log(`Fetched ${courses.length} courses, total: ${allCourses.length}`);
  } while (cursor);

  return allCourses;
}
```

### Find Easy Courses

```typescript
async function findEasyCourses(
  client: BearTracksApiClient,
  subject?: string
) {
  const { courses } = await client.getCourses({
    subject,
    maxDifficulty: 3.0,
    minGpa: 3.5,
    limit: 100,
  });

  return courses
    .filter((c) => c.sentiment?.workloadAvg && c.sentiment.workloadAvg < 10)
    .sort((a, b) => (a.sentiment?.gpaEstimate ?? 0) - (b.sentiment?.gpaEstimate ?? 0));
}
```

### Build Course Dependency Graph

```typescript
async function buildDependencyGraph(
  client: BearTracksApiClient,
  subject: string,
  number: number
) {
  const tree = await client.getPrerequisiteTree(subject, number, 10);

  const graph = new Map<string, string[]>();

  function traverse(node: PrerequisiteNode) {
    const key = `${node.course.subject} ${node.course.number}`;
    const prereqs = node.children.map(
      (child) => `${child.course.subject} ${child.course.number}`
    );

    graph.set(key, prereqs);

    for (const child of node.children) {
      traverse(child);
    }
  }

  traverse(tree);
  return graph;
}
```

### Smart Search with Filters

```typescript
async function smartSearch(
  client: BearTracksApiClient,
  query: string,
  options?: {
    difficulty?: 'easy' | 'medium' | 'hard';
    workload?: 'light' | 'moderate' | 'heavy';
  }
) {
  const filters: any = {};

  if (options?.difficulty === 'easy') {
    filters.maxDifficulty = 3.0;
  } else if (options?.difficulty === 'hard') {
    filters.minGpa = 2.5; // Harder courses often have lower GPAs
  }

  const results = await client.searchCourses({
    query,
    filters,
    limit: 20,
  });

  return results.filter((r) => {
    if (options?.workload === 'light') {
      return (r.sentiment?.workloadAvg ?? 99) < 10;
    } else if (options?.workload === 'heavy') {
      return (r.sentiment?.workloadAvg ?? 0) > 15;
    }
    return true;
  });
}
```

## 🔧 Advanced Configuration

### Custom Timeout and Retries

```typescript
const client = createBearTracksClient({
  baseUrl: 'http://localhost:8000',
  timeout: 60000, // 60 seconds
  retries: 5, // Retry up to 5 times
});
```

### React Hook Example

```typescript
import { useState, useEffect } from 'react';
import { createBearTracksClient, Course } from '@bear-tracks/types';

const client = createBearTracksClient({ baseUrl: process.env.NEXT_PUBLIC_API_URL! });

export function useCourses(subject?: string) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchCourses() {
      try {
        setLoading(true);
        const { courses } = await client.getCourses({ subject, limit: 50 });
        setCourses(courses);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    }

    fetchCourses();
  }, [subject]);

  return { courses, loading, error };
}
```

## 📝 Available Schemas

- `CourseSchema` - Course information
- `CourseSentimentSchema` - Sentiment and metrics
- `CourseWithSentimentSchema` - Course with optional sentiment
- `CourseSearchResultSchema` - Search result with relevance
- `PaginationParamsSchema` - Pagination parameters
- `PaginationMetaSchema` - Pagination metadata
- `CourseFiltersSchema` - Filtering options
- `SearchQuerySchema` - Search query
- `PrerequisiteNodeSchema` - Recursive prerequisite tree
- `ScrapeJobRequestSchema` - Scrape job request
- `ScrapeJobResponseSchema` - Scrape job response
- `HealthResponseSchema` - Health check response
- `ErrorResponseSchema` - Error response
- `ValidationErrorSchema` - Validation error details

## 🔗 Related Packages

- `@bear-tracks/database` - Prisma database client
- `apps/web` - Next.js frontend using these types
- `apps/api` - FastAPI backend implementing these contracts

---

Built with ❤️ for type-safe development
