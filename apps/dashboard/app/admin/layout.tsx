import { type ReactNode } from "react";
import { requirePlatformAdmin } from "@focus/auth/server";

export default async function AdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  await requirePlatformAdmin();
  return (
    <div className="min-h-screen bg-amber-50 dark:bg-zinc-950">
      <header className="border-b border-amber-200 bg-amber-100 px-6 py-4 dark:border-amber-900 dark:bg-amber-950">
        <p className="text-sm font-semibold text-amber-950 dark:text-amber-100">
          Platform admin
        </p>
      </header>
      <div className="mx-auto max-w-3xl px-6 py-8">{children}</div>
    </div>
  );
}
