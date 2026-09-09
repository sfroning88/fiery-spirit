"use client";

import { useState } from "react";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import { useFetchModels } from "@/app/(hooks)/use-fetch-models";
import { useIngest } from "@/app/(hooks)/use-ingest";
import { useRefine } from "@/app/(hooks)/use-refine";
import { useTrain } from "@/app/(hooks)/use-train";
import { useBatch } from "@/app/(hooks)/use-batch";
import { usePromote } from "@/app/(hooks)/use-promote";
import { useRefresh } from "@/app/(hooks)/use-refresh";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { AdminModel } from "./AdminModel";
import { MOBILE_BREAKPOINT } from "@/lib/constants";
import { TEST_IDS } from "@lib/test-ids";
import { SignalDropdown, SourceDropdown, StageDropdown } from "@fiery/ui";
import { dateLikeToMs, formatNullableInt } from "@fiery/utils";
import {
  ModelDashboard,
  TrainingSampleSource,
  TrainingSignal,
  TrainingStage,
} from "@fiery/types";

type AdminPanelProps = {
  initialData?: ModelDashboard[];
};

export function AdminPanel({ initialData }: AdminPanelProps) {
  const userId = useUserId();
  const isMobile = !useMediaQuery(`(min-width: ${MOBILE_BREAKPOINT}px)`, true);

  const {
    data: models,
    isLoading,
    isError,
    error,
  } = useFetchModels(userId, initialData);

  const ingestMutation = useIngest(userId);
  const refineMutation = useRefine(userId);
  const trainMutation = useTrain(userId);
  const batchMutation = useBatch(userId);
  const promoteMutation = usePromote(userId);
  const refreshMutation = useRefresh(userId);

  const [maxSamplesInput, setMaxSamplesInput] = useState("");
  const maxSamples = formatNullableInt(maxSamplesInput);
  const [source, setSource] = useState<"hephaestus" | "okada" | "llaima">(
    TrainingSampleSource.hephaestus,
  );
  const [stage, setStage] = useState<TrainingStage>(TrainingStage.lora);
  const [signal, setSignal] = useState<TrainingSignal>(
    TrainingSignal.deformation,
  );

  const listed = models ?? [];
  const ranked = [...listed].sort((modelA, modelB) => {
    if (modelA.promoted !== modelB.promoted) return modelA.promoted ? -1 : 1;
    return dateLikeToMs(modelB.promotedAt) - dateLikeToMs(modelA.promotedAt);
  });

  let lastDeformationModel: ModelDashboard | null = null;
  let lastSeismicModel: ModelDashboard | null = null;

  for (const model of ranked) {
    switch (model.session.signal) {
      case TrainingSignal.deformation:
        if (!lastDeformationModel) lastDeformationModel = model;
        break;
      case TrainingSignal.seismic:
        if (!lastSeismicModel) lastSeismicModel = model;
        break;
    }
  }

  const lastModel =
    signal === TrainingSignal.deformation
      ? lastDeformationModel
      : lastSeismicModel;
  const hasLastModel = lastModel != null;
  const fieldClass = isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm";

  return (
    <div className="space-y-4 font-data">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2
          data-testid={TEST_IDS.modelsHeading}
          className={`font-semibold text-fiery-crimson-400 ${isMobile ? "text-lg" : "text-2xl"}`}
        >
          Models
        </h2>
        <div className="flex flex-wrap items-center justify-end gap-2">
          <input
            type="text"
            inputMode="numeric"
            data-testid={TEST_IDS.maxSamplesField}
            aria-label="Max samples"
            placeholder="Max samples"
            value={maxSamplesInput}
            onChange={(event) => setMaxSamplesInput(event.target.value)}
            className={`
                            w-28 rounded-md border border-white/20 bg-white/4 font-data text-white/80 placeholder:text-white/30
                            ${fieldClass}
                        `}
          />
          <SignalDropdown
            value={signal}
            onChange={setSignal}
            testId={TEST_IDS.signalField}
            className={fieldClass}
          />
          <SourceDropdown
            value={source}
            onChange={setSource}
            testId={TEST_IDS.sourceField}
            className={fieldClass}
          />
          <StageDropdown
            value={stage}
            onChange={setStage}
            testId={TEST_IDS.stageField}
            className={fieldClass}
          />
          <button
            type="button"
            data-testid={TEST_IDS.ingestButton}
            disabled={ingestMutation.isPending}
            onClick={() => {
              ingestMutation.mutate({
                source,
                maxSamples,
              });
            }}
            className={`
                            rounded-md border font-data font-medium transition-colors
                            ${isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"}
                            ${
                              ingestMutation.isPending
                                ? "border-white/10 bg-white/2 text-white/30 cursor-not-allowed"
                                : "border-white/20 bg-white/4 text-white/70 hover:bg-white/8"
                            }
                        `}
          >
            {ingestMutation.isPending ? "Ingesting…" : "Ingest Samples"}
          </button>
          <button
            type="button"
            data-testid={TEST_IDS.refineButton}
            disabled={refineMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              refineMutation.mutate({
                contractId: lastModel.session.contract.id,
                maxSamples,
              });
            }}
            className={`
                            rounded-md border font-data font-medium transition-colors
                            ${isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"}
                            ${
                              refineMutation.isPending || !hasLastModel
                                ? "border-white/10 bg-white/2 text-white/30 cursor-not-allowed"
                                : "border-white/20 bg-white/4 text-white/70 hover:bg-white/8"
                            }
                        `}
          >
            {refineMutation.isPending ? "Refining…" : "Refine Shards"}
          </button>
          <button
            type="button"
            data-testid={TEST_IDS.trainButton}
            disabled={trainMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              trainMutation.mutate({
                contractId: lastModel.session.contract.id,
                versionId: lastModel.session.version.id,
                stage,
                parentId: lastModel.parentId,
              });
            }}
            className={`
                            rounded-md border font-data font-medium transition-colors
                            ${isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"}
                            ${
                              trainMutation.isPending || !hasLastModel
                                ? "border-white/10 bg-white/2 text-white/30 cursor-not-allowed"
                                : "border-white/20 bg-white/4 text-white/70 hover:bg-white/8"
                            }
                        `}
          >
            {trainMutation.isPending ? "Training…" : "Train Model"}
          </button>
          <button
            type="button"
            data-testid={TEST_IDS.batchButton}
            disabled={batchMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              batchMutation.mutate({
                tier: lastModel.tier,
                role: lastModel.role,
              });
            }}
            className={`
                            rounded-md border font-data font-medium transition-colors
                            ${isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"}
                            ${
                              batchMutation.isPending || !hasLastModel
                                ? "border-white/10 bg-white/2 text-white/30 cursor-not-allowed"
                                : "border-white/20 bg-white/4 text-white/70 hover:bg-white/8"
                            }
                        `}
          >
            {batchMutation.isPending ? "Caching…" : "Cache Inferences"}
          </button>
          <button
            type="button"
            data-testid={TEST_IDS.promoteButton}
            disabled={promoteMutation.isPending}
            onClick={() => promoteMutation.mutate()}
            className={`
                            rounded-md border font-data font-medium transition-colors
                            ${isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"}
                            ${
                              promoteMutation.isPending
                                ? "border-white/10 bg-white/2 text-white/30 cursor-not-allowed"
                                : "border-white/20 bg-white/4 text-white/70 hover:bg-white/8"
                            }
                        `}
          >
            {promoteMutation.isPending ? "Evaluating…" : "Evaluate Models"}
          </button>
          <button
            type="button"
            data-testid={TEST_IDS.refreshButton}
            disabled={refreshMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              refreshMutation.mutate({
                tier: lastModel.tier,
                role: lastModel.role,
              });
            }}
            className={`
                            rounded-md border font-data font-medium transition-colors
                            ${isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"}
                            ${
                              refreshMutation.isPending || !hasLastModel
                                ? "border-white/10 bg-white/2 text-white/30 cursor-not-allowed"
                                : "border-white/20 bg-white/4 text-white/70 hover:bg-white/8"
                            }
                        `}
          >
            {refreshMutation.isPending ? "Refreshing…" : "Refresh Model"}
          </button>
        </div>
      </div>

      {ingestMutation.isError && (
        <p className="text-red-400 text-sm">
          {ingestMutation.error instanceof Error
            ? ingestMutation.error.message
            : "Ingest request failed."}
        </p>
      )}

      {ingestMutation.isSuccess && (
        <p className="text-green-400 text-sm">
          Ingest started — {ingestMutation.data.jobIds.length} job(s) queued.
        </p>
      )}

      {refineMutation.isError && (
        <p className="text-red-400 text-sm">
          {refineMutation.error instanceof Error
            ? refineMutation.error.message
            : "Refine request failed."}
        </p>
      )}

      {refineMutation.isSuccess && (
        <p className="text-green-400 text-sm">
          Refine started — {refineMutation.data.jobIds.length} job(s) queued.
        </p>
      )}

      {trainMutation.isError && (
        <p className="text-red-400 text-sm">
          {trainMutation.error instanceof Error
            ? trainMutation.error.message
            : "Training request failed."}
        </p>
      )}

      {trainMutation.isSuccess && (
        <p className="text-green-400 text-sm">
          Training started — {trainMutation.data.jobIds.length} job(s) queued.
        </p>
      )}

      {batchMutation.isError && (
        <p className="text-red-400 text-sm">
          {batchMutation.error instanceof Error
            ? batchMutation.error.message
            : "Batch request failed."}
        </p>
      )}

      {batchMutation.isSuccess && (
        <p className="text-green-400 text-sm">
          Batch started — {batchMutation.data.jobIds.length} job(s) queued.
        </p>
      )}

      {promoteMutation.isError && (
        <p className="text-red-400 text-sm">
          {promoteMutation.error instanceof Error
            ? promoteMutation.error.message
            : "Promote request failed."}
        </p>
      )}

      {promoteMutation.isSuccess && (
        <p className="text-green-400 text-sm">
          Promote started — {promoteMutation.data.evaluatedModels.length}{" "}
          model(s) evalutated.
        </p>
      )}

      {refreshMutation.isError && (
        <p className="text-red-400 text-sm">
          {refreshMutation.error instanceof Error
            ? refreshMutation.error.message
            : "Refresh request failed."}
        </p>
      )}

      {refreshMutation.isSuccess && (
        <p className="text-green-400 text-sm">
          Refresh started — model {refreshMutation.data.artifactId} refreshed.
        </p>
      )}

      {isLoading ? (
        <p className="text-white/50 text-sm">Loading models…</p>
      ) : isError ? (
        <p className="text-red-400 text-sm">
          {error instanceof Error ? error.message : "Could not load models."}
        </p>
      ) : !ranked?.length ? (
        <p className="text-white/40 text-sm">No models yet...</p>
      ) : (
        <>
          <ul className="border border-white/10 rounded-md overflow-hidden bg-surface-dark">
            {ranked.map((model) => (
              <AdminModel key={model.id} model={model} isMobile={isMobile} />
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
