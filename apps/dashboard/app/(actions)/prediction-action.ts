"use server";

import { z } from "zod";
import { selfUserAction } from "@focus/auth/server";
import { PredictionType, TrainingType } from "@focus/db";
import { PredictionService } from "@lib/services";
import { PREDICTION_TYPES, type PredictionsForProperty } from "@focus/types";

const predictionService = new PredictionService();

const predictModelsSchema = z.object({
  propertyId: z.string(),
  multiEnabled: z.boolean().default(false),
});

export const predictModelsAction = selfUserAction(
  predictModelsSchema,
  async (ctx): Promise<PredictionsForProperty> => {
    const entries = await Promise.all(
      PREDICTION_TYPES.map(async (predictionType) => {
        const response = await predictionService.predict(predictionType, {
          propertyId: ctx.propertyId,
          multiEnabled: ctx.multiEnabled || false,
        });
        return [predictionType, response] as const;
      }),
    );
    return Object.fromEntries(entries) as PredictionsForProperty;
  },
);

const givePredictionFeedbackSchema = z.object({
  type: z.nativeEnum(PredictionType),
  modelType: z.nativeEnum(TrainingType),
  modelBatchId: z.string(),
  propertyId: z.string(),
  feedbackScore: z.number().min(0).max(1),
});

export const givePredictionFeedbackAction = selfUserAction(
  givePredictionFeedbackSchema,
  async (ctx): Promise<void> => {
    await predictionService.givePredictionFeedback(
      ctx.type,
      ctx.modelType,
      ctx.modelBatchId,
      ctx.propertyId,
      ctx.feedbackScore,
    );
  },
);
