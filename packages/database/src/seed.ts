/**
 * Seed script for Bear Tracks Course Insight Platform
 * Populates the database with real UAlberta course data and generated sentiment data
 */

import { PrismaClient } from '@prisma/client';
import { faker } from '@faker-js/faker';
import { ALL_COURSES, CourseData } from './data/courses';
import {
  parsePrerequisites,
  generateNormalRandom,
  getFacultyFromSubject,
  getTermAvailability,
  generateWarnings,
  log,
} from './utils/helpers';

const prisma = new PrismaClient();

interface SeedStats {
  coursesCreated: number;
  coursesUpdated: number;
  sentimentsCreated: number;
  prerequisitesCreated: number;
  errors: number;
}

/**
 * Generate sentiment data for a course
 */
function generateSentimentData(subject: string, number: number) {
  const isIntro = number < 200;
  const isAdvanced = number >= 400;

  // Difficulty: intro courses easier, advanced courses harder
  const difficultyMean = isIntro ? 2.5 : isAdvanced ? 3.8 : 3.2;
  const difficultyAvg = generateNormalRandom(difficultyMean, 0.6, 1.5, 4.5);

  // Workload: intro courses lighter, advanced courses heavier
  const workloadMean = isIntro ? 10 : isAdvanced ? 15 : 12;
  const workloadAvg = generateNormalRandom(workloadMean, 3, 5, 20);

  // GPA: intro courses slightly higher, advanced courses varied
  const gpaMean = isIntro ? 3.2 : isAdvanced ? 2.9 : 3.0;
  const gpaEstimate = generateNormalRandom(gpaMean, 0.4, 2.3, 3.8);

  // Generate professor mentions (1-3 professors)
  const numProfessors = Math.floor(Math.random() * 3) + 1;
  const professorMentions: Record<string, number> = {};

  for (let i = 0; i < numProfessors; i++) {
    const professorName = `${faker.person.lastName()}, ${faker.person.firstName().charAt(0)}.`;
    const sentiment = generateNormalRandom(3.5, 0.7, 2.5, 4.5);
    professorMentions[professorName] = sentiment;
  }

  // Generate Reddit thread IDs (mock data)
  const numThreads = Math.floor(Math.random() * 5) + 1;
  const redditThreadIds = Array.from({ length: numThreads }, () =>
    faker.string.alphanumeric(6)
  );

  // Generate warnings
  const warnings = generateWarnings(subject, number, difficultyAvg);

  return {
    redditThreadIds,
    difficultyAvg,
    workloadAvg,
    gpaEstimate,
    professorMentions,
    warnings,
  };
}

/**
 * Seed a single course
 */
async function seedCourse(courseData: CourseData): Promise<'created' | 'updated' | 'error'> {
  try {
    const { subject, number, title, description, credits } = courseData;

    // Parse prerequisites from description
    const prerequisitesCodes = parsePrerequisites(description);

    // Get faculty and term availability
    const faculty = getFacultyFromSubject(subject);
    const termAvailability = getTermAvailability(subject, number);

    // Check if course already exists
    const existingCourse = await prisma.course.findUnique({
      where: {
        unique_course: {
          subject,
          number,
        },
      },
    });

    let course;
    let action: 'created' | 'updated';

    if (existingCourse) {
      // Update existing course
      course = await prisma.course.update({
        where: { id: existingCourse.id },
        data: {
          title,
          description,
          credits,
          faculty,
          prerequisitesCodes,
          termAvailability,
        },
      });
      action = 'updated';
    } else {
      // Create new course
      course = await prisma.course.create({
        data: {
          subject,
          number,
          title,
          description,
          credits,
          faculty,
          prerequisitesCodes,
          termAvailability,
        },
      });
      action = 'created';
    }

    // Generate and upsert sentiment data
    const sentimentData = generateSentimentData(subject, number);

    await prisma.courseSentiment.upsert({
      where: { courseId: course.id },
      update: sentimentData,
      create: {
        courseId: course.id,
        ...sentimentData,
      },
    });

    log(`${action === 'created' ? 'Created' : 'Updated'} ${subject} ${number}: ${title}`, 'success');
    return action;
  } catch (error) {
    log(`Error seeding ${courseData.subject} ${courseData.number}: ${error}`, 'error');
    return 'error';
  }
}

/**
 * Create prerequisite relationships
 */
async function createPrerequisites(): Promise<number> {
  log('Creating prerequisite relationships...', 'info');
  let prerequisitesCreated = 0;

  // Get all courses
  const courses = await prisma.course.findMany({
    select: {
      id: true,
      subject: true,
      number: true,
      prerequisitesCodes: true,
    },
  });

  // Create a map for quick course lookup
  const courseMap = new Map(
    courses.map((c) => [`${c.subject} ${c.number}`, c.id])
  );

  for (const course of courses) {
    for (const prereqCode of course.prerequisitesCodes) {
      const prereqId = courseMap.get(prereqCode);

      if (prereqId) {
        try {
          // Check if prerequisite already exists
          const existing = await prisma.prerequisite.findUnique({
            where: {
              unique_prerequisite: {
                courseId: course.id,
                requiresId: prereqId,
              },
            },
          });

          if (!existing) {
            await prisma.prerequisite.create({
              data: {
                courseId: course.id,
                requiresId: prereqId,
              },
            });
            prerequisitesCreated++;
          }
        } catch (error) {
          log(
            `Error creating prerequisite ${prereqCode} for ${course.subject} ${course.number}: ${error}`,
            'warn'
          );
        }
      }
    }
  }

  log(`Created ${prerequisitesCreated} prerequisite relationships`, 'success');
  return prerequisitesCreated;
}

/**
 * Main seed function
 */
async function seed() {
  log('Starting database seed...', 'info');
  log(`Seeding ${ALL_COURSES.length} courses`, 'info');

  const stats: SeedStats = {
    coursesCreated: 0,
    coursesUpdated: 0,
    sentimentsCreated: 0,
    prerequisitesCreated: 0,
    errors: 0,
  };

  // Seed all courses
  for (const courseData of ALL_COURSES) {
    const result = await seedCourse(courseData);

    if (result === 'created') {
      stats.coursesCreated++;
      stats.sentimentsCreated++;
    } else if (result === 'updated') {
      stats.coursesUpdated++;
    } else {
      stats.errors++;
    }

    // Add a small delay to avoid overwhelming the database
    await new Promise((resolve) => setTimeout(resolve, 50));
  }

  // Create prerequisite relationships
  stats.prerequisitesCreated = await createPrerequisites();

  // Print summary
  log('', 'info');
  log('=== Seed Summary ===', 'info');
  log(`Courses created: ${stats.coursesCreated}`, 'success');
  log(`Courses updated: ${stats.coursesUpdated}`, 'success');
  log(`Sentiments created: ${stats.sentimentsCreated}`, 'success');
  log(`Prerequisites created: ${stats.prerequisitesCreated}`, 'success');
  log(`Errors: ${stats.errors}`, stats.errors > 0 ? 'error' : 'success');
  log('', 'info');

  const totalSuccess = stats.coursesCreated + stats.coursesUpdated;
  const successRate = ((totalSuccess / ALL_COURSES.length) * 100).toFixed(1);
  log(`Success rate: ${totalSuccess}/${ALL_COURSES.length} (${successRate}%)`, 'success');
}

/**
 * Run the seed script
 */
async function main() {
  try {
    await seed();
  } catch (error) {
    log(`Fatal error during seed: ${error}`, 'error');
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

// Run the script
main();
