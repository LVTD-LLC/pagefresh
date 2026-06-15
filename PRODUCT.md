# Product

## Product Overview

PageFresh turns sitemap maintenance into a recurring review workflow. Users add sitemaps, PageFresh imports active pages, queues URLs for review on a cadence, and currently sends email digests with direct review links. The product replaces the spreadsheet/reminder-system version of website maintenance with a simple loop users and AI agents can trust.

PageFresh should evolve into an AI-agent-first tool. The UI and email digest remain useful human surfaces, but the core product should be available through first-class API and MCP interfaces so agents, scripts, n8n, Zapier, and other automations can add sites, inspect queues, pick pages, run checks, and mark work complete.

The public product name is PageFresh. The repository, Django project package, Docker services, database names, and some deployment resources still use `cleanapp`. Do not rename those technical surfaces unless a task is explicitly about a coordinated rename.

## Target Users

Primary users:

- Website owners who need recurring reminders to keep key pages current.
- Solo operators maintaining a small portfolio of owned sites.
- Small agencies responsible for multiple client sites.

Secondary users:

- Admin/operator users who need basic visibility into users, sitemaps, feedback, and scheduled jobs.
- Self-hosters deploying through Render, Docker Compose, or a Python/Django environment.
- AI agents and automation builders acting on behalf of a user or agency account.
- Operators wiring PageFresh into scheduled workflows through API clients, MCP clients, n8n, Zapier, scripts, or hosted jobs.

## Core Jobs

PageFresh should help users:

1. Add a sitemap quickly and know that pages were imported.
2. Group sites by client or workspace.
3. Decide how many pages each digest should surface and how often.
4. Receive a digest that is easy to scan by client and site, when email is the chosen workflow.
5. Let an agent or automation request the next due page, a random page, or a filtered page without using email.
6. Open a page from email, UI, API, or MCP context; review it in the real context; and mark it reviewed.
7. Keep billing, site limits, auth scopes, and integration setup understandable.

## Agent Jobs

AI agents should be able to:

- Add a site or sitemap for a user.
- Refresh sitemap pages and inspect import status.
- List clients, sites, pages, due pages, and recently reviewed pages.
- Pull one page at a time for a daily review flow.
- Pull a random or filtered page when an agent wants exploratory maintenance work.
- Read page metadata and stable URLs needed for SEO, schema, freshness, and content checks.
- Mark a page as reviewed, skipped, stale, or needing follow-up.
- Attach structured notes about what was checked and what changed outside PageFresh.
- Respect account limits, ownership, auth scopes, and audit logs.

## Current Product Surface

The app currently includes:

- Landing, pricing, authentication, dashboard, sitemap detail, settings, admin, blog, and uses pages.
- Django Allauth username/email authentication with optional GitHub social login.
- Sitemap import through background tasks, including nested sitemap traversal.
- Page review queueing with cadence windows and per-sitemap page limits.
- Email digests grouped by client and site.
- Multiple email recipients per profile.
- Stripe Checkout, Billing Portal, webhook handling, and site limits for free/starter/agency plans.
- Soft archive behavior for sitemaps and pages.
- Session-authenticated Django Ninja endpoints for feedback, sitemap archive, bulk page state, and email preferences.
- PostHog/Plausible analytics hooks, Buttondown newsletter hooks, and Sentry/Logfire observability hooks.

The app does not yet have a complete public API or MCP server. Future work should treat those as first-class product surfaces, not afterthought wrappers around the UI.

## Business Model

PageFresh is self-serve SaaS with a free tier and paid site-limit tiers. Billing logic is centered on active sitemap count, plan keys, Stripe price IDs, and profile state transitions. Treat billing changes as product-sensitive because they affect access, trust, and paid conversion.

Plan names and defaults currently favor:

- Free: small initial usage.
- Starter: a handful of active sites.
- Agency: larger client portfolios.

## Product Principles

- The review loop is the product. Do not let new features obscure sitemap import, queueing, review selection, and reviewed state.
- AI agents are first-class users. New features should be designed so a human can use them through the UI and an agent can use them through API/MCP without scraping pages or emails.
- Agencies are first-class users. Client labels, grouped digests, and multi-site scanning matter.
- Email is a current workflow surface, not the whole product. The dashboard supports setup and visibility; API and MCP should support recurring behavior for agents and automations.
- Trust beats novelty. Prefer clear state, predictable scheduling, and recoverable errors over clever UI.
- Keep the free/self-host path practical. Avoid changes that require paid infrastructure for small usage unless the task is explicitly about scale.
- Make external service failure understandable. Stripe, Mailgun, PostHog, Buttondown, S3/MinIO, Redis, and sitemap fetches should fail visibly in logs and gracefully in user flows.
- Keep integration primitives stable. IDs, pagination, filters, auth scopes, and write semantics matter as much as screens.

## Anti-Goals

Do not turn PageFresh into:

- A full SEO crawler or audit suite.
- A CMS, content editor, or AI content generator.
- A project management system.
- A noisy analytics dashboard.
- A multi-channel notification platform before the UI/API/MCP review loop is excellent.
- A generic SaaS template with decorative metrics and vague productivity copy.

## UX Voice

The voice is plain, useful, and low-drama. Prefer concrete labels like `Add sitemap`, `Archive`, `Open pages`, `Pages per review email`, and `Review cadence`. Avoid hype and vague claims.

## Success Measures

When making product changes, optimize for:

- Time from signup to first sitemap added.
- Successful sitemap import rate.
- Due pages delivered per digest without repeats inside the same cadence window.
- Review completion from digest links.
- API/MCP task completion by agents without UI scraping or email parsing.
- Number of successful external automations using PageFresh primitives.
- Clarity of plan limit and billing state.
- Low support burden for setup, email delivery, API keys, MCP clients, and webhook configuration.

## Accessibility

Target WCAG AA contrast for text and controls. Preserve keyboard navigation, visible focus states, reduced motion preferences, semantic form labels, and clear validation errors. Long URLs, email addresses, and client labels must wrap without breaking layout.
