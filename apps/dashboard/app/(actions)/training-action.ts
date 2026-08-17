"use server";

import { z } from "zod";
import { platformAdminAction } from "@focus/auth/server";
import { TrainingService } from "@lib/services";
import {
  PREDICTION_TYPES,
  type TrainingBatchListEntry,
  type TrainingFunctionCounts,
  type TrainingJobs,
  ModelShuffleResponse,
} from "@focus/types";

const trainingService = new TrainingService();

const shuffleGroupsSchema = z.object({});

export const shuffleGroupsAction = platformAdminAction(
  shuffleGroupsSchema,
  async (): Promise<ModelShuffleResponse> => {
    return await trainingService.shuffleGroups();
  },
);

const trainModelsSchema = z.object({});

export const trainModelsAction = platformAdminAction(
  trainModelsSchema,
  async (): Promise<TrainingJobs> => {
    const responses = await Promise.all(
      PREDICTION_TYPES.map((predictionType) =>
        trainingService.train(predictionType),
      ),
    );
    return { jobIds: responses.flatMap((response) => response.jobIds) };
  },
);

const fetchFunctionCountsSchema = z.object({});

export const fetchFunctionCountsAction = platformAdminAction(
  fetchFunctionCountsSchema,
  async (): Promise<TrainingFunctionCounts> => {
    return await trainingService.fetchFunctionCounts();
  },
);

const fetchBatchesSchema = z.object({});

export const fetchBatchesAction = platformAdminAction(
  fetchBatchesSchema,
  async (): Promise<TrainingBatchListEntry[]> => {
    return await trainingService.fetchBatches();
  },
);
