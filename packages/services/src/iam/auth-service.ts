import "server-only";

import { db } from "@focus/db";
import type { SupabaseClient } from "@supabase/supabase-js";
import { SignInResult, SignOutResult, CurrentUser } from "@focus/types";

export const AuthService = {
  async signIn(params: {
    email: string;
    password: string;
    supabaseClient: SupabaseClient;
  }): Promise<SignInResult> {
    const { error } = await params.supabaseClient.auth.signInWithPassword({
      email: params.email,
      password: params.password,
    });
    if (error) return { ok: false, error: "Invalid email or password" };
    return { ok: true };
  },

  async signOut(params: {
    supabaseClient: SupabaseClient;
  }): Promise<SignOutResult> {
    const { error } = await params.supabaseClient.auth.signOut();
    if (error) return { ok: false, error: error.message };
    return { ok: true };
  },

  async fetchCurrentUser(userId: string): Promise<CurrentUser | null> {
    return db.user.findUnique({
      where: { id: userId },
    });
  },
};
