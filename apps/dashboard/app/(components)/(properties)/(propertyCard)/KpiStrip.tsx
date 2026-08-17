import type { PropertyCard } from "@focus/types";
import { KpiCard, SectionLabel } from "@focus/ui";
import { formatCompactCurrency, formatDate, formatPercent } from "@focus/utils";

type KpiStripProps = {
  card: PropertyCard;
  latestSnapshot: PropertyCard["snapshots"][number];
};

export function KpiStrip({ card, latestSnapshot }: KpiStripProps) {
  const occupancy = latestSnapshot.occupancy;
  const reportedLabel = formatDate(latestSnapshot.reportedAt);

  return (
    <div>
      <SectionLabel>
        Key Metrics — Latest Snapshot ({reportedLabel})
      </SectionLabel>
      <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3">
        <KpiCard
          label="Occupancy"
          sublabel={`of ${card.totalUnits} units`}
          accent
        >
          {formatPercent(occupancy)}
        </KpiCard>
        <KpiCard label="Total revenues" sublabel="trailing period">
          {formatCompactCurrency(latestSnapshot.totalRevenues)}
        </KpiCard>
        <KpiCard label="Operating margin" sublabel="controllable basis">
          {formatPercent(latestSnapshot.operatingMargin)}
        </KpiCard>
        <KpiCard label="Controllable PRD" sublabel="per res. per day">
          {formatCompactCurrency(latestSnapshot.controllablePRD)}
        </KpiCard>
      </div>
    </div>
  );
}
