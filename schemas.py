from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

class ClientBase(BaseModel):
    client_code: str
    company_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    payment_terms_days: Optional[int] = 30
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    is_active: Optional[bool] = True


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    payment_terms_days: Optional[int] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    is_active: Optional[bool] = None


class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------

class VendorBase(BaseModel):
    vendor_code: str
    vendor_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    category: Optional[str] = None
    payment_terms_days: Optional[int] = 0
    opening_balance: Optional[float] = 0
    is_active: Optional[bool] = True


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    category: Optional[str] = None
    payment_terms_days: Optional[int] = None
    opening_balance: Optional[float] = None
    is_active: Optional[bool] = None


class VendorOut(VendorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

class ItemBase(BaseModel):
    item_code: str
    item_name: str
    category: Optional[str] = None
    unit: str
    minimum_stock: Optional[float] = 0
    is_active: Optional[bool] = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    minimum_stock: Optional[float] = None
    is_active: Optional[bool] = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
