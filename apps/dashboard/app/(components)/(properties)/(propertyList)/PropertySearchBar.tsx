"use client";

import { Search } from "lucide-react";
import { SortDir, SortField } from "@focus/utils";
import { TEST_IDS } from "@lib/test-ids";

type PropertySearchBarProps = {
  query: string;
  onQueryChange: (q: string) => void;
  sortField: SortField;
  sortDir: SortDir;
  onToggleSort: (field: SortField) => void;
  isMobile: boolean;
};

export function PropertySearchBar({
  query,
  onQueryChange,
  sortField,
  sortDir,
  onToggleSort,
  isMobile,
}: PropertySearchBarProps) {
  return (
    <div
      className={`flex gap-2 ${isMobile ? "flex-col" : "flex-row items-center"}`}
    >
      <div className="relative flex-1">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30"
          size={isMobile ? 14 : 16}
        />
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          aria-label="Search properties"
          data-testid={TEST_IDS.propertySearchInput}
          className={`
            w-full rounded-md border border-white/10 bg-white/4
            text-white placeholder:text-white/30
            focus:outline-none focus:ring-1 focus:ring-fhp-blue-500 focus:border-fhp-blue-500
            font-data transition-colors
            ${isMobile ? "pl-8 pr-3 py-2 text-xs" : "pl-10 pr-4 py-2.5 text-sm"}
          `}
        />
      </div>

      <div className="flex gap-1.5 shrink-0">
        <SortButton
          label="NAME"
          testId={TEST_IDS.sortButtonName}
          active={sortField === SortField.name}
          dir={sortField === SortField.name ? sortDir : undefined}
          onClick={() => onToggleSort(SortField.name)}
          isMobile={isMobile}
        />
        <SortButton
          label="MSA"
          testId={TEST_IDS.sortButtonMsa}
          active={sortField === SortField.msa}
          dir={sortField === SortField.msa ? sortDir : undefined}
          onClick={() => onToggleSort(SortField.msa)}
          isMobile={isMobile}
        />
        <SortButton
          label="OCC"
          testId={TEST_IDS.sortButtonOcc}
          active={sortField === SortField.occupancy}
          dir={sortField === SortField.occupancy ? sortDir : undefined}
          onClick={() => onToggleSort(SortField.occupancy)}
          isMobile={isMobile}
        />
        <SortButton
          label="SNAPS"
          testId={TEST_IDS.sortButtonSnaps}
          active={sortField === SortField.snapshots}
          dir={sortField === SortField.snapshots ? sortDir : undefined}
          onClick={() => onToggleSort(SortField.snapshots)}
          isMobile={isMobile}
        />
      </div>
    </div>
  );
}

function SortButton({
  label,
  testId,
  active,
  dir,
  onClick,
  isMobile,
}: {
  label: string;
  testId: string;
  active: boolean;
  dir?: SortDir;
  onClick: () => void;
  isMobile: boolean;
}) {
  const arrow = dir === SortDir.asc ? "↑" : dir === SortDir.desc ? "↓" : "↕";

  return (
    <button
      type="button"
      data-testid={testId}
      onClick={onClick}
      aria-pressed={active ? "true" : "false"}
      className={`
        inline-flex items-center gap-1 rounded-md border font-data font-medium
        uppercase tracking-wider transition-colors
        ${isMobile ? "px-2.5 py-1.5 text-[10px]" : "px-3.5 py-2 text-xs"}
        ${
          active
            ? "border-fhp-blue-500 bg-fhp-blue-800/50 text-white"
            : "border-white/10 bg-white/3 text-white/50 hover:text-white/70 hover:border-white/20"
        }
      `}
    >
      {label}
      <span className="text-white/30">{arrow}</span>
    </button>
  );
}
