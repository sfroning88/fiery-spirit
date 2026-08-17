-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "property";

-- CreateEnum
CREATE TYPE "property"."nic_state" AS ENUM ('AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY');

-- AlterTable
ALTER TABLE "iam"."users" ALTER COLUMN "is_active" DROP NOT NULL,
ALTER COLUMN "is_platform_admin" DROP NOT NULL;

-- CreateTable
CREATE TABLE IF NOT EXISTS "property"."nic_msa" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" TEXT NOT NULL,
    "population" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "nic_msa_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "property"."property" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" TEXT NOT NULL,
    "address" TEXT NOT NULL,
    "city" TEXT NOT NULL,
    "state" "property"."nic_state" NOT NULL,
    "zip" TEXT NOT NULL,
    "year_built" INTEGER NOT NULL,
    "year_renovated" INTEGER,
    "unit_size" DECIMAL(14,2) NOT NULL,
    "cottage_units" INTEGER NOT NULL DEFAULT 0,
    "independent_units" INTEGER NOT NULL DEFAULT 0,
    "assisted_units" INTEGER NOT NULL DEFAULT 0,
    "memory_units" INTEGER NOT NULL DEFAULT 0,
    "total_units" INTEGER NOT NULL DEFAULT 0,
    "total_beds" INTEGER NOT NULL DEFAULT 0,
    "msa_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "property_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "property"."property_snapshot" (
    "reported_at" DATE NOT NULL,
    "occupancy" DECIMAL(5,2) NOT NULL DEFAULT 0,
    "total_revenues" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "repairs_maintenance" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "payroll" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "utilities" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "contract_services" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "raw_food" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "culinary_supplies" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "administrative" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "marketing_promotions" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "activities" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "other_expenses" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "controllable_expenses" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "management_fee" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "real_estate_taxes" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "insurance" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "non_controllable_expenses" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "total_expenses" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "operating_margin" DECIMAL(5,2) NOT NULL DEFAULT 0,
    "controllable_prd" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "property_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "property_snapshot_pkey" PRIMARY KEY ("property_id","reported_at")
);

-- CreateIndex
CREATE UNIQUE INDEX IF NOT EXISTS "property_name_key" ON "property"."property"("name");

-- CreateIndex
CREATE INDEX IF NOT EXISTS "idx_property_by_msa" ON "property"."property"("msa_id");

-- AddForeignKey
ALTER TABLE "property"."property" ADD CONSTRAINT "property_msa_id_fkey" FOREIGN KEY ("msa_id") REFERENCES "property"."nic_msa"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "property"."property_snapshot" ADD CONSTRAINT "property_snapshot_property_id_fkey" FOREIGN KEY ("property_id") REFERENCES "property"."property"("id") ON DELETE CASCADE ON UPDATE CASCADE;
