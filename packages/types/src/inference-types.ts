import { InferenceAbstainReason } from "@fiery/db/enums";
import type {
  InferenceDeformation as PrismaInferenceDeformation,
  InferenceSeismic as PrismaInferenceSeismic,
  InferenceFeedback as PrismaInferenceFeedback,
} from "@fiery/db";
import {
  TrainingDeformationLabel,
  TrainingSeismicLabel,
} from "./training-types";

export { InferenceAbstainReason };

export type InferenceDeformation = PrismaInferenceDeformation;
export type InferenceSeismic = PrismaInferenceSeismic;
export type InferenceFeedback = PrismaInferenceFeedback;

export type InferenceOutcome = {
  artifact_id: string;
  transform_hash: string;
  op_version: number;
  threshold_used: number;
  abstention_band: number;
  abstained: boolean;
  abstained_reason: string | null;
  latency_ms: number | null;
  inferred_at: string;
  probabilities: Record<string, number>[];
  label: TrainingDeformationLabel | TrainingSeismicLabel | null;
  score: number | null;
  interferogramId: string | null;
  seismicEventId: string | null;
  volcanoId: string | null;
};
