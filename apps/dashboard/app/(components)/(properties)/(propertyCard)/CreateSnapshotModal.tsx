"use client";

import {
  useCallback,
  useId,
  useState,
  type ChangeEvent,
  type SubmitEvent,
} from "react";
import { createPortal } from "react-dom";
import { Plus, X } from "lucide-react";
import { occupancyColors } from "@focus/ui";
import {
  DASHBOARD_DARK_FORM_INPUT_CLASS,
  DASHBOARD_DARK_FORM_LABEL_CLASS,
  getDefaultSnapshotFormState,
  getOccupancyTier,
  numberInputDisplayValue,
  patchObjectField,
  readNumberInputString,
  SNAPSHOT_FORM_EXPENSE_FIELDS,
  SNAPSHOT_FORM_SUMMARY_FIELDS,
  type SnapshotFormNumericKey,
  type SnapshotFormState,
  toNum,
} from "@focus/utils";
import { useCreateSnapshot } from "@/app/(hooks)/use-create-snapshot";
import { SectionLabel } from "@focus/ui";
import { TEST_IDS } from "@lib/test-ids";

type CreateSnapshotModalProps = {
  userId: string;
  propertyId: string;
};

export function CreateSnapshotModal({
  userId,
  propertyId,
}: CreateSnapshotModalProps) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<SnapshotFormState>(
    getDefaultSnapshotFormState,
  );
  const formId = useId();
  const createSnapshot = useCreateSnapshot(userId);

  const setField = useCallback(
    <K extends keyof SnapshotFormState>(
      key: K,
      value: SnapshotFormState[K],
    ) => {
      setForm((f) => patchObjectField(f, key, value));
    },
    [],
  );

  const onNumber =
    (key: SnapshotFormNumericKey) => (e: ChangeEvent<HTMLInputElement>) => {
      setField(key, readNumberInputString(e.target.value));
    };

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    createSnapshot.mutate(
      { propertyId, ...form },
      {
        onSuccess: () => setOpen(false),
      },
    );
  };

  const tier =
    toNum(form.occupancy) > 0 ? getOccupancyTier(form.occupancy) : null;

  const modal =
    open && typeof document !== "undefined" ? (
      <>
        <div
          className="fixed inset-0 z-60 bg-black/70 backdrop-blur-[2px]"
          onClick={() => {
            if (!createSnapshot.isPending) setOpen(false);
          }}
          aria-hidden
        />
        <div
          className="fixed z-61 left-3 right-3 top-8 bottom-8 md:left-1/2 md:top-1/2 md:right-auto md:bottom-auto md:-translate-x-1/2 md:-translate-y-1/2 md:w-[min(100vw-2rem,520px)] md:max-h-[min(90vh,720px)] flex flex-col overflow-hidden rounded-md border border-white/10 bg-surface-dark shadow-2xl font-data"
          role="dialog"
          aria-modal
          aria-labelledby={formId}
          data-testid={TEST_IDS.snapshotFormDialog}
        >
          <div className="flex items-center justify-between gap-3 border-b border-white/10 px-3 py-2.5 md:px-4 md:py-3 shrink-0">
            <h2 id={formId} className="text-sm font-semibold text-white">
              New snapshot
            </h2>
            <button
              type="button"
              onClick={() => !createSnapshot.isPending && setOpen(false)}
              className="p-1.5 -mr-1 text-white/40 hover:text-white/80 transition-colors"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <form
            onSubmit={handleSubmit}
            className="overflow-y-auto flex-1 min-h-0 p-3 md:p-4 flex flex-col gap-4"
          >
            {createSnapshot.isError && (
              <p className="text-xs text-red-400">
                {createSnapshot.error instanceof Error
                  ? createSnapshot.error.message
                  : "Could not save snapshot."}
              </p>
            )}

            <div>
              <SectionLabel>Reporting period</SectionLabel>
              <div className="mt-2 max-w-[200px]">
                <label
                  className={DASHBOARD_DARK_FORM_LABEL_CLASS}
                  htmlFor={`${formId}-date`}
                >
                  As of date
                </label>
                <input
                  id={`${formId}-date`}
                  type="date"
                  className={DASHBOARD_DARK_FORM_INPUT_CLASS}
                  value={form.reportedAt}
                  onChange={(e) => setField("reportedAt", e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <SectionLabel>Key metrics</SectionLabel>
              <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {SNAPSHOT_FORM_SUMMARY_FIELDS.map(({ key, label }) => (
                  <div key={key}>
                    <label
                      className={DASHBOARD_DARK_FORM_LABEL_CLASS}
                      htmlFor={`${formId}-${String(key)}`}
                    >
                      {label}
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        id={`${formId}-${String(key)}`}
                        type="number"
                        className={DASHBOARD_DARK_FORM_INPUT_CLASS}
                        step={
                          key === "occupancy" || key === "operatingMargin"
                            ? "0.01"
                            : "1"
                        }
                        value={numberInputDisplayValue(form[key] as number)}
                        onChange={onNumber(key)}
                      />
                      {key === "occupancy" && tier && (
                        <span
                          className={`shrink-0 rounded-sm border px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide font-sans ${occupancyColors[tier]}`}
                        >
                          {tier}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <SectionLabel>Expense lines</SectionLabel>
              <p className="mt-1.5 text-[10px] text-white/35">
                Enter dollar amounts (0 if none). Same period as reporting date
                above.
              </p>
              <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {SNAPSHOT_FORM_EXPENSE_FIELDS.map(({ key, label }) => (
                  <div key={key}>
                    <label
                      className={DASHBOARD_DARK_FORM_LABEL_CLASS}
                      htmlFor={`${formId}-${String(key)}`}
                    >
                      {label}
                    </label>
                    <input
                      id={`${formId}-${String(key)}`}
                      type="number"
                      className={DASHBOARD_DARK_FORM_INPUT_CLASS}
                      step="1"
                      value={numberInputDisplayValue(form[key] as number)}
                      onChange={onNumber(key)}
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-auto pt-1 flex flex-col-reverse sm:flex-row sm:justify-end gap-2 border-t border-white/10 -mx-3 md:-mx-4 -mb-3 md:-mb-4 px-3 md:px-4 py-2.5 md:py-3">
              <button
                type="button"
                onClick={() => setOpen(false)}
                disabled={createSnapshot.isPending}
                className="rounded-sm border border-white/15 px-3 py-2 text-xs font-medium text-white/70 hover:bg-white/5 hover:text-white transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createSnapshot.isPending}
                className="rounded-sm border border-fhp-blue-600 bg-fhp-blue-800/80 px-3 py-2 text-xs font-medium text-white hover:bg-fhp-blue-800 transition-colors disabled:opacity-50"
              >
                {createSnapshot.isPending ? "Saving…" : "Save snapshot"}
              </button>
            </div>
          </form>
        </div>
      </>
    ) : null;

  return (
    <>
      <button
        type="button"
        data-testid={TEST_IDS.propertyCardAddSnapshotButton}
        onClick={() => {
          setForm(getDefaultSnapshotFormState());
          setOpen(true);
        }}
        className="inline-flex items-center gap-1.5 rounded-sm border border-white/15 px-2.5 py-1.5 text-xs font-medium text-white/80 hover:bg-white/5 hover:text-white transition-colors"
      >
        <Plus className="h-3.5 w-3.5" aria-hidden />
        <span className="hidden min-[400px]:inline">Add snapshot</span>
        <span className="min-[400px]:hidden">Add</span>
      </button>
      {typeof window !== "undefined" && modal
        ? createPortal(modal, document.body)
        : null}
    </>
  );
}
