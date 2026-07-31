from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PestDiseaseBase(BaseModel):
    farmer_id: str = Field(default="default_farmer", description="Farmer profile ID")
    crop_type: Optional[str] = Field(default=None, description="Target crop affected")
    crop_name: Optional[str] = Field(default=None, description="Crop name alias")
    issue_type: Optional[str] = Field(default="PEST", description="Classification: DISEASE, PEST, WEED, NUTRIENT_DEFICIENCY")
    issue_name: str = Field(..., description="Name of pest/disease/weed")
    severity: str = Field(default="MEDIUM", description="Severity: LOW, MEDIUM, HIGH, CRITICAL")
    image_path: Optional[str] = Field(default=None, description="Local photo path or URI")
    symptoms_description: Optional[str] = Field(default=None, description="Symptoms observed by farmer")
    description: Optional[str] = Field(default=None, description="Description alias")
    ai_diagnosis_summary: Optional[str] = Field(default=None, description="AI diagnosis result")
    recommended_treatment: Optional[str] = Field(default=None, description="Recommended treatment")
    treatment: Optional[str] = Field(default=None, description="Treatment alias")
    chemical_safety_warning: Optional[str] = Field(default=None, description="Chemical safety warning")
    status: str = Field(default="ACTIVE", description="Status: ACTIVE, RESOLVED, MONITORING")
    detected_at: Optional[datetime] = Field(default=None, description="Detection timestamp")

    def get_crop_type(self) -> str:
        return self.crop_type or self.crop_name or "Unknown Crop"

    def get_symptoms(self) -> str:
        return self.symptoms_description or self.description or ""

    def get_treatment(self) -> str:
        return self.recommended_treatment or self.treatment or ""


class PestDiseaseCreate(PestDiseaseBase):
    pass


class PestDiseaseUpdate(BaseModel):
    farmer_id: Optional[str] = None
    crop_type: Optional[str] = None
    crop_name: Optional[str] = None
    issue_type: Optional[str] = None
    issue_name: Optional[str] = None
    severity: Optional[str] = None
    image_path: Optional[str] = None
    symptoms_description: Optional[str] = None
    description: Optional[str] = None
    ai_diagnosis_summary: Optional[str] = None
    recommended_treatment: Optional[str] = None
    treatment: Optional[str] = None
    chemical_safety_warning: Optional[str] = None
    status: Optional[str] = None
    detected_at: Optional[datetime] = None


class PestDiseaseResponse(PestDiseaseBase):
    id: int
    created_at: datetime
    crop_name: Optional[str] = None
    description: Optional[str] = None
    treatment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            c_name = data.get("crop_name") or data.get("crop_type")
            desc = data.get("description") or data.get("symptoms_description")
            treat = data.get("treatment") or data.get("recommended_treatment")
            data["crop_name"] = c_name
            data["crop_type"] = c_name
            data["description"] = desc
            data["symptoms_description"] = desc
            data["treatment"] = treat
            data["recommended_treatment"] = treat
            return data
        elif hasattr(data, "crop_type") or hasattr(data, "crop_name"):
            crop = getattr(data, "crop_name", None) or getattr(data, "crop_type", None)
            desc = getattr(data, "description", None) or getattr(data, "symptoms_description", None)
            treat = getattr(data, "treatment", None) or getattr(data, "recommended_treatment", None)
            return {
                "id": getattr(data, "id", None),
                "farmer_id": getattr(data, "farmer_id", "default_farmer"),
                "crop_type": crop,
                "crop_name": crop,
                "issue_type": getattr(data, "issue_type", "PEST"),
                "issue_name": getattr(data, "issue_name", None),
                "severity": getattr(data, "severity", "MEDIUM"),
                "symptoms_description": desc,
                "description": desc,
                "recommended_treatment": treat,
                "treatment": treat,
                "status": getattr(data, "status", "ACTIVE"),
                "detected_at": getattr(data, "detected_at", None),
                "created_at": getattr(data, "created_at", None),
            }
        return data


class PestDiseaseListResponse(BaseModel):
    total: int
    records: List[PestDiseaseResponse]
