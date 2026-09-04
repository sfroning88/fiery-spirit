"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS, QUERY_STALE_TIME } from "@/lib/constants";
import { ModelDashboard } from "@fiery/types";
import { fetchModelsAction } from "../(actions)/admin-action";

export function useFetchModels(userId: string, initialData?: ModelDashboard[]) {
  return useQuery<ModelDashboard[]>({
    queryKey: QUERY_KEYS.artifacts(userId),
    queryFn: () => fetchModelsAction(),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId,
    initialData,
  });
}
