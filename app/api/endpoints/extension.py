from typing import Optional, Union, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.extension import ExtensionDirectory
from app.schemas.extension import (
    ExtensionDirectoryCreate,
    ExtensionDirectoryResponse,
    ExtensionDirectoryListResponse,
)

router = APIRouter()


@router.get("", response_model=Union[ExtensionDirectoryListResponse, List[ExtensionDirectoryResponse]])
@router.get("/", response_model=Union[ExtensionDirectoryListResponse, List[ExtensionDirectoryResponse]])
def search_extension_directory(
    request: Request,
    county: Optional[str] = Query(default=None, description="Filter by county/region"),
    region: Optional[str] = Query(default=None, description="Filter by region alias"),
    role_type: Optional[str] = Query(default=None, description="Filter by role or type"),
    search: Optional[str] = Query(default=None, description="Free text search in name, organization, services"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(ExtensionDirectory)
    target_region = county or region
    if target_region:
        query = query.filter(ExtensionDirectory.county_region.ilike(f"%{target_region}%"))
    if role_type:
        query = query.filter(ExtensionDirectory.role_or_type.ilike(f"%{role_type}%"))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ExtensionDirectory.name.ilike(search_term),
                ExtensionDirectory.organization.ilike(search_term),
                ExtensionDirectory.services_offered.ilike(search_term),
                ExtensionDirectory.role_or_type.ilike(search_term),
            )
        )

    total = query.count()
    directory = query.order_by(ExtensionDirectory.id.desc()).offset(offset).limit(limit).all()

    res_directory = []
    for item in directory:
        res_obj = ExtensionDirectoryResponse.model_validate(item)
        res_obj.provider_name = item.name
        res_obj.region = item.county_region
        res_obj.contact_info = item.phone_number
        res_directory.append(res_obj)

    if "/v1" not in request.url.path:
        return res_directory

    return ExtensionDirectoryListResponse(total=total, directory=res_directory)


@router.post("", response_model=ExtensionDirectoryResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ExtensionDirectoryResponse, status_code=status.HTTP_201_CREATED)
def register_extension_contact(
    contact_in: ExtensionDirectoryCreate,
    db: Session = Depends(get_db),
):
    contact_data = contact_in.model_dump()
    contact_data["name"] = contact_in.get_name()
    contact_data["county_region"] = contact_in.get_region()
    contact_data["phone_number"] = contact_in.get_contact()

    contact_data["created_at"] = datetime.now(timezone.utc)

    valid_keys = {c.name for c in ExtensionDirectory.__table__.columns}
    filtered_data = {k: v for k, v in contact_data.items() if k in valid_keys}

    db_contact = ExtensionDirectory(**filtered_data)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)

    res_obj = ExtensionDirectoryResponse.model_validate(db_contact)
    res_obj.provider_name = db_contact.name
    res_obj.region = db_contact.county_region
    res_obj.contact_info = db_contact.phone_number
    return res_obj


@router.get("/{contact_id}", response_model=ExtensionDirectoryResponse)
def get_extension_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    contact = db.query(ExtensionDirectory).filter(ExtensionDirectory.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extension contact with ID {contact_id} not found",
        )
    res_obj = ExtensionDirectoryResponse.model_validate(contact)
    res_obj.provider_name = contact.name
    res_obj.region = contact.county_region
    res_obj.contact_info = contact.phone_number
    return res_obj
