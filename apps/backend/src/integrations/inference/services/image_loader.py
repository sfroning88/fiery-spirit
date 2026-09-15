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
        png = cls._png_image(sample)
        return Response(
            content=png,
            status_code=200,
            media_type="image/png",
        )

    @classmethod
    def _png_image(cls, sample: np.ndarray) -> bytes:
        phase = cls._phase_plane(sample)
        index = cls._phase_to_uint8_index(phase)
        rgb = cls._hsv_to_rgb_uint8(index.astype(np.float32) / 255.0)
        return cls._png_bytes_from_rgb(rgb)

    @staticmethod
    def _phase_plane(sample: np.ndarray) -> np.ndarray:
        if sample.ndim >= 2:
            return np.asarray(sample[0], dtype=np.float32)
        return sample.reshape(1, -1).astype(np.float32)

    @staticmethod
    def _phase_to_uint8_index(phase: np.ndarray) -> np.ndarray:
        lo, hi = float(np.nanmin(phase)), float(np.nanmax(phase))
        if hi <= lo:
            return np.zeros(phase.shape, dtype=np.uint8)
        scaled = (phase - lo) / (hi - lo) * 255.0
        return scaled.clip(0, 255).astype(np.uint8)

    @staticmethod
    def _png_bytes_from_rgb(rgb: np.ndarray) -> bytes:
        if rgb.ndim != 3 or rgb.shape[-1] != 3:
            raise ValueError("expected RGB array with shape (H, W, 3)")
        buf = io.BytesIO()
        Image.fromarray(np.ascontiguousarray(rgb), mode="RGB").save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _hsv_to_rgb_uint8(h01: np.ndarray) -> np.ndarray:
        h = (h01 % 1.0) * 6.0
        i = np.floor(h).astype(np.int32)
        f = h - i
        p = np.zeros_like(h01)
        q = 1.0 - f
        t = f
        r = np.choose(i % 6, [1, q, p, p, t, 1])
        g = np.choose(i % 6, [t, 1, 1, q, p, p])
        b = np.choose(i % 6, [p, p, t, 1, 1, q])
        rgb = np.stack([r, g, b], axis=-1)
        return (rgb * 255.0).clip(0, 255).astype(np.uint8)
