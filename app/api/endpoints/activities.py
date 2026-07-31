from typing import Optional, Union, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.activity import FarmerActivityLog
from app.schemas.activity import (
    FarmerActivityCreate,
    FarmerActivityUpdate,
    FarmerActivityResponse,
    FarmerActivityListResponse,
)

router = APIRouter()


@router.get("", response_model=Union[FarmerActivityListResponse, List[FarmerActivityResponse]])
@router.get("/", response_model=Union[FarmerActivityListResponse, List[FarmerActivityResponse]])
def list_activities(
    request: Request,
    farmer_id: Optional[str] = Query(default=None, description="Filter by farmer ID"),
    farmer_name: Optional[str] = Query(default=None, description="Filter by farmer name alias"),
    crop_type: Optional[str] = Query(default=None, description="Filter by crop type"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(FarmerActivityLog)
    target_farmer = farmer_id or farmer_name
    if target_farmer:
        query = query.filter(FarmerActivityLog.farmer_id == target_farmer)
    if crop_type:
        query = query.filter(FarmerActivityLog.crop_type.ilike(f"%{crop_type}%"))

    total = query.count()
    activities = query.order_by(FarmerActivityLog.logged_at.desc(), FarmerActivityLog.id.desc()).offset(offset).limit(limit).all()

    res_activities = []
    for a in activities:
        res_obj = FarmerActivityResponse.model_validate(a)
        res_obj.farmer_name = a.farmer_id
        res_obj.details = a.description
        res_activities.append(res_obj)

    if "/v1" not in request.url.path:
        return res_activities

    return FarmerActivityListResponse(total=total, activities=res_activities)


@router.post("", response_model=FarmerActivityResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=FarmerActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_in: FarmerActivityCreate,
    db: Session = Depends(get_db),
):
    activity_data = activity_in.model_dump()
    activity_data["farmer_id"] = activity_in.get_farmer_id()
    activity_data["description"] = activity_in.get_description()
    if activity_data.get("logged_at") is None:
        activity_data["logged_at"] = datetime.now(timezone.utc)
    activity_data["created_at"] = datetime.now(timezone.utc)

    valid_keys = {c.name for c in FarmerActivityLog.__table__.columns}
    filtered_data = {k: v for k, v in activity_data.items() if k in valid_keys}

    db_activity = FarmerActivityLog(**filtered_data)
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)

    res_obj = FarmerActivityResponse.model_validate(db_activity)
    res_obj.farmer_name = db_activity.farmer_id
    res_obj.details = db_activity.description
    return res_obj


@router.get("/{activity_id}", response_model=FarmerActivityResponse)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
):
    activity = db.query(FarmerActivityLog).filter(FarmerActivityLog.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity log with ID {activity_id} not found",
        )
    res_obj = FarmerActivityResponse.model_validate(activity)
    res_obj.farmer_name = activity.farmer_id
    res_obj.details = activity.description
    return res_obj


@router.put("/{activity_id}", response_model=FarmerActivityResponse)
def update_activity(
    activity_id: int,
    activity_in: FarmerActivityUpdate,
    db: Session = Depends(get_db),
):
    activity = db.query(FarmerActivityLog).filter(FarmerActivityLog.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity log with ID {activity_id} not found",
        )

    update_data = activity_in.model_dump(exclude_unset=True)
    if "details" in update_data and not update_data.get("description"):
        update_data["description"] = update_data["details"]
    if "farmer_name" in update_data and not update_data.get("farmer_id"):
        update_data["farmer_id"] = update_data["farmer_name"]

    valid_keys = {c.name for c in FarmerActivityLog.__table__.columns}
    for field, value in update_data.items():
        if field in valid_keys:
            setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    res_obj = FarmerActivityResponse.model_validate(activity)
    res_obj.farmer_name = activity.farmer_id
    res_obj.details = activity.description
    return res_obj


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
):
    activity = db.query(FarmerActivityLog).filter(FarmerActivityLog.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity log with ID {activity_id} not found",
        )

    db.delete(activity)
    db.commit()
    return None
