"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { Button } from "@fiery/ui";
import { SignupForm } from "@fiery/auth";
import { TEST_IDS } from "@lib/test-ids";

type SignupButtonProps = {
  defaultEmail?: string;
};

export function SignupButton({ defaultEmail }: SignupButtonProps) {
  const [open, setOpen] = useState(false);
  const modal =
    open && typeof document !== "undefined" ? (
      <>
        <div
          className="fixed inset-0 z-100 bg-black/50"
          onClick={() => setOpen(false)}
          aria-hidden
        />
        <div
          className="fixed left-1/2 top-1/2 z-110 w-[min(90vw,400px)] max-h-[90vh] overflow-y-auto -translate-x-1/2 -translate-y-1/2 rounded-sm border border-white bg-surface-dark p-5 shadow-lg"
          role="dialog"
          aria-modal
          aria-labelledby="signup-title"
          data-testid={TEST_IDS.signupDialog}
        >
          <div className="flex items-center justify-between gap-3">
            <h2
              id="signup-title"
              className="text-base font-semibold text-white"
            >
              Create profile
            </h2>
            <button
              type="button"
              data-testid={TEST_IDS.signupCloseButton}
              onClick={() => setOpen(false)}
              className="p-1 -mr-1 text-white/70 hover:text-white transition-colors"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="mt-4">
            <SignupForm defaultEmail={defaultEmail} />
          </div>
        </div>
      </>
    ) : null;

  return (
    <>
      <Button
        data-testid={TEST_IDS.createProfileLink}
        onClick={() => setOpen(true)}
      >
        Create profile
      </Button>
      {typeof window !== "undefined" && modal
        ? createPortal(modal, document.body)
        : null}
    </>
  );
}
