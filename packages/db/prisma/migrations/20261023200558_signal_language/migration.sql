-- CreateEnum
CREATE TYPE "ai"."training_language_label" AS ENUM ('green', 'yellow', 'orange', 'red');

-- AlterEnum
ALTER TYPE "ai"."model_role" ADD VALUE 'analyst';

-- AlterEnum
ALTER TYPE "ai"."training_sample_source" ADD VALUE 'academic';

-- AlterEnum
ALTER TYPE "ai"."training_signal" ADD VALUE 'language';

-- AlterEnum
BEGIN;
CREATE TYPE "ai"."training_stage_new" AS ENUM ('pretrain', 'loraVisual', 'loraLanguage', 'distill', 'prune', 'quantize');
ALTER TABLE "ai"."model_artifact" ALTER COLUMN "stage" TYPE "ai"."training_stage_new" USING (
    CASE "stage"::text WHEN 'lora' THEN 'loraVisual' ELSE "stage"::text END::"ai"."training_stage_new"
);
ALTER TABLE "ai"."training_session" ALTER COLUMN "stage" TYPE "ai"."training_stage_new" USING (
    CASE "stage"::text WHEN 'lora' THEN 'loraVisual' ELSE "stage"::text END::"ai"."training_stage_new"
);
ALTER TYPE "ai"."training_stage" RENAME TO "training_stage_old";
ALTER TYPE "ai"."training_stage_new" RENAME TO "training_stage";
DROP TYPE "ai"."training_stage_old";
COMMIT;

-- RenameTable
ALTER TABLE "ai"."training_hyperparameter_lora" RENAME TO "training_hyperparameter_lora_visual";

-- RenameConstraint
ALTER TABLE "ai"."training_hyperparameter_lora_visual" RENAME CONSTRAINT "training_hyperparameter_lora_pkey" TO "training_hyperparameter_lora_visual_pkey";

-- RenameConstraint
ALTER TABLE "ai"."training_hyperparameter_lora_visual" RENAME CONSTRAINT "training_hyperparameter_lora_target_modules_id_fkey" TO "training_hyperparameter_lora_visual_target_modules_id_fkey";

-- RenameColumn
ALTER TABLE "ai"."training_session" RENAME COLUMN "hyperparameter_lora_id" TO "hyperparameter_lora_visual_id";

-- RenameConstraint
ALTER TABLE "ai"."training_session" RENAME CONSTRAINT "training_session_hyperparameter_lora_id_fkey" TO "training_session_hyperparameter_lora_visual_id_fkey";

-- DropConstraint
ALTER TABLE "ai"."inference_feedback" DROP CONSTRAINT "feedback_one_per_user_per_prediction";

-- AlterTable
ALTER TABLE "ai"."inference_feedback" ADD COLUMN     "corrected_language" "ai"."training_language_label",
ADD COLUMN     "language_id" UUID;

-- AlterTable
ALTER TABLE "ai"."training_contract" ADD COLUMN     "language_id" UUID;

