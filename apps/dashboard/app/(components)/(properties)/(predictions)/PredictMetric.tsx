import { MetricFormat, DeltaBox, ValueBox } from "@focus/ui";

type PredictMetricsProps = {
  metricLabel: string;
  placeholderLabel: string;
  current: number | null;
  predicted: number | null;
  delta: number | null;
  isPending: boolean;
  format?: MetricFormat;
};

export function PredictMetric({
  metricLabel,
  placeholderLabel,
  current,
  predicted,
  delta,
  isPending,
  format = "currency",
}: PredictMetricsProps) {
  return (
    <div>
      <p className="text-[10px] md:text-[11px] font-medium text-white/50">
        {metricLabel}
      </p>
      <div
        className={`mt-1.5 grid gap-2 md:gap-3 ${
          current != null ? "grid-cols-3" : "grid-cols-1"
        }`}
      >
        {current != null && (
          <ValueBox label="Actual" value={current} format={format} />
        )}

        {predicted != null ? (
          <>
            <ValueBox
              label="Predicted"
              value={predicted}
              highlight
              format={format}
            />
            {delta != null && current != null && (
              <DeltaBox delta={delta} baseline={current} format={format} />
            )}
          </>
        ) : (
          <div
            className={`rounded-sm px-2 md:px-4 py-2.5 md:py-3 text-center bg-white/3 border border-white/10 ${
              current != null ? "col-span-2" : ""
            }`}
          >
            <p className="min-h-6 md:min-h-8 flex items-center justify-center">
              <span className="text-[10px] md:text-xs text-white/30">
                {isPending ? "Running model…" : "No prediction yet"}
              </span>
            </p>
            <p className="mt-0.5 text-[9px] md:text-[11px] text-white/40">
              {placeholderLabel}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
