import { Suspense } from "react";
import Link from "next/link";
import { requireUser } from "@fiery/auth/server";
import { MyProfileButton } from "@/app/(components)/(privacy)/MyProfileButton";
import { routes } from "@lib/routes";
import { TEST_IDS } from "@lib/test-ids";

export default async function HomePage() {
  const { appUser, supabaseUser } = await requireUser();

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
          <div className="mt-1 flex items-center gap-3">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              {appUser.name} · {appUser.email}
            </p>
            <MyProfileButton userId={supabaseUser.id} />
          </div>
        </div>
        {appUser.isPlatformAdmin ? (
          <Link
            href={routes.admin.root}
            data-testid={TEST_IDS.openAdminLink}
            className="inline-flex w-fit shrink-0 text-sm font-medium text-zinc-900 underline underline-offset-4 dark:text-zinc-100"
          >
            Open admin
          </Link>
        ) : null}
      </div>
      <Suspense />
    </div>
  );
}
