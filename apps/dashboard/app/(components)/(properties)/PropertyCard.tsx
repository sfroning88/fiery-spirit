"use client";

import { createPortal } from "react-dom";
import { toNum } from "@focus/utils";
import { useFetchPropertyCard } from "@/app/(hooks)/use-fetch-property-card";
import { CardHeader } from "./(propertyCard)/CardHeader";
import { CreateSnapshotModal } from "./(propertyCard)/CreateSnapshotModal";
import { KpiStrip } from "./(propertyCard)/KpiStrip";
import { UnitMixCard } from "./(propertyCard)/UnitMixCard";
import { ExpenseBreakdownCard } from "./(propertyCard)/ExpenseBreakdownCard";
import { PrdDetailCard } from "./(propertyCard)/PrdDetailCard";
import { PredictCard } from "./(predictions)/PredictCard";
import { SnapshotHistoryTable } from "./(propertyCard)/SnapshotHistoryTable";
import { TEST_IDS } from "@lib/test-ids";

type PropertyCardProps = {
  userId: string;
  propertyId: string | null;
  onClose: () => void;
};

export function PropertyCard({
  userId,
  propertyId,
  onClose,
}: PropertyCardProps) {
  const {
    data: card,
    isLoading: cardLoading,
    isError: cardError,
    error: cardErrorObj,
  } = useFetchPropertyCard(userId, propertyId);

  if (propertyId == null) return null;

  const latestSnapshot = card
    ? [...card.snapshots].sort(
        (a, b) =>
          new Date(b.reportedAt).getTime() - new Date(a.reportedAt).getTime(),
      )[0]
    : null;

  const modal = (
    <>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
        aria-hidden
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="property-card-title"
        data-testid={TEST_IDS.propertyCardDialog}
        className="
          fixed inset-3 md:inset-auto
          md:left-1/2 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2
          z-50 flex flex-col overflow-hidden
          bg-surface-dark border border-white/10 shadow-2xl
          rounded-md md:rounded-lg
          md:w-[820px] md:max-h-[88vh]
          font-data
        "
      >
        {cardLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-white/70" />
          </div>
        )}

        {cardError && (
          <div className="p-4 md:p-6">
            <p className="text-xs md:text-sm text-red-400">
              {cardErrorObj instanceof Error
                ? cardErrorObj.message
                : "Could not load property details."}
            </p>
          </div>
        )}

        {card && latestSnapshot && (
          <div className="overflow-y-auto flex-1 min-h-0 flex flex-col gap-4 md:gap-5 p-4 md:p-6">
            <CardHeader
              card={card}
              onClose={onClose}
              actions={
                <CreateSnapshotModal userId={userId} propertyId={card.id} />
              }
            />
            <KpiStrip card={card} latestSnapshot={latestSnapshot} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
              <UnitMixCard card={card} />
              <ExpenseBreakdownCard snapshot={latestSnapshot} />
            </div>

            <PrdDetailCard card={card} snapshot={latestSnapshot} />
            <PredictCard
              userId={userId}
              propertyId={card.id}
              currentPrd={toNum(latestSnapshot.controllablePRD)}
              currentOccupancy={toNum(latestSnapshot.occupancy)}
              currentMargin={toNum(latestSnapshot.operatingMargin)}
            />
            <SnapshotHistoryTable snapshots={card.snapshots} />
          </div>
        )}

        {card && !latestSnapshot && (
          <div className="flex flex-col gap-4 md:gap-5 p-4 md:p-6">
            <CardHeader
              card={card}
              onClose={onClose}
              actions={
                <CreateSnapshotModal userId={userId} propertyId={card.id} />
              }
            />
            <p className="text-xs md:text-sm text-white/40">
              No snapshots on file for this property.
            </p>
          </div>
        )}
      </div>
    </>
  );

  return typeof window !== "undefined"
    ? createPortal(modal, document.body)
    : null;
}
