import type { CreateSnapshotArgs } from "@focus/types";
import { toNum } from "./number-utils";

export type SnapshotFormState = Omit<CreateSnapshotArgs, "propertyId">;

export type SnapshotFormNumericKey = Exclude<
  keyof SnapshotFormState,
  "reportedAt"
>;

export type FormFieldKey<T> = {
  key: keyof T;
  label: string;
};

export type SnapshotFormFieldDef = {
  key: SnapshotFormNumericKey;
  label: string;
};

export function defaultIsoDateString(): string {
  const now = new Date();
  const year = String(now.getFullYear());
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function getDefaultSnapshotFormState(): SnapshotFormState {
  return {
    reportedAt: defaultIsoDateString(),
    occupancy: 0,
    totalRevenues: 0,
    repairsMaintenance: 0,
    payroll: 0,
    utilities: 0,
    contractServices: 0,
    rawFood: 0,
    culinarySupplies: 0,
    administrative: 0,
    marketingPromotions: 0,
    activities: 0,
    otherExpenses: 0,
    controllableExpenses: 0,
    managementFee: 0,
    realEstateTaxes: 0,
    insurance: 0,
    nonControllableExpenses: 0,
    totalExpenses: 0,
    operatingMargin: 0,
    controllablePRD: 0,
  };
}

export const SNAPSHOT_FORM_SUMMARY_FIELDS: SnapshotFormFieldDef[] = [
  { key: "occupancy", label: "Occupancy (%)" },
  { key: "totalRevenues", label: "Total revenues" },
  { key: "operatingMargin", label: "Operating margin (%)" },
  { key: "controllablePRD", label: "Controllable PRD" },
];

export const SNAPSHOT_FORM_EXPENSE_FIELDS: SnapshotFormFieldDef[] = [
  { key: "repairsMaintenance", label: "Repairs & maintenance" },
  { key: "payroll", label: "Payroll" },
  { key: "utilities", label: "Utilities" },
  { key: "contractServices", label: "Contract services" },
  { key: "rawFood", label: "Raw food" },
  { key: "culinarySupplies", label: "Culinary supplies" },
  { key: "administrative", label: "Administrative" },
  { key: "marketingPromotions", label: "Marketing" },
  { key: "activities", label: "Activities" },
  { key: "otherExpenses", label: "Other expenses" },
  { key: "controllableExpenses", label: "Controllable (total)" },
  { key: "managementFee", label: "Management fee" },
  { key: "realEstateTaxes", label: "Real estate taxes" },
  { key: "insurance", label: "Insurance" },
  { key: "nonControllableExpenses", label: "Non-controllable (total)" },
  { key: "totalExpenses", label: "Total expenses" },
];

export const DASHBOARD_DARK_FORM_INPUT_CLASS =
  "w-full rounded-sm border border-white/10 bg-white/5 px-2 py-1.5 text-xs font-data-mono text-white placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-white/25";

export const DASHBOARD_DARK_FORM_LABEL_CLASS =
  "text-[10px] text-white/50 block mb-0.5";

export function patchObjectField<T extends object, K extends keyof T>(
  state: T,
  key: K,
  value: T[K],
): T {
  return { ...state, [key]: value };
}

export function readNumberInputString(raw: string): number {
  return toNum(raw);
}

export function numberInputDisplayValue(n: number): number | "" {
  return Number.isNaN(n) ? "" : n;
}
