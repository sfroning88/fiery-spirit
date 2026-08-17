# Identity Access Management

Last updated: **May 2026**

## Users

Basic email and password user management. There are two separate user entities:

- `Supabase User`: Tracks active sessions by `Supabase auth`
- `Platform User`: Tracks permissions and memberships by profile

Users exist as their own entity:

- Users have an `Authentication` entity within Supabase
- Users have a `User` entity within our `Users` table
- The two entities are linked by `uuid`
- Membership, role, and permissions are organization scoped
- Users can belong to multiple organizations at one time

The main API paths are:

- `/profile` for editing basic information and security details
- `/auth/login` for signing into a `Supabase client` session
- `/unauthorized` if the user is not authenticated by Supabase

Upon accepting an invitation for the first time, users will not have any permissions. They must be granted via `/users` by someone else in that organization.

## Authentication

The platform relies on `Supabase client` for sessions. This is basic and secure email/password management.

Interaction with the platform is three basic levels:

- The `User Session` is required to do anything managed by `Supabase client`
- Every `server action` within the platform is guarded by `@focus/auth`
- All `env secrets` are stored `server-only` from `@focus/config`

Theres a couple basic methods for auth checks:

- `selfUserAction`: Must be a signed-in Supabase user
- `selfUserAction`: Must be own self for profile
- `requirePlatformAdmin`: User must be an `ADMIN`

## Admin

**Only Platform Admins have special privileges** from the `/admin` panel. These activities are guarded by `requirePlatformAdmin`.
