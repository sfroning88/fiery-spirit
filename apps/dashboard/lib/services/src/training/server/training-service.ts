import "server-only";

import { db, PredictionType, TrainingFunction } from "@focus/db";
import type {
  ModelShuffleResponse,
  ModelTrainingResponse,
  TrainingBatchListEntry,
  TrainingFunctionCounts,
} from "@focus/types";
import { AIWorkerService } from "@focus/services";

export class TrainingService {
  private workerService: AIWorkerService;
  constructor() {
    this.workerService = AIWorkerService.fromEnvironment();
  }

  async shuffleGroups(): Promise<ModelShuffleResponse> {
    return this.workerService.modelShuffle();
  }

  async train(predictionType: PredictionType): Promise<ModelTrainingResponse> {
    return this.workerService.modelTrain(predictionType);
  }

  async fetchFunctionCounts(): Promise<TrainingFunctionCounts> {
    const rows = await db.propertySnapshot.groupBy({
      by: ["function"],
      _count: { _all: true },
    });
    const counts: TrainingFunctionCounts = {
      train: 0,
      validate: 0,
      test: 0,
      unassigned: 0,
    };
    for (const row of rows) {
      if (row.function === TrainingFunction.train)
        counts.train = row._count._all;
      else if (row.function === TrainingFunction.validate)
        counts.validate = row._count._all;
      else if (row.function === TrainingFunction.test)
        counts.test = row._count._all;
      else counts.unassigned = row._count._all;
    }
    return counts;
  }

  async fetchBatches(): Promise<TrainingBatchListEntry[]> {
    const batches = await db.trainingBatch.findMany({
      include: {
        models: {
          select: {
            type: true,
            status: true,
            r2score: true,
            winner: true,
          },
        },
      },
      orderBy: { createdAt: "desc" },
    });
    return batches;
  }
}
