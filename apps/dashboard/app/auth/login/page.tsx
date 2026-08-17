import { Suspense } from "react";
import Link from "next/link";
import { LoginForm } from "@focus/auth";
import { routes } from "@lib/routes";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-zinc-50 px-4 dark:bg-black">
      <Suspense fallback={<p className="text-sm text-zinc-500">Loading…</p>}>
        <LoginForm />
      </Suspense>
      <Link
        href={routes.root}
        className="text-sm text-zinc-600 underline underline-offset-4 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200"
      >
        Back to home
      </Link>
    </div>
  );
}
