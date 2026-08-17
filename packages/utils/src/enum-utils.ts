import { PredictionType } from "@focus/db/enums";

const PREDICTION_TYPE_API_PATH: Record<PredictionType, string> = {
  [PredictionType.controllablePrd]: "controllable_prd",
  [PredictionType.occupancy]: "occupancy",
  [PredictionType.operatingMargin]: "operating_margin",
};

export function predictionTypeToApiPath(type: PredictionType): string {
  return PREDICTION_TYPE_API_PATH[type];
}

const PREDICTION_TYPE_FROM_API_PATH = Object.fromEntries(
  Object.entries(PREDICTION_TYPE_API_PATH).map(([prisma, api]) => [
    api,
    prisma,
  ]),
) as Record<string, PredictionType>;

export function normalizePredictionType(type: string): PredictionType {
  if ((Object.values(PredictionType) as string[]).includes(type)) {
    return type as PredictionType;
  }
  const mapped = PREDICTION_TYPE_FROM_API_PATH[type];
  if (mapped) return mapped;
  throw new Error(`Unknown prediction type: ${type}`);
}
