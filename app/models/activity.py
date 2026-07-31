from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class FarmerActivityLog(Base):
    __tablename__ = "farmer_activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(String, nullable=False, default="default_farmer", index=True)
    activity_type = Column(String, nullable=False)
    crop_type = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    field_location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_activity_farmer_crop", "farmer_id", "crop_type"),
        Index("idx_activity_logged_at", logged_at.desc()),
    )
