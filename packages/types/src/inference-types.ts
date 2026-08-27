import { InferenceAbstainReason } from "@fiery/db/enums";
import type {
  InferenceDeformation as PrismaInferenceDeformation,
  InferenceSeismic as PrismaInferenceSeismic,
  InferenceFeedback as PrismaInferenceFeedback,
} from "@fiery/db";

export { InferenceAbstainReason };

export type InferenceDeformation = PrismaInferenceDeformation;
export type InferenceSeismic = PrismaInferenceSeismic;
export type InferenceFeedback = PrismaInferenceFeedback;
