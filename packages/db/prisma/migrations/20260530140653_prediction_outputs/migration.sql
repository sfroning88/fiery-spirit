-- AlterEnum
-- This migration adds more than one value to an enum.
-- With PostgreSQL versions 11 and earlier, this is not possible
-- in a single migration. This can be worked around by creating
-- multiple migrations, each migration adding only one value to
-- the enum.


ALTER TYPE "ai"."prediction_type" ADD VALUE 'occupancy';
ALTER TYPE "ai"."prediction_type" ADD VALUE 'operating_margin';

-- AlterTable
ALTER TABLE "ai"."training_batch" ADD COLUMN     "prediction_type" "ai"."prediction_type" NOT NULL DEFAULT 'controllable_prd';
