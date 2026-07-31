from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ExtensionDirectory(Base):
    __tablename__ = "extension_directory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    role_or_type = Column(String, nullable=False, index=True)
    organization = Column(String, nullable=True)
    county_region = Column(String, nullable=False, index=True)
    sub_county_ward = Column(String, nullable=True)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=True)
    services_offered = Column(Text, nullable=True)
    is_verified = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_extension_county", "county_region", "role_or_type"),
    )
