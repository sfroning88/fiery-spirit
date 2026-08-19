import { ModelTier, ModelRole, ModelMetricName } from "@fiery/db/enums";
import type {
  ModelArtifact as PrismaModelArtifact,
  ModelMetric as PrismaModelMetric,
  ModelBudget as PrismaModelBudget,
} from "@fiery/db";

export { ModelTier, ModelRole, ModelMetricName };

export type ModelArtifact = PrismaModelArtifact;
export type ModelMetric = PrismaModelMetric;
export type ModelBudget = PrismaModelBudget;
