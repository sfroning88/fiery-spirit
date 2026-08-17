import type { TrainingStatus } from "@focus/types";

export const trainingStatusLabel: Record<TrainingStatus, string> = {
  pending: "Pending",
  executing: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};
