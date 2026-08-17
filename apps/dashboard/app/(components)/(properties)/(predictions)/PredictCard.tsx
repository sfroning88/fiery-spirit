"use client";

import { SectionLabel } from "@focus/ui";
import { toNum } from "@focus/utils";
import { PREDICTION_TYPES } from "@focus/types";
import { firstPredictionResult } from "@focus/utils";
import { usePredictModels } from "@/app/(hooks)/use-predict-models";
import { PredictFeedback } from "./PredictFeedback";
import { PredictMetric } from "./PredictMetric";
import { TEST_IDS } from "@lib/test-ids";

type PredictCardProps = {
  userId: string;
  propertyId: string;
  currentPrd: number | null;
  currentOccupancy: number | null;
  currentMargin: number | null;
};

export function PredictCard({
  userId,
  propertyId,
  currentPrd,
  currentOccupancy,
  currentMargin,
}: PredictCardProps) {
  const { mutate, data, isPending, isError, error, isSuccess, reset } =
    usePredictModels(userId);

  const predictedPrd = isSuccess
    ? firstPredictionResult(data, "controllablePrd")
    : null;
  const predictedOccupancy = isSuccess
    ? firstPredictionResult(data, "occupancy")
    : null;
  const predictedMargin = isSuccess
    ? firstPredictionResult(data, "operatingMargin")
    : null;

  const deltaPrd =
    predictedPrd != null && currentPrd != null
      ? predictedPrd - currentPrd
      : null;
  const deltaOccupancy =
    predictedOccupancy != null && currentOccupancy != null
      ? predictedOccupancy - currentOccupancy
      : null;
  const deltaMargin =
    predictedMargin != null && currentMargin != null
      ? predictedMargin - currentMargin
      : null;

  return (
    <div className="border border-white/10 rounded-sm p-3 md:p-4">
      <div className="flex items-center justify-between gap-2">
        <SectionLabel>AI Predictions</SectionLabel>
        <button
          type="button"
          data-testid={TEST_IDS.predictButton}
          disabled={isPending}
          onClick={() => {
            reset();
            mutate({ propertyId });
          }}
          className={`
            rounded-md border font-data font-medium transition-colors shrink-0
            px-2.5 py-1 text-[10px] md:px-3 md:py-1.5 md:text-xs
            ${
              isPending
                ? "border-white/10 bg-white/2 text-white/30 cursor-not-allowed"
                : "border-fhp-blue-500 bg-fhp-blue-800/50 text-white hover:bg-fhp-blue-700/60"
            }
          `}
        >
          {isPending ? "Predicting…" : isSuccess ? "Re-predict" : "Predict"}
        </button>
      </div>

      {isError && (
        <p className="mt-2 text-red-400 text-xs">
          {error instanceof Error ? error.message : "Prediction failed."}
        </p>
      )}

      <div className="mt-2.5 md:mt-3 flex flex-col gap-3 md:gap-4">
        <PredictMetric
          metricLabel="Controllable PRD"
          placeholderLabel="Predicted PRD"
          current={currentPrd}
          predicted={predictedPrd}
          delta={deltaPrd}
          isPending={isPending}
        />
        <PredictMetric
          metricLabel="Occupancy"
          placeholderLabel="Predicted occupancy"
          current={currentOccupancy}
          predicted={predictedOccupancy}
          delta={deltaOccupancy}
          isPending={isPending}
          format="percent"
        />
        <PredictMetric
          metricLabel="Operating margin"
          placeholderLabel="Predicted margin"
          current={currentMargin}
          predicted={predictedMargin}
          delta={deltaMargin}
          isPending={isPending}
          format="percent"
        />
      </div>

      {isSuccess
        ? PREDICTION_TYPES.map((type) => {
            const prediction = data[type].predictions[0];
            if (!prediction) return null;
            return (
              <PredictFeedback
                key={type}
                userId={userId}
                propertyId={propertyId}
                type={prediction.type}
                modelType={prediction.modelType}
                modelBatchId={prediction.modelBatchId}
                feedbackScore={
                  prediction.feedbackScore != null
                    ? toNum(prediction.feedbackScore)
                    : null
                }
              />
            );
          })
        : null}
    </div>
  );
}
