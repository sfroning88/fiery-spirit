import {
  TrainingType,
  TrainingStatus,
  TrainingFunction,
} from "@focus/db/enums";
import type {
  Prisma,
  TrainingFeature as PrismaTrainingFeature,
  TrainingSplit as PrismaTrainingSplit,
  TrainingBatch as PrismaTrainingBatch,
  TrainingModel as PrismaTrainingModel,
} from "@focus/db";

export { TrainingType, TrainingStatus, TrainingFunction };

export type TrainingFeature = PrismaTrainingFeature;
export type TrainingSplit = PrismaTrainingSplit;
export type TrainingBatch = PrismaTrainingBatch;
export type TrainingModel = PrismaTrainingModel;

export type TrainingFunctionCounts = {
  train: number;
  validate: number;
  test: number;
  unassigned: number;
};

export type TrainingBatchListEntry = Prisma.TrainingBatchGetPayload<{
  include: {
    models: {
      select: {
        type: true;
        status: true;
        r2score: true;
        winner: true;
      };
    };
  };
}>;

export type TrainingJobs = {
  jobIds: string[];
};
