import type { ReactNode } from "react";
import { X } from "lucide-react";
import type { PropertyCard } from "@focus/types";
import { Badge, Dot } from "@focus/ui";

type CardHeaderProps = {
  card: PropertyCard;
  onClose: () => void;
  actions?: ReactNode;
};

export function CardHeader({ card, onClose, actions }: CardHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <h2 className="text-base md:text-xl font-semibold text-white truncate">
          {card.name}
        </h2>
        <div className="mt-1 flex flex-wrap items-center gap-x-1.5 md:gap-x-2 gap-y-1 text-xs md:text-sm text-white/60">
          <span className="wrap-break-word">
            {card.address}, {card.city}, {card.state} {card.zip}
          </span>
          <Dot />
          <span>{card.msa.name}</span>
          <Dot />
          <Badge>Built {card.yearBuilt}</Badge>
          <Badge>{card.totalUnits} units</Badge>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0 -mt-1">
        {actions}
        <button
          type="button"
          onClick={onClose}
          className="p-1.5 -mr-1.5 text-white/40 hover:text-white/80 transition-colors"
          aria-label="Close"
        >
          <X className="h-4 w-4 md:h-[18px] md:w-[18px]" />
        </button>
      </div>
    </div>
  );
}
