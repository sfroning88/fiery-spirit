import { createRoute } from "./route-types";
import { Prediction } from "./prediction-types";

export type WorkerServiceConfig = {
  baseUrl: string;
  authToken: string;
  timeout?: number;
};

export type ModelShuffleResponse = {
  jobId: string;
};

export type ModelTrainingResponse = {
  jobIds: string[];
};

export type ModelPredictRequest = {
  propertyId: string;
  multiEnabled: boolean;
};

export type ModelPredictResponse = {
  predictions: Prediction[];
};

export const WORKER_API_ROUTES = {
  // apps/ai: shuffle train/validate/test groups
  modelShuffleGroups: createRoute("/api/shuffle"),

  // apps/ai: train models for a prediction type
  modelTrain: createRoute("/api/train/:predictionType"),

  // apps/backend: predict controllable prd for property
  modelPredict: createRoute("/api/predict/:predictionType"),
};
