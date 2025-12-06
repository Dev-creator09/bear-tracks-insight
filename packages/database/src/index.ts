import { PrismaClient } from '@prisma/client';

// Export all Prisma types
export * from '@prisma/client';

// Global Prisma instance for singleton pattern
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

// Create Prisma client with logging configuration
export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
  });

// In development, save the client to the global object to prevent multiple instances
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma;

// Export types for convenience
export type { Course, CourseSentiment, CourseEmbedding, Prerequisite } from '@prisma/client';
