import { z } from 'zod';

// Common utility types and schemas

export const idSchema = z.number().int().positive();

export const timestampSchema = z.object({
  createdAt: z.date(),
  updatedAt: z.date(),
});

export const emailSchema = z.string().email();

export const uuidSchema = z.string().uuid();

// Type exports
export type Id = z.infer<typeof idSchema>;
export type Timestamp = z.infer<typeof timestampSchema>;
