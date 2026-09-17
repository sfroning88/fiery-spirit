import { use } from "react";
import type { ModelDashboard } from "@fiery/types";
import { AdminPanel } from "./AdminPanel";

type AdminAsyncProps = {
  initialWinnersPromise: Promise<ModelDashboard[]>;
};

export function AdminAsync({ initialWinnersPromise }: AdminAsyncProps) {
  const initialWinners = use(initialWinnersPromise);
  return <AdminPanel initialWinners={initialWinners} />;
}
