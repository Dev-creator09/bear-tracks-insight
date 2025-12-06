/**
 * Type-safe API client for Bear Tracks Course Insight Platform
 * Provides automatic validation, error handling, and TypeScript types
 */

import {
  Course,
  CourseWithSentiment,
  CourseSearchResult,
  PrerequisiteNode,
  PaginationParams,
  CourseFilters,
  SearchQuery,
  ScrapeJobRequest,
  ScrapeJobResponse,
  HealthResponse,
  CourseListResponseSchema,
  CourseDetailResponseSchema,
  CourseSearchResponseSchema,
  PrerequisiteTreeResponseSchema,
  ScrapeJobResponseSchema,
  HealthResponseSchema,
  ErrorResponseSchema,
  CourseDetailResponse,
} from './schemas';

// ============================================================================
// Error Classes
// ============================================================================

export class BearTracksApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'BearTracksApiError';
  }
}

export class ValidationError extends BearTracksApiError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'VALIDATION_ERROR', 400, details);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends BearTracksApiError {
  constructor(message: string) {
    super(message, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

export class UnauthorizedError extends BearTracksApiError {
  constructor(message: string) {
    super(message, 'UNAUTHORIZED', 401);
    this.name = 'UnauthorizedError';
  }
}

export class RateLimitError extends BearTracksApiError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'RATE_LIMIT_EXCEEDED', 429, details);
    this.name = 'RateLimitError';
  }
}

// ============================================================================
// API Client Configuration
// ============================================================================

export interface BearTracksApiClientConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
  retries?: number;
  onError?: (error: BearTracksApiError) => void;
}

// ============================================================================
// API Client
// ============================================================================

export class BearTracksApiClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private retries: number;
  private onError?: (error: BearTracksApiError) => void;

  constructor(config: BearTracksApiClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000; // 30 seconds default
    this.retries = config.retries || 3;
    this.onError = config.onError;
  }

  /**
   * Internal method to make HTTP requests with retries and error handling
   */
  private async request<T>(
    path: string,
    options: RequestInit = {},
    schema?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        const response = await fetch(url, {
          ...options,
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Handle error responses
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          const parsedError = ErrorResponseSchema.safeParse(errorData);

          const error = parsedError.success
            ? parsedError.data
            : { code: 'UNKNOWN_ERROR', message: response.statusText };

          const apiError = this.createError(response.status, error.code, error.message, error.details);

          if (this.onError) {
            this.onError(apiError);
          }

          throw apiError;
        }

        // Parse response
        const data = await response.json();

        // Validate with schema if provided
        if (schema) {
          const result = schema.safeParse(data);
          if (!result.success) {
            throw new ValidationError('Invalid response format', {
              errors: result.error.errors,
            });
          }
          return result.data as T;
        }

        return data as T;
      } catch (error) {
        lastError = error as Error;

        // Don't retry on client errors (4xx) or validation errors
        if (
          error instanceof BearTracksApiError &&
          (error.status >= 400 && error.status < 500)
        ) {
          throw error;
        }

        // Wait before retrying (exponential backoff)
        if (attempt < this.retries - 1) {
          await new Promise((resolve) => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        }
      }
    }

    throw lastError || new Error('Request failed after retries');
  }

  /**
   * Create appropriate error based on status code
   */
  private createError(
    status: number,
    code: string,
    message: string,
    details?: Record<string, any>
  ): BearTracksApiError {
    switch (status) {
      case 400:
        return new ValidationError(message, details);
      case 401:
        return new UnauthorizedError(message);
      case 404:
        return new NotFoundError(message);
      case 429:
        return new RateLimitError(message, details);
      default:
        return new BearTracksApiError(message, code, status, details);
    }
  }

  /**
   * Build query string from parameters
   */
  private buildQueryString(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach((v) => searchParams.append(key, String(v)));
        } else {
          searchParams.append(key, String(value));
        }
      }
    });

    const queryString = searchParams.toString();
    return queryString ? `?${queryString}` : '';
  }

  // ==========================================================================
  // Public API Methods
  // ==========================================================================

  /**
   * Get a paginated list of courses with optional filters
   */
  async getCourses(
    params: Partial<PaginationParams> & CourseFilters = {}
  ): Promise<{
    courses: CourseWithSentiment[];
    nextCursor: string | null;
    hasMore: boolean;
  }> {
    const queryString = this.buildQueryString({
      cursor: params.cursor,
      limit: params.limit,
      faculty: params.faculty,
      subject: params.subject,
      min_gpa: params.minGpa,
      max_difficulty: params.maxDifficulty,
      term: params.term,
    });

    const response = await this.request<{
      courses: CourseWithSentiment[];
      pagination: { nextCursor: string | null; hasMore: boolean };
    }>(
      `/api/v1/courses${queryString}`,
      { method: 'GET' },
      CourseListResponseSchema
    );

    return {
      courses: response.courses,
      nextCursor: response.pagination.nextCursor,
      hasMore: response.pagination.hasMore,
    };
  }

  /**
   * Get detailed information about a specific course
   */
  async getCourseDetail(
    subject: string,
    number: number
  ): Promise<CourseDetailResponse> {
    return this.request(
      `/api/v1/courses/${encodeURIComponent(subject)}/${number}`,
      { method: 'GET' },
      CourseDetailResponseSchema
    );
  }

  /**
   * Search for courses using semantic search
   */
  async searchCourses(query: SearchQuery): Promise<CourseSearchResult[]> {
    const response = await this.request<{ results: CourseSearchResult[] }>(
      '/api/v1/courses/search',
      {
        method: 'POST',
        body: JSON.stringify({
          query: query.query,
          filters: query.filters,
          limit: query.limit,
        }),
      },
      CourseSearchResponseSchema
    );

    return response.results;
  }

  /**
   * Get the prerequisite tree for a course
   */
  async getPrerequisiteTree(
    subject: string,
    number: number,
    depth: number = 5
  ): Promise<PrerequisiteNode> {
    const response = await this.request<{ tree: PrerequisiteNode }>(
      `/api/v1/prerequisites/${encodeURIComponent(subject)}/${number}?depth=${depth}`,
      { method: 'GET' },
      PrerequisiteTreeResponseSchema
    );

    return response.tree;
  }

  /**
   * Trigger a scrape job (admin only)
   */
  async triggerScrape(params: ScrapeJobRequest): Promise<ScrapeJobResponse> {
    return this.request(
      '/api/v1/scrape/trigger',
      {
        method: 'POST',
        body: JSON.stringify({
          subject: params.subject,
          number: params.number,
          term: params.term,
          force: params.force,
        }),
      },
      ScrapeJobResponseSchema
    );
  }

  /**
   * Check API health status
   */
  async healthCheck(): Promise<HealthResponse> {
    return this.request('/api/v1/health', { method: 'GET' }, HealthResponseSchema);
  }
}

// ============================================================================
// Convenience Factory
// ============================================================================

/**
 * Create a new API client instance
 */
export function createBearTracksClient(
  config: BearTracksApiClientConfig
): BearTracksApiClient {
  return new BearTracksApiClient(config);
}

// ============================================================================
// Default Export
// ============================================================================

export default BearTracksApiClient;
