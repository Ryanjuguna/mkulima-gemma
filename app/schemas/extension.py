from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ExtensionDirectoryBase(BaseModel):
    name: Optional[str] = Field(default=None, description="Officer or organization name")
    provider_name: Optional[str] = Field(default=None, description="Provider name alias")
    role_or_type: Optional[str] = Field(default="Extension Officer", description="Type e.g. EXTENSION_OFFICER, VETERINARIAN, AGROVET, COOPERATIVE")
    organization: Optional[str] = Field(default=None, description="Sponsoring organization")
    county_region: Optional[str] = Field(default=None, description="County or region")
    region: Optional[str] = Field(default=None, description="Region alias")
    sub_county_ward: Optional[str] = Field(default=None, description="Sub-county or ward")
    phone_number: Optional[str] = Field(default=None, description="Contact telephone number")
    contact_info: Optional[str] = Field(default=None, description="Contact info alias")
    email: Optional[str] = Field(default=None, description="Email address")
    services_offered: Optional[str] = Field(default=None, description="Services offered description")
    is_verified: int = Field(default=1, description="1 if verified, 0 if unverified")

    def get_name(self) -> str:
        return self.name or self.provider_name or "Unknown Provider"

    def get_region(self) -> str:
        return self.county_region or self.region or "General"

    def get_contact(self) -> str:
        return self.phone_number or self.contact_info or "N/A"


class ExtensionDirectoryCreate(ExtensionDirectoryBase):
    pass


from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Any

class ExtensionDirectoryResponse(ExtensionDirectoryBase):
    id: int
    created_at: datetime
    provider_name: Optional[str] = None
    region: Optional[str] = None
    contact_info: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            p_name = data.get("provider_name") or data.get("name")
            reg = data.get("region") or data.get("county_region")
            contact = data.get("contact_info") or data.get("phone_number")
            data["provider_name"] = p_name
            data["name"] = p_name
            data["region"] = reg
            data["county_region"] = reg
            data["contact_info"] = contact
            data["phone_number"] = contact
            return data
        elif hasattr(data, "name") or hasattr(data, "provider_name"):
            p_name = getattr(data, "provider_name", None) or getattr(data, "name", None)
            reg = getattr(data, "region", None) or getattr(data, "county_region", None)
            contact = getattr(data, "contact_info", None) or getattr(data, "phone_number", None)
            return {
                "id": getattr(data, "id", None),
                "name": p_name,
                "provider_name": p_name,
                "role_or_type": getattr(data, "role_or_type", "Extension Officer"),
                "organization": getattr(data, "organization", None),
                "county_region": reg,
                "region": reg,
                "sub_county_ward": getattr(data, "sub_county_ward", None),
                "phone_number": contact,
                "contact_info": contact,
                "email": getattr(data, "email", None),
                "services_offered": getattr(data, "services_offered", None),
                "is_verified": getattr(data, "is_verified", 1),
                "created_at": getattr(data, "created_at", None),
            }
        return data


class ExtensionDirectoryListResponse(BaseModel):
    total: int
    directory: List[ExtensionDirectoryResponse]
