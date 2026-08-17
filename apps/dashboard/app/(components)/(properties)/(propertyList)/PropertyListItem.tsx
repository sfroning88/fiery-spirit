"use client";

import {
  formatPercent,
  getLatestByRecency,
  getOccupancyTier,
  toNum,
} from "@focus/utils";
import { Dot, occupancyColors } from "@focus/ui";
import type { PropertyListEntry } from "@focus/types";
import { TEST_IDS } from "@lib/test-ids";

type PropertyListItemProps = {
  property: PropertyListEntry;
  isMobile: boolean;
  onSelect: (id: string) => void;
};

export function PropertyListItem({
  property,
  isMobile,
  onSelect,
}: PropertyListItemProps) {
  const snapshotCount = property._count.snapshots;
  const hasNoSnapshots = snapshotCount === 0;
  const latestSnapshot = getLatestByRecency(property.snapshots);
  const latestOcc = latestSnapshot?.occupancy;
  const occValue = latestOcc != null ? toNum(latestOcc) : null;
  const tier = occValue != null ? getOccupancyTier(occValue) : null;

  return (
    <li className="flex items-center justify-between gap-3 border-b border-white/5 last:border-0 px-3 md:px-5 py-3 md:py-4 transition-colors hover:bg-white/2">
      <div className="min-w-0">
        <p
          className={`font-semibold text-white truncate ${isMobile ? "text-sm" : "text-base"}`}
        >
          {property.name}
        </p>
        <div
          className={`mt-0.5 flex flex-wrap items-center gap-x-1.5 text-white/50 ${isMobile ? "text-[11px]" : "text-xs"}`}
        >
          <span>
            {property.city}, {property.state}
          </span>
          {property.msa?.name && (
            <>
              <Dot />
              <span>{property.msa.name}</span>
            </>
          )}
          <Dot />
          <span>{property.totalUnits} units</span>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-3 shrink-0">
        {hasNoSnapshots && (
          <span
            className={`
              inline-flex items-center rounded-sm border border-amber-600/50
              bg-amber-950/50 px-2 py-0.5 font-data font-medium text-amber-100/90
              ${isMobile ? "text-[10px]" : "text-xs"}
            `}
            title="No expense comp snapshots on file"
          >
            No snapshots
          </span>
        )}
        {tier && occValue != null && (
          <span
            className={`
              inline-flex items-center rounded-sm border px-2 py-0.5
              font-data-mono font-semibold
              ${isMobile ? "text-xs" : "text-sm"}
              ${occupancyColors[tier]}
            `}
          >
            {formatPercent(occValue)}
          </span>
        )}
        <button
          type="button"
          data-testid={TEST_IDS.propertyViewButton}
          onClick={() => onSelect(property.id)}
          aria-label={`View ${property.name}`}
          className={`
            rounded-md border border-white/15 bg-white/4
            font-data font-medium text-white/70
            hover:bg-white/8 hover:text-white transition-colors
            ${isMobile ? "px-2.5 py-1.5 text-xs" : "px-4 py-2 text-sm"}
          `}
        >
          View →
        </button>
      </div>
    </li>
  );
}
