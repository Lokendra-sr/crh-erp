from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_admin
from ..database import get_db

router = APIRouter(prefix="/clients", tags=["clients"], dependencies=[Depends(get_current_admin)])


@router.post("", response_model=schemas.ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    if db.query(models.Client).filter(models.Client.client_code == payload.client_code).first():
        raise HTTPException(status_code=400, detail="client_code already exists")
    client = models.Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=List[schemas.ClientOut])
def list_clients(
    is_active: Optional[bool] = None,
    search: Optional[str] = Query(None, description="Search by company name or client_code"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Client)
    if is_active is not None:
        query = query.filter(models.Client.is_active == is_active)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (models.Client.company_name.ilike(like)) | (models.Client.client_code.ilike(like))
        )
    return query.order_by(models.Client.company_name).all()


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=schemas.ClientOut)
def update_client(client_id: int, payload: schemas.ClientUpdate, db: Session = Depends(get_db)):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_client(client_id: int, db: Session = Depends(get_db)):
    """Soft delete: we never hard-delete a client since it may be referenced
    by historical invoices and meal entries."""
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.is_active = False
    db.commit()
    return None
