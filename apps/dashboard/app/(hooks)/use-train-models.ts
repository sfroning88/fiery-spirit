"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { TrainingJobs, POSTHOG_EVENTS } from "@focus/types";
import { trainModelsAction } from "../(actions)/training-action";
import { QUERY_KEYS } from "@/lib/constants";

export function useTrainModels(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (): Promise<TrainingJobs> => trainModelsAction({}),
    onSuccess: async (data) => {
      posthog.capture(POSTHOG_EVENTS.model_training_started, {
        job_count: data.jobIds.length,
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.trainingBatches(userId),
      });
    },
  });
}
