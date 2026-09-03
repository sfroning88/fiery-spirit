"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS, QUERY_STALE_TIME } from "@/lib/constants";
import { VolcanoDashboard } from "@fiery/types";
import { fetchVolcanoesAction } from "../(actions)/volcano-action";

export function useFetchVolcanoes(
  userId: string,
  initialData?: VolcanoDashboard[],
) {
  return useQuery<VolcanoDashboard[]>({
    queryKey: QUERY_KEYS.volcanoes(userId),
    queryFn: () => fetchVolcanoesAction(),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId,
    initialData,
  });
}
