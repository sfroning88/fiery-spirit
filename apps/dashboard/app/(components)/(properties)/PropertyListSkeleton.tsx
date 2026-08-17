export function PropertyListSkeleton() {
  return (
    <div className="space-y-4 animate-pulse font-data">
      <div className="h-8 w-40 rounded bg-white/10" />
      <div className="flex gap-2">
        <div className="h-10 flex-1 rounded-md bg-white/4 border border-white/10" />
        <div className="h-10 w-20 rounded-md bg-white/4 border border-white/10" />
        <div className="h-10 w-16 rounded-md bg-white/4 border border-white/10" />
        <div className="h-10 w-16 rounded-md bg-white/4 border border-white/10" />
      </div>
      <div className="border border-white/10 rounded-md overflow-hidden bg-surface-dark">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="flex items-center justify-between gap-3 px-5 py-4 border-b border-white/5 last:border-0"
          >
            <div className="flex flex-col gap-1.5 min-w-0">
              <div className="h-4 w-48 rounded bg-white/10" />
              <div className="h-3 w-64 rounded bg-white/5" />
            </div>
            <div className="flex items-center gap-3">
              <div className="h-6 w-16 rounded-sm bg-white/5" />
              <div className="h-8 w-20 rounded-md border border-white/10 bg-white/4" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
