"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { PredictionType, TrainingType, POSTHOG_EVENTS } from "@focus/types";
import { givePredictionFeedbackAction } from "../(actions)/prediction-action";
import { QUERY_KEYS } from "@/lib/constants";

type GivePredictionFeedbackArgs = {
  type: PredictionType;
  modelType: TrainingType;
  modelBatchId: string;
  propertyId: string;
  feedbackScore: number;
};

export function useGivePredictionFeedback(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (args: GivePredictionFeedbackArgs) =>
      givePredictionFeedbackAction({
        type: args.type,
        modelType: args.modelType,
        modelBatchId: args.modelBatchId,
        propertyId: args.propertyId,
        feedbackScore: args.feedbackScore,
      }),
    onSuccess: async (_data, args) => {
      posthog.capture(POSTHOG_EVENTS.prediction_feedback_given, {
        type: args.type,
        modelType: args.modelType,
        modelBatchId: args.modelBatchId,
        propertyId: args.propertyId,
        feedbackScore: args.feedbackScore,
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.predictions(userId, args.propertyId),
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.propertyCard(userId, args.propertyId),
      });
    },
  });
}
