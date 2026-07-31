from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FarmerActivityBase(BaseModel):
    farmer_id: Optional[str] = Field(default=None, description="Farmer profile ID")
    farmer_name: Optional[str] = Field(default=None, description="Farmer name alias")
    activity_type: str = Field(..., description="Classification of activity (e.g. PLANTING, FERTILIZER_APPLICATION)")
    crop_type: str = Field(..., description="Crop targeted")
    description: Optional[str] = Field(default=None, description="Activity description")
    details: Optional[str] = Field(default=None, description="Details description alias")
    quantity: Optional[float] = Field(default=None, description="Quantity applied or harvested")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    field_location: Optional[str] = Field(default=None, description="Field location or plot name")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    logged_at: Optional[datetime] = Field(default=None, description="Timestamp of activity execution")

    def get_description(self) -> str:
        return self.description or self.details or ""

    def get_farmer_id(self) -> str:
        return self.farmer_id or self.farmer_name or "default_farmer"


class FarmerActivityCreate(FarmerActivityBase):
    pass


class FarmerActivityUpdate(BaseModel):
    farmer_id: Optional[str] = None
    farmer_name: Optional[str] = None
    activity_type: Optional[str] = None
    crop_type: Optional[str] = None
    description: Optional[str] = None
    details: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    field_location: Optional[str] = None
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None


class FarmerActivityResponse(FarmerActivityBase):
    id: int
    created_at: datetime
    farmer_name: Optional[str] = None
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            f_name = data.get("farmer_name") or data.get("farmer_id") or "default_farmer"
            dets = data.get("details") or data.get("description") or ""
            data["farmer_name"] = f_name
            data["details"] = dets
            data["farmer_id"] = f_name
            data["description"] = dets
            return data
        elif hasattr(data, "farmer_id") or hasattr(data, "farmer_name"):
            f_name = getattr(data, "farmer_name", None) or getattr(data, "farmer_id", None) or "default_farmer"
            desc = getattr(data, "details", None) or getattr(data, "description", None) or ""
            return {
                "id": getattr(data, "id", None),
                "farmer_id": f_name,
                "farmer_name": f_name,
                "activity_type": getattr(data, "activity_type", None),
                "crop_type": getattr(data, "crop_type", None),
                "description": desc,
                "details": desc,
                "quantity": getattr(data, "quantity", None),
                "unit": getattr(data, "unit", None),
                "field_location": getattr(data, "field_location", None),
                "notes": getattr(data, "notes", None),
                "logged_at": getattr(data, "logged_at", None),
                "created_at": getattr(data, "created_at", None),
            }
        return data


class FarmerActivityListResponse(BaseModel):
    total: int
    activities: List[FarmerActivityResponse]
