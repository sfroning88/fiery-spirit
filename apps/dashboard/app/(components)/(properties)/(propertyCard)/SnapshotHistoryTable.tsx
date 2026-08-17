import { ChevronDown } from "lucide-react";
import type { PropertyCard } from "@focus/types";
import { SectionLabel } from "@focus/ui";
import { formatCurrency, formatDate, formatPercent } from "@focus/utils";

type SnapshotHistoryTableProps = {
  snapshots: PropertyCard["snapshots"];
};

export function SnapshotHistoryTable({ snapshots }: SnapshotHistoryTableProps) {
  const sorted = [...snapshots].sort(
    (a, b) =>
      new Date(b.reportedAt).getTime() - new Date(a.reportedAt).getTime(),
  );

  if (sorted.length === 0) {
    return (
      <div className="border border-white/10 rounded-sm p-3 md:p-4">
        <SectionLabel>Snapshot History</SectionLabel>
        <p className="mt-2.5 md:mt-3 text-xs md:text-sm text-white/40">
          No snapshots on file.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-white/10 rounded-sm p-3 md:p-4">
      <SectionLabel>Snapshot History</SectionLabel>
      <div className="mt-2.5 md:mt-3 -mx-3 md:-mx-4 overflow-x-auto">
        <table className="w-full text-xs md:text-sm min-w-[400px]">
          <thead>
            <tr className="text-[9px] md:text-[11px] uppercase tracking-wider text-white/35">
              <th className="pb-2 pl-3 md:pl-4 text-left font-medium">Date</th>
              <th className="pb-2 text-left font-medium">Occ %</th>
              <th className="pb-2 hidden md:table-cell" />
              <th className="pb-2 text-right font-medium">Revenues</th>
              <th className="pb-2 pr-3 md:pr-4 text-right font-medium">
                Op. Mgn
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((s) => (
              <tr
                key={s.reportedAt.toString()}
                className="border-b border-white/5 last:border-0"
              >
                <td className="py-1.5 md:py-2 pl-3 md:pl-4 text-white/60 font-data-mono text-[10px] md:text-xs whitespace-nowrap">
                  {formatDate(s.reportedAt)}
                </td>
                <td className="py-1.5 md:py-2 font-data-mono font-semibold text-white whitespace-nowrap">
                  {formatPercent(s.occupancy)}
                </td>
                <td className="hidden md:table-cell" />
                <td className="py-1.5 md:py-2 text-right font-data-mono text-white/70 whitespace-nowrap">
                  {formatCurrency(s.totalRevenues)}
                </td>
                <td className="py-1.5 md:py-2 pr-3 md:pr-4 text-right font-data-mono text-white/60 whitespace-nowrap">
                  {formatPercent(s.operatingMargin)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sorted.length > 3 && (
        <div className="mt-1.5 md:mt-2 flex justify-center">
          <ChevronDown size={14} className="text-white/30 md:h-4 md:w-4" />
        </div>
      )}
    </div>
  );
}
