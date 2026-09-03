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

export type EvaluatedModel = {
  artifact_id: string;
  tier: ModelTier;
  role: ModelRole;
  evaluated_at: Date | null;
  promoted: boolean;
  promoted_at: Date | null;
  denied_reason: string | null;
  ready: boolean;
};
