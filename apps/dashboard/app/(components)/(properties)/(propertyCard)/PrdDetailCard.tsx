import type { PropertyCard } from "@focus/types";
import { SectionLabel, ValueBox } from "@focus/ui";
import { toNum } from "@focus/utils";

type PrdDetailCardProps = {
  card: PropertyCard;
  snapshot: PropertyCard["snapshots"][number];
};

export function PrdDetailCard({ card, snapshot }: PrdDetailCardProps) {
  const occupancy = toNum(snapshot.occupancy) / 100;
  const occupiedUnits = card.totalUnits * occupancy;
  const days = occupiedUnits * 365;

  const controllablePrd = toNum(snapshot.controllablePRD);
  const revenuePrd = days > 0 ? toNum(snapshot.totalRevenues) / days : null;
  const expensePrd =
    days > 0 ? toNum(snapshot.controllableExpenses) / days : null;

  return (
    <div className="border border-white/10 rounded-sm p-3 md:p-4">
      <SectionLabel>Controllable PRD Detail</SectionLabel>
      <div className="mt-2.5 md:mt-3 grid grid-cols-3 gap-2 md:gap-3">
        <ValueBox label="Controllable PRD" value={controllablePrd} />
        <ValueBox label="Revenue PRD" value={revenuePrd} />
        <ValueBox label="Expense PRD" value={expensePrd} highlight />
      </div>
    </div>
  );
}
