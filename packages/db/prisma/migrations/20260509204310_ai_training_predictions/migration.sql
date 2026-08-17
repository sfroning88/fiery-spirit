-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "ai";

-- CreateEnum
CREATE TYPE "ai"."prediction_type" AS ENUM ('controllable_prd');

-- CreateEnum
CREATE TYPE "ai"."training_type" AS ENUM ('linear', 'ridge', 'forest', 'gbm');

-- CreateEnum
CREATE TYPE "ai"."training_status" AS ENUM ('pending', 'executing', 'completed', 'failed', 'cancelled');

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."prediction" (
    "type" "ai"."prediction_type" NOT NULL,
    "result" DECIMAL(14,2) NOT NULL,
    "feedbackScore" DECIMAL(14,2),
    "model_type" "ai"."training_type" NOT NULL,
    "model_batch_id" UUID NOT NULL,
    "property_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "prediction_pkey" PRIMARY KEY ("type","model_type","model_batch_id","property_id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_feature" (
    "columns" TEXT[],
    "target" TEXT NOT NULL,
    "classes" TEXT[],
    "schema_version" INTEGER NOT NULL DEFAULT 1,
    "batch_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_feature_pkey" PRIMARY KEY ("batch_id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_batch" (
    "id" UUID NOT NULL,
    "status" "ai"."training_status" NOT NULL,
    "samples" INTEGER NOT NULL,
    "split_seed" INTEGER NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_batch_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_model" (
    "type" "ai"."training_type" NOT NULL,
    "status" "ai"."training_status" NOT NULL,
    "score" DECIMAL(6,4) NOT NULL,
    "rmse" DECIMAL(14,2) NOT NULL,
    "winner" BOOLEAN NOT NULL DEFAULT false,
    "storage_path" TEXT NOT NULL,
    "trained_at" TIMESTAMPTZ(6) NOT NULL,
    "error_message" TEXT,
    "batch_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_model_pkey" PRIMARY KEY ("type","batch_id")
);

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "training_feature_batch_id_key" ON "ai"."training_feature"("batch_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_training_batch_by_recency" ON "ai"."training_batch"("created_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "training_model_batch_id_winner_idx" ON "ai"."training_model"("batch_id", "winner");

-- AddForeignKey
ALTER TABLE "ai"."prediction" ADD CONSTRAINT "prediction_model_type_model_batch_id_fkey" FOREIGN KEY ("model_type", "model_batch_id") REFERENCES "ai"."training_model"("type", "batch_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."prediction" ADD CONSTRAINT "prediction_property_id_fkey" FOREIGN KEY ("property_id") REFERENCES "property"."property"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_feature" ADD CONSTRAINT "training_feature_batch_id_fkey" FOREIGN KEY ("batch_id") REFERENCES "ai"."training_batch"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_model" ADD CONSTRAINT "training_model_batch_id_fkey" FOREIGN KEY ("batch_id") REFERENCES "ai"."training_batch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
