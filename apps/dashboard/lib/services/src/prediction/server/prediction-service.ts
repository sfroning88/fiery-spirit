import "server-only";

import { db } from "@focus/db";
import type {
  Prediction,
  PredictionType,
  TrainingType,
  ModelPredictRequest,
  ModelPredictResponse,
} from "@focus/types";
import { BackendWorkerService } from "@focus/services";
import { normalizePredictionType } from "@focus/utils";

export class PredictionService {
  private workerService: BackendWorkerService;
  constructor() {
    this.workerService = BackendWorkerService.fromEnvironment();
  }

  async predict(
    predictionType: PredictionType,
    args: ModelPredictRequest,
  ): Promise<ModelPredictResponse> {
    const response = await this.workerService.modelPredict(
      predictionType,
      args,
    );
    const predictions = this.normalizePredictions(response.predictions);
    await this.persistPredictions(predictions);
    return { predictions };
  }

  async givePredictionFeedback(
    type: PredictionType,
    modelType: TrainingType,
    modelBatchId: string,
    propertyId: string,
    feedbackScore: number,
  ): Promise<void> {
    await db.prediction.update({
      data: { feedbackScore },
      where: {
        type_modelType_modelBatchId_propertyId: {
          type,
          modelType,
          modelBatchId,
          propertyId,
        },
      },
    });
  }

  private normalizePredictions(predictions: Prediction[]): Prediction[] {
    return predictions.map((p) => ({
      ...p,
      type: normalizePredictionType(String(p.type)),
    }));
  }

  private async persistPredictions(predictions: Prediction[]): Promise<void> {
    const operations = predictions.map((p) =>
      db.prediction.upsert({
        where: {
          type_modelType_modelBatchId_propertyId: {
            type: p.type,
            modelType: p.modelType,
            modelBatchId: p.modelBatchId,
            propertyId: p.propertyId,
          },
        },
        update: { result: p.result },
        create: {
          type: p.type,
          result: p.result,
          modelType: p.modelType,
          modelBatchId: p.modelBatchId,
          propertyId: p.propertyId,
        },
      }),
    );
    await db.$transaction(operations);
  }
}
