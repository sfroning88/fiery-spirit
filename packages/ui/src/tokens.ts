import {
  type ModelTier,
  type ModelRole,
  type ModelMetricName,
  type TrainingSignal,
  type TrainingStatus,
  TrainingStage,
  TrainingSampleSource,
} from "@fiery/types";

export const tierColors: Record<ModelTier, string> = {
  cloud: "border-white-600/50 bg-white-950/50 text-white-100/90",
  edge: "border-amber-600/50 bg-amber-950/50 text-amber-100/90",
};

export const tierLabel: Record<ModelTier, string> = {
  cloud: "Cloud",
  edge: "Edge",
};

export const roleColors: Record<ModelRole, string> = {
  screener: "border-green-600/50 bg-green-950/50 text-green-100/90",
  teacher: "border-blue-600/50 bg-blue-950/50 text-blue-100/90",
  student: "border-red-600/50 bg-red-950/50 text-red-100/90",
};

export const roleLabel: Record<ModelRole, string> = {
  screener: "Screener",
  teacher: "Teacher",
  student: "Student",
};

export const signalColors: Record<TrainingSignal, string> = {
  deformation: "border-cyan-600/50 bg-cyan-950/50 text-cyan-100/90",
  seismic: "border-violet-600/50 bg-violet-950/50 text-violet-100/90",
};

export const signalLabel: Record<TrainingSignal, string> = {
  deformation: "Ground Deformations",
  seismic: "Seismic Activity",
};

export const metricLabel: Record<ModelMetricName, string> = {
  accuracy: "Acc",
  recall: "Rec",
  precision: "Prec",
  falsePositiveRate: "FPR",
  abstentionRate: "Abs",
  f1Score: "F1",
  macrof1Score: "Macro-F1",
};

export const statusColors: Record<TrainingStatus, string> = {
  pending: "border-zinc-600/50 bg-zinc-950/50 text-zinc-100/80",
  executing: "border-blue-600/50 bg-blue-950/50 text-blue-100/90",
  completed: "border-green-600/50 bg-green-950/50 text-green-100/90",
  failed: "border-red-600/50 bg-red-950/50 text-red-100/90",
  cancelled: "border-amber-600/50 bg-amber-950/50 text-amber-100/90",
};

export const statusLabel: Record<TrainingStatus, string> = {
  pending: "Pending",
  executing: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

export const sourceValues = [
  TrainingSampleSource.hephaestus,
  TrainingSampleSource.okada,
  TrainingSampleSource.llaima,
] as const;

export const sourceLabel: Record<(typeof sourceValues)[number], string> = {
  hephaestus: "Hephaestus",
  okada: "Okada",
  llaima: "Llaima",
};

export const stageValues = [
  TrainingStage.pretrain,
  TrainingStage.lora,
  TrainingStage.distill,
  TrainingStage.prune,
  TrainingStage.quantize,
] as const;

export const stageLabel: Record<(typeof stageValues)[number], string> = {
  pretrain: "Pretrain",
  lora: "LoRA",
  distill: "Distill",
  prune: "Prune",
  quantize: "Quantize",
};
