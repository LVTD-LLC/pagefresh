# Vision

PageFresh exists because stale website content is usually an operational problem, not an ideas problem. People know their pages should be reviewed, but the work lives in forgotten spreadsheets, calendar reminders, inboxes, or someone's memory. PageFresh makes that maintenance loop explicit, scheduled, and easy to finish.

The product should become the small, dependable system a website owner, agency, or AI agent trusts to answer: which pages need attention, for which client, what should be reviewed next, and how can that review be completed from the tool already doing the work?

PageFresh should be AI-agent-first. The current email digest is a useful human workflow and can remain, but the long-term product should make the sitemap/page review loop easy for agents, automations, and external workflows to call directly.

## Direction

The near-term product is intentionally narrow:

- Import pages from sitemaps.
- Keep an active review queue.
- Send useful email digests on a configurable cadence.
- Group work by client/site for agency maintenance.
- Let users mark pages reviewed from the real page context.
- Keep billing, plan limits, and setup understandable.

The long-term direction is a maintenance operating layer for small web portfolios that works equally well for humans and agents. PageFresh can grow into better prioritization, freshness signals, review history, lightweight reporting, MCP tools, public APIs, and team workflows, but only if those features strengthen the recurring review loop.

## AI-Agent-First Direction

Agents should be able to use PageFresh without scraping the UI or depending on email. Future product work should expose the same core primitives through the app UI, a documented API, and an MCP server:

- Add and archive sites/sitemaps.
- Refresh a sitemap and inspect import status.
- List sites, clients, pages, due pages, and review history.
- Request the next due page, a random page, or a filtered page by site/client/status.
- Fetch enough page metadata for an agent to decide what to inspect next.
- Mark pages reviewed, skipped, stale, or needing follow-up with structured notes.
- Support automation flows that run daily/weekly through agents, n8n, Zapier, scripts, or hosted jobs.

The agent experience should be boring in the best way: stable identifiers, predictable pagination, explicit auth scopes, clear errors, idempotent writes where possible, and audit trails for what changed.

## Principles

- Be useful before being clever.
- Make routine maintenance feel calm and finite.
- Keep the user close to the real page they are reviewing.
- Prefer clear schedules and states over opaque automation.
- Treat email as one workflow surface, not the product boundary.
- Design features so API and MCP access can use the same product primitives as the UI.
- Make agency use natural without making solo use heavy.
- Keep self-hosting and small deployments practical.

## Current Focus

- Reliability of sitemap import and nested sitemap handling.
- Deterministic review queues that do not repeat pages inside the same cadence window.
- Digest quality: grouped, scannable, and action-oriented.
- API-ready domain primitives for sites, pages, queue selection, and reviewed state.
- MCP-ready tool boundaries for agent workflows.
- First-run onboarding and empty states.
- Billing correctness, site limits, and Stripe state transitions.
- Clear settings for email recipients, timezones, cadence, and pages per review email.
- Operational visibility through logs, admin views, and focused tests.

## What We Will Not Build For Now

- A full SEO audit/crawling suite.
- A CMS or page editor.
- AI content generation as the default workflow. Agents may inspect, suggest, or automate reviews, but PageFresh should not become a generic content generator.
- Heavy project management, assignments, or kanban boards.
- Broad notification channels before the core UI/API/MCP review loop is excellent.
- Decorative analytics that do not change maintenance behavior.
- Complex enterprise permission models before small teams and agencies are solid.

This list is a guardrail, not a permanent ceiling. New features should explain how they improve the core review loop before they add surface area.
