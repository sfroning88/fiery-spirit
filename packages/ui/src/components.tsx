import type { ReactNode } from "react";
import { TrainingSignal, TrainingStage } from "@fiery/types";
import { ThumbsDown, ThumbsUp } from "iconoir-react";
import { iconClass, btnClass, selectClass, onSelectChange } from "./dynamics";
import {
  signalLabel,
  sourceValues,
  sourceLabel,
  stageValues,
  stageLabel,
} from "./tokens";

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
      className={`${iconClass} shrink-0 text-fiery-crimson-400 ${className ?? ""}`}
      strokeWidth={2}
    />
  );
}

export function SignalDropdown({
  value,
  onChange,
  className,
  testId,
}: {
  value: TrainingSignal;
  onChange: (value: TrainingSignal) => void;
  className?: string;
  testId?: string;
}) {
  return (
    <select
      aria-label="Signal"
      data-testid={testId}
      value={value}
      onChange={onSelectChange(onChange)}
      className={`${selectClass} ${className ?? ""}`}
    >
      {([TrainingSignal.deformation, TrainingSignal.seismic] as const).map(
        (signal) => (
          <option key={signal} value={signal}>
            {signalLabel[signal]}
          </option>
        ),
      )}
    </select>
  );
}

export function SourceDropdown({
  value,
  onChange,
  className,
  testId,
}: {
  value: (typeof sourceValues)[number];
  onChange: (value: (typeof sourceValues)[number]) => void;
  className?: string;
  testId?: string;
}) {
  return (
    <select
      aria-label="Source"
      data-testid={testId}
      value={value}
      onChange={onSelectChange(onChange)}
      className={`${selectClass} ${className ?? ""}`}
    >
      {sourceValues.map((source) => (
        <option key={source} value={source}>
          {sourceLabel[source]}
        </option>
      ))}
    </select>
  );
}

export function StageDropdown({
  value,
  onChange,
  className,
  testId,
}: {
  value: TrainingStage;
  onChange: (value: TrainingStage) => void;
  className?: string;
  testId?: string;
}) {
  return (
    <select
      aria-label="Stage"
      data-testid={testId}
      value={value}
      onChange={onSelectChange(onChange)}
      className={`${selectClass} ${className ?? ""}`}
    >
      {stageValues.map((stage) => (
        <option key={stage} value={stage}>
          {stageLabel[stage]}
        </option>
      ))}
    </select>
  );
}
