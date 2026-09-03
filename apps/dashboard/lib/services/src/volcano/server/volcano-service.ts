import "server-only";

import { db, TrainingDeformationLabel, TrainingSeismicLabel } from "@fiery/db";
import {
  type VolcanoDashboard,
  volcanoDashboardInclude,
  type ApiInferenceRequest,
  type ApiInferenceResponse,
} from "@fiery/types";
import { toVolcanoDashboard } from "@fiery/utils";
import { ApiBackendService } from "@fiery/services";

export class VolcanoService {
  private backendService: ApiBackendService;
  constructor() {
    this.backendService = ApiBackendService.fromEnvironment();
  }

  async inference(args: ApiInferenceRequest): Promise<ApiInferenceResponse> {
    return await this.backendService.inference(args);
  }

  async feedback(
    agreed: boolean,
    correctedDeformation: TrainingDeformationLabel | null,
    correctedSeismic: TrainingSeismicLabel | null,
    note: string | null,
    interferogramId: string | null,
    seismicEventId: string | null,
    userId: string | null,
    artifactId: string,
  ): Promise<void> {
    let data = null;
    if (correctedDeformation && interferogramId) {
      data = {
        agreed: agreed,
        correctedDeformation: correctedDeformation,
        note: note,
        interferogramId: interferogramId,
        userId: userId,
        artifactId: artifactId,
      };
    } else if (correctedSeismic && seismicEventId) {
      data = {
        agreed: agreed,
        correctedSeismic: correctedSeismic,
        note: note,
        seismicEventId: seismicEventId,
        userId: userId,
        artifactId: artifactId,
      };
    }
    if (!data) {
      throw new Error("Missing deformation/interferogram or seismic/event");
    }
    await db.inferenceFeedback.create({
      data: data,
    });
  }

  async fetchVolcanoes(): Promise<VolcanoDashboard[]> {
    const rows = await db.volcano.findMany({
      include: volcanoDashboardInclude,
    });
    return rows.map(toVolcanoDashboard);
  }
}
