from typing import Optional, Union, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.pest_disease import PestDiseaseHistory
from app.schemas.pest_disease import (
    PestDiseaseCreate,
    PestDiseaseUpdate,
    PestDiseaseResponse,
    PestDiseaseListResponse,
)

router = APIRouter()


@router.get("", response_model=Union[PestDiseaseListResponse, List[PestDiseaseResponse]])
@router.get("/", response_model=Union[PestDiseaseListResponse, List[PestDiseaseResponse]])
def list_pest_disease_history(
    request: Request,
    farmer_id: Optional[str] = Query(default=None, description="Filter by farmer ID"),
    crop_type: Optional[str] = Query(default=None, description="Filter by crop type"),
    crop_name: Optional[str] = Query(default=None, description="Filter by crop name alias"),
    issue_type: Optional[str] = Query(default=None, description="Filter by issue type: DISEASE, PEST, WEED, NUTRIENT_DEFICIENCY"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status: ACTIVE, RESOLVED, MONITORING"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(PestDiseaseHistory)
    target_crop = crop_type or crop_name
    if farmer_id:
        query = query.filter(PestDiseaseHistory.farmer_id == farmer_id)
    if target_crop:
        query = query.filter(PestDiseaseHistory.crop_type.ilike(f"%{target_crop}%"))
    if issue_type:
        query = query.filter(PestDiseaseHistory.issue_type.ilike(issue_type))
    if status_filter:
        query = query.filter(PestDiseaseHistory.status.ilike(status_filter))

    total = query.count()
    records = query.order_by(PestDiseaseHistory.detected_at.desc(), PestDiseaseHistory.id.desc()).offset(offset).limit(limit).all()

    res_records = []
    for r in records:
        res_obj = PestDiseaseResponse.model_validate(r)
        res_obj.crop_name = r.crop_type
        res_obj.description = r.symptoms_description
        res_obj.treatment = r.recommended_treatment
        res_records.append(res_obj)

    if "/v1" not in request.url.path:
        return res_records

    return PestDiseaseListResponse(total=total, records=res_records)


@router.post("", response_model=PestDiseaseResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PestDiseaseResponse, status_code=status.HTTP_201_CREATED)
def create_pest_disease_record(
    record_in: PestDiseaseCreate,
    db: Session = Depends(get_db),
):
    record_data = record_in.model_dump()
    now = datetime.now(timezone.utc)

    record_data["crop_type"] = record_in.get_crop_type()
    record_data["symptoms_description"] = record_in.get_symptoms()
    record_data["recommended_treatment"] = record_in.get_treatment()

    if record_data.get("detected_at") is None:
        record_data["detected_at"] = now
    record_data["created_at"] = now

    valid_keys = {c.name for c in PestDiseaseHistory.__table__.columns}
    filtered_data = {k: v for k, v in record_data.items() if k in valid_keys}

    db_record = PestDiseaseHistory(**filtered_data)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    res_obj = PestDiseaseResponse.model_validate(db_record)
    res_obj.crop_name = db_record.crop_type
    res_obj.description = db_record.symptoms_description
    res_obj.treatment = db_record.recommended_treatment
    return res_obj


@router.get("/{record_id}", response_model=PestDiseaseResponse)
def get_pest_disease_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    record = db.query(PestDiseaseHistory).filter(PestDiseaseHistory.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pest/disease record with ID {record_id} not found",
        )
    res_obj = PestDiseaseResponse.model_validate(record)
    res_obj.crop_name = record.crop_type
    res_obj.description = record.symptoms_description
    res_obj.treatment = record.recommended_treatment
    return res_obj


@router.patch("/{record_id}", response_model=PestDiseaseResponse)
def update_pest_disease_record(
    record_id: int,
    record_in: PestDiseaseUpdate,
    db: Session = Depends(get_db),
):
    record = db.query(PestDiseaseHistory).filter(PestDiseaseHistory.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pest/disease record with ID {record_id} not found",
        )

    update_data = record_in.model_dump(exclude_unset=True)
    if "crop_name" in update_data and not update_data.get("crop_type"):
        update_data["crop_type"] = update_data["crop_name"]
    if "description" in update_data and not update_data.get("symptoms_description"):
        update_data["symptoms_description"] = update_data["description"]
    if "treatment" in update_data and not update_data.get("recommended_treatment"):
        update_data["recommended_treatment"] = update_data["treatment"]

    valid_keys = {c.name for c in PestDiseaseHistory.__table__.columns}
    for field, value in update_data.items():
        if field in valid_keys:
            setattr(record, field, value)

    db.commit()
    db.refresh(record)
    res_obj = PestDiseaseResponse.model_validate(record)
    res_obj.crop_name = record.crop_type
    res_obj.description = record.symptoms_description
    res_obj.treatment = record.recommended_treatment
    return res_obj
