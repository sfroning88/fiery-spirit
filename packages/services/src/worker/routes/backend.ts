import { env } from "@focus/config";
import { PredictionType } from "@focus/db";
import {
  WORKER_API_ROUTES,
  type ModelPredictRequest,
  type ModelPredictResponse,
} from "@focus/types";
import { predictionTypeToApiPath } from "@focus/utils";
import { WorkerService } from "../worker-service";

export class BackendWorkerService extends WorkerService {
  static fromEnvironment(): BackendWorkerService {
    const baseUrl = env.BACKEND_API_URL ?? "";
    const authToken = env.AUTH_TOKEN ?? "";
    if (!baseUrl || !authToken) {
      console.warn(
        "BackendWorkerService: BACKEND_API_URL or AUTH_TOKEN is missing",
      );
    }
    return new BackendWorkerService({ baseUrl, authToken, timeout: 300000 });
  }

  async modelPredict(
    predictionType: PredictionType,
    request: ModelPredictRequest,
  ): Promise<ModelPredictResponse> {
    const endpoint = `${this.config.baseUrl}${WORKER_API_ROUTES.modelPredict({
      predictionType: predictionTypeToApiPath(predictionType),
    })}`;
    return this.makeRequest<ModelPredictResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        property_id: request.propertyId,
        multi_enabled: request.multiEnabled,
      }),
    });
  }
}
