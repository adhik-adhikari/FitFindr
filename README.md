# FitFindr

FitFindr is being built incrementally. This repository currently contains the Milestone 0 walking skeleton: a Next.js frontend and a FastAPI backend connected through a public health endpoint. Wardrobe and recommendation features are not implemented yet.

## Requirements

- Node.js 22 and npm
- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)

## Local setup

In one terminal:

```sh
cd backend
uv sync --locked --dev
cp .env.example .env
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
uv run pytest
```

`frontend/package-lock.json` and `backend/uv.lock` lock the dependency versions. CI uses `npm ci` and `uv sync --locked --dev` to reproduce them.

## Repository structure and decisions

- `frontend/` — Next.js and TypeScript browser UI.
- `backend/` — FastAPI application and deterministic tests.
- `docs/product.md` — source of truth for product behavior and scope.
- `docs/architecture.md` — source of truth for system boundaries and technology choices.
- `docs/data-model.md` — source of truth for persistence design when persistence is implemented.
- `.github/workflows/ci.yml` — frontend and backend validation.

The documents describe the intended MVP. Their later features are not part of this milestone.
