# FitFindr

FitFindr is being built incrementally. The repository contains the Milestone 0 walking skeleton and the Milestone 1A PostgreSQL persistence foundation. Wardrobe API behavior and recommendation features are not implemented yet.

## Requirements

- Node.js 22 and npm
- Python 3.11 or newer
- PostgreSQL 14 or newer for isolated migration tests
- [uv](https://docs.astral.sh/uv/)

## Local setup

In one terminal:

```sh
cd backend
uv sync --locked --dev
cp .env.example .env
```

Set `DATABASE_URL` in `backend/.env` to the development Supabase project's shared session-pooler URL. The real development migration depends on Supabase-managed `auth.users`, `anon`, and `authenticated`; an arbitrary empty local PostgreSQL database is not a supported development migration target. Apply reviewed migrations deliberately:

```sh
cd backend
uv run --env-file .env alembic upgrade head
uv run --env-file .env uvicorn app.main:app --reload
```

In another terminal:

```sh
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Open <http://localhost:3000>. The page makes a browser request to <http://localhost:8000/health> and displays the connection result. `NEXT_PUBLIC_API_URL` sets the browser-visible backend URL. `CORS_ALLOWED_ORIGINS` is a comma-separated list of frontend origins accepted by the backend; set it separately for each environment. Do not include a trailing slash in an origin.

## Validation

```sh
cd frontend
npm run lint
npm run typecheck
npm run build

cd ../backend
uv run ruff check .
FITFINDR_TEST_DATABASE_URL=postgresql:///fitfindr_test \
FITFINDR_ALLOW_DESTRUCTIVE_TEST_DATABASE=fitfindr_test_is_disposable \
uv run pytest
```

Backend migration/integration tests require a local disposable database named exactly `fitfindr_test` plus the explicit destructive-test opt-in shown above. The fixture bootstraps representative provider-managed schemas, `auth.users`, and browser-facing roles, then exercises upgrade/downgrade only in that isolated database. Its guards require a loopback or Unix-socket client target and a disposable superuser connection, and reject replicas, differently named databases, service indirection, and managed endpoints. Never point `FITFINDR_TEST_DATABASE_URL` at development or production data.

## Database access boundary

FastAPI remains the application authorization boundary. The deployed backend database role must have normal table privileges and must either own `public.garments` or have PostgreSQL `BYPASSRLS`, so it can access the table while RLS is enabled without ownership policies. Never use the browser-facing `anon` or `authenticated` roles for the backend connection: their direct table privileges are revoked, and they cannot read or write `public.garments` through the Supabase Data API.

`frontend/package-lock.json` and `backend/uv.lock` lock the dependency versions. CI uses `npm ci` and `uv sync --locked --dev` to reproduce them.

## Repository structure and decisions

- `frontend/` — Next.js and TypeScript browser UI.
- `backend/` — FastAPI application and deterministic tests.
- `backend/alembic/` — reviewed application-schema migrations.
- `docs/product.md` — source of truth for product behavior and scope.
- `docs/architecture.md` — source of truth for system boundaries and technology choices.
- `docs/data-model.md` — source of truth for persistence design when persistence is implemented.
- `.github/workflows/ci.yml` — frontend and backend validation.

The documents describe the intended MVP. Their later features are not part of this milestone.
