"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS, QUERY_STALE_TIME } from "@/lib/constants";
import { fetchPropertiesAction } from "../(actions)/property-action";
import type { PropertyListEntry } from "@focus/types";

export function useFetchProperties(
  userId: string,
  initialData?: PropertyListEntry[],
) {
  return useQuery<PropertyListEntry[]>({
    queryKey: QUERY_KEYS.properties(userId),
    queryFn: () => fetchPropertiesAction({}),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId,
    initialData,
  });
}
