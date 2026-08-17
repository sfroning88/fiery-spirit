import type {
  Prisma,
  Property as PrismaProperty,
  PropertySnapshot as PrismaPropertySnapshot,
} from "@focus/db";

export type Property = PrismaProperty;
export type PropertySnapshot = PrismaPropertySnapshot;

export type PropertyCard = Prisma.PropertyGetPayload<{
  include: { snapshots: true; msa: true };
}>;

export type PropertyListEntry = Prisma.PropertyGetPayload<{
  include: {
    msa: { select: { name: true } };
    snapshots: {
      select: { occupancy: true; reportedAt: true; createdAt: true };
    };
    _count: { select: { snapshots: true } };
  };
}>;

export type CreateSnapshotArgs = {
  propertyId: string;
  reportedAt: string;
  occupancy: number;
  totalRevenues: number;
  repairsMaintenance: number;
  payroll: number;
  utilities: number;
  contractServices: number;
  rawFood: number;
  culinarySupplies: number;
  administrative: number;
  marketingPromotions: number;
  activities: number;
  otherExpenses: number;
  controllableExpenses: number;
  managementFee: number;
  realEstateTaxes: number;
  insurance: number;
  nonControllableExpenses: number;
  totalExpenses: number;
  operatingMargin: number;
  controllablePRD: number;
};
