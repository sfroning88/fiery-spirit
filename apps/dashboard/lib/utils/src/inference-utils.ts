import { dateLikeToMs } from "@fiery/utils";
import {
  VolcanoDashboard,
  TrainingSignal,
  ModelTier,
  ModelRole,
  ApiInferenceRequest,
  InferenceLatest,
} from "@fiery/types";

export function inferenceRequest(
  volcano: VolcanoDashboard,
  signal: TrainingSignal,
): ApiInferenceRequest | null {
  if (signal === TrainingSignal.deformation) {
    const sample = volcano.deformation.sample;
    if (!sample) return null;
    const artifact = volcano.deformation.artifact;
    return {
      tier: artifact?.tier ?? ModelTier.cloud,
      role: artifact?.role ?? ModelRole.screener,
      interferogramId: sample.id,
      seismicEventId: null,
      volcanoId: volcano.id,
    };
  }
  const sample = volcano.seismic.sample;
  if (!sample) return null;
  const artifact =
    volcano.seismic.cloud.artifact ?? volcano.seismic.edge.artifact;
  return {
    tier: artifact?.tier ?? ModelTier.cloud,
    role: artifact?.role ?? ModelRole.teacher,
    interferogramId: null,
    seismicEventId: sample.id,
    volcanoId: volcano.id,
  };
}

export function latestSignalInference(
  volcano: VolcanoDashboard,
  signal: TrainingSignal,
): InferenceLatest | null {
  if (signal === TrainingSignal.deformation) {
    if (!volcano.deformation.inference) return null;
    return {
      kind: "deformation",
      inference: volcano.deformation.inference,
      feedback: volcano.deformation.feedback,
    };
  }
  const candidates: InferenceLatest[] = [];
  if (volcano.seismic.cloud.inference) {
    candidates.push({
      kind: "seismic",
      inference: volcano.seismic.cloud.inference,
      feedback: volcano.seismic.cloud.feedback,
    });
  }
  if (volcano.seismic.edge.inference) {
    candidates.push({
      kind: "seismic",
      inference: volcano.seismic.edge.inference,
      feedback: volcano.seismic.edge.feedback,
    });
  }
  return candidates.reduce<InferenceLatest | null>((best, next) => {
    if (!best) return next;
    return dateLikeToMs(next.inference.inferredAt) >
      dateLikeToMs(best.inference.inferredAt)
      ? next
      : best;
  }, null);
}
