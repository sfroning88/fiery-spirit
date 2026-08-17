import { Suspense } from "react";
import Link from "next/link";
import { routes } from "@lib/routes";
import { TEST_IDS } from "@lib/test-ids";
import { requirePlatformAdmin } from "@focus/auth/server";
import type { TrainingBatchListEntry } from "@focus/types";
import { fetchBatchesCached } from "@lib/api/cache/training-cache";
import { BatchListAsync } from "@/app/(components)/(training)/BatchListAsync";
import { BatchListSkeleton } from "@/app/(components)/(training)/BatchListSkeleton";

export default async function AdminPage() {
  const { supabaseUser } = await requirePlatformAdmin();
  const batchesPromise = fetchBatchesCached(supabaseUser.id).catch(
    (): TrainingBatchListEntry[] => [],
  );

  return (
    <div className="flex flex-col gap-6" data-testid={TEST_IDS.adminScreen}>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1
            className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50"
            data-testid={TEST_IDS.adminHeading}
          >
            Admin
          </h1>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
            Platform admin tools — model training and management.
          </p>
        </div>
        <Link
          href={routes.base.home}
          data-testid={TEST_IDS.backToDashboardLink}
          className="w-fit shrink-0 text-sm font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-100"
        >
          Back to dashboard
        </Link>
      </div>
      <Suspense fallback={<BatchListSkeleton />}>
        <BatchListAsync initialDataPromise={batchesPromise} />
      </Suspense>
    </div>
  );
}
