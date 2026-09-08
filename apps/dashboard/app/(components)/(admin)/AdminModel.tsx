"use client";

import {
  Badge,
  Dot,
  metricLabel,
  roleColors,
  roleLabel,
  signalColors,
  signalLabel,
  tierColors,
  tierLabel,
} from "@fiery/ui";
import {
  formatDateTime,
  formatKeyMetrics,
  formatMetricValue,
} from "@fiery/utils";
import type { ModelDashboard } from "@fiery/types";

type AdminModelProps = {
  model: ModelDashboard;
  isMobile: boolean;
};

export function AdminModel({ model, isMobile }: AdminModelProps) {
  const signal = model.session.signal;
  const registryKey = `${model.tier}/${model.role}`;
  const metrics = formatKeyMetrics(model.metrics);
  const chipText = isMobile ? "text-[10px]" : "text-xs";
  const chipClass = `inline-flex items-center rounded-sm border px-2 py-0.5 font-data font-medium ${chipText}`;

  return (
    <li className="flex items-center justify-between gap-3 border-b border-white/5 last:border-0 px-3 md:px-5 py-3 md:py-4 transition-colors hover:bg-white/2">
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p
            className={`font-semibold text-white truncate ${isMobile ? "text-sm" : "text-base"}`}
          >
            Model
          </p>
          <span className={`${chipClass} ${signalColors[signal]}`}>
            {signalLabel[signal]}
          </span>
          <span className={`${chipClass} ${tierColors[model.tier]}`}>
            {tierLabel[model.tier]}
          </span>
          <span className={`${chipClass} ${roleColors[model.role]}`}>
            {roleLabel[model.role]}
          </span>
        </div>
        <div
          className={`mt-0.5 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-white/50 ${isMobile ? "text-[11px]" : "text-xs"}`}
        >
          <span>{formatDateTime(model.createdAt)}</span>
          <Dot />
          <Badge>{registryKey}</Badge>
          {metrics.map((metric) => (
            <span
              key={`${metric.split}-${metric.name}`}
              className="inline-flex items-center gap-x-1.5"
            >
              <Dot />
              <Badge>
                {metricLabel[metric.name]} {formatMetricValue(metric.value)}
              </Badge>
            </span>
          ))}
        </div>
      </div>
    </li>
  );
}
