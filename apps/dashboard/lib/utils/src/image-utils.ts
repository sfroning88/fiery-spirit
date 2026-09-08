const HTTP_PROTOCOLS = new Set(["http:", "https:"]);

export function httpSafeImageUrl(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (trimmed.startsWith("/") && !trimmed.startsWith("//")) {
    if (trimmed.includes("\\") || trimmed.includes("..")) return null;
    return trimmed;
  }
  try {
    const url = new URL(trimmed);
    if (!HTTP_PROTOCOLS.has(url.protocol)) return null;
    return url.href;
  } catch {
    return null;
  }
}
