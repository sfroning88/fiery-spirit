import { env } from "@focus/config";
import { PredictionType } from "@focus/db";
import {
  WORKER_API_ROUTES,
  type ModelShuffleResponse,
  type ModelTrainingResponse,
} from "@focus/types";
import { predictionTypeToApiPath } from "@focus/utils";
import { WorkerService } from "../worker-service";

export class AIWorkerService extends WorkerService {
  static fromEnvironment(): AIWorkerService {
    const baseUrl = env.AI_API_URL ?? "";
    const authToken = env.AUTH_TOKEN ?? "";
    if (!baseUrl || !authToken) {
      console.warn("AIWorkerService: AI_API_URL or AUTH_TOKEN is missing");
    }
    return new AIWorkerService({ baseUrl, authToken, timeout: 300000 });
  }

  async modelShuffle(): Promise<ModelShuffleResponse> {
    const endpoint = `${this.config.baseUrl}${WORKER_API_ROUTES.modelShuffleGroups()}`;
    return this.makeRequest<ModelShuffleResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  }

  async modelTrain(
    predictionType: PredictionType,
  ): Promise<ModelTrainingResponse> {
    const endpoint = `${this.config.baseUrl}${WORKER_API_ROUTES.modelTrain({
      predictionType: predictionTypeToApiPath(predictionType),
    })}`;
    return this.makeRequest<ModelTrainingResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  }
}
