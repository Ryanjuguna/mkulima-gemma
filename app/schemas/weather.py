from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class WeatherCacheBase(BaseModel):
    location_name: str = Field(..., description="Location/City name")
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate")
    forecast_date: date = Field(..., description="Forecast date (YYYY-MM-DD)")
    temp_min_c: float = Field(..., description="Minimum temperature in Celsius")
    temp_max_c: float = Field(..., description="Maximum temperature in Celsius")
    condition_text: str = Field(..., description="Weather condition description")
    precipitation_mm: float = Field(default=0.0, description="Expected precipitation in mm")
    humidity_pct: Optional[int] = Field(default=None, description="Humidity percentage")
    wind_speed_kmh: Optional[float] = Field(default=None, description="Wind speed in km/h")
    is_synced: int = Field(default=1, description="1 if synced from API, 0 if manual")


class WeatherCacheCreate(WeatherCacheBase):
    pass


class WeatherCacheResponse(WeatherCacheBase):
    id: int
    fetched_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeatherListResponse(BaseModel):
    location: str
    cached_forecasts: List[WeatherCacheResponse]


class WeatherSyncRequest(BaseModel):
    location_name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def get_location(self) -> str:
        return self.location_name or self.location or "Nairobi"


class WeatherSyncResponse(BaseModel):
    synced: bool
    message: str
    updated_records: int
    forecasts: List[WeatherCacheResponse] = []
    location: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    precipitation: Optional[float] = None
    forecast: Optional[str] = None
