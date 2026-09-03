import { env } from "@fiery/config";
import {
  API_ROUTES,
  type ApiKeyRequest,
  type ApiJobsResponse,
  type ApiInferenceRequest,
  type ApiInferenceResponse,
  type ApiPromoteResponse,
  type ApiRefreshResponse,
} from "@fiery/types";
import { ApiService } from "../api-service";

export class ApiBackendService extends ApiService {
  static fromEnvironment(): ApiBackendService {
    const baseUrl = env.BACKEND_API_URL ?? "";
    const authToken = env.AUTH_TOKEN ?? "";
    if (!baseUrl || !authToken) {
      console.warn(
        "ApiBackendService: BACKEND_API_URL or AUTH_TOKEN is missing",
      );
    }
    return new ApiBackendService({ baseUrl, authToken, timeout: 300000 });
  }

  async inference(request: ApiInferenceRequest): Promise<ApiInferenceResponse> {
    const endpoint = `${this.config.baseUrl}${API_ROUTES.inference()}`;
    return this.makeRequest<ApiInferenceResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tier: request.tier,
        role: request.role,
        interferogram_id: request.interferogramId,
        seismicEvent_id: request.seismicEventId,
        volcano_id: request.volcanoId,
      }),
    });
  }

  async batch(request: ApiKeyRequest): Promise<ApiJobsResponse> {
    const endpoint = `${this.config.baseUrl}${API_ROUTES.batch()}`;
    return this.makeRequest<ApiJobsResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tier: request.tier,
        role: request.role,
      }),
    });
  }

  async promote(): Promise<ApiPromoteResponse> {
    const endpoint = `${this.config.baseUrl}${API_ROUTES.promote()}`;
    return this.makeRequest<ApiPromoteResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  }

  async refresh(request: ApiKeyRequest): Promise<ApiRefreshResponse> {
    const endpoint = `${this.config.baseUrl}${API_ROUTES.refresh()}`;
    return this.makeRequest<ApiRefreshResponse>(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tier: request.tier,
        role: request.role,
      }),
    });
  }
}