-- AlterTable
ALTER TABLE "ai"."training_session" ADD COLUMN "hyperparameter_lora_language_id" UUID;

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."inference_language" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "label" "ai"."training_language_label",
    "probabilities" DECIMAL(6,5)[],
    "class_order" "ai"."training_language_label"[],
    "threshold_used" DECIMAL(6,5) NOT NULL,
    "abstention_band" DECIMAL(6,5) NOT NULL,
    "abstained" BOOLEAN NOT NULL DEFAULT false,
    "abstained_reason" "ai"."inference_abstain_reason",
    "generated_text" TEXT NOT NULL,
    "latency_ms" DECIMAL(10,3),
    "inferred_at" TIMESTAMPTZ(6) NOT NULL,
    "artifact_id" UUID NOT NULL,
    "volcano_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "inference_language_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_language_class" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "background" BOOLEAN NOT NULL DEFAULT true,
    "unrest" BOOLEAN NOT NULL DEFAULT true,
    "eruption" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_language_class_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_passage" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "source" "ai"."training_sample_source" NOT NULL,
    "split" "ai"."training_split" NOT NULL,
    "label" "ai"."training_language_label" NOT NULL,
    "citation" TEXT NOT NULL,
    "published_at" TIMESTAMPTZ(6) NOT NULL,
    "chunk_index" INTEGER NOT NULL,
    "storage_path" TEXT NOT NULL,
    "volcano_id" UUID,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_passage_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_language" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "max_characters" INTEGER NOT NULL,
    "class_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_language_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_hyperparameter_lora_language" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "rank" INTEGER NOT NULL DEFAULT 8,
    "alpha" INTEGER NOT NULL DEFAULT 16,
    "dropout" DOUBLE PRECISION NOT NULL DEFAULT 0.05,
    "epochs" INTEGER NOT NULL DEFAULT 3,
    "learning_rate" DOUBLE PRECISION NOT NULL DEFAULT 0.00002,
    "gradient_accumulation_steps" INTEGER NOT NULL DEFAULT 8,
    "target_modules_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_hyperparameter_lora_language_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_language_by_volcano" ON "ai"."inference_language"("volcano_id", "inferred_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_language_by_artifact" ON "ai"."inference_language"("volcano_id", "artifact_id");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_language_abstained" ON "ai"."inference_language"("artifact_id", "abstained");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_language_abstained_reason" ON "ai"."inference_language"("artifact_id", "abstained_reason");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_language_recency" ON "ai"."inference_language"("created_at" DESC);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_inference_language_by_label" ON "ai"."inference_language"("label");

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "training_language_class_background_unrest_eruption_key" ON "ai"."training_language_class"("background", "unrest", "eruption");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_passage_by_split" ON "ai"."training_passage"("split", "source", "label");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_passage_by_volcano" ON "ai"."training_passage"("volcano_id", "published_at" DESC);

-- AddForeignKey
ALTER TABLE "ai"."inference_language" ADD CONSTRAINT "inference_language_artifact_id_fkey" FOREIGN KEY ("artifact_id") REFERENCES "ai"."model_artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_language" ADD CONSTRAINT "inference_language_volcano_id_fkey" FOREIGN KEY ("volcano_id") REFERENCES "geo"."volcano"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."inference_feedback" ADD CONSTRAINT "inference_feedback_language_id_fkey" FOREIGN KEY ("language_id") REFERENCES "ai"."inference_language"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_passage" ADD CONSTRAINT "training_passage_volcano_id_fkey" FOREIGN KEY ("volcano_id") REFERENCES "geo"."volcano"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_language" ADD CONSTRAINT "training_language_class_id_fkey" FOREIGN KEY ("class_id") REFERENCES "ai"."training_language_class"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_hyperparameter_lora_language" ADD CONSTRAINT "training_hyperparameter_lora_language_target_modules_id_fkey" FOREIGN KEY ("target_modules_id") REFERENCES "ai"."training_target_modules"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_contract" ADD CONSTRAINT "training_contract_language_id_fkey" FOREIGN KEY ("language_id") REFERENCES "ai"."training_language"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_session" ADD CONSTRAINT "training_session_hyperparameter_lora_language_id_fkey" FOREIGN KEY ("hyperparameter_lora_language_id") REFERENCES "ai"."training_hyperparameter_lora_language"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddConstraint
ALTER TABLE "ai"."inference_feedback"
    ADD CONSTRAINT "feedback_one_per_user_per_prediction"
    UNIQUE NULLS NOT DISTINCT ("artifact_id", "interferogram_id", "seismic_event_id", "language_id", "user_id");

-- DropConstraint
ALTER TABLE "ai"."inference_feedback" DROP CONSTRAINT "feedback_single_target";

-- AddConstraint
ALTER TABLE "ai"."inference_feedback"
    ADD CONSTRAINT "feedback_single_target"
    CHECK (num_nonnulls("interferogram_id", "seismic_event_id", "language_id") = 1);

-- DropConstraint
ALTER TABLE "ai"."inference_feedback" DROP CONSTRAINT "feedback_corrected_scope";

-- AddConstraint
ALTER TABLE "ai"."inference_feedback"
    ADD CONSTRAINT "feedback_corrected_scope"
    CHECK (
        ("corrected_deformation" IS NULL OR "interferogram_id" IS NOT NULL)
        AND ("corrected_seismic" IS NULL OR "seismic_event_id" IS NOT NULL)
        AND ("corrected_language" IS NULL OR "language_id" IS NOT NULL)
    );

-- DropConstraint
ALTER TABLE "ai"."inference_feedback" DROP CONSTRAINT "feedback_corrected_required";

-- AddConstraint
ALTER TABLE "ai"."inference_feedback"
    ADD CONSTRAINT "feedback_corrected_required"
    CHECK (
        "agreed"
        OR "corrected_deformation" IS NOT NULL
        OR "corrected_seismic" IS NOT NULL
        OR "corrected_language" IS NOT NULL
    );
