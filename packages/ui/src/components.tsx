import type { ReactNode } from "react";
import { formatCurrency, formatPercent } from "@focus/utils";
import { MetricFormat } from "./types";

function formatMetricValue(value: number, format: MetricFormat): string {
  return format === "percent" ? formatPercent(value) : formatCurrency(value);
}
import { ThumbsDown, ThumbsUp } from "iconoir-react";

const iconClass = "h-4 w-4 md:h-[18px] md:w-[18px]";

const btnClass = `
  inline-flex items-center justify-center rounded-md border transition-colors p-1.5 md:p-2
  border-white/15 bg-white/4 text-white/80 hover:bg-white/8
  disabled:opacity-40 disabled:pointer-events-none
`;

export function Dot({ className }: { className?: string }) {
  return (
    <span className={`select-none ${className ?? "text-white/25"}`}>·</span>
  );
}

export function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-sm border border-white/15 px-1.5 md:px-2 py-0.5 text-[10px] md:text-xs text-white/50 font-data-mono whitespace-nowrap">
      {children}
    </span>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h3 className="text-[10px] md:text-[11px] font-semibold uppercase tracking-[0.15em] text-white/40">
      {children}
    </h3>
  );
}

export function KpiCard({
  label,
  sublabel,
  accent,
  children,
}: {
  label: string;
  sublabel: string;
  accent?: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className={`rounded-sm px-3 md:px-4 py-2.5 md:py-3 ${
        accent
          ? "bg-fhp-blue-800 text-white"
          : "border border-white/10 text-white"
      }`}
    >
      <p className="text-[10px] md:text-[11px] font-medium uppercase tracking-wider text-white/50">
        {label}
      </p>
      <p className="mt-0.5 md:mt-1 text-lg md:text-2xl font-semibold font-data-mono leading-tight">
        {children}
      </p>
      <p className="mt-0.5 text-[10px] md:text-xs text-white/40">{sublabel}</p>
    </div>
  );
}

export function ValueBox({
  label,
  value,
  highlight,
  format = "currency",
}: {
  label: string;
  value: number | null;
  highlight?: boolean;
  format?: MetricFormat;
}) {
  return (
    <div
      className={`rounded-sm px-2 md:px-4 py-2.5 md:py-3 text-center ${
        highlight
          ? "bg-fhp-blue-800/60 border border-fhp-blue-600/40"
          : "bg-white/3 border border-white/10"
      }`}
    >
      {value === null ? (
        <p
          className="min-h-6 md:min-h-8 flex items-center justify-center"
          aria-label="Not available"
        >
          <span className="block w-9 md:w-11 max-w-[60%] h-px bg-white/35 rounded-full" />
        </p>
      ) : (
        <p className="text-base md:text-xl font-semibold font-data-mono text-white">
          {formatMetricValue(value, format)}
        </p>
      )}
      <p className="mt-0.5 text-[9px] md:text-[11px] text-white/40">{label}</p>
    </div>
  );
}

export function DeltaBox({
  delta,
  baseline,
  format = "currency",
}: {
  delta: number;
  baseline: number | null;
  format?: MetricFormat;
}) {
  const pct =
    baseline != null && baseline !== 0
      ? ((delta / Math.abs(baseline)) * 100).toFixed(1)
      : null;

  const isPositive = delta > 0;
  const isNeutral = delta === 0;

  const color = isNeutral
    ? "text-white/50"
    : isPositive
      ? "text-green-400"
      : "text-red-400";

  const sign = isPositive ? "+" : "";

  return (
    <div className="rounded-sm px-2 md:px-4 py-2.5 md:py-3 text-center bg-white/3 border border-white/10">
      <p
        className={`text-base md:text-xl font-semibold font-data-mono ${color}`}
      >
        {format === "percent"
          ? `${isPositive ? "+" : ""}${delta.toFixed(2)}%`
          : `${sign}${formatCurrency(delta)}`}
      </p>
      {pct != null ? (
        <p className={`mt-0.5 text-[9px] md:text-[11px] ${color}`}>
          {sign}
          {pct}%
        </p>
      ) : (
        <p className="mt-0.5 text-[9px] md:text-[11px] text-white/40">
          Variance
        </p>
      )}
    </div>
  );
}

export function FeedbackThumbs({
  onPositive,
  onNegative,
  disabled,
  className,
}: {
  onPositive: () => void;
  onNegative: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <div
      className={`inline-flex items-center gap-1.5 ${className ?? ""}`}
      role="group"
      aria-label="Prediction feedback"
    >
      <button
        type="button"
        disabled={disabled}
        onClick={onPositive}
        className={btnClass}
        aria-label="Mark prediction as helpful"
      >
        <ThumbsUp className={iconClass} strokeWidth={2} />
      </button>
      <button
        type="button"
        disabled={disabled}
        onClick={onNegative}
        className={btnClass}
        aria-label="Mark prediction as not helpful"
      >
        <ThumbsDown className={iconClass} strokeWidth={2} />
      </button>
    </div>
  );
}

export function FeedbackThanksIcon({
  variant,
  className,
}: {
  variant: "up" | "down";
  className?: string;
}) {
  const Icon = variant === "up" ? ThumbsUp : ThumbsDown;
  return (
    <Icon
      className={`${iconClass} shrink-0 text-fhp-blue-400 ${className ?? ""}`}
      strokeWidth={2}
    />
  );
}
