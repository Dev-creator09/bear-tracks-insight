-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "vector";

-- CreateTable
CREATE TABLE "courses" (
    "id" TEXT NOT NULL,
    "subject" TEXT NOT NULL,
    "number" INTEGER NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "credits" DOUBLE PRECISION NOT NULL,
    "faculty" TEXT NOT NULL,
    "prerequisitesCodes" TEXT[],
    "termAvailability" TEXT[],
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "courses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "course_sentiments" (
    "id" TEXT NOT NULL,
    "course_id" TEXT NOT NULL,
    "redditThreadIds" TEXT[],
    "difficultyAvg" DOUBLE PRECISION,
    "workloadAvg" DOUBLE PRECISION,
    "gpaEstimate" DOUBLE PRECISION,
    "professorMentions" JSONB,
    "warnings" TEXT[],
    "lastScrapedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "course_sentiments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "course_embeddings" (
    "course_id" TEXT NOT NULL,
    "descriptionVector" vector(1536),
    "reviewsVector" vector(1536),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "course_embeddings_pkey" PRIMARY KEY ("course_id")
);

-- CreateTable
CREATE TABLE "prerequisites" (
    "id" TEXT NOT NULL,
    "course_id" TEXT NOT NULL,
    "requires_id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "prerequisites_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "idx_faculty_number" ON "courses"("faculty", "number");

-- CreateIndex
CREATE INDEX "idx_updated_at" ON "courses"("updatedAt");

-- CreateIndex
CREATE UNIQUE INDEX "courses_subject_number_key" ON "courses"("subject", "number");

-- CreateIndex
CREATE UNIQUE INDEX "course_sentiments_course_id_key" ON "course_sentiments"("course_id");

-- CreateIndex
CREATE INDEX "idx_last_scraped" ON "course_sentiments"("lastScrapedAt");

-- CreateIndex
CREATE INDEX "idx_prereq_course" ON "prerequisites"("course_id");

-- CreateIndex
CREATE INDEX "idx_prereq_requires" ON "prerequisites"("requires_id");

-- CreateIndex
CREATE UNIQUE INDEX "prerequisites_course_id_requires_id_key" ON "prerequisites"("course_id", "requires_id");

-- AddForeignKey
ALTER TABLE "course_sentiments" ADD CONSTRAINT "course_sentiments_course_id_fkey" FOREIGN KEY ("course_id") REFERENCES "courses"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "course_embeddings" ADD CONSTRAINT "course_embeddings_course_id_fkey" FOREIGN KEY ("course_id") REFERENCES "courses"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "prerequisites" ADD CONSTRAINT "prerequisites_course_id_fkey" FOREIGN KEY ("course_id") REFERENCES "courses"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "prerequisites" ADD CONSTRAINT "prerequisites_requires_id_fkey" FOREIGN KEY ("requires_id") REFERENCES "courses"("id") ON DELETE CASCADE ON UPDATE CASCADE;
