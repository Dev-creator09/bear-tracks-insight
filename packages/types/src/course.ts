import { z } from 'zod';

// Course schemas
export const courseBaseSchema = z.object({
  code: z.string().min(1).max(20),
  name: z.string().min(1).max(255),
  description: z.string().nullable().optional(),
  credits: z.number().int().min(1).max(12),
  department: z.string().min(1).max(100),
  level: z.number().int().min(100).max(999),
});

export const courseCreateSchema = courseBaseSchema;

export const courseUpdateSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().nullable().optional(),
  credits: z.number().int().min(1).max(12).optional(),
  department: z.string().min(1).max(100).optional(),
  level: z.number().int().min(100).max(999).optional(),
});

export const courseSchema = courseBaseSchema.extend({
  id: z.number().int(),
  createdAt: z.date(),
  updatedAt: z.date(),
});

// Course Sentiment schemas
export const courseSentimentSchema = z.object({
  id: z.number().int(),
  courseId: z.number().int(),
  rating: z.number().min(0).max(5),
  difficulty: z.number().min(0).max(5),
  workload: z.number().min(0).max(5),
  sentimentScore: z.number().min(-1).max(1),
  reviewText: z.string().nullable().optional(),
  createdAt: z.date(),
});

export const courseSentimentCreateSchema = z.object({
  courseId: z.number().int(),
  rating: z.number().min(0).max(5),
  difficulty: z.number().min(0).max(5),
  workload: z.number().min(0).max(5),
  sentimentScore: z.number().min(-1).max(1),
  reviewText: z.string().optional(),
});

// Prerequisite schemas
export const prerequisiteSchema = z.object({
  id: z.number().int(),
  courseId: z.number().int(),
  prerequisiteId: z.number().int(),
  isRequired: z.boolean().default(true),
  createdAt: z.date(),
});

export const prerequisiteCreateSchema = z.object({
  courseId: z.number().int(),
  prerequisiteId: z.number().int(),
  isRequired: z.boolean().default(true),
});

// Type exports
export type CourseBase = z.infer<typeof courseBaseSchema>;
export type CourseCreate = z.infer<typeof courseCreateSchema>;
export type CourseUpdate = z.infer<typeof courseUpdateSchema>;
export type Course = z.infer<typeof courseSchema>;

export type CourseSentiment = z.infer<typeof courseSentimentSchema>;
export type CourseSentimentCreate = z.infer<typeof courseSentimentCreateSchema>;

export type Prerequisite = z.infer<typeof prerequisiteSchema>;
export type PrerequisiteCreate = z.infer<typeof prerequisiteCreateSchema>;
