"use client";

import { useState } from "react";
import Image from "next/image";
import { Badge, Dot } from "@fiery/ui";
import { formatDecimal } from "@fiery/utils";
import type { VolcanoDashboard } from "@fiery/types";
import { httpSafeImageUrl } from "@/lib/utils";
import { TEST_IDS } from "@lib/test-ids";
import { IMAGE_LOADING } from "@/lib/constants";

type HomeVolcanoProps = {
  volcano: VolcanoDashboard;
  isMobile: boolean;
};

export function HomeVolcano({ volcano, isMobile }: HomeVolcanoProps) {
  const chipText = isMobile ? "text-[10px]" : "text-xs";
  const chipClass = `inline-flex items-center rounded-sm border px-2 py-0.5 font-data font-medium ${chipText}`;
  const metaText = isMobile ? "text-[11px]" : "text-xs";
  const imageSrc = httpSafeImageUrl(volcano.imagePath);
  const [failedImageSrc, setFailedImageSrc] = useState<string | null>(null);
  const imageFailed = imageSrc != null && imageSrc === failedImageSrc;

  return (
    <div data-testid={TEST_IDS.volcanoPopup} className="min-w-0">
      {imageSrc && !imageFailed ? (
        <Image
          src={imageSrc}
          alt={volcano.name}
          width={256}
          height={128}
          sizes="256px"
          quality={32}
          className="mb-2 h-32 w-64 object-cover"
          onError={() => setFailedImageSrc(imageSrc)}
        />
      ) : (
        <Image
          src={IMAGE_LOADING}
          alt={volcano.name}
          width={256}
          height={256}
          sizes="256px"
          quality={16}
          className="mb-2 h-48 w-64 object-contain"
        />
      )}
      <div className="flex items-center gap-2 flex-wrap">
        <p
          className={`font-semibold text-zinc-900 truncate ${isMobile ? "text-sm" : "text-base"}`}
        >
          {volcano.name}
        </p>
        <span className={`${chipClass} border-zinc-300 text-zinc-700`}>
          {volcano.zone.toUpperCase()}
        </span>
        <span className={`${chipClass} border-zinc-200 text-zinc-600`}>
          {formatDecimal(volcano.latitude)}
        </span>
        <span className={`${chipClass} border-zinc-200 text-zinc-600`}>
          {formatDecimal(volcano.longitude)}
        </span>
        <span className={`${chipClass} border-zinc-200 text-zinc-600`}>
          {volcano.elevationM} m
        </span>
      </div>
      <div
        className={`mt-0.5 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-zinc-600 ${metaText}`}
      >
        <span>{volcano.country}</span>
        <Dot />
        <Badge>{volcano._count.interferograms} interferograms</Badge>
        <Dot />
        <Badge>{volcano._count.seismicEvents} seismic</Badge>
        {volcano.deformation.sample ? (
          <>
            <Dot />
            <Badge>deformation sample</Badge>
          </>
        ) : null}
        {volcano.seismic.sample ? (
          <>
            <Dot />
            <Badge>seismic sample</Badge>
          </>
        ) : null}
      </div>
    </div>
  );
}
