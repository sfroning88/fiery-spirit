"use client";

import { useState } from "react";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import { useFetchModels } from "@/app/(hooks)/use-fetch-models";
import { useFetchWinners } from "@/app/(hooks)/use-fetch-winners";
import { useIngest } from "@/app/(hooks)/use-ingest";
import { useRefine } from "@/app/(hooks)/use-refine";
import { useTrain } from "@/app/(hooks)/use-train";
import { useBatch } from "@/app/(hooks)/use-batch";
import { usePromote } from "@/app/(hooks)/use-promote";
import { useRefresh } from "@/app/(hooks)/use-refresh";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { AdminModel } from "./AdminModel";
import { MOBILE_BREAKPOINT, EMPTY_MODELS } from "@/lib/constants";
import { TEST_IDS } from "@lib/test-ids";
import {
  Button,
  Input,
  SectionLabel,
  SignalDropdown,
  SourceDropdown,
  StageDropdown,
} from "@fiery/ui";
import { dateLikeToMs, formatNullableInt, pickWinners } from "@fiery/utils";
import {
  ModelDashboard,
  TrainingSampleSource,
  TrainingSignal,
  TrainingStage,
} from "@fiery/types";

type AdminPanelProps = {
  initialWinners?: ModelDashboard[];
};

export function AdminPanel({ initialWinners }: AdminPanelProps) {
  const userId = useUserId();
  const isMobile = !useMediaQuery(`(min-width: ${MOBILE_BREAKPOINT}px)`, true);
  const [loadAll, setLoadAll] = useState(false);

  const {
    data: winnersData,
    isLoading: winnersLoading,
    isError: winnersError,
    error: winnersErrorDetail,
  } = useFetchWinners(userId, initialWinners);

  const {
    data: allModels,
    isLoading: allModelsLoading,
    isError: allModelsError,
    error: allModelsErrorDetail,
  } = useFetchModels(userId, { enabled: loadAll });

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

  const winners =
    loadAll && allModels
      ? pickWinners(allModels)
      : (winnersData ?? EMPTY_MODELS);
  const winnerIds = new Set(winners.map((model) => model.id));

  const catalog = loadAll ? (allModels ?? EMPTY_MODELS) : winners;
  const ranked = [...catalog].sort((modelA, modelB) => {
    if (modelA.promoted !== modelB.promoted) return modelA.promoted ? -1 : 1;
    return dateLikeToMs(modelB.promotedAt) - dateLikeToMs(modelA.promotedAt);
  });
  const remainingModels = loadAll
    ? ranked.filter((model) => !winnerIds.has(model.id))
    : [];

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
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <SectionLabel>inputs</SectionLabel>
          <Input
            type="text"
            inputMode="numeric"
            data-testid={TEST_IDS.maxSamplesField}
            aria-label="Max samples"
            placeholder="Max samples"
            value={maxSamplesInput}
            onChange={(event) => setMaxSamplesInput(event.target.value)}
            className="w-28"
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
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <SectionLabel>requests</SectionLabel>
          <Button
            data-testid={TEST_IDS.ingestButton}
            disabled={ingestMutation.isPending}
            onClick={() => {
              ingestMutation.mutate({
                source,
                maxSamples,
              });
            }}
          >
            {ingestMutation.isPending ? "Ingesting…" : "Ingest Samples"}
          </Button>
          <Button
            data-testid={TEST_IDS.refineButton}
            disabled={refineMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              refineMutation.mutate({
                contractId: lastModel.session.contract.id,
                maxSamples,
              });
            }}
          >
            {refineMutation.isPending ? "Refining…" : "Refine Shards"}
          </Button>
          <Button
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
          >
            {trainMutation.isPending ? "Training…" : "Train Model"}
          </Button>
          <Button
            data-testid={TEST_IDS.batchButton}
            disabled={batchMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              batchMutation.mutate({
                tier: lastModel.tier,
                role: lastModel.role,
              });
            }}
          >
            {batchMutation.isPending ? "Caching…" : "Cache Inferences"}
          </Button>
          <Button
            data-testid={TEST_IDS.promoteButton}
            disabled={promoteMutation.isPending}
            onClick={() => promoteMutation.mutate()}
          >
            {promoteMutation.isPending ? "Evaluating…" : "Evaluate Models"}
          </Button>
          <Button
            data-testid={TEST_IDS.refreshButton}
            disabled={refreshMutation.isPending || !hasLastModel}
            onClick={() => {
              if (!lastModel) return;
              refreshMutation.mutate({
                tier: lastModel.tier,
                role: lastModel.role,
              });
            }}
          >
            {refreshMutation.isPending ? "Refreshing…" : "Refresh Model"}
          </Button>
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

      {winnersLoading ? (
        <p className="text-white/50 text-sm">Loading current winners…</p>
      ) : winnersError ? (
        <p className="text-red-400 text-sm">
          {winnersErrorDetail instanceof Error
            ? winnersErrorDetail.message
            : "Could not load current winners."}
        </p>
      ) : (
        <div className="space-y-2">
          <SectionLabel>current winners</SectionLabel>
          {!winners.length ? (
            <p className="text-white/40 text-sm">No promoted models yet…</p>
          ) : (
            <ul className="border border-white/10 rounded-md overflow-hidden bg-surface-dark">
              {winners.map((model) => (
                <AdminModel
                  key={model.id}
                  model={model}
                  isMobile={isMobile}
                  showTrophy
                />
              ))}
            </ul>
          )}
          {!loadAll ? (
            <Button
              data-testid={TEST_IDS.loadAllModelsButton}
              onClick={() => setLoadAll(true)}
            >
              Load All
            </Button>
          ) : allModelsLoading ? (
            <p className="text-white/50 text-sm">Loading all models…</p>
          ) : allModelsError ? (
            <p className="text-red-400 text-sm">
              {allModelsErrorDetail instanceof Error
                ? allModelsErrorDetail.message
                : "Could not load all models."}
            </p>
          ) : remainingModels.length > 0 ? (
            <div className="space-y-2">
              <SectionLabel>all models</SectionLabel>
              <ul className="border border-white/10 rounded-md overflow-hidden bg-surface-dark">
                {remainingModels.map((model) => (
                  <AdminModel
                    key={model.id}
                    model={model}
                    isMobile={isMobile}
                  />
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-white/40 text-sm">No other models to show.</p>
          )}
        </div>
      )}
    </div>
  );
}
