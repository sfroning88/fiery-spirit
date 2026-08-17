"use client";

import { Dot, Badge, trainingStatusColors } from "@focus/ui";
import {
  formatDateTime,
  predictionTypeToApiPath,
  trainingStatusLabel,
} from "@focus/utils";
import type { TrainingBatchListEntry } from "@focus/types";

type BatchListItemProps = {
  batch: TrainingBatchListEntry;
  isMobile: boolean;
};

export function BatchListItem({ batch, isMobile }: BatchListItemProps) {
  const winnerModel = batch.models.find((m) => m.winner);
  const modelCount = batch.models.length;
  const completedCount = batch.models.filter(
    (m) => m.status === "completed",
  ).length;

  return (
    <li className="flex items-center justify-between gap-3 border-b border-white/5 last:border-0 px-3 md:px-5 py-3 md:py-4 transition-colors hover:bg-white/2">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <p
            className={`font-semibold text-white truncate ${isMobile ? "text-sm" : "text-base"}`}
          >
            Batch
          </p>
          <span
            className={`inline-flex items-center rounded-sm border px-2 py-0.5 font-data font-medium ${isMobile ? "text-[10px]" : "text-xs"} ${trainingStatusColors[batch.status]}`}
          >
            {trainingStatusLabel[batch.status]}
          </span>
        </div>
        <div
          className={`mt-0.5 flex flex-wrap items-center gap-x-1.5 text-white/50 ${isMobile ? "text-[11px]" : "text-xs"}`}
        >
          <span>{formatDateTime(batch.createdAt)}</span>
          <Dot />
          <span>{predictionTypeToApiPath(batch.predictionType)}</span>
          <Dot />
          <span>{batch.samples} samples</span>
          <Dot />
          <span>
            {completedCount}/{modelCount} models
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-3 shrink-0">
        {winnerModel && winnerModel.r2score != null && (
          <Badge>
            {winnerModel.type} · R&sup2;{" "}
            {Number(winnerModel.r2score).toFixed(3)}
          </Badge>
        )}
      </div>
    </li>
  );
}
