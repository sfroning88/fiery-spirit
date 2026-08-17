"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import posthog from "posthog-js";
import { POSTHOG_EVENTS, type CreateSnapshotArgs } from "@focus/types";
import { createSnapshotAction } from "../(actions)/property-action";
import { QUERY_KEYS } from "@/lib/constants";

export function useCreateSnapshot(userId: string) {
  const queryClient = useQueryClient();
  const router = useRouter();
  return useMutation({
    mutationFn: (args: CreateSnapshotArgs) => createSnapshotAction(args),
    onSuccess: async (_data, args) => {
      posthog.capture(POSTHOG_EVENTS.property_snapshot_created, {
        property_id: args.propertyId,
        reported_at: args.reportedAt,
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.propertyCard(userId, args.propertyId),
      });
      await queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.properties(userId),
      });
      router.refresh();
    },
  });
}
