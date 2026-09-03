import { unstable_cache } from "next/cache";
import { CACHE_STALE_TIME, QUERY_KEYS } from "@/lib/constants";
import type { VolcanoDashboard } from "@fiery/types";
import { VolcanoService } from "@/lib/services";

const volcanoService = new VolcanoService();

export async function fetchVolcanoesCached(
  userId: string,
): Promise<VolcanoDashboard[]> {
  return unstable_cache(
    async () => {
      return await volcanoService.fetchVolcanoes();
    },
    [...QUERY_KEYS.volcanoes(userId)],
    {
      tags: [...QUERY_KEYS.volcanoes(userId)],
      revalidate: CACHE_STALE_TIME,
    },
  )();
}
