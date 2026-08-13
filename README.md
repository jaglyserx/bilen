# Bilen & Jag product catalogue

A searchable automotive-parts catalogue and order-flow CRM built with PostgreSQL, FastAPI, and React/Vite.

## Quick start with Docker

Requirements: Docker with Compose and `curl`.

```bash
cp .env.example .env
docker compose up -d db api
mkdir -p data
curl -L 'https://docs.google.com/spreadsheets/d/1xwqu0iQk-aS8ssIBvr6b8tRaTlgKdce2qYli-AU0Sgo/export?format=csv&gid=462267230' -o data/catalogue.csv
docker compose run --rm api uv run --no-sync python -m app.importers.catalogue /data/catalogue.csv
docker compose up -d frontend
```

The API is available at <http://localhost:8000/docs> and the catalogue at <http://localhost:5173>. The local `data` directory is mounted read-only into the API container.

## Local development

Start PostgreSQL:

```bash
cp .env.example .env
docker compose up -d db
```

Backend (requires [uv](https://docs.astral.sh/uv/)):

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Frontend, in another terminal:

```bash
cd frontend
npm install
npm run dev
```

## Importing the catalogue

Download the selected sheet as CSV and run the importer:

```bash
mkdir -p data
curl -L 'https://docs.google.com/spreadsheets/d/1xwqu0iQk-aS8ssIBvr6b8tRaTlgKdce2qYli-AU0Sgo/export?format=csv&gid=462267230' -o data/catalogue.csv
cd backend
uv run python -m app.importers.catalogue ../data/catalogue.csv
```

The importer is idempotent using normalized manufacturer and article number as product identity. It retains every source row in `import_rows`, records missing identifiers as warnings, converts Swedish decimal values, interprets `UTGÅTT` as discontinued, and separates repeated vehicle fitments from products.

It can also download the configured Google Sheet directly, which is useful for containerized deployments:

```bash
cd backend
uv run python -m app.importers.catalogue --sheet
```

Known limitation: vehicle labels in the source are free text. Makes and year ranges are extracted conservatively while the original label is always preserved. They should be curated through the future admin interface before driving strict ecommerce compatibility rules.

## API

- `GET /api/v1/products` — search, filter, sort, and paginate
- `GET /api/v1/products/{id}` — product details and fitments
- `GET /api/v1/filters` — available catalogue filters
- `GET /api/v1/health` — database health
- `GET /api/v1/orders` — search, filter, and paginate orders
- `GET /api/v1/orders/summary` — workflow totals and unmatched-item count
- `GET /api/v1/orders/{id}` — order, customer, and explicitly linked product lines
- `GET /api/v1/workshops` — search and paginate collaborating workshops
- `GET /api/v1/workshops/{id}` — workshop contact and operational details

## Importing orders

Apply migrations after deploying the version that introduces the order flow, then import the current workbook tab:

```bash
cd backend
uv run alembic upgrade head
uv run python -m app.importers.orders --download --sheet 2024
```

Or run `make import-orders`. The import is idempotent by source and external order number. Product links are resolved only through exact, unique values in `product_identifiers`; names are never searched or regex-matched. The migration safely backfills globally unique catalogue article numbers. Missing or ambiguous article numbers remain unlinked and are surfaced in the order UI for later mapping.

## Importing workshops

Import the `Våra Verkstäder` tab from the local `lager.xlsx` workbook:

```bash
make migrate
make import-workshops
```

The import is idempotent by workbook tab and source row. Workshops are available at `/workshops` after importing.

The backend container image includes the workbook at `/imports/lager.xlsx`, so a
deployed Kubernetes API pod can import it without copying files into the pod:

```bash
kubectl exec -n bilen deployment/api -- \
  uv run --no-sync python -m app.importers.workshops /imports/lager.xlsx
```

Example:

```text
/api/v1/products?q=alfa+147&manufacturer=steinhof&sort=article_number&page=1&page_size=24
```

## Quality checks

```bash
make test
make lint
make typecheck
cd frontend && npm run build
```

Run every backend and frontend quality gate with:

```bash
make check
```

The backend uses Ruff for linting and formatting and ty for static type checking. Both tools are pinned in `uv.lock` and run through `uv`, so contributors use the same versions.

## Commit hooks

[prek](https://prek.j178.dev/) runs repository hygiene checks, Ruff, and ty before each commit. Install the Git hook once after cloning:

```bash
make hooks
```

Run the complete hook suite manually against the repository with:

```bash
cd backend
uv run prek run --all-files
```

Hooks intentionally check formatting without rewriting staged files. Apply fixes explicitly with `cd backend && uv run ruff format .` and stage the result before committing.

## Production notes

- Change all database credentials and restrict CORS.
- Terminate TLS at a reverse proxy or managed platform.
- Run Alembic migrations as a release step.
- Back up PostgreSQL and test restores.
- Add authentication before implementing product writes or import uploads.
- Store future product images in object storage rather than PostgreSQL.

## CI and container images

GitHub Actions runs backend and frontend quality checks and builds both Docker images for pull requests. Pushes to `main`, version tags such as `v1.0.0`, and manually dispatched runs publish to GitHub Container Registry:

```text
ghcr.io/jaglyserx/bilen-backend
ghcr.io/jaglyserx/bilen-frontend
```

Published images receive `latest`, branch, semantic-version, and immutable `sha-…` tags as applicable. Deploy using a version or SHA tag rather than `latest` when reproducibility matters.

The frontend defaults to the same-origin `/api/v1` endpoint. Nginx proxies that path to the API in local Docker, while Kubernetes routes it directly at the ingress. This makes one frontend image portable across environments. Set the optional GitHub repository variable `VITE_API_URL` only when the API intentionally lives on a different origin.

No registry secret is required: the workflow publishes with GitHub's scoped `GITHUB_TOKEN`. If the packages should be publicly pullable, change their visibility in the repository owner's **Packages** settings after the first publication.
