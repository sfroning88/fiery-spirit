import {
  ModelDashboard,
  ModelDashboardRow,
  ModelMetric,
  TrainingSampleSource,
  TrainingSignal,
} from "@fiery/types";
import { toNum } from "./number-utils";

export function uniqueModels(
  models: ModelDashboard[],
  key: (model: ModelDashboard) => string,
): ModelDashboard[] {
  const seen = new Set<string>();
  const unique: ModelDashboard[] = [];
  for (const model of models) {
    const next = key(model);
    if (seen.has(next)) continue;
    seen.add(next);
    unique.push(model);
  }
  return unique;
}

export function ingestSources(signal: TrainingSignal): TrainingSampleSource[] {
  return signal === "seismic" ? ["llaima"] : ["hephaestus", "okada"];
}

export function toModelDashboard(row: ModelDashboardRow): ModelDashboard {
  return {
    ...row,
    metrics: row.metrics,
    budget: row.budget,
    session: row.session,
    parent: row.parent,
    _count: row._count,
  };
}

export function formatKeyMetrics(metrics: ModelMetric[]): ModelMetric[] {
  const holdout = metrics.filter((metric) => metric.split === "holdout");
  return holdout.length > 0
    ? holdout
    : metrics.filter((metric) => metric.split === "test");
}

export function formatMetricValue(value: ModelMetric["value"]): string {
  return `${(toNum(value) * 100).toFixed(1)}%`;
}
