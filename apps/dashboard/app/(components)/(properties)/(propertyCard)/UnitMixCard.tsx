import type { PropertyCard } from "@focus/types";
import { SectionLabel } from "@focus/ui";
import { UnitRow } from "./UnitRow";

type UnitMixCardProps = {
  card: PropertyCard;
};

const ACUITY_SEGMENTS = [
  { key: "cottageUnits", label: "Cottage", color: "bg-fhp-blue-300" },
  { key: "independentUnits", label: "Independent", color: "bg-fhp-blue-500" },
  { key: "assistedUnits", label: "Assisted", color: "bg-fhp-blue-700" },
  { key: "memoryUnits", label: "Memory", color: "bg-fhp-blue-400" },
] as const;

export function UnitMixCard({ card }: UnitMixCardProps) {
  const total = card.totalUnits || 1;
  const segments = ACUITY_SEGMENTS.map((s) => ({
    ...s,
    count: card[s.key] as number,
    pct: ((card[s.key] as number) / total) * 100,
  }));

  return (
    <div className="border border-white/10 rounded-sm p-3 md:p-4 flex flex-col">
      <SectionLabel>Unit Mix by Acuity</SectionLabel>

      <div className="mt-2.5 md:mt-3 flex h-1.5 md:h-2 rounded-full overflow-hidden">
        {segments.map(
          (s) =>
            s.count > 0 && (
              <div
                key={s.key}
                className={`${s.color} transition-all`}
                style={{ width: `${s.pct}%` }}
              />
            ),
        )}
      </div>

      <div className="mt-1.5 md:mt-2 flex flex-wrap gap-x-2.5 md:gap-x-3 gap-y-1 text-[9px] md:text-[10px] text-white/50">
        {segments.map((s) => (
          <span key={s.key} className="inline-flex items-center gap-1">
            <span
              className={`inline-block h-1.5 w-1.5 md:h-2 md:w-2 rounded-sm ${s.color}`}
            />
            {s.label} ({s.count})
          </span>
        ))}
      </div>

      <div className="mt-3 md:mt-4 flex-1">
        <table className="w-full text-xs md:text-sm">
          <tbody>
            {segments.map((s) => (
              <UnitRow key={s.key} label={s.label} value={s.count} />
            ))}
            <UnitRow label="Total units" value={card.totalUnits} bold />
            <UnitRow label="Total beds" value={card.totalBeds} />
          </tbody>
        </table>
      </div>
    </div>
  );
}
