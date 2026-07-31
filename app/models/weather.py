from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint, Index
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_name = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    forecast_date = Column(Date, nullable=False, index=True)
    temp_min_c = Column(Float, nullable=False)
    temp_max_c = Column(Float, nullable=False)
    condition_text = Column(String, nullable=False)
    precipitation_mm = Column(Float, nullable=False, default=0.0)
    humidity_pct = Column(Integer, nullable=True)
    wind_speed_kmh = Column(Float, nullable=True)
    is_synced = Column(Integer, nullable=False, default=1)
    fetched_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("location_name", "forecast_date", name="uq_weather_loc_date"),
        Index("idx_weather_loc_date", "location_name", "forecast_date"),
    )
