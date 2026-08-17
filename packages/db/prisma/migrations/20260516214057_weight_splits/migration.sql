-- CreateEnum
CREATE TYPE "ai"."training_function" AS ENUM ('train', 'validate', 'test');

-- AlterTable
ALTER TABLE "ai"."training_batch" ADD COLUMN     "split_version" INTEGER;

-- AlterTable
ALTER TABLE "property"."property_snapshot" ADD COLUMN     "function" "ai"."training_function";

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_split" (
    "version" INTEGER NOT NULL,
    "train_ratio" DECIMAL(3,2) NOT NULL,
    "validate_ratio" DECIMAL(3,2) NOT NULL,
    "test_ratio" DECIMAL(3,2) NOT NULL,
    "shuffled_at" TIMESTAMPTZ(6) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_split_pkey" PRIMARY KEY ("version")
);

-- AddForeignKey
ALTER TABLE "ai"."training_batch" ADD CONSTRAINT "training_batch_split_version_fkey" FOREIGN KEY ("split_version") REFERENCES "ai"."training_split"("version") ON DELETE RESTRICT ON UPDATE CASCADE;
