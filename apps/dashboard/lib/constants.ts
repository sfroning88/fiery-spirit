import { ModelTier, ModelRole, TrainingSampleSource } from "@fiery/types";

export const PROVIDER_STALE_TIME = 60 * 1000;

export const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

export const USER_ID_COOKIE_NAME = "fiery-spirit-user-id";

export const COOKIE_BANNER_DISMISSED_KEY =
  "fiery-spirit-cookie-banner-dismissed";

export const COOKIE_BANNER_SYNC_EVENT = `${COOKIE_BANNER_DISMISSED_KEY}:sync`;

export const COOKIE_BANNER_MESSAGE =
  "This site uses one first-party cookie for anonymous analytics. No third-party tracking.";

export const QUERY_STALE_TIME = 60 * 60 * 5;

export const QUERY_KEYS = {
  user: (userId: string) => ["user", userId] as const,
  volcanoes: (userId: string) => ["volcanoes", userId] as const,
  volcano: (volcanoId: string) => ["volcano", volcanoId] as const,
  interferogram: (interferogramId: string) =>
    ["interferogram", interferogramId] as const,
  seismicEvent: (seismicEventId: string) =>
    ["seismicEvent", seismicEventId] as const,
  source: (source: TrainingSampleSource) => ["source", source] as const,
  version: (versionId: string) => ["version", versionId] as const,
  contract: (contractId: string) => ["contract", contractId] as const,
  session: (sessionId: string) => ["session", sessionId] as const,
  artifacts: (userId: string) => ["artifacts", userId] as const,
  artifact: (tier: ModelTier, role: ModelRole) =>
    ["artifact", tier, role] as const,
};

export const CACHE_STALE_TIME = 60 * 60 * 60;

export const PRIVACY_DOC_PATH = "lib/docs/PRIVACY.md";

export const MOBILE_BREAKPOINT = 768;
