"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import posthog from "posthog-js";
import { QUERY_KEYS } from "@/lib/constants";
import { POSTHOG_EVENTS, ApiPromoteResponse } from "@fiery/types";
import { promoteAction } from "../(actions)/admin-action";

export function usePromote(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<ApiPromoteResponse> => promoteAction(),
    onSuccess: async (data) => {
      posthog.capture(POSTHOG_EVENTS.promote, {
        user_id: userId,
        artifact_count: data.evaluatedModels.length,
      });
      await Promise.all([
        data.evaluatedModels.map((evaluatedModel) =>
          queryClient.invalidateQueries({
            queryKey: QUERY_KEYS.artifact(
              evaluatedModel.tier,
              evaluatedModel.role,
            ),
          }),
        ),
      ]);
    },
  });
}
