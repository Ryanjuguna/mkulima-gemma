from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class PestDiseaseHistory(Base):
    __tablename__ = "pest_disease_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(String, nullable=False, default="default_farmer", index=True)
    crop_type = Column(String, nullable=False, index=True)
    issue_type = Column(String, nullable=False, index=True)
    issue_name = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="MEDIUM", index=True)
    image_path = Column(String, nullable=True)
    symptoms_description = Column(Text, nullable=False)
    ai_diagnosis_summary = Column(Text, nullable=True)
    recommended_treatment = Column(Text, nullable=True)
    chemical_safety_warning = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="ACTIVE", index=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_pest_history_crop", "crop_type", "issue_type"),
        Index("idx_pest_history_status", "status", "severity"),
    )
