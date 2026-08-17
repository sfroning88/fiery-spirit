import type { User as SupabaseUser } from "@supabase/supabase-js";
import type { User as PrismaUser } from "@focus/db";

export type SessionProfile = {
  supabaseUser: SupabaseUser | null;
};

export type CurrentUser = PrismaUser;

export type SignInResult = { ok: true } | { ok: false; error: string };

export type SignOutResult = { ok: true } | { ok: false; error: string };
