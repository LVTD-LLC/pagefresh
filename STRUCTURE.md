# Project Structure

## Root

- `README.md`: setup, deployment, local development, and Stripe notes.
- `AGENTS.md`: root operating instructions for coding agents.
- `VISION.md`: product direction and non-goals.
- `PRODUCT.md`: users, workflows, and product constraints.
- `TECH.md`: stack, commands, integrations, and technical constraints.
- `DESIGN.md`: visual system tokens and UI guidance.
- `Makefile`: Docker-backed development commands.
- `pyproject.toml`, `poetry.lock`, `requirements.txt`: Python dependency sources and exported install file.
- `package.json`, `package-lock.json`: frontend build dependencies and scripts.
- `docker-compose-local.yml`, `docker-compose-prod.yml`, `render.yaml`: local and deployment infrastructure.
- `.env.example`: environment variable contract for local and deployed use.

## Django Project Package: `cleanapp/`

- `settings.py`: application settings, installed apps, auth, storage, queues, logging, observability, billing plan config, and integration keys.
- `settings_test.py`: optional test settings module. It is not wired into pytest by default; `pytest.ini` currently uses `cleanapp.settings`.
- `urls.py`: root URL routing for admin, accounts, anymail, static pages, core routes, and sitemap.xml.
- `sitemaps.py`: Django sitemap definitions.
- `storages.py`: storage helpers.
- `logging_utils.py`, `sentry_utils.py`, `utils.py`: project-level utilities.
- `wsgi.py`, `asgi.py`: deployment entry points.

The package name is legacy. Do not rename `cleanapp` without a coordinated migration across settings, imports, Docker, Render, docs, and environment references.

## Main App: `core/`

- `models.py`: Profile, billing state fields, sitemap/page models, email preferences, blog posts, and feedback.
- `base_models.py`: shared model base.
- `choices.py`: enum-like choices for profile states, review cadence, and blog status.
- `forms.py`: Allauth form customization, profile settings, sitemap creation, and sitemap settings forms.
- `views.py`: page views, auth/signup extensions, dashboard, settings, pricing, Stripe checkout/portal, admin panel, review redirect, and utility triggers.
- `urls.py`: app URL declarations.
- `billing.py`: plan aliases, plan lookup, site limits, active billing states, and cadence conversion.
- `stripe_webhooks.py`: Stripe subscription and checkout event handling.
- `review_queue.py`: deterministic due-page selection and reservation.
- `email_digest.py`: digest period labels and client grouping.
- `tasks.py`: Django Q tasks for sitemap processing, page metadata extraction, email delivery, scheduling, analytics, and newsletter hooks.
- `signals.py`: profile/email preference creation, Buttondown hooks, and sitemap-processing dispatch.
- `api/`: Django Ninja API definitions, auth, and schemas.
- `templatetags/`: custom template filters.
- `tests/`: pytest coverage for queueing, billing, webhooks, views, signals, and digest behavior.
- `migrations/`: generated Django migrations only.

## Frontend

- `frontend/templates/base_app.html`: authenticated app shell, metadata, analytics scripts, navigation, messages, feedback widget, and asset includes.
- `frontend/templates/base_landing.html`: public/marketing shell.
- `frontend/templates/pages/`: landing, dashboard, sitemap detail, settings, pricing, uses, and admin pages.
- `frontend/templates/account/`: Allauth templates and email templates.
- `frontend/templates/emails/`: PageFresh review digest templates.
- `frontend/templates/components/`: reusable template components.
- `frontend/templates/blog/`: blog list/detail templates.
- `frontend/src/styles/index.css`: Tailwind imports, `--pf-*` design variables, and `pf-*` component classes.
- `frontend/src/controllers/`: Stimulus controllers.
- `frontend/src/application/index.js`: Stimulus app bootstrap and controller registration.
- `frontend/src/utils/`: frontend utility modules.
- `frontend/webpack/`: webpack configs.
- `frontend/vendors/images/`: static images and logos.

## Deployment

- `deployment/Dockerfile.python`: Python-only image for local backend/workers.
- `deployment/Dockerfile.server`: production server image with frontend build stage.
- `deployment/Dockerfile.workers`: production worker image with frontend build stage.
- `deployment/entrypoint.sh`: server/worker entrypoint behavior.
- `render.yaml`: Render blueprint. Worker service is modeled as a web service for free-tier constraints.

## Naming And Routing Conventions

- Public product copy says PageFresh.
- Technical imports and settings use `cleanapp`.
- Route names are short Django names such as `home`, `settings`, `pricing`, `sitemap_detail`, and `review_page_redirect`.
- Preserve existing URL shapes unless the task explicitly asks for routing cleanup. Some routes have no trailing slash.
- Use `reverse()` and `{% url %}` instead of hardcoded internal paths.

## Data Ownership

- `Profile` is the account-scoped owner for product data.
- `Sitemap` belongs to a profile and owns pages through `related_name="pages"`.
- `Page` belongs to both profile and sitemap.
- `EmailPreference` belongs to a profile.
- User-facing views and API endpoints must scope reads/writes to the authenticated profile.
- Sitemaps and pages are archived with `is_active=False` where current product behavior expects recoverable state.

## Feature Placement

- New profile/account settings: `core/forms.py`, `core/views.py`, `frontend/templates/pages/user-settings.html`, and related tests.
- New dashboard behavior: `HomeView`, `frontend/templates/pages/home.html`, Stimulus controller if interactive, and tests.
- New sitemap/page queue behavior: `core/review_queue.py`, `core/tasks.py`, and `core/tests/test_review_queue.py`.
- New billing behavior: `core/billing.py`, `core/stripe_webhooks.py`, settings plan config, pricing/settings templates, and billing/webhook tests.
- New API behavior: schema in `core/api/schemas.py`, endpoint in `core/api/views.py`, auth in `core/api/auth.py` if needed, and tests.
- New frontend interactivity: Stimulus controller under `frontend/src/controllers/`, data attributes in templates, and no inline behavior unless unavoidable.
- New global styles: extend `frontend/src/styles/index.css` and update `DESIGN.md` when tokens/components change.

## Generated And Local Files

- Do not edit generated migrations by hand.
- Do not commit local `.env`, media uploads, static build artifacts, Docker volumes, or node modules.
- `frontend/build/` is build output consumed by Django, not the source of UI truth.
- `requirements.txt` is generated from Poetry when Python dependencies change.

## Documentation Notes

Some older docs still reflect the original boilerplate or local non-Docker flow. When docs conflict with code, prefer current source plus these root steering files, then update the docs if the task touches setup or deployment.
