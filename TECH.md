# Technology Stack

## Runtime

- Backend: Python/Django.
- Python dependency manager: Poetry, with `requirements.txt` exported for Docker/Render installs.
- Declared Poetry runtime: Python `^3.13`.
- Docker Python image: `python:3.13`.
- Render config currently sets `PYTHON_VERSION` to `3.11.6`; verify deployment behavior before assuming parity with Docker.
- Frontend runtime/build: Node, npm, webpack, Tailwind CSS, PostCSS, Sass.
- `.nvmrc` is legacy `lts/gallium`; Dockerfiles use Node 16 for production asset builds and local Compose uses Node 18 for the frontend service. Do not update this casually.

## Backend

- Django 5 application package: `cleanapp`.
- Main app: `core`.
- Authentication: Django Allauth with username/email login and optional GitHub social login.
- API: Django Ninja mounted at `/api/`, with session auth for app users and API-key auth for selected admin/superuser surfaces.
- Background jobs: Django Q2 backed by Redis.
- Database: PostgreSQL in local Docker and deployment configs.
- Cache/queue: Redis.
- Static files: webpack build output plus WhiteNoise `CompressedManifestStaticFilesStorage`.
- Media storage: local filesystem by default, S3-compatible storage when `AWS_S3_ENDPOINT_URL` is set. Local Compose includes MinIO.
- Email: console backend fallback, MailHog in local Docker, Mailgun through Anymail when configured.
- MJML: `django-mjml` with a local MJML service in Docker Compose.

## Product Integrations

- Stripe: Checkout, Billing Portal, subscription webhooks, plan/site limits, and billing state transitions.
- PostHog: optional product analytics and aliasing.
- Plausible: public page analytics script in the base template.
- Buttondown: optional newsletter/subscriber integration.
- Sentry: optional error reporting.
- Logfire: optional observability processor.
- BeautifulSoup/requests: page metadata extraction for email digests.

Treat all integrations as optional unless a setting requires them. Missing optional keys should degrade gracefully.

## API And Agent Surfaces

- Existing API: Django Ninja mounted at `/api/`. Today it mainly supports authenticated UI-adjacent actions.
- Future public API: should expose stable, documented primitives for sites/sitemaps, pages, review queues, page selection, review state, notes, and account limits.
- Future MCP server: should wrap the same domain services as the API, not duplicate business logic. Treat MCP tools as a first-class product surface for AI agents.
- Future automation support: should be usable from agents, n8n, Zapier, scripts, and scheduled jobs through explicit auth and predictable JSON contracts.

When building API or MCP features:

- Keep auth account-scoped through `Profile` and explicit API keys/scopes.
- Use stable object IDs and clear ownership checks.
- Prefer cursor or deterministic pagination for page lists.
- Make page selection operations explicit: next due, random, by site, by client, by status, and by cadence window.
- Make write operations idempotent where practical, especially marking a page reviewed or skipped.
- Return structured errors that agents can recover from.
- Log agent/API actions with enough context for audit without leaking secrets.
- Put shared business logic in `core` services/modules so UI, API, tasks, and MCP tools call the same behavior.

## Frontend

- Django templates are the primary UI layer.
- Tailwind CSS utilities and project `pf-*` component classes live in `frontend/src/styles/index.css`.
- Stimulus is used for client-side behavior. Controllers live in `frontend/src/controllers/` and are auto-loaded by `frontend/src/application/index.js`.
- Third-party Stimulus components currently include dropdown and reveal controllers.
- Webpack config lives in `frontend/webpack/`.
- Built frontend assets are emitted to `frontend/build/` and consumed by `webpack_loader`.

## Testing And Quality

- Test framework: pytest plus `pytest-django`.
- Test settings module: `cleanapp.settings`.
- Run tests through Docker with `make test`, not host `pytest`.
- Focused tests can be passed after `make test`, for example `make test core/tests/test_billing.py`.
- Formatting/linting:
  - Ruff check/format for Python.
  - djlint with Django profile for templates.
  - Pre-commit hooks include YAML checks, trailing whitespace, EOF fixer, Ruff, djlint, and requirements export.
- Ruff line length: 100.
- Ruff lint families include pycodestyle, pyflakes, bugbear, isort, Django rules, pyupgrade, and mccabe.

## Development Commands

- `make serve`: build/start local Docker Compose stack and follow backend logs.
- `make shell`: open Django shell_plus in the backend container.
- `make manage <command>`: run a Django management command in the backend container.
- `make makemigrations`: generate Django migrations in Docker.
- `make migrate`: apply migrations in Docker.
- `make test`: run pytest in Docker.
- `make restart-worker`: recreate the Django Q worker container.
- `npm run start`: webpack dev server.
- `npm run watch`: webpack watch build.
- `npm run build`: production asset build.

## Environment

The canonical local starting point is `.env.example`. Important settings include:

- `ENVIRONMENT`, `DEBUG`, `SECRET_KEY`, `SITE_URL`
- Postgres: `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PORT`, `POSTGRES_PASSWORD`
- Redis: `REDIS_HOST`, `REDIS_PASSWORD`, `REDIS_PORT`, `REDIS_DB`
- Email: `MAILGUN_API_KEY`, `MAILGUN_SENDER_DOMAIN`, `DEFAULT_FROM_EMAIL`
- Billing: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_*`
- Optional services: GitHub OAuth, Buttondown, PostHog, Sentry, Logfire, S3/MinIO

Do not require optional services for local tests unless the feature specifically depends on them.

## Technical Constraints

- Keep Django routes compatible. Several public routes intentionally omit trailing slashes, while utility/review routes include them.
- Keep generated frontend assets out of source changes unless the task explicitly needs build output.
- Avoid new infrastructure for small features. Use Django, Django Q, Redis, Postgres, Tailwind, and Stimulus before introducing another service.
- Do not add AI framework usage just because `pydantic-ai` is installed. Any AI feature needs a product reason, cost/failure handling, and tests around fallback behavior.
- Do not make MCP tools scrape templates, parse email text, or bypass domain permissions. They should call shared review-queue and sitemap/page services.
