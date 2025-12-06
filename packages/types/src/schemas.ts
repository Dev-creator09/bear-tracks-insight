/**
 * Comprehensive Zod schemas for Bear Tracks API contracts
 * These schemas ensure type safety across frontend and backend
 */

import { z } from 'zod';

// ============================================================================
// Course Schemas
// ============================================================================

export const CourseSchema = z.object({
  id: z.string().uuid(),
  subject: z.string().min(2).max(10), // e.g., "CMPUT", "MATH"
  number: z.number().int().min(100).max(999),
  title: z.string().min(1).max(255),
  description: z.string(),
  credits: z.number().positive(),
  faculty: z.string().min(1).max(100),
  prerequisiteCodes: z.array(z.string()), // ["CMPUT 201", "MATH 101"]
  termAvailability: z.array(z.string()), // ["Fall", "Winter"]
  updatedAt: z.coerce.date(),
  createdAt: z.coerce.date(),
});

export const CourseSentimentSchema = z.object({
  id: z.string().uuid(),
  courseId: z.string().uuid(),
  redditThreadIds: z.array(z.string()),
  difficultyAvg: z.number().min(1).max(5).nullable().optional(),
  workloadAvg: z.number().min(0).max(40).nullable().optional(), // hours per week
  gpaEstimate: z.number().min(0).max(4).nullable().optional(),
  professorMentions: z.record(z.string(), z.number()).nullable().optional(),
  warnings: z.array(z.string()),
  lastScrapedAt: z.coerce.date(),
});

export const CourseWithSentimentSchema = CourseSchema.extend({
  sentiment: CourseSentimentSchema.nullable(),
});

export const CourseSearchResultSchema = CourseWithSentimentSchema.extend({
  relevanceScore: z.number().min(0).max(1),
  reasoning: z.string().optional(),
});

// ============================================================================
// Pagination Schemas
// ============================================================================

export const PaginationParamsSchema = z.object({
  cursor: z.string().optional(),
  limit: z.number().int().min(1).max(100).default(50),
});

export const PaginationMetaSchema = z.object({
  cursor: z.string().nullable(),
  nextCursor: z.string().nullable(),
  limit: z.number().int(),
  hasMore: z.boolean(),
});

// ============================================================================
// Filter Schemas
// ============================================================================

export const CourseFiltersSchema = z.object({
  faculty: z.string().optional(),
  subject: z.string().optional(),
  minGpa: z.number().min(0).max(4).optional(),
  maxDifficulty: z.number().min(1).max(5).optional(),
  term: z.string().optional(),
});

// ============================================================================
// Search Schemas
// ============================================================================

export const SearchQuerySchema = z.object({
  query: z.string().min(1).max(500),
  filters: CourseFiltersSchema.optional(),
  limit: z.number().int().min(1).max(50).default(10),
});

// ============================================================================
// Prerequisite Schemas
// ============================================================================

// Recursive schema for prerequisite tree
export const PrerequisiteNodeSchema: z.ZodType<{
  course: z.infer<typeof CourseSchema>;
  children: Array<{
    course: z.infer<typeof CourseSchema>;
    children: any[];
  }>;
}> = z.lazy(() =>
  z.object({
    course: CourseSchema,
    children: z.array(PrerequisiteNodeSchema),
  })
);

export const PrerequisiteTreeParamsSchema = z.object({
  subject: z.string().min(2).max(10),
  number: z.number().int().min(100).max(999),
  depth: z.number().int().min(1).max(10).default(5),
});

// ============================================================================
// Scrape Schemas
// ============================================================================

export const ScrapeJobRequestSchema = z.object({
  subject: z.string().min(2).max(10),
  number: z.number().int().min(100).max(999),
  term: z.string().min(1).max(50),
  force: z.boolean().default(false),
});

export const ScrapeJobResponseSchema = z.object({
  jobId: z.string().uuid(),
  status: z.enum(['queued', 'processing', 'completed', 'failed']),
  message: z.string().optional(),
});

// ============================================================================
// Response Schemas
// ============================================================================

export const CourseListResponseSchema = z.object({
  courses: z.array(CourseWithSentimentSchema),
  pagination: PaginationMetaSchema,
});

export const CourseDetailResponseSchema = CourseWithSentimentSchema.extend({
  prerequisites: z.array(
    z.object({
      id: z.string().uuid(),
      course: CourseSchema,
    })
  ),
  requiredBy: z.array(
    z.object({
      id: z.string().uuid(),
      course: CourseSchema,
    })
  ),
});

export const CourseSearchResponseSchema = z.object({
  results: z.array(CourseSearchResultSchema),
  query: z.string(),
  totalResults: z.number().int(),
});

export const PrerequisiteTreeResponseSchema = z.object({
  course: CourseSchema,
  tree: PrerequisiteNodeSchema,
  depth: z.number().int(),
});

// ============================================================================
// Health Check Schemas
// ============================================================================

export const HealthResponseSchema = z.object({
  status: z.enum(['healthy', 'unhealthy', 'degraded']),
  database: z.string(),
  redis: z.string(),
  version: z.string().optional(),
  uptimeSeconds: z.number().optional(),
  timestamp: z.coerce.date().optional(),
});

// ============================================================================
// Error Schemas
// ============================================================================

export const ErrorResponseSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.record(z.any()).optional(),
  path: z.string().optional(),
  timestamp: z.coerce.date().optional(),
});

export const ValidationErrorSchema = ErrorResponseSchema.extend({
  code: z.literal('VALIDATION_ERROR'),
  errors: z.array(
    z.object({
      field: z.string(),
      message: z.string(),
      code: z.string().optional(),
    })
  ),
});

// ============================================================================
// Type Exports
// ============================================================================

export type Course = z.infer<typeof CourseSchema>;
export type CourseSentiment = z.infer<typeof CourseSentimentSchema>;
export type CourseWithSentiment = z.infer<typeof CourseWithSentimentSchema>;
export type CourseSearchResult = z.infer<typeof CourseSearchResultSchema>;

export type PaginationParams = z.infer<typeof PaginationParamsSchema>;
export type PaginationMeta = z.infer<typeof PaginationMetaSchema>;

export type CourseFilters = z.infer<typeof CourseFiltersSchema>;
export type SearchQuery = z.infer<typeof SearchQuerySchema>;

export type PrerequisiteNode = z.infer<typeof PrerequisiteNodeSchema>;
export type PrerequisiteTreeParams = z.infer<typeof PrerequisiteTreeParamsSchema>;

export type ScrapeJobRequest = z.infer<typeof ScrapeJobRequestSchema>;
export type ScrapeJobResponse = z.infer<typeof ScrapeJobResponseSchema>;

export type CourseListResponse = z.infer<typeof CourseListResponseSchema>;
export type CourseDetailResponse = z.infer<typeof CourseDetailResponseSchema>;
export type CourseSearchResponse = z.infer<typeof CourseSearchResponseSchema>;
export type PrerequisiteTreeResponse = z.infer<typeof PrerequisiteTreeResponseSchema>;

export type HealthResponse = z.infer<typeof HealthResponseSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
export type ValidationErrorResponse = z.infer<typeof ValidationErrorSchema>;
