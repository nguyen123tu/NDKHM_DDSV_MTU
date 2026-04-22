import json

import numpy as np
from sqlalchemy.orm import Session

from app.ai.similarity import cosine_similarity
from app.db.models import Embedding


def save_embedding(db: Session, user_id: int, emb: np.ndarray, model_version: str):
    row = Embedding(user_id=user_id, vector_json=json.dumps(emb.tolist()), model_version=model_version)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def find_best_match(db: Session, query_emb: np.ndarray, threshold: float):
    rows = db.query(Embedding).all()
    best_user_id = None
    best_score = -1.0

    for row in rows:
        vec = np.asarray(json.loads(row.vector_json), dtype="float32")
        score = cosine_similarity(query_emb, vec)
        if score > best_score:
            best_score = score
            best_user_id = row.user_id

    if best_user_id is None or best_score < threshold:
        return None, best_score
    return best_user_id, best_score
