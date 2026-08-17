import "server-only";

import { db } from "@focus/db";
import {
  type CreateSnapshotArgs,
  type PropertyCard,
  type PropertyListEntry,
  type PropertySnapshot,
} from "@focus/types";
import { parseCalendarDate } from "@focus/utils";

export const PropertyService = {
  async fetchProperties(): Promise<PropertyListEntry[]> {
    const properties = await db.property.findMany({
      orderBy: { name: "asc" },
      include: {
        msa: { select: { name: true } },
        snapshots: {
          select: { occupancy: true, reportedAt: true, createdAt: true },
        },
        _count: { select: { snapshots: true } },
      },
    });
    return properties;
  },

  async fetchPropertyCard(id: string): Promise<PropertyCard> {
    const property = await db.property.findUnique({
      where: { id },
      include: { snapshots: true, msa: true },
    });
    if (!property) {
      throw new Error("Property does not exist");
    }
    return property;
  },

  async createSnapshot(args: CreateSnapshotArgs): Promise<PropertySnapshot> {
    const property = await db.property.findUnique({
      where: { id: args.propertyId },
    });
    if (!property) {
      throw new Error("Property does not exist");
    }
    const { propertyId, reportedAt: reportedAtRaw, ...metrics } = args;
    const reportedAt = parseCalendarDate(reportedAtRaw);
    return db.propertySnapshot.upsert({
      where: {
        propertyId_reportedAt: { propertyId, reportedAt },
      },
      create: {
        propertyId,
        reportedAt,
        ...metrics,
      },
      update: metrics,
    });
  },
};
