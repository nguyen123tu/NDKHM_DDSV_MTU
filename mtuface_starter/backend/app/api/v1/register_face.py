import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai.insightface_engine import engine
from app.db.models import User
from app.db.session import get_db
from app.services.face_service import save_embedding

router = APIRouter()


@router.post("/register-face")
async def register_face(
    student_code: str = Form(...),
    full_name: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await image.read()
    np_img = np.frombuffer(content, np.uint8)
    bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if bgr is None:
        raise HTTPException(status_code=400, detail="Cannot decode image")

    emb, bbox = engine.extract_embedding(bgr)
    if emb is None:
        raise HTTPException(status_code=400, detail="No face detected")

    user = db.query(User).filter(User.student_code == student_code).first()
    if not user:
        user = User(student_code=student_code, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)

    save_embedding(db, user.id, emb, model_version="insightface-buffalo_l")
    return {
        "success": True,
        "user_id": user.id,
        "student_code": user.student_code,
        "bbox": bbox,
        "message": "Face registration successful",
    }
