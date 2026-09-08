import { use } from "react";
import type { ModelDashboard } from "@fiery/types";
import { AdminPanel } from "./AdminPanel";

type AdminAsyncProps = {
  initialDataPromise: Promise<ModelDashboard[]>;
};

export function AdminAsync({ initialDataPromise }: AdminAsyncProps) {
  const initialData = use(initialDataPromise);
  return <AdminPanel initialData={initialData} />;
}
