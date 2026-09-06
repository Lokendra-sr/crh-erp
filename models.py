import enum
from datetime import datetime, date

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


# ---------------------------------------------------------------------------
# Enums (stored as plain VARCHAR + CHECK constraint via native_enum=False, so
# these behave identically on SQLite and on Postgres later)
# ---------------------------------------------------------------------------

class PaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    UPI = "UPI"
    CHEQUE = "CHEQUE"
    OTHER = "OTHER"


class InventoryTransactionType(str, enum.Enum):
    OPENING = "OPENING"
    PURCHASE = "PURCHASE"
    CONSUMPTION = "CONSUMPTION"
    WASTAGE = "WASTAGE"
    ADJUSTMENT = "ADJUSTMENT"


class InventoryReferenceType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    MEAL_ENTRY = "MEAL_ENTRY"
    MANUAL = "MANUAL"


def _enum(py_enum, **kw):
    """Helper: store enums as plain strings (portable across SQLite/Postgres)."""
    return SAEnum(py_enum, native_enum=False, validate_strings=True, **kw)


TIMESTAMP_KW = dict(server_default=func.now())


# ---------------------------------------------------------------------------
# 1. admins
# ---------------------------------------------------------------------------

class Admin(Base):
    __tablename__ = "admins"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# 2. clients
# ---------------------------------------------------------------------------

class Client(Base):
    __tablename__ = "clients"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_code = Column(String(20), nullable=False, unique=True, index=True)
    company_name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(150))
    address = Column(Text)
    gst_number = Column(String(20))
    payment_terms_days = Column(Integer, default=30, server_default="30")
    contract_start_date = Column(Date)
    contract_end_date = Column(Date)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    meal_rates = relationship("ClientMealRate", back_populates="client", cascade="all, delete-orphan")
    meal_entries = relationship("MealEntry", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")
    payments = relationship("ClientPayment", back_populates="client")


# ---------------------------------------------------------------------------
# 3. vendors
# ---------------------------------------------------------------------------

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vendor_code = Column(String(20), nullable=False, unique=True, index=True)
    vendor_name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(150))
    address = Column(Text)
    gst_number = Column(String(20))
    category = Column(String(100))
    payment_terms_days = Column(Integer, default=0, server_default="0")
    opening_balance = Column(Numeric(12, 2), default=0, server_default="0")
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    purchases = relationship("Purchase", back_populates="vendor")
    payments = relationship("VendorPayment", back_populates="vendor")
    expenses = relationship("Expense", back_populates="vendor")


# ---------------------------------------------------------------------------
# 4. meal_types
# ---------------------------------------------------------------------------

class MealType(Base):
    __tablename__ = "meal_types"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")

    client_rates = relationship("ClientMealRate", back_populates="meal_type")
    meal_entries = relationship("MealEntry", back_populates="meal_type")
    invoice_items = relationship("InvoiceItem", back_populates="meal_type")


# ---------------------------------------------------------------------------
# 5. client_meal_rates
# ---------------------------------------------------------------------------

class ClientMealRate(Base):
    __tablename__ = "client_meal_rates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(BigInteger, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    meal_type_id = Column(BigInteger, ForeignKey("meal_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    rate = Column(Numeric(10, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)

    client = relationship("Client", back_populates="meal_rates")
    meal_type = relationship("MealType", back_populates="client_rates")

    __table_args__ = (
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_client_meal_rate_date_range",
        ),
        Index("ix_client_meal_rate_lookup", "client_id", "meal_type_id", "effective_from"),
    )


# ---------------------------------------------------------------------------
# 6. items
# ---------------------------------------------------------------------------

class Item(Base):
    __tablename__ = "items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_code = Column(String(30), nullable=False, unique=True, index=True)
    item_name = Column(String(150), nullable=False)
    category = Column(String(100))
    unit = Column(String(20), nullable=False)
    minimum_stock = Column(Numeric(12, 3), default=0, server_default="0")
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    purchase_items = relationship("PurchaseItem", back_populates="item")
    inventory_transactions = relationship("InventoryTransaction", back_populates="item")


# ---------------------------------------------------------------------------
# 7. meal_entries
# ---------------------------------------------------------------------------

