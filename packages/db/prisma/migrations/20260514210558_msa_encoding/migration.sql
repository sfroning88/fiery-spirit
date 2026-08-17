-- AlterTable
ALTER TABLE "ai"."training_model" RENAME COLUMN "score" TO "r2_score";

-- AlterTable
ALTER TABLE "ai"."training_model" ADD COLUMN "train_score" DECIMAL(6,4);

-- CreateTable
CREATE TABLE IF NOT EXISTS "ai"."training_msa_encoding" (
    "mean_target" DECIMAL(14,2) NOT NULL,
    "sample_count" INTEGER NOT NULL,
    "msa_id" UUID NOT NULL,
    "batch_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "training_msa_encoding_pkey" PRIMARY KEY ("batch_id","msa_id")
);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_msa_encoding_by_batch" ON "ai"."training_msa_encoding"("batch_id");

-- AddForeignKey
ALTER TABLE "ai"."training_msa_encoding" ADD CONSTRAINT "training_msa_encoding_msa_id_fkey" FOREIGN KEY ("msa_id") REFERENCES "property"."nic_msa"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai"."training_msa_encoding" ADD CONSTRAINT "training_msa_encoding_batch_id_fkey" FOREIGN KEY ("batch_id") REFERENCES "ai"."training_batch"("id") ON DELETE CASCADE ON UPDATE CASCADE;
