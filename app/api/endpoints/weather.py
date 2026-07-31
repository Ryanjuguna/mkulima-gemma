from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.weather import (
    WeatherListResponse,
    WeatherSyncRequest,
    WeatherSyncResponse,
    WeatherCacheResponse,
)
from app.services.weather_service import (
    get_cached_weather as service_get_cached_weather,
    sync_weather_forecast as service_sync_weather_forecast,
)

router = APIRouter()


@router.get("", response_model=WeatherListResponse)
@router.get("/", response_model=WeatherListResponse)
def get_cached_weather(
    location_name: Optional[str] = Query(default=None, description="City or location name"),
    location: Optional[str] = Query(default=None, description="City or location name alias"),
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """
    Get cached weather forecast records for a location from SQLite database.
    """
    target_location = location_name or location
    if not target_location:
        raise HTTPException(status_code=400, detail="location or location_name query parameter required.")

    forecasts = service_get_cached_weather(db, location_name=target_location, days=days)
    if not forecasts:
        raise HTTPException(
            status_code=404,
            detail=f"No weather cached for location '{target_location}'.",
        )

    return WeatherListResponse(location=target_location, cached_forecasts=forecasts)


@router.post("/sync", response_model=WeatherSyncResponse)
@router.post("/sync/", response_model=WeatherSyncResponse)
def sync_weather_cache(
    request: WeatherSyncRequest,
    db: Session = Depends(get_db),
):
    """
    Trigger sync from Open-Meteo API, update SQLite weather_cache table,
    or fallback to offline cached forecast on failure.
    """
    loc_name = request.get_location()
    forecast_records, synced, message = service_sync_weather_forecast(
        db=db,
        location_name=loc_name,
        latitude=request.latitude,
        longitude=request.longitude,
    )

    forecast_responses = [WeatherCacheResponse.model_validate(r) for r in forecast_records]
    first = forecast_responses[0] if forecast_responses else None

    forecast_str = None
    if first:
        if first.precipitation_mm and first.precipitation_mm > 0:
            forecast_str = f"Expecting Rain ({first.condition_text})"
        else:
            forecast_str = first.condition_text

    return WeatherSyncResponse(
        synced=synced,
        message=message,
        updated_records=len(forecast_responses),
        forecasts=forecast_responses,
        location=loc_name,
        temperature=first.temp_max_c if first else None,
        humidity=float(first.humidity_pct) if first and first.humidity_pct is not None else None,
        precipitation=first.precipitation_mm if first else None,
        forecast=forecast_str,
    )

