import {
  VolcanoZone,
  VolcanoActivitySource,
  VolcanoAlertLevel,
} from "@fiery/db/enums";
import type {
  Volcano as PrismaVolcano,
  VolcanoActivity as PrismaVolcanoActivity,
} from "@fiery/db";

export { VolcanoZone, VolcanoActivitySource, VolcanoAlertLevel };

export type Volcano = PrismaVolcano;
export type VolcanoActivity = PrismaVolcanoActivity;
