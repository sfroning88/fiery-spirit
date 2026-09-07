import { authRoutes } from "@fiery/auth/routes";

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

export const publicAppPaths = [routes.base.root, routes.base.home] as const;

export const adminAppPaths = [routes.admin.root];
