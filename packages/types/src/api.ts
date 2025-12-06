import { z } from 'zod';

// API Response schemas
export const apiErrorSchema = z.object({
  message: z.string(),
  code: z.string().optional(),
  details: z.record(z.unknown()).optional(),
});

export const paginationSchema = z.object({
  page: z.number().int().min(1).default(1),
  limit: z.number().int().min(1).max(100).default(20),
  total: z.number().int(),
  totalPages: z.number().int(),
});

export const paginatedResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    data: z.array(dataSchema),
    pagination: paginationSchema,
  });

export const healthCheckSchema = z.object({
  status: z.enum(['healthy', 'unhealthy']),
  database: z.string(),
  redis: z.string(),
  timestamp: z.date().optional(),
});

// Search and filter schemas
export const courseSearchSchema = z.object({
  query: z.string().optional(),
  department: z.string().optional(),
  minCredits: z.number().int().min(1).optional(),
  maxCredits: z.number().int().max(12).optional(),
  minLevel: z.number().int().min(100).optional(),
  maxLevel: z.number().int().max(999).optional(),
  minRating: z.number().min(0).max(5).optional(),
  sortBy: z.enum(['code', 'name', 'credits', 'rating', 'createdAt']).default('code'),
  sortOrder: z.enum(['asc', 'desc']).default('asc'),
});

// Type exports
export type ApiError = z.infer<typeof apiErrorSchema>;
export type Pagination = z.infer<typeof paginationSchema>;
export type HealthCheck = z.infer<typeof healthCheckSchema>;
export type CourseSearch = z.infer<typeof courseSearchSchema>;

export type PaginatedResponse<T> = {
  data: T[];
  pagination: Pagination;
};
