import { type PredictionType, type PredictionsForProperty } from "@focus/types";
import { toNum } from "./number-utils";

export function firstPredictionResult(
  data: PredictionsForProperty | undefined,
  type: PredictionType,
): number | null {
  if (!data) return null;
  const row = data[type].predictions[0];
  return row ? toNum(row.result) : null;
}
