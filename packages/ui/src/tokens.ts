import type { TrainingStatus } from "@fiery/types";

export const trainingStatusColors: Record<TrainingStatus, string> = {
  pending: "border-zinc-600/50 bg-zinc-950/50 text-zinc-100/80",
  executing: "border-blue-600/50 bg-blue-950/50 text-blue-100/90",
  completed: "border-green-600/50 bg-green-950/50 text-green-100/90",
  failed: "border-red-600/50 bg-red-950/50 text-red-100/90",
  cancelled: "border-amber-600/50 bg-amber-950/50 text-amber-100/90",
};
