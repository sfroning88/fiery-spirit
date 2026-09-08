import {
  VolcanoDashboard,
  TrainingSignal,
  ModelTier,
  ModelRole,
  ApiInferenceRequest,
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
