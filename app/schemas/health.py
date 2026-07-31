from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    status: str = Field(default="ok", description="Application status")
    app: str = Field(default="mkulima_gemma", description="Application name")
    database: str = Field(default="connected", description="Database connection status")
    timestamp: datetime = Field(..., description="Health check timestamp")
