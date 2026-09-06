from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import (
    create_access_token,
    get_current_admin,
    hash_password,
    verify_password,
)
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bootstrap", response_model=schemas.AdminOut, status_code=status.HTTP_201_CREATED)
def bootstrap_first_admin(payload: schemas.AdminCreate, db: Session = Depends(get_db)):
    """Create the very first admin account. Disable/remove this route once
    at least one admin exists, or protect it behind an env-var secret."""
    if db.query(models.Admin).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An admin already exists. Use /admins (authenticated) to add more.",
        )
    admin = models.Admin(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.email == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account is inactive")

    token = create_access_token(subject=admin.email)
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.AdminOut)
def read_current_admin(current_admin: models.Admin = Depends(get_current_admin)):
    return current_admin
