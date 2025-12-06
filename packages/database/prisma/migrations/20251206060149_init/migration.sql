/*
  Warnings:

  - Made the column `descriptionVector` on table `course_embeddings` required. This step will fail if there are existing NULL values in that column.
  - Made the column `reviewsVector` on table `course_embeddings` required. This step will fail if there are existing NULL values in that column.

*/
-- AlterTable
ALTER TABLE "course_embeddings" ALTER COLUMN "descriptionVector" SET NOT NULL,
ALTER COLUMN "reviewsVector" SET NOT NULL;
