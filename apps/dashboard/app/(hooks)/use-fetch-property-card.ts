"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS, QUERY_STALE_TIME } from "@/lib/constants";
import { fetchPropertyCardAction } from "../(actions)/property-action";
import type { PropertyCard } from "@focus/types";

export function useFetchPropertyCard(
  userId: string,
  propertyId: string | null,
) {
  return useQuery<PropertyCard>({
    queryKey: QUERY_KEYS.propertyCard(userId, propertyId ?? ""),
    queryFn: () => fetchPropertyCardAction({ id: propertyId! }),
    staleTime: QUERY_STALE_TIME,
    enabled: !!userId && !!propertyId,
  });
}
