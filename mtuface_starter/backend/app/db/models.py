from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(32), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    embeddings = relationship("Embedding", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("AttendanceLog", back_populates="user", cascade="all, delete-orphan")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vector_json = Column(Text, nullable=False)
    model_version = Column(String(64), nullable=False, default="insightface-buffalo_l")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="embeddings")


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    image_path = Column(String(255), nullable=True)

    user = relationship("User", back_populates="logs")


Index("ix_attendance_logs_user_checked_at", AttendanceLog.user_id, AttendanceLog.checked_at.desc())
