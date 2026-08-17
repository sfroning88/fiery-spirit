import { unstable_cache } from "next/cache";
import { CACHE_STALE_TIME, QUERY_KEYS } from "@/lib/constants";
import type { TrainingBatchListEntry } from "@focus/types";
import { TrainingService } from "@lib/services";

const trainingService = new TrainingService();

export async function fetchBatchesCached(
  userId: string,
): Promise<TrainingBatchListEntry[]> {
  return unstable_cache(
    async () => {
      return await trainingService.fetchBatches();
    },
    [...QUERY_KEYS.trainingBatches(userId)],
    {
      tags: [...QUERY_KEYS.trainingBatches(userId)],
      revalidate: CACHE_STALE_TIME,
    },
  )();
}
