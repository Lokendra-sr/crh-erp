from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_admin
from ..database import get_db

router = APIRouter(prefix="/items", tags=["items"], dependencies=[Depends(get_current_admin)])


@router.post("", response_model=schemas.ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    if db.query(models.Item).filter(models.Item.item_code == payload.item_code).first():
        raise HTTPException(status_code=400, detail="item_code already exists")
    item = models.Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=List[schemas.ItemOut])
def list_items(
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search by item name or item_code"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Item)
    if is_active is not None:
        query = query.filter(models.Item.is_active == is_active)
    if category:
        query = query.filter(models.Item.category == category)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Item.item_name.ilike(like)) | (models.Item.item_code.ilike(like))
        )
    return query.order_by(models.Item.item_name).all()


@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/{item_id}/current-stock")
def get_current_stock(item_id: int, db: Session = Depends(get_db)):
    """Sum of all inventory_transactions for this item = current stock on hand."""
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    from sqlalchemy import func

    total = (
        db.query(func.coalesce(func.sum(models.InventoryTransaction.quantity), 0))
        .filter(models.InventoryTransaction.item_id == item_id)
        .scalar()
    )
    return {
        "item_id": item_id,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "unit": item.unit,
        "current_stock": float(total),
        "minimum_stock": float(item.minimum_stock),
        "below_minimum": float(total) < float(item.minimum_stock),
    }


@router.patch("/{item_id}", response_model=schemas.ItemOut)
def update_item(item_id: int, payload: schemas.ItemUpdate, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.is_active = False
    db.commit()
    return None
