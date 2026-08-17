export function toNum(value: unknown): number {
  if (value == null) return 0;
  if (typeof value === "number") return value;
  if (typeof value === "string") return parseFloat(value) || 0;
  if (typeof value === "object" && "toNumber" in value) {
    return (value as { toNumber: () => number }).toNumber();
  }
  return Number(value) || 0;
}

export function formatDecimal(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "number") return value.toLocaleString();
  return String(value);
}

export function formatCurrency(value: unknown): string {
  const n = toNum(value);
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

export function formatCompactCurrency(value: unknown): string {
  const n = toNum(value);
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(0)}K`;
  return formatCurrency(value);
}

export function formatPercent(value: unknown): string {
  const n = toNum(value);
  return `${n.toFixed(2)}%`;
}

export enum OccupancyTier {
  high = "high",
  mid = "mid",
  low = "low",
}

export function getOccupancyTier(occ: unknown): OccupancyTier {
  const n = toNum(occ);
  if (n >= 80) return OccupancyTier.high;
  if (n >= 65) return OccupancyTier.mid;
  return OccupancyTier.low;
}

export function formatDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function formatDateTime(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

const CALENDAR_DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

export function parseCalendarDate(raw: string): Date {
  const match = CALENDAR_DATE_RE.exec(raw);
  if (!match) {
    throw new Error(
      `Invalid calendar date "${raw}" — expected YYYY-MM-DD with no time component`,
    );
  }
  const [, year, month, day] = match;
  return new Date(Date.UTC(Number(year), Number(month) - 1, Number(day)));
}

export enum SortField {
  name = "name",
  msa = "msa",
  occupancy = "occupancy",
  snapshots = "snapshots",
}

export enum SortDir {
  asc = "asc",
  desc = "desc",
}

export type RecencySortable = {
  timestamp?: unknown;
  reportedAt?: unknown;
  createdAt?: unknown;
};

export function dateLikeToMs(value: unknown): number {
  if (value == null) return 0;
  if (value instanceof Date) {
    const t = value.getTime();
    return Number.isNaN(t) ? 0 : t;
  }
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const t = Date.parse(value);
    return Number.isNaN(t) ? 0 : t;
  }
  return 0;
}

export function getRecencySortKey(item: RecencySortable): number {
  return dateLikeToMs(item.timestamp ?? item.reportedAt ?? item.createdAt);
}

export function sortByRecencyDesc<T extends RecencySortable>(
  items: readonly T[],
): T[] {
  return [...items].sort((a, b) => getRecencySortKey(b) - getRecencySortKey(a));
}

export function getLatestByRecency<T extends RecencySortable>(
  items: readonly T[] | null | undefined,
): T | undefined {
  return sortByRecencyDesc(items ?? [])[0];
}
