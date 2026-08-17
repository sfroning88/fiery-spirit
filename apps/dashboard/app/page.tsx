import Link from "next/link";
import Image from "next/image";
import { getSession } from "@focus/auth/server";
import { routes } from "@lib/routes";

export default async function Home() {
  const { supabaseUser } = await getSession();
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between gap-10 py-24 px-8 sm:items-start">
        <Image
          className="dark:invert"
          src="/default/next.svg"
          alt="Next.js logo"
          width={100}
          height={20}
          priority
        />
        <div className="flex flex-col gap-4">
          <h1 className="max-w-md text-3xl font-semibold leading-tight text-black dark:text-zinc-50">
            Deep Focus
          </h1>
          <p className="max-w-lg text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            {supabaseUser
              ? `Signed in as ${supabaseUser.email ?? supabaseUser.id}.`
              : "Anyone can open the sign-in page and try to authenticate."}
          </p>
          <nav className="flex flex-wrap gap-3 text-sm font-medium">
            <Link
              href={routes.auth.login}
              className="rounded-full border border-zinc-300 px-4 py-2 text-zinc-900 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-900"
            >
              Sign in
            </Link>
            {supabaseUser ? (
              <>
                <Link
                  href={routes.base.home}
                  className="rounded-full bg-zinc-900 px-4 py-2 text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
                >
                  Dashboard
                </Link>
                <Link
                  href={routes.admin.root}
                  className="rounded-full border border-amber-600 px-4 py-2 text-amber-900 hover:bg-amber-50 dark:border-amber-500 dark:text-amber-100 dark:hover:bg-amber-950"
                >
                  Admin
                </Link>
              </>
            ) : null}
          </nav>
        </div>
      </main>
    </div>
  );
}
