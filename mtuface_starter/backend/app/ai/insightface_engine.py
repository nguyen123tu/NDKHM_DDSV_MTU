import numpy as np

from app.core.config import settings


class InsightFaceEngine:
    def __init__(self):
        self._app = None

    def _lazy_init(self):
        if self._app is not None:
            return
        from insightface.app import FaceAnalysis

        self._app = FaceAnalysis(name=settings.INSIGHTFACE_MODEL, providers=["CPUExecutionProvider"])
        self._app.prepare(ctx_id=0, det_size=settings.INSIGHTFACE_DET_SIZE)

    def extract_embedding(self, bgr_image: np.ndarray):
        self._lazy_init()
        faces = self._app.get(bgr_image)
        if not faces:
            return None, None
        best = sorted(faces, key=lambda f: f.det_score, reverse=True)[0]
        emb = best.embedding.astype("float32")
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        return emb, best.bbox.astype(int).tolist()


engine = InsightFaceEngine()
