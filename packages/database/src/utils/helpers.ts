/**
 * Helper utilities for seeding the Bear Tracks database
 */

/**
 * Parse prerequisite course codes from a description string
 * Extracts course codes in the format: SUBJECT NUMBER (e.g., "CMPUT 201", "MATH 100")
 */
export function parsePrerequisites(description: string): string[] {
  if (!description) return [];

  // Regex to match course codes: 1-5 capital letters followed by space and 3 digits
  const courseCodePattern = /\b([A-Z]{2,5})\s+(\d{3})\b/g;
  const matches = description.matchAll(courseCodePattern);
  const prerequisites = new Set<string>();

  for (const match of matches) {
    const courseCode = `${match[1]} ${match[2]}`;
    prerequisites.add(courseCode);
  }

  return Array.from(prerequisites);
}

/**
 * Generate a random number with normal distribution
 * Uses Box-Muller transform for normal distribution
 */
export function generateNormalRandom(
  mean: number,
  stddev: number,
  min: number,
  max: number
): number {
  // Box-Muller transform
  const u1 = Math.random();
  const u2 = Math.random();
  const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);

  // Scale and shift
  let value = z0 * stddev + mean;

  // Clamp to min/max
  value = Math.max(min, Math.min(max, value));

  return Math.round(value * 10) / 10; // Round to 1 decimal place
}

/**
 * Get faculty from subject code
 */
export function getFacultyFromSubject(subject: string): string {
  const facultyMap: Record<string, string> = {
    CMPUT: 'Science',
    MATH: 'Science',
    STAT: 'Science',
    ENGG: 'Engineering',
    ECON: 'Arts',
    PSYCH: 'Arts',
    BIOL: 'Science',
    CHEM: 'Science',
    PHYS: 'Science',
    ENG: 'Arts',
    HIST: 'Arts',
    POL: 'Arts',
    SOC: 'Arts',
  };

  return facultyMap[subject] || 'Science';
}

/**
 * Determine if a course is typically offered in which terms
 * Based on course level and type
 */
export function getTermAvailability(subject: string, number: number): string[] {
  // Most courses are offered Fall and Winter
  const bothTerms = ['Fall', 'Winter'];
  const fallOnly = ['Fall'];
  const winterOnly = ['Winter'];

  // Intro courses (100-level) - usually both terms
  if (number < 200) {
    return bothTerms;
  }

  // 200-level courses - mostly both terms, some fall/winter only
  if (number < 300) {
    if (number % 2 === 0) return bothTerms;
    return number % 3 === 0 ? fallOnly : winterOnly;
  }

  // 300-level courses - more specialized, often single term
  if (number < 400) {
    return number % 2 === 0 ? fallOnly : winterOnly;
  }

  // 400-level courses - advanced, often single term
  return number % 2 === 0 ? fallOnly : winterOnly;
}

/**
 * Generate realistic warnings based on course level and subject
 */
export function generateWarnings(
  subject: string,
  number: number,
  difficulty: number
): string[] {
  const warnings: string[] = [];

  // 20% chance of having warnings
  if (Math.random() > 0.2) {
    return warnings;
  }

  const possibleWarnings = [
    'heavy math',
    'lots of coding',
    'time-consuming',
    'difficult exams',
    'group project heavy',
    'attendance required',
    'fast-paced',
    'requires strong background',
  ];

  // Subject-specific warnings
  if (subject === 'CMPUT') {
    possibleWarnings.push('debugging intensive', 'late nights', 'avoid if weak at programming');
  } else if (subject === 'MATH') {
    possibleWarnings.push('proof heavy', 'avoid if weak at algebra', 'theoretical');
  } else if (subject === 'STAT') {
    possibleWarnings.push('R programming required', 'avoid if weak at probability');
  }

  // Difficulty-based warnings
  if (difficulty > 3.5) {
    possibleWarnings.push('challenging material', 'study group recommended');
  }

  // Add 1-2 random warnings
  const numWarnings = Math.random() > 0.5 ? 1 : 2;
  const shuffled = possibleWarnings.sort(() => Math.random() - 0.5);
  return shuffled.slice(0, numWarnings);
}

/**
 * Log with timestamp
 */
export function log(message: string, type: 'info' | 'success' | 'error' | 'warn' = 'info'): void {
  const timestamp = new Date().toISOString();
  const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : type === 'warn' ? '⚠️' : 'ℹ️';
  console.log(`[${timestamp}] ${prefix} ${message}`);
}

/**
 * Retry a promise-based function with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxAttempts) {
        throw error;
      }
      const waitTime = delay * Math.pow(2, attempt - 1);
      log(`Attempt ${attempt} failed, retrying in ${waitTime}ms...`, 'warn');
      await new Promise((resolve) => setTimeout(resolve, waitTime));
    }
  }
  throw new Error('Retry failed');
}
