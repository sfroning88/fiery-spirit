"""
Author: Sean Froning
Created Date: 9.14.2026
Processing functions for Image loading
"""

import io
import numpy as np
from fastapi.responses import Response
from PIL import Image
from fiery_python import error
from fiery_python import BlobStorageServices
from ..schemas import InferencePreviewRequest
from .persist_service import InferencePersistService


class InferenceImageLoader:
    """Load and return the image"""

    @classmethod
    def run(cls, payload: InferencePreviewRequest) -> Response:
        interferogram_id = payload.interferogram_id
        seismic_event_id = payload.seismic_event_id
        interferogram = None
        seismic_event = None
        if interferogram_id:
            interferogram = InferencePersistService.select_interferogram(
                (interferogram_id, None)
            )
        elif seismic_event_id:
            seismic_event = InferencePersistService.select_seismic_event(
                (seismic_event_id, None)
            )
        else:
            raise error("No interferogram or seismic_event is selected")
        if interferogram:
            if not interferogram.id:
                interferogram.id = interferogram.deterministic_id()
            if not interferogram.id:
                raise error("Invalid interferogram_id")
            storage_path = interferogram.storage_path
            interferogram_id = interferogram.id
            seismic_event_id = None
        elif seismic_event:
            if not seismic_event.id:
                seismic_event.id = seismic_event.deterministic_id()
            if not seismic_event.id:
                raise error("Invalid seismic_event_id")
            storage_path = seismic_event.waveform_path
            seismic_event_id = seismic_event.id
            interferogram_id = None
        else:
            raise error("No image asset was found")
        body = BlobStorageServices.get_unrefined(storage_path)
        sample = InferencePersistService.load_npz(body)
        png = cls._interferogram_png_bytes(sample)
        return Response(
            content=png,
            status_code=200,
            media_type="image/png",
        )

    @staticmethod
    def _interferogram_png_bytes(sample: np.ndarray) -> bytes:
        phase = sample[0] if sample.ndim >= 2 else sample.reshape(1, -1)
        lo, hi = float(np.nanmin(phase)), float(np.nanmax(phase))
        scaled = (
            np.zeros(phase.shape, dtype=np.uint8)
            if hi <= lo
            else ((phase - lo) / (hi - lo) * 255).clip(0, 255).astype(np.uint8)
        )
        buf = io.BytesIO()
        Image.fromarray(scaled, mode="L").save(buf, format="PNG")
        return buf.getvalue()
