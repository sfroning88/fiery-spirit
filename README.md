# Deep Focus

Portal + AI system for **senior healthcare investing** deployed to [deep-focus.vercel.app](https://deep-focus.vercel.app).
Simple [Next.js](https://nextjs.org) project bootstrapped with [create-next-app](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

**Like what you see? Reach out!**
Check out the full nitty gritty on [**LinkedIn**](https://www.linkedin.com/in/sean-froning/).
I'm always looking to apply full stack AI/ML to problems that actually matter for people.

## Libraries

This application uses lightweight and free `libraries`:

- `Tailwind colors` -- see official documentation at [tailwindcss.com/docs/colors](https://tailwindcss.com/docs/colors)
- `Lucide React` -- see the official documentation at [lucide.dev/icons/](https://lucide.dev/icons/)
- `React Icons` -- see the official documentation at [react-icons.github.io/react-icons/](https://react-icons.github.io/react-icons/)
- `Sonner Toast` -- see the official documentation at [ui.shadcn.com/docs/components/radix/sonner](https://ui.shadcn.com/docs/components/radix/sonner)

## Database

Connection and schema is managed by [`@focus/db`](packages/db):

- `Prisma v7` + `PostgreSQL v17.6` installations
- Config and migrations live under [`packages/db`](packages/db)
- [`prisma.config.ts`](packges/db/prisma.config.ts) points to `prisma/`
- CLI uses **`DIRECT_URL`** to run `prisma/migrations`
- Apps use **`DATABASE_URL`** to manage a _pooled connection_

Supabase **Auth** manages _security and IAM_:

- Database profiles stored as **`auth.users`**
- App profiles stored as **`iam.users`**
- `UUID` fields must match to create link
- Trigger [`on_auth_user_created`](packages/db/prisma/migrations/20260414000000_on_auth_user_created/migration.sql)

Developers can manage the database by:

- `pnpm db:generate` to regenerate the client
- `pnpm db:migrate <migration_name>` creates `.sql`
- `pnpm db:deploy` applies pending migrations
- `pnpm run db:prisma <prisma-args>` runs Prisma CLI
- _Do not run `pnpm prisma` bare from root_

## Developer

For `TypeScript`, frontend apps, and `Prisma`:

```sh
pnpm install
```

For `Python` and backend apps:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e "packages/python[dev]"
```

At root create:

- `.env.prod`
- `.env.local`

Switch between which `.env` is used with:

```sh
pnpm use:[prod|local]
```

Create symbolic links to each app and Prisma:

```sh
./scripts/load-symbolic-links.sh
```

## Analytics

This application uses a single **anonymous** cookie to track general web analytics using [**PostHog**](https://posthog.com/).
Tracking is only used for page visits and basic events.

## License

```md
MIT License

Copyright (c) 2026 Sean Froning
```
