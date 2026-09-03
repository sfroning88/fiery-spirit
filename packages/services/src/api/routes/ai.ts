import { env } from "@fiery/config";
import {
  API_ROUTES,
  type ApiJobsResponse,
  type ApiIngestRequest,
  type ApiRefineRequest,
  type ApiRefineResponse,
  type ApiTrainRequest,
  type ApiTrainResponse,
} from "@fiery/types";
import { ApiService } from "../api-service";

export class ApiAiService extends ApiService {
  static fromEnvironment(): ApiAiService {
    const baseUrl = env.AI_API_URL ?? "";
    const authToken = env.AUTH_TOKEN ?? "";
    if (!baseUrl || !authToken) {
      console.warn("ApiAiService: AI_API_URL or AUTH_TOKEN is missing");
    }
    return new ApiAiService({ baseUrl, authToken, timeout: 300000 });
  }

  async ingest(request: ApiIngestRequest): Promise<ApiJobsResponse> {
    const endpoint = `${this.config.baseUrl}${API_ROUTES.ingest()}`;
    return this.makeRequest<ApiJobsResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: request.source,
        max_samples: request.maxSamples,
      }),
    });
  }

  async refine(request: ApiRefineRequest): Promise<ApiRefineResponse> {
    const endpoint = `${this.config.baseUrl}${API_ROUTES.refine()}`;
    return this.makeRequest<ApiRefineResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contractId: request.contractId,
        max_samples: request.maxSamples,
      }),
    });
  }

  async train(request: ApiTrainRequest): Promise<ApiTrainResponse> {
    const endpoint = `${this.config.baseUrl}${API_ROUTES.train()}`;
    return this.makeRequest<ApiTrainResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contract_id: request.contractId,
        version_id: request.versionId,
        stage: request.stage,
        parent_id: request.parentId,
      }),
    });
  }
}
