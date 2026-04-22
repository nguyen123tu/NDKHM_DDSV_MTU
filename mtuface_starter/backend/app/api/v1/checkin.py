import os
import uuid
from datetime import datetime

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai.insightface_engine import engine
from app.core.config import settings
from app.db.models import AttendanceLog, User
from app.db.session import get_db
from app.services.face_service import find_best_match

router = APIRouter()


@router.post("/check-in")
async def check_in(image: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await image.read()
    np_img = np.frombuffer(content, np.uint8)
    bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if bgr is None:
        raise HTTPException(status_code=400, detail="Cannot decode image")

    emb, bbox = engine.extract_embedding(bgr)
    if emb is None:
        raise HTTPException(status_code=400, detail="No face detected")

    user_id, score = find_best_match(db, emb, threshold=settings.FACE_THRESHOLD)
    if user_id is None:
        return {"success": False, "message": "Unknown face", "confidence": float(score)}

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    os.makedirs(settings.EVIDENCE_DIR, exist_ok=True)
    filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
    output_path = os.path.join(settings.EVIDENCE_DIR, filename)
    cv2.imwrite(output_path, bgr)

    log = AttendanceLog(user_id=user.id, confidence=float(score), image_path=output_path)
    db.add(log)
    db.commit()

    return {
        "success": True,
        "student_code": user.student_code,
        "full_name": user.full_name,
        "confidence": float(score),
        "bbox": bbox,
        "image_path": output_path,
    }
