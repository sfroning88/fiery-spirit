import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { Cinzel, DM_Sans, DM_Mono, Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import { getSession } from "@fiery/auth/server";
import { routes } from "@/lib/routes";
import Link from "next/link";
import { CookieBanner } from "@/app/(components)/(privacy)/CookieBanner";
import { PrivacyNotice } from "@/app/(components)/(privacy)/PrivacyNotice";
import "./globals.css";
import { QueryProvider, SupabaseProvider } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const focusDisplay = Cinzel({
  variable: "--font-focus-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const dmMono = DM_Mono({
  variable: "--font-dm-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Fiery Spirit",
  description: "Focus Healthcare Partners dashboard",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { supabaseUser } = await getSession();
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${focusDisplay.variable} ${dmSans.variable} ${dmMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header>
          <Link href={routes.base.home}>Dashboard</Link>
          {supabaseUser ? (
            <Link href={routes.base.home}>Signed in</Link>
          ) : (
            <Link href={routes.auth.login}>Create profile</Link>
          )}
        </header>
        <QueryProvider>
          <SupabaseProvider>{children}</SupabaseProvider>
        </QueryProvider>
        <CookieBanner />
        <PrivacyNotice />
        <Toaster richColors closeButton position="top-center" />
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
