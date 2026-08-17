import { WorkerServiceConfig } from "@focus/types";

export class WorkerService {
  protected config: WorkerServiceConfig;
  constructor(config: WorkerServiceConfig) {
    this.config = {
      timeout: 30 * 1000,
      ...config,
    };
  }

  protected async makeRequest<T = unknown>(
    endpoint: string,
    options: RequestInit,
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
    try {
      const response = await fetch(endpoint, {
        ...options,
        headers: {
          "auth-token": this.config.authToken,
          ...options.headers,
        },
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        const errorData = (await response.json().catch(() => ({}))) as Record<
          string,
          unknown
        >;
        throw new WorkerServiceError(
          `Request failed with status ${response.status}`,
          response.status,
          errorData,
        );
      }
      return (await response.json()) as T;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  protected handleError(error: unknown, message: string): WorkerServiceError {
    if (error instanceof WorkerServiceError) {
      return error;
    }
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        return new WorkerServiceError("Request timeout", 408, {
          originalError: error.message,
        });
      }
      return new WorkerServiceError(message, 500, {
        originalError: error.message,
      });
    }
    return new WorkerServiceError(message, 500, {
      originalError: String(error),
    });
  }
}

export class WorkerServiceError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "WorkerServiceError";
  }
}
