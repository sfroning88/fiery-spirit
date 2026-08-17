import { authRoutes } from "@focus/auth/routes";

export const routes = {
  ...authRoutes,
  base: {
    root: "/" as const,
    home: "/home" as const,
  },
  admin: {
    root: "/admin" as const,
  },
} as const;
