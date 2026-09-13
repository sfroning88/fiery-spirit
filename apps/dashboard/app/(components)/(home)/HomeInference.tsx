"use client";

import { useState } from "react";
import { FeedbackThumbs, FeedbackThanksIcon, Input } from "@fiery/ui";
import { TEST_IDS } from "@/lib/test-ids";
import { useFeedback } from "@/app/(hooks)/use-feedback";
import { TrainingDeformationLabel, TrainingSeismicLabel } from "@fiery/types";

type HomeInferenceProps = {
  userId: string;
  interferogramId: string | null;
  seismicEventId: string | null;
  artifactId: string;
  agreed: boolean | null;
  correctedDeformation: TrainingDeformationLabel | null;
  correctedSeismic: TrainingSeismicLabel | null;
  notes: string | null;
};

export function HomeInference({
  userId,
  interferogramId,
  seismicEventId,
  artifactId,
  agreed,
  correctedDeformation,
  correctedSeismic,
  notes,
}: HomeInferenceProps) {
  const [inputAgreed, setInputAgreed] = useState<boolean | null>(null);
  const [inputCorrectedDeformation, setInputCorrectedDeformation] =
    useState<TrainingDeformationLabel | null>(null);
  const [inputCorrectedSeismic, setInputCorrectedSeismic] =
    useState<TrainingSeismicLabel | null>(null);
  const [inputNotes, setInputNotes] = useState<string | null>(null);

  const submittedAgreed = inputAgreed ?? agreed;
  const submittedCorrectedDeformation =
    inputCorrectedDeformation ?? correctedDeformation;
  const submittedCorrectedSeismic = inputCorrectedSeismic ?? correctedSeismic;
  const submittedNotes = inputNotes ?? notes;

  const feedbackMutation = useFeedback(userId);
  const isDeformation = interferogramId != null && seismicEventId == null;
  const isSeismic = seismicEventId != null && interferogramId == null;
  const hasSubmitted =
    inputAgreed != null || agreed != null || feedbackMutation.isSuccess;
  const fieldsDisabled = hasSubmitted || feedbackMutation.isPending;

  const send = (nextAgreed: boolean) => {
    if (!isDeformation && !isSeismic) return;
    if (
      (isDeformation && submittedCorrectedDeformation == null) ||
      (isSeismic && submittedCorrectedSeismic == null)
    )
      return;
    if (feedbackMutation.isError) feedbackMutation.reset();
    setInputAgreed(nextAgreed);
    feedbackMutation.mutate({
      agreed: nextAgreed,
      correctedDeformation: isDeformation
        ? submittedCorrectedDeformation
        : null,
      correctedSeismic: isSeismic ? submittedCorrectedSeismic : null,
      note: submittedNotes,
      volcanoId: null,
      interferogramId,
      seismicEventId,
      artifactId,
    });
  };

  return (
    <div data-testid={TEST_IDS.inferenceBox} className="space-y-2 font-data">
      {isDeformation ? (
        <select
          aria-label="Corrected deformation label"
          disabled={fieldsDisabled}
          value={submittedCorrectedDeformation ?? ""}
          onChange={(event) =>
            setInputCorrectedDeformation(
              event.target.value as TrainingDeformationLabel,
            )
          }
          className="w-full rounded-md border border-white/10 bg-surface-dark px-3 py-1.5 text-xs text-white"
        >
          {Object.values(TrainingDeformationLabel).map((label) => (
            <option key={label} value={label}>
              {label}
            </option>
          ))}
        </select>
      ) : null}
      {isSeismic ? (
        <select
          aria-label="Corrected seismic label"
          disabled={fieldsDisabled}
          value={submittedCorrectedSeismic ?? ""}
          onChange={(event) =>
            setInputCorrectedSeismic(event.target.value as TrainingSeismicLabel)
          }
          className="w-full rounded-md border border-white/10 bg-surface-dark px-3 py-1.5 text-xs text-white"
        >
          {Object.values(TrainingSeismicLabel).map((label) => (
            <option key={label} value={label}>
              {label}
            </option>
          ))}
        </select>
      ) : null}
      <Input
        type="text"
        aria-label="Feedback notes"
        placeholder="Notes"
        disabled={fieldsDisabled}
        value={submittedNotes ?? ""}
        onChange={(event) => setInputNotes(event.target.value || null)}
      />
      {hasSubmitted ? (
        <FeedbackThanksIcon variant={submittedAgreed ? "up" : "down"} />
      ) : (
        <FeedbackThumbs
          disabled={
            feedbackMutation.isPending || (!isDeformation && !isSeismic)
          }
          onPositive={() => send(true)}
          onNegative={() => send(false)}
        />
      )}
      {feedbackMutation.isError ? (
        <p className="text-red-400 text-sm">
          {feedbackMutation.error instanceof Error
            ? feedbackMutation.error.message
            : "Feedback request failed."}
        </p>
      ) : null}
    </div>
  );
}
