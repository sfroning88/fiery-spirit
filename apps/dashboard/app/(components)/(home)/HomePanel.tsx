"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import { useFetchVolcanoes } from "@/app/(hooks)/use-fetch-volcanoes";
import { useInference } from "@/app/(hooks)/use-inference";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { MOBILE_BREAKPOINT, EMPTY_VOLCANOES } from "@/lib/constants";
import { inferenceRequest } from "@/lib/utils";
import { TEST_IDS } from "@lib/test-ids";
import { VolcanoDashboard, TrainingSignal } from "@fiery/types";
import { Button, signalLabel } from "@fiery/ui";

const HomeMap = dynamic(() => import("./HomeMap").then((map) => map.HomeMap), {
  ssr: false,
  loading: () => <p className="text-white/50 text-sm">Loading map...</p>,
});

type HomePanelProps = {
  initialData?: VolcanoDashboard[];
};

export function HomePanel({ initialData }: HomePanelProps) {
  const userId = useUserId();
  const isMobile = !useMediaQuery(`(min-width: ${MOBILE_BREAKPOINT}px)`, true);

  const {
    data: volcanos,
    isLoading,
    isError,
    error,
  } = useFetchVolcanoes(userId, initialData);

  const inferenceMutation = useInference(userId);

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const listed = volcanos ?? EMPTY_VOLCANOES;
  const selectedVolcano =
    listed.find((volcano) => volcano.id === selectedId) ?? null;
  const deformationRequest = selectedVolcano
    ? inferenceRequest(selectedVolcano, TrainingSignal.deformation)
    : null;
  const seismicRequest = selectedVolcano
    ? inferenceRequest(selectedVolcano, TrainingSignal.seismic)
    : null;
  const canInferDeformation = deformationRequest != null;
  const canInferSeismic = seismicRequest != null;

  return (
    <div className="space-y-4 font-data">
      <div className="flex flex-wrap items-center justify-end gap-2">
        <Button
          data-testid={TEST_IDS.inferenceDeformationButton}
          disabled={inferenceMutation.isPending || !canInferDeformation}
          onClick={() => {
            if (!deformationRequest) return;
            inferenceMutation.mutate(deformationRequest);
          }}
        >
          {inferenceMutation.isPending &&
          inferenceMutation.variables?.interferogramId
            ? "Inferencing…"
            : signalLabel.deformation}
        </Button>
        <Button
          data-testid={TEST_IDS.inferenceSeismicButton}
          disabled={inferenceMutation.isPending || !canInferSeismic}
          onClick={() => {
            if (!seismicRequest) return;
            inferenceMutation.mutate(seismicRequest);
          }}
        >
          {inferenceMutation.isPending &&
          inferenceMutation.variables?.seismicEventId
            ? "Inferencing…"
            : signalLabel.seismic}
        </Button>
      </div>

      {inferenceMutation.isError && (
        <p className="text-red-400 text-sm">
          {inferenceMutation.error instanceof Error
            ? inferenceMutation.error.message
            : "Inference request failed."}
        </p>
      )}

      {inferenceMutation.isSuccess && (
        <p className="text-green-400 text-sm">
          Served inference from model{" "}
          {inferenceMutation.data?.result.artifact_id}.
        </p>
      )}

      {isLoading ? (
        <p className="text-white/50 text-sm">Loading volcanoes…</p>
      ) : isError ? (
        <p className="text-red-400 text-sm">
          {error instanceof Error ? error.message : "Could not load volcanoes."}
        </p>
      ) : (
        <div
          data-testid={TEST_IDS.homeMap}
          className="h-[70vh] overflow-hidden border border-white/10 rounded-md bg-surface-dark"
        >
          <HomeMap
            volcanoes={listed}
            selectedId={selectedId}
            onSelect={setSelectedId}
            isMobile={isMobile}
          />
        </div>
      )}
    </div>
  );
}
