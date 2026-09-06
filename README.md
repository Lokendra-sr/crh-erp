# Canteen/Catering ERP — Phase 1 Backend

FastAPI + SQLAlchemy + SQLite (swap to PostgreSQL later with zero code changes).

## What's included

- `app/models.py` — all 16 Phase 1 tables (admins, clients, vendors, meal_types,
  client_meal_rates, items, meal_entries, purchases, purchase_items,
  inventory_transactions, expense_categories, expenses, invoices,
  invoice_items, client_payments, vendor_payments), with PKs, FKs, indexes,
  unique/check constraints, and ORM relationships.
- `app/database.py` — engine/session setup. Reads `DATABASE_URL` from the
  environment; defaults to a local `erp.db` SQLite file.
- `app/auth.py` — bcrypt password hashing + JWT issuing/validation.
- `app/schemas.py` — Pydantic request/response models for auth, clients,
  vendors, items (the other modules follow the same pattern as you build them
  out).
- `app/routers/auth.py` — `/auth/bootstrap` (create the first admin),
  `/auth/login`, `/auth/me`.
- `app/routers/clients.py`, `vendors.py`, `items.py` — full CRUD, each
  protected by admin JWT auth. Deletes are soft (`is_active = false`) since
  clients/vendors/items are referenced by historical records.
- `app/main.py` — wires everything together and auto-creates tables on
  startup (fine for Phase 1; switch to Alembic migrations once the schema is
  stable and you have real data you can't afford to lose).

## Design notes carried over from the schema discussion

- No duplicate income/expense master tables — income flows from
  `invoices`/`client_payments`, expenses flow from `purchases`/
  `vendor_payments`/`expenses`.
- `client_meal_rates` is versioned with `effective_from`/`effective_to` so
  rate changes never rewrite history.
- `meal_entries.rate` and `.amount` are a snapshot taken at entry time, so a
  later rate change never alters a historical entry.
- Stock is derived from summing `inventory_transactions` rather than a mutable
  `current_stock` column, so every stock movement is auditable. See
  `GET /items/{id}/current-stock`.
- `expense_categories` is a lookup table (not a hardcoded enum) so categories
  can be managed from the admin panel without a schema change — same
  philosophy as `meal_types`.

## Setup

```bash
cd erp_backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be live at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

## First-time use

1. Create the first admin (only works once — the route locks itself after):
   ```bash
   curl -X POST http://localhost:8000/auth/bootstrap \
     -H "Content-Type: application/json" \
     -d '{"name": "Owner", "email": "owner@example.com", "password": "changeme123"}'
   ```
2. Log in to get a token:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -F "username=owner@example.com" -F "password=changeme123"
   ```
3. Use the returned `access_token` as a Bearer token for every other request
   (the `/docs` page has an "Authorize" button that does this for you).

## Switching to PostgreSQL later

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/erp_db"
pip install psycopg2-binary
```
No other code changes are needed — `app/database.py` reads this automatically.

## Next steps (not yet built)

- `meal_types` / `client_meal_rates` / `meal_entries` routers (daily meal
  logging + rate history)
- `items` → `purchases` / `purchase_items` → auto-generated
  `inventory_transactions` on purchase confirmation
- `expense_categories` / `expenses` routers
- `invoices` / `invoice_items` generation from a date range of `meal_entries`
- `client_payments` / `vendor_payments` routers, plus outstanding-balance
  reports for clients and vendors
- Alembic migrations once you move past the prototyping stage
