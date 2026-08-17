import { use } from "react";
import type { TrainingBatchListEntry } from "@focus/types";
import { BatchList } from "./BatchList";

type BatchListAsyncProps = {
  initialDataPromise: Promise<TrainingBatchListEntry[]>;
};

export function BatchListAsync({ initialDataPromise }: BatchListAsyncProps) {
  const initialData = use(initialDataPromise);
  return <BatchList initialData={initialData} />;
}
