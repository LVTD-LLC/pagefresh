# AGENTS.md

Root instructions for AI coding agents working in this repo.

## Start Here

- Product: PageFresh, scheduled page review reminders for every sitemap.
- Legacy technical name: `cleanapp`. The Django project package, Docker services, Render resources, Redis queue name, and database examples still use it. Do not rename those surfaces unless the user explicitly asks for a coordinated rename.
- Read the relevant steering docs before changing code:
  - `VISION.md` for product direction and non-goals.
  - `PRODUCT.md` for users, workflows, and business constraints.
  - `TECH.md` for stack, commands, and integration details.
  - `STRUCTURE.md` for file ownership and naming conventions.
  - `DESIGN.md` for UI tokens and component guidance.

## Operating Rules

- Inspect code before editing. Read callers, tests, templates, forms, routes, tasks, and settings for the surface you touch.
- Keep changes scoped. Do not bundle unrelated cleanup, migrations, dependency upgrades, formatting sweeps, or renames.
- Prefer existing Django, Tailwind, Stimulus, and project helper patterns over new abstractions.
- Preserve user-owned changes in the worktree. Do not revert or overwrite unrelated edits.
- Never print secrets from `.env`, Stripe, Mailgun, PostHog, Buttondown, Sentry, Logfire, S3/MinIO, or GitHub.
- If a behavior depends on an external API or library contract, verify against current docs/source when feasible instead of guessing.
- Summaries should name changed files and the exact checks run.

## Commands

- Start local stack: `make serve`
- Django shell: `make shell`
- Django management commands: `make manage <command>`
- Generate migrations after model changes: `make makemigrations`
- Apply migrations: `make migrate`
- Run tests in the Docker sandbox: `make test`
- Run focused tests: `make test core/tests/test_review_queue.py`
- Pass pytest flags after `--`: `make test -- -k review_queue -q`
- Frontend dev server only: `npm run start`
- Frontend watch build only: `npm run watch`
- Production frontend build: `npm run build`
- Export requirements after Poetry dependency changes: `poetry export -f requirements.txt --output requirements.txt --without-hashes`

Do not run host `pytest` directly for normal validation. The project rules expect Docker-backed tests through `make test`.

## Tests And Proof

- Add or update tests for behavior changes, bug fixes, billing logic, queues, webhooks, API responses, and permission boundaries.
- Existing tests live in `core/tests/` and use pytest with `pytest-django`.
- Background task dispatch is monkeypatched in `core/tests/conftest.py`; account for that when testing signals or async workflows.
- Mock network and provider calls. Do not hit real Stripe, Mailgun, PostHog, Buttondown, Sentry, Logfire, sitemap URLs, or page URLs from unit tests.
- For docs-only changes, `git diff --check` is usually sufficient.

## Migrations

- Do not hand-write migration files.
- If models change, update the model code first, then generate migrations with `make makemigrations`.
- Review generated migrations before finishing, especially for data loss, defaults, nullability, and backfills.
- Migration files are excluded from pre-commit formatting; keep them generated and minimal.

## Backend Rules

- This is a Django app. Use Django ORM, forms, class-based views, messages, and URL reversing in the existing style.
- Tenant data belongs to `Profile`. User-facing queries for sitemaps, pages, email preferences, feedback, billing, and API mutations must be scoped to `request.user.profile` or `request.auth`.
- Use soft archive behavior for sitemaps/pages where the current product does. Do not hard-delete user data unless explicitly required.
- Queue recurring work with Django Q (`async_task`) and existing task modules. Prefer dotted task names where the surrounding code does.
- Keep review queue behavior deterministic. Preserve cadence windows, `last_review_email_sent_at`, `review_queue_attempts`, `needs_review`, `reviewed`, and `is_active` semantics.
- Billing state transitions belong in `core.billing`, `core.stripe_webhooks`, and `Profile.track_state_change`. Treat plan aliases, site limits, Stripe metadata, and webhook idempotency as compatibility-sensitive.
- API endpoints use Django Ninja schemas in `core/api/schemas.py` and auth in `core/api/auth.py`.
- Log with `get_cleanapp_logger(__name__)` and structured key/value context. Avoid sensitive payloads.

## Frontend Rules

- Templates live under `frontend/templates/` and usually extend `base_app.html` or `base_landing.html`.
- Styles live in `frontend/src/styles/index.css`. Reuse `pf-*` classes before adding new component CSS.
- Tailwind scans Django templates, frontend JS, and `core/**/*.py` through `tailwind.config.js`.
- Prefer Stimulus controllers for interactivity. New controllers go in `frontend/src/controllers/` and are auto-loaded from `frontend/src/application/index.js`.
- Do not add inline `<script>` behavior to templates when a Stimulus controller fits.
- Keep long URLs, client labels, email addresses, and billing messages from overflowing on mobile.
- Follow `DESIGN.md` for color, type, shape, motion, and component decisions.

## Product Guardrails

- The core loop is sitemap import -> due page queue -> email digest -> review redirect -> reviewed state.
- Do not turn PageFresh into a CMS, SEO crawler, AI content generator, project management tool, or noisy analytics dashboard.
- Agencies matter. Preserve client labels, grouped digests, multi-site scanning, and clear plan usage.
- Email is the primary workflow surface. Dashboard features should support digest setup and follow-through.
- Keep setup practical for small self-hosted/Render deployments.

## Security And Privacy

- Stripe webhooks must validate signatures and keep idempotency protection.
- Authenticated API mutations must verify ownership through `Profile`.
- Do not expose API keys, profile keys, session data, webhook secrets, provider payloads, or PII in client-visible output.
- External fetches need timeouts and reasonable limits. Sitemap parsing should keep recursion and max-sitemap protections.
- For destructive or access-changing behavior, prefer explicit POST/PATCH/DELETE flows with CSRF/session protections or existing API auth.

## Documentation

- Update AI steering docs when project direction, stack, structure, or design conventions change.
- Update README/docs when setup, deployment, environment variables, or user-facing workflows change.
- Existing docs may contain boilerplate or legacy references. Prefer current code and root steering files when they conflict.
