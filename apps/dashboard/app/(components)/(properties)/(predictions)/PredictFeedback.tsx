"use client";

import { useState } from "react";
import type { PredictionType, TrainingType } from "@focus/types";
import { FeedbackThumbs } from "@focus/ui";
import { useGivePredictionFeedback } from "@/app/(hooks)/use-give-prediction-feedback";

type PredictFeedbackProps = {
  userId: string;
  propertyId: string;
  type: PredictionType;
  modelType: TrainingType;
  modelBatchId: string;
  feedbackScore: number | null;
};

export function PredictFeedback({
  userId,
  propertyId,
  type,
  modelType,
  modelBatchId,
  feedbackScore: feedbackScoreFromServer,
}: PredictFeedbackProps) {
  const { mutate, isPending, isError, reset } =
    useGivePredictionFeedback(userId);
  const [submittedScore, setSubmittedScore] = useState<number | null>(null);

  const feedbackScore = submittedScore ?? feedbackScoreFromServer;
  const hasAnswered = feedbackScore != null;
  const disabled = hasAnswered || isPending;

  const send = (score: number) => {
    if (isError) reset();
    mutate(
      {
        type,
        modelType,
        modelBatchId,
        propertyId,
        feedbackScore: score,
      },
      { onSuccess: () => setSubmittedScore(score) },
    );
  };

  return (
    <div className="mt-2.5 flex flex-wrap items-center gap-2 md:gap-3">
      <span className="text-[10px] md:text-[11px] text-white/40">
        {isError
          ? "Something went wrong — try again?"
          : hasAnswered
            ? "Thanks for the feedback!"
            : "Was this prediction helpful?"}
      </span>
      {!hasAnswered && (
        <FeedbackThumbs
          disabled={disabled}
          onPositive={() => send(1)}
          onNegative={() => send(0)}
        />
      )}
    </div>
  );
}
