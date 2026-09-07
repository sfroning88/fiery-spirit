import { type ReactNode } from "react";
import { getSession } from "@fiery/auth/server";

export default async function HomeLayout({
  children,
}: {
  children: ReactNode;
}) {
  const { supabaseUser } = await getSession();
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white px-6 py-4 dark:border-zinc-800 dark:bg-zinc-900">
        {supabaseUser ? (
          <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
            Signed-in area
          </p>
        ) : (
          <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
            Create profile area
          </p>
        )}
      </header>
      <div className="mx-auto max-w-3xl px-6 py-8">{children}</div>
    </div>
  );
}
