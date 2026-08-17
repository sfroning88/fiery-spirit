import { unstable_cache } from "next/cache";
import { CACHE_STALE_TIME, QUERY_KEYS } from "@/lib/constants";
import type { PropertyListEntry } from "@focus/types";
import { PropertyService } from "@lib/services";

export async function fetchPropertiesCached(
  userId: string,
): Promise<PropertyListEntry[]> {
  return unstable_cache(
    async () => {
      return await PropertyService.fetchProperties();
    },
    [...QUERY_KEYS.properties(userId)],
    {
      tags: [...QUERY_KEYS.properties(userId)],
      revalidate: CACHE_STALE_TIME,
    },
  )();
}
