# MediStock

MediStock is a pharmacy inventory application for medicine cataloguing, batch expiry, supplier receipts, bin-level stock, FEFO sales, transfers and stock movement history.

## Run with Docker Compose

1. Copy `.env.example` to `.env` and set a private `POSTGRES_PASSWORD`. Set the same password in `DATABASE_URL`.
2. Start the services from this directory:

   ```powershell
   docker compose up --build -d
   docker compose ps
   ```

   PostgreSQL is health-checked before the API starts. The API applies Alembic migrations before serving requests. The named PostgreSQL volume survives container rebuilds and `docker compose down`; do not add `-v` unless you intend to delete the database.

3. Open the application at <http://localhost:5173>. The first visit asks for the pharmacy name. The production Nginx server proxies `/api/` to FastAPI, so the browser uses the same origin.

## Development URLs

- Frontend: <http://localhost:5173>
- API root: <http://localhost:8000>
- API health and PostgreSQL check: <http://localhost:8000/health>
- OpenAPI UI: <http://localhost:8000/docs>

For local frontend development, run `npm ci` and `npm run dev` inside `frontend`. Vite proxies `/api` to `localhost:8000`. Run the backend with `DATABASE_URL` set and `uvicorn app.main:app --reload --port 8000` from `backend` after installing `requirements.txt`.

## Inventory workflow

Create categories, suppliers, medicines and a Block → Rack → Shelf → Bin hierarchy. Receive purchases into a Bin; each receipt creates or updates its medicine batch, location stock and stock transaction in one database transaction. Sales allocate unexpired stock by earliest expiry date. Transfers write paired outbound/inbound movements and preserve the total quantity.

Search is database-side, case-insensitive, paginated and includes medicine name, generic name, manufacturer and batch number. Search results show batch quantities, expiry status and the full location path. PostgreSQL `pg_trgm` GIN indexes support partial matching.

## Verification

Run the integration flow against the running Compose services:

```powershell
docker compose exec backend python -m unittest discover -s tests -p 'test_*.py' -v
```

The test creates isolated pharmacy data and removes it afterward. It verifies a purchase, a cross-bin transfer, partial receipts, search and location resolution, FEFO sales, expired-batch exclusion, low-stock/expiry summaries, audit transactions, validation failures and rollback behavior.

## Data and configuration

`.env` contains local credentials and is ignored by Git and Docker build contexts. `.env.example` is a template only. PostgreSQL data is stored in the `postgres_data` named volume. Database schema changes belong in new Alembic revisions; the initial deployed schema is at revision `20261001_schema`.
