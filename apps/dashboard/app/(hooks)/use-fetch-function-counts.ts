"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS, QUERY_STALE_TIME } from "@/lib/constants";
import { fetchFunctionCountsAction } from "../(actions)/training-action";
import type { TrainingFunctionCounts } from "@focus/types";

export function useFetchFunctionCounts(userId: string) {
  return useQuery<TrainingFunctionCounts>({
    queryKey: QUERY_KEYS.trainingFunctionCounts(userId),
    queryFn: () => fetchFunctionCountsAction({}),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId,
  });
}
