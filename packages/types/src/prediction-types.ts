import { PredictionType } from "@focus/db/enums";
import type { Prediction as PrismaPrediction } from "@focus/db";
import { ModelPredictResponse } from "./worker-types";

export type { PredictionType };

export type Prediction = PrismaPrediction;

export const PREDICTION_TYPES = [
  PredictionType.controllablePrd,
  PredictionType.occupancy,
  PredictionType.operatingMargin,
] as const;

export type PredictionsForProperty = Record<
  PredictionType,
  ModelPredictResponse
>;
