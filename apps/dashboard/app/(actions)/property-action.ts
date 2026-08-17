"use server";

import { z } from "zod";
import { selfUserAction } from "@focus/auth/server";
import { PropertyService } from "@lib/services";
import { type PropertyCard, type PropertyListEntry } from "@focus/types";

const fetchPropertiesSchema = z.object({});

export const fetchPropertiesAction = selfUserAction(
  fetchPropertiesSchema,
  async (): Promise<PropertyListEntry[]> => {
    return await PropertyService.fetchProperties();
  },
);

const fetchPropertyCardSchema = z.object({
  id: z.string().uuid(),
});

export const fetchPropertyCardAction = selfUserAction(
  fetchPropertyCardSchema,
  async (ctx): Promise<PropertyCard> => {
    return await PropertyService.fetchPropertyCard(ctx.id);
  },
);

const createSnapshotSchema = z.object({
  propertyId: z.string().uuid(),
  reportedAt: z
    .string()
    .min(1)
    .refine((s) => !Number.isNaN(Date.parse(s)), {
      message: "Invalid reportedAt",
    }),
  occupancy: z.number(),
  totalRevenues: z.number(),
  repairsMaintenance: z.number(),
  payroll: z.number(),
  utilities: z.number(),
  contractServices: z.number(),
  rawFood: z.number(),
  culinarySupplies: z.number(),
  administrative: z.number(),
  marketingPromotions: z.number(),
  activities: z.number(),
  otherExpenses: z.number(),
  controllableExpenses: z.number(),
  managementFee: z.number(),
  realEstateTaxes: z.number(),
  insurance: z.number(),
  nonControllableExpenses: z.number(),
  totalExpenses: z.number(),
  operatingMargin: z.number(),
  controllablePRD: z.number(),
});

export const createSnapshotAction = selfUserAction(
  createSnapshotSchema,
  async (ctx) => {
    const { userId, ...args } = ctx;
    void userId;
    return await PropertyService.createSnapshot(args);
  },
);
