"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { POSTHOG_EVENTS } from "@focus/types";
import { shuffleGroupsAction } from "../(actions)/training-action";
import { QUERY_KEYS } from "@/lib/constants";

export function useShuffleGroups(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => shuffleGroupsAction({}),
    onSuccess: async (data) => {
      posthog.capture(POSTHOG_EVENTS.shuffle_training_groups, {
        job_id: data.jobId,
      });
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.trainingBatches(userId),
        }),
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.trainingFunctionCounts(userId),
        }),
      ]);
    },
  });
}
