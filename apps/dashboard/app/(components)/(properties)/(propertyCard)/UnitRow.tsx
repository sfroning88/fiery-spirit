export function UnitRow({
  label,
  value,
  bold,
}: {
  label: string;
  value: number;
  bold?: boolean;
}) {
  return (
    <tr className="border-b border-white/5 last:border-0">
      <td
        className={`py-1 md:py-1.5 text-white/70 ${bold ? "font-semibold text-white" : ""}`}
      >
        {label}
      </td>
      <td
        className={`py-1 md:py-1.5 text-right font-data-mono text-white/70 ${bold ? "font-semibold text-white" : ""}`}
      >
        {value}
      </td>
    </tr>
  );
}
