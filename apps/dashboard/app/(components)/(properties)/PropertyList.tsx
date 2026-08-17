"use client";

import { useState, useTransition, useMemo } from "react";
import { useMediaQuery } from "@/app/(hooks)/use-media-query";
import { useFetchProperties } from "@/app/(hooks)/use-fetch-properties";
import { useUserId } from "@/app/(hooks)/use-user-id";
import { PropertyCard } from "@/app/(components)/(properties)/PropertyCard";
import { PropertySearchBar } from "./(propertyList)/PropertySearchBar";
import { PropertyListItem } from "./(propertyList)/PropertyListItem";
import { MOBILE_BREAKPOINT } from "@/lib/constants";
import { TEST_IDS } from "@lib/test-ids";
import { getLatestByRecency, SortDir, SortField, toNum } from "@focus/utils";
import type { PropertyListEntry } from "@focus/types";

type PropertyListProps = {
  initialData?: PropertyListEntry[];
};

export function PropertyList({ initialData }: PropertyListProps) {
  const userId = useUserId();
  const isMobile = !useMediaQuery(`(min-width: ${MOBILE_BREAKPOINT}px)`, true);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sortField, setSortField] = useState<SortField>(SortField.name);
  const [sortDir, setSortDir] = useState<SortDir>(SortDir.asc);
  const [, startTransition] = useTransition();

  const {
    data: properties,
    isLoading: listLoading,
    isError: listError,
    error: listErrorObj,
  } = useFetchProperties(userId, initialData);

  const handleQueryChange = (q: string) => {
    startTransition(() => setQuery(q));
  };

  const handleToggleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDir((d) => (d === SortDir.asc ? SortDir.desc : SortDir.asc));
    } else {
      setSortField(field);
      setSortDir(SortDir.asc);
    }
  };

  const filtered = useMemo(() => {
    if (!properties) return [];
    const q = query.toLowerCase().trim();

    const list = q
      ? properties.filter(
          (p) =>
            p.name.toLowerCase().includes(q) ||
            p.city.toLowerCase().includes(q) ||
            p.state.toLowerCase().includes(q),
        )
      : [...properties];

    list.sort((a, b) => {
      if (sortField === SortField.name) {
        const cmp = a.name.localeCompare(b.name);
        return sortDir === SortDir.asc ? cmp : -cmp;
      }
      if (sortField === SortField.msa) {
        const aMsa = a.msa?.name ?? "";
        const bMsa = b.msa?.name ?? "";
        const cmp = aMsa.localeCompare(bMsa);
        return sortDir === SortDir.asc ? cmp : -cmp;
      }
      if (sortField === SortField.snapshots) {
        const aN = a._count.snapshots;
        const bN = b._count.snapshots;
        return sortDir === SortDir.asc ? aN - bN : bN - aN;
      }
      const aOcc = toNum(getLatestByRecency(a.snapshots)?.occupancy ?? 0);
      const bOcc = toNum(getLatestByRecency(b.snapshots)?.occupancy ?? 0);
      return sortDir === SortDir.asc ? aOcc - bOcc : bOcc - aOcc;
    });

    return list;
  }, [properties, query, sortField, sortDir]);

  return (
    <div className="space-y-4 font-data">
      <h1
        data-testid={TEST_IDS.propertiesHeading}
        className={`font-semibold text-fhp-blue-400 ${isMobile ? "text-lg" : "text-2xl"}`}
      >
        Properties
      </h1>

      <PropertySearchBar
        query={query}
        onQueryChange={handleQueryChange}
        sortField={sortField}
        sortDir={sortDir}
        onToggleSort={handleToggleSort}
        isMobile={isMobile}
      />

      {listLoading ? (
        <p className="text-white/50 text-sm">Loading properties…</p>
      ) : listError ? (
        <p className="text-red-400 text-sm">
          {listErrorObj instanceof Error
            ? listErrorObj.message
            : "Could not load properties."}
        </p>
      ) : !filtered.length ? (
        <p
          className="text-white/40 text-sm"
          data-testid={query ? TEST_IDS.propertySearchEmpty : undefined}
        >
          {query
            ? "No properties match your search."
            : "No properties to show."}
        </p>
      ) : (
        <>
          <ul
            data-testid={TEST_IDS.propertiesList}
            className="border border-white/10 rounded-md overflow-hidden bg-surface-dark"
          >
            {filtered.map((p) => (
              <PropertyListItem
                key={p.id}
                property={p}
                isMobile={isMobile}
                onSelect={setDetailId}
              />
            ))}
          </ul>
          <p className="text-[11px] text-white/30 font-data-mono">
            {filtered.length}{" "}
            {filtered.length === 1 ? "property" : "properties"}
          </p>
        </>
      )}

      <PropertyCard
        userId={userId}
        propertyId={detailId}
        onClose={() => setDetailId(null)}
      />
    </div>
  );
}
