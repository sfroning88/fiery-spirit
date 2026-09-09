import { Suspense } from "react";
import Link from "next/link";
import { getSession } from "@fiery/auth/server";
import { AppUserProfileNotFoundError, UserService } from "@fiery/services";
import { MyProfileButton } from "@/app/(components)/(privacy)/MyProfileButton";
import { routes } from "@lib/routes";
import { TEST_IDS } from "@lib/test-ids";
import { VolcanoDashboard } from "@fiery/types";
import { fetchVolcanoesCached } from "@/lib/api/cache/volcano-cache";
import { HomeSkeleton } from "@/app/(components)/(home)/HomeSkeleton";
import { HomeAsync } from "@/app/(components)/(home)/HomeAsync";

export default async function HomePage() {
  const { supabaseUser } = await getSession();
  let appUser = null;
  if (supabaseUser) {
    try {
      appUser = await UserService.ensureAppUserFromSupabaseAuth(supabaseUser);
    } catch (error) {
      if (error instanceof AppUserProfileNotFoundError) {
        appUser = null;
      } else {
        throw error;
      }
    }
  }
  const volcanoesPromise = fetchVolcanoesCached(
    supabaseUser ? supabaseUser.id : null,
  ).catch((): VolcanoDashboard[] => []);

  return (
    <div className="flex flex-col gap-6" data-testid={TEST_IDS.homeScreen}>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1
            className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50"
            data-testid={TEST_IDS.dashboardHeading}
          >
            Dashboard
          </h1>
          {supabaseUser && appUser ? (
            <div className="mt-1 flex items-center gap-3">
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {appUser.name} · {appUser.email}
              </p>
              <MyProfileButton userId={supabaseUser.id} />
            </div>
          ) : (
            <div className="mt-1 flex flex-col gap-2 sm:flex-row sm:items-center">
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Create profile to unlock all features
              </p>
              <Link
                href={`${routes.auth.login}?next=${routes.base.home}`}
                data-testid={TEST_IDS.createProfileLink}
                className="inline-flex w-fit shrink-0 text-sm font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-100"
              >
                Create profile
              </Link>
            </div>
          )}
        </div>
        {appUser && appUser.isPlatformAdmin ? (
          <Link
            href={routes.admin.root}
            data-testid={TEST_IDS.openAdminLink}
            className="inline-flex w-fit shrink-0 text-sm font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-100"
          >
            Open admin
          </Link>
        ) : null}
      </div>
      <Suspense fallback={<HomeSkeleton />}>
        <HomeAsync initialDataPromise={volcanoesPromise} />
      </Suspense>
    </div>
  );
}