class MealEntry(Base):
    __tablename__ = "meal_entries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entry_date = Column(Date, nullable=False, index=True)
    client_id = Column(BigInteger, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)
    meal_type_id = Column(BigInteger, ForeignKey("meal_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    planned_quantity = Column(Integer, nullable=False, default=0, server_default="0")
    actual_quantity = Column(Integer, nullable=False, default=0, server_default="0")
    # Snapshot of the rate at the time the meal was served -- intentionally
    # duplicated from client_meal_rates so historical entries never change
    # when rates change later.
    rate = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    notes = Column(Text)
    created_by = Column(BigInteger, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    client = relationship("Client", back_populates="meal_entries")
    meal_type = relationship("MealType", back_populates="meal_entries")
    created_by_admin = relationship("Admin")

    __table_args__ = (
        UniqueConstraint("entry_date", "client_id", "meal_type_id", name="uq_meal_entry_per_day"),
        CheckConstraint("actual_quantity >= 0 AND planned_quantity >= 0", name="ck_meal_entry_qty_non_negative"),
    )


# ---------------------------------------------------------------------------
# 8. purchases
# ---------------------------------------------------------------------------

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    purchase_number = Column(String(30), nullable=False, unique=True, index=True)
    vendor_id = Column(BigInteger, ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_date = Column(Date, nullable=False, index=True)
    invoice_number = Column(String(100))
    subtotal = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    total_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    payment_status = Column(_enum(PaymentStatus), nullable=False, default=PaymentStatus.UNPAID,
                             server_default=PaymentStatus.UNPAID.value)
    notes = Column(Text)
    created_by = Column(BigInteger, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    vendor = relationship("Vendor", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    payments = relationship("VendorPayment", back_populates="purchase")
    created_by_admin = relationship("Admin")


# ---------------------------------------------------------------------------
# 9. purchase_items
# ---------------------------------------------------------------------------

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    purchase_id = Column(BigInteger, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(BigInteger, ForeignKey("items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit = Column(String(20), nullable=False)
    rate = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    total_amount = Column(Numeric(12, 2), nullable=False)

    purchase = relationship("Purchase", back_populates="items")
    item = relationship("Item", back_populates="purchase_items")


# ---------------------------------------------------------------------------
# 10. inventory_transactions
# ---------------------------------------------------------------------------

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_id = Column(BigInteger, ForeignKey("items.id", ondelete="RESTRICT"), nullable=False, index=True)
    transaction_type = Column(_enum(InventoryTransactionType), nullable=False)
    # Positive quantity for inflows (OPENING, PURCHASE, positive ADJUSTMENT),
    # negative quantity for outflows (CONSUMPTION, WASTAGE, negative ADJUSTMENT).
    quantity = Column(Numeric(12, 3), nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    reference_type = Column(_enum(InventoryReferenceType), nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    notes = Column(Text)
    created_by = Column(BigInteger, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)

    item = relationship("Item", back_populates="inventory_transactions")
    created_by_admin = relationship("Admin")

    __table_args__ = (
        Index("ix_inventory_txn_item_date", "item_id", "transaction_date"),
    )


# ---------------------------------------------------------------------------
# 11. expense_categories
# ---------------------------------------------------------------------------

class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")

    expenses = relationship("Expense", back_populates="category")


# ---------------------------------------------------------------------------
# 12. expenses
# ---------------------------------------------------------------------------

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    expense_date = Column(Date, nullable=False, index=True)
    category_id = Column(BigInteger, ForeignKey("expense_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    description = Column(Text)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(_enum(PaymentMethod), nullable=False, default=PaymentMethod.CASH,
                             server_default=PaymentMethod.CASH.value)
    reference_number = Column(String(100))
    vendor_id = Column(BigInteger, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text)
    created_by = Column(BigInteger, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)

    category = relationship("ExpenseCategory", back_populates="expenses")
    vendor = relationship("Vendor", back_populates="expenses")
    created_by_admin = relationship("Admin")


# ---------------------------------------------------------------------------
# 13. invoices
# ---------------------------------------------------------------------------

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    client_id = Column(BigInteger, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    total_amount = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    due_date = Column(Date)
    status = Column(_enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT,
                     server_default=InvoiceStatus.DRAFT.value)
    notes = Column(Text)
    created_by = Column(BigInteger, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)

    client = relationship("Client", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("ClientPayment", back_populates="invoice")
    created_by_admin = relationship("Admin")

    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="ck_invoice_period_range"),
    )


# ---------------------------------------------------------------------------
# 14. invoice_items
# ---------------------------------------------------------------------------

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(BigInteger, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    meal_type_id = Column(BigInteger, ForeignKey("meal_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    rate = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    meal_type = relationship("MealType", back_populates="invoice_items")


# ---------------------------------------------------------------------------
# 15. client_payments
# ---------------------------------------------------------------------------

class ClientPayment(Base):
    __tablename__ = "client_payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(BigInteger, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_id = Column(BigInteger, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(_enum(PaymentMethod), nullable=False, default=PaymentMethod.BANK_TRANSFER,
                             server_default=PaymentMethod.BANK_TRANSFER.value)
    reference_number = Column(String(100))
    notes = Column(Text)
    created_by = Column(BigInteger, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)

    client = relationship("Client", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")
    created_by_admin = relationship("Admin")


# ---------------------------------------------------------------------------
# 16. vendor_payments
# ---------------------------------------------------------------------------

class VendorPayment(Base):
    __tablename__ = "vendor_payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vendor_id = Column(BigInteger, ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_id = Column(BigInteger, ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(_enum(PaymentMethod), nullable=False, default=PaymentMethod.BANK_TRANSFER,
                             server_default=PaymentMethod.BANK_TRANSFER.value)
    reference_number = Column(String(100))
    notes = Column(Text)
    created_by = Column(BigInteger, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, **TIMESTAMP_KW)

    vendor = relationship("Vendor", back_populates="payments")
    purchase = relationship("Purchase", back_populates="payments")
    created_by_admin = relationship("Admin")
