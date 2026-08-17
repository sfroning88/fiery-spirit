import type { PropertyCard } from "@focus/types";
import { SectionLabel } from "@focus/ui";
import { formatCurrency, toNum } from "@focus/utils";

type ExpenseBreakdownCardProps = {
  snapshot: PropertyCard["snapshots"][number];
};

export function ExpenseBreakdownCard({ snapshot }: ExpenseBreakdownCardProps) {
  const otherControllable =
    toNum(snapshot.activities) +
    toNum(snapshot.culinarySupplies) +
    toNum(snapshot.otherExpenses);

  const lines: { label: string; value: unknown; bold?: boolean }[] = [
    { label: "Payroll", value: snapshot.payroll },
    { label: "Contract services", value: snapshot.contractServices },
    { label: "Raw food", value: snapshot.rawFood },
    { label: "Repairs & maint.", value: snapshot.repairsMaintenance },
    { label: "Utilities", value: snapshot.utilities },
    { label: "Admin", value: snapshot.administrative },
    { label: "Marketing", value: snapshot.marketingPromotions },
    { label: "Other controllable", value: otherControllable },
    {
      label: "Total controllable",
      value: snapshot.controllableExpenses,
      bold: true,
    },
  ];

  return (
    <div className="border border-white/10 rounded-sm p-3 md:p-4 flex flex-col">
      <SectionLabel>Expense Breakdown</SectionLabel>
      <div className="mt-2.5 md:mt-3 flex-1">
        <table className="w-full text-xs md:text-sm">
          <tbody>
            {lines.map((l) => (
              <tr
                key={l.label}
                className={`border-b border-white/5 last:border-0 ${l.bold ? "border-t border-white/10" : ""}`}
              >
                <td
                  className={`py-1 md:py-1.5 text-white/70 ${l.bold ? "font-semibold text-white pt-2 md:pt-2.5" : ""}`}
                >
                  {l.label}
                </td>
                <td
                  className={`py-1 md:py-1.5 text-right font-data-mono text-white/70 whitespace-nowrap ${l.bold ? "font-semibold text-white pt-2 md:pt-2.5" : ""}`}
                >
                  {formatCurrency(l.value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
