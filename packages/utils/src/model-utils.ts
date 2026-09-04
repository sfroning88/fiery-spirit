import { ModelDashboard, ModelDashboardRow } from "@fiery/types";

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
