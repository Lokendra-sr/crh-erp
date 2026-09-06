from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_admin
from ..database import get_db

router = APIRouter(prefix="/vendors", tags=["vendors"], dependencies=[Depends(get_current_admin)])


@router.post("", response_model=schemas.VendorOut, status_code=status.HTTP_201_CREATED)
def create_vendor(payload: schemas.VendorCreate, db: Session = Depends(get_db)):
    if db.query(models.Vendor).filter(models.Vendor.vendor_code == payload.vendor_code).first():
        raise HTTPException(status_code=400, detail="vendor_code already exists")
    vendor = models.Vendor(**payload.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("", response_model=List[schemas.VendorOut])
def list_vendors(
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by vendor name or vendor_code"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Vendor)
    if is_active is not None:
        query = query.filter(models.Vendor.is_active == is_active)
    if category:
        query = query.filter(models.Vendor.category == category)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Vendor.vendor_name.ilike(like)) | (models.Vendor.vendor_code.ilike(like))
        )
    return query.order_by(models.Vendor.vendor_name).all()


@router.get("/{vendor_id}", response_model=schemas.VendorOut)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.get(models.Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.patch("/{vendor_id}", response_model=schemas.VendorOut)
def update_vendor(vendor_id: int, payload: schemas.VendorUpdate, db: Session = Depends(get_db)):
    vendor = db.get(models.Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vendor, field, value)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.get(models.Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.is_active = False
    db.commit()
    return None
