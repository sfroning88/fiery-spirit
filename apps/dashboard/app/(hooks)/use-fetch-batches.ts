"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS, QUERY_STALE_TIME } from "@/lib/constants";
import { fetchBatchesAction } from "../(actions)/training-action";
import type { TrainingBatchListEntry } from "@focus/types";

export function useFetchBatches(
  userId: string,
  initialData?: TrainingBatchListEntry[],
) {
  return useQuery<TrainingBatchListEntry[]>({
    queryKey: QUERY_KEYS.trainingBatches(userId),
    queryFn: () => fetchBatchesAction({}),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId,
    initialData,
  });
}
