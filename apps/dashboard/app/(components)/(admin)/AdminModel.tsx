"use client";

import {
  Badge,
  SectionLabel,
  metricLabel,
  signalColors,
  signalLabel,
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
  const trainedAt = model.session.finishedAt ?? model.createdAt;
  const metaText = isMobile ? "text-[11px]" : "text-xs";

  return (
    <li className="border-b border-white/5 last:border-0 px-3 md:px-5 py-3 md:py-4 transition-colors hover:bg-white/2">
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p
            className={`font-semibold text-white truncate ${isMobile ? "text-sm" : "text-base"}`}
          >
            Model ({model.id})
          </p>
          <span
            className={`inline-flex items-center rounded-sm border border-fiery-crimson-400 bg-fiery-crimson-800/40 px-2 py-0.5 font-bold text-fiery-crimson-400 ${isMobile ? "text-sm" : "text-lg"}`}
          >
            {registryKey}
          </span>
          <span
            className={`inline-flex items-center rounded-sm border px-2 py-0.5 font-data font-medium ${isMobile ? "text-[10px]" : "text-xs"} ${signalColors[signal]}`}
          >
            {signalLabel[signal]}
          </span>
        </div>
        <div
          className={`mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-white/50 ${metaText}`}
        >
          <SectionLabel>trained at</SectionLabel>
          <span>{formatDateTime(trainedAt)}</span>
        </div>
        <div
          className={`mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 ${metaText}`}
        >
          <SectionLabel>scores</SectionLabel>
          {metrics.map((metric) => (
            <Badge key={`${metric.split}-${metric.name}`}>
              {metricLabel[metric.name]} {formatMetricValue(metric.value)}
            </Badge>
          ))}
        </div>
      </div>
    </li>
  );
}
