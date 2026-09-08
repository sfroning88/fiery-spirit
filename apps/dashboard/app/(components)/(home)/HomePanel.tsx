"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import { useFetchVolcanoes } from "@/app/(hooks)/use-fetch-volcanoes";
import { useInference } from "@/app/(hooks)/use-inference";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { MOBILE_BREAKPOINT } from "@/lib/constants";
import { inferenceRequest } from "@/lib/utils";
import { TEST_IDS } from "@lib/test-ids";
import { SignalDropdown } from "@fiery/ui";
import { VolcanoDashboard, TrainingSignal } from "@fiery/types";

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

  const [signal, setSignal] = useState<TrainingSignal>(
    TrainingSignal.deformation,
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const listed = volcanos ?? [];
  const selectedVolcano =
    listed.find((volcano) => volcano.id === selectedId) ?? null;
  const request = selectedVolcano
    ? inferenceRequest(selectedVolcano, signal)
    : null;
  const canInfer = request != null;
  const fieldClass = isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm";

  return (
    <div className="space-y-4 font-data">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2
          data-testid={TEST_IDS.volcanoesHeading}
          className={`font-semibold text-fiery-crimson-400 ${isMobile ? "text-lg" : "text-2xl"}`}
        >
          Volcanos
        </h2>
        <div className="flex flex-wrap items-center justify-end gap-2">
          <SignalDropdown
            value={signal}
            onChange={setSignal}
            testId={TEST_IDS.signalField}
            className={fieldClass}
          />
          <button
            type="button"
            data-testid={TEST_IDS.inferenceButton}
            disabled={inferenceMutation.isPending || !canInfer}
            onClick={() => {
              if (!request) return;
              inferenceMutation.mutate(request);
            }}
            className={`
                            rounded-md border font-data font-medium transition-colors
                            ${isMobile ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"}
                            ${
                              inferenceMutation.isPending || !canInfer
                                ? "border-white/10 bg-white/2 text-white/30 cursor-not-allowed"
                                : "border-white/20 bg-white/4 text-white/70 hover:bg-white/8"
                            }
                        `}
          >
            {inferenceMutation.isPending ? "Inferencing…" : "Live Inference"}
          </button>
        </div>
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
      ) : !listed.length ? (
        <p className="text-white/40 text-sm">No volcanoes yet...</p>
      ) : (
        <div className="h-[70vh] overflow-hidden border border-white/10 rounded-md bg-surface-dark">
          <HomeMap
            volcanoes={listed}
            selectedId={selectedId}
            onSelect={setSelectedId}
            isMobile={isMobile}
            signal={signal}
          />
        </div>
      )}
    </div>
  );
}
