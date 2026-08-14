# Fridge Refill

Fridge Refill is an iPhone-first retail replenishment PWA. Employees select an assigned store, check each fridge, enter required units, collect one aggregated back-store pick list, record shortages, and refill each destination fridge. Django and PostgreSQL remain the source of truth; pending quantity updates are queued in the browser only during network loss.

## Requirements

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (or Docker)
- A modern browser; Safari on iOS 16.4+ is recommended for installation and camera capabilities

## Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

SQLite is used only when `DATABASE_URL` is absent, making a quick local smoke test possible. Configure PostgreSQL for shared development and all deployments.

## PostgreSQL setup

Create a database and user, then set a URL such as:

```text
DATABASE_URL=postgresql://fridge:strong-password@localhost:5432/fridge_refill
```

Run `python manage.py migrate` after every deployment. Migration `core/0001_initial.py` creates all production tables, indexes, foreign keys, and uniqueness constraints.

## Frontend setup

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000/api npm run dev
```

For the Vite dev server, the explicit API URL is required. Docker's nginx proxies `/api` and `/media` automatically.

## Environment variables

Copy `.env.example` to `.env`. Replace `DJANGO_SECRET_KEY` and database credentials. Set `DJANGO_DEBUG=False`, HTTPS origins in `CORS_ALLOWED_ORIGINS`, and the deployed hostname in `ALLOWED_HOSTS` for production. `MEDIA_STORAGE=local` is supported now; Django `ImageField` paths allow a later S3/R2 storage backend without schema changes.

## Demo data and accounts

`python manage.py seed_demo` safely creates Romford and Ilford, two fridges per store, five sample products, assignments, and these repeatable local accounts:

- Admin: `admin` / `AdminDemo123!`
- Employee: `employee` / `EmployeeDemo123!`

Change these passwords outside local development. Create another administrator with `python manage.py createsuperuser`.

## Running tests

```bash
cd backend && python manage.py test
cd frontend && npm test
cd frontend && npm run build
```

Backend coverage includes assigned-store isolation, optimistic concurrency, and the critical `4 + 6 = 10` pick aggregation while retaining both fridge quantities.

## API

JWT authentication is at `/api/auth/token/` and `/api/auth/refresh/`. Authenticated resources include `/api/stores/`, `/api/fridges/`, `/api/products/`, `/api/fridge-products/`, `/api/refill-sessions/`, `/api/fridge-checks/`, `/api/requirements/`, `/api/shortages/`, and `/api/history/`. Useful nested/actions include:

- `GET /api/stores/{id}/fridges/`
- `GET /api/fridges/{id}/products/`
- `GET /api/refill-sessions/{id}/pick-list/`
- `POST /api/refill-sessions/{id}/generate_pick_list/`
- `POST /api/refill-sessions/{id}/start_refilling/`
- `POST /api/refill-sessions/{id}/complete/`

Server-side querysets restrict employees and managers to assigned stores. Quantity writes use a `version` field and return HTTP 409 for stale edits.

## Frontend routes

`/login`, `/stores`, `/fridges`, `/fridges/:id`, `/pick-list`, `/refill`, and `/history`. Login always leads to mandatory store selection. Change Store clears active store/session UI state so stores cannot be mixed.

## Docker and production deployment

```bash
cp .env.example .env
# edit secrets in .env
docker compose up --build
docker compose exec backend python manage.py seed_demo
```

The containers run PostgreSQL 17, Gunicorn with three workers, and nginx serving the built PWA. In production, terminate TLS at a reverse proxy/load balancer, use a managed PostgreSQL database, persist or replace media storage, restrict CORS/hosts, rotate secrets, and add database backups and monitoring.

## Installing on iPhone

Open the HTTPS application URL in Safari, tap **Share**, then **Add to Home Screen**. Launch the new Fridge Refill icon. The manifest, standalone mode, Apple touch icon, service worker, safe-area padding, offline fallback, and update prompt are included. Barcode entry is supported through API/search fields; native camera barcode decoding depends on browser support and is a documented enhancement point.

## Administration

Django Admin at `/admin/` supports stores, users, employee-store access, fridges, products, ordered fridge assignments, sessions, requirements, and shortages. Uploaded images are validated to image MIME types and a maximum of 5 MB at the API layer. The React app focuses on the complete employee workflow; richer React CRUD screens, client-side image resizing, drag ordering, and a camera barcode overlay are the principal remaining UI enhancements.
