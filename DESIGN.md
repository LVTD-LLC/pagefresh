---
version: alpha
name: PageFresh
description: Calm, compact visual system for recurring sitemap review workflows.
colors:
  primary: "oklch(0.38 0.12 166)"
  primary-hover: "oklch(0.19 0.028 250)"
  secondary: "oklch(0.51 0.14 166)"
  primary-soft: "oklch(0.92 0.05 166)"
  on-primary: "oklch(1 0 0)"
  text: "oklch(0.19 0.028 250)"
  text-muted: "oklch(0.42 0.035 250)"
  text-subtle: "oklch(0.56 0.03 250)"
  border: "oklch(0.88 0.018 250)"
  background: "oklch(0.985 0.006 250)"
  surface: "oklch(1 0 0)"
  surface-muted: "oklch(0.96 0.012 250)"
  warning: "oklch(0.58 0.14 72)"
  danger: "oklch(0.52 0.16 26)"
typography:
  page-title:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 36px
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: 0px
  section-title:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 30px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0px
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: 0px
  label:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0px
  caption:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0px
rounded:
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  shell-x: 24px
  shell-max: 1280px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  panel-muted:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  badge:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    padding: "4px 10px"
  metadata:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-subtle}"
    typography: "{typography.caption}"
  divider:
    backgroundColor: "{colors.border}"
    height: 1px
  warning-stripe:
    backgroundColor: "{colors.warning}"
    height: 4px
  danger-action:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.danger}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
---

# PageFresh Design

## Overview

PageFresh should feel like a quiet maintenance console for people responsible for keeping websites current. The design language is calm, crisp, and practical: high-contrast ink, restrained green accents, thin borders, compact data surfaces, and no generic SaaS spectacle.

Marketing screens should show the review loop immediately: sitemap import, due pages, client grouping, email digest, and one-click review. Authenticated app screens should be task-first and scannable, with visual emphasis reserved for the next useful action.

## Colors

The implementation source of truth is `frontend/src/styles/index.css`, where the `--pf-*` variables use OKLCH values. Keep DESIGN.md and those CSS tokens aligned when changing brand or product UI colors.

- `primary` / `--pf-brand-dark`: primary actions, active links, and durable brand marks.
- `primary-hover` / `--pf-ink`: dark hover states for primary actions.
- `secondary` / `--pf-brand`: lighter orientation accents and focus rings.
- `primary-soft` / `--pf-brand-soft`: low-pressure status badges and gentle highlight backgrounds.
- `on-primary`: white text on dark action surfaces; it matches `oklch(1 0 0)`.
- `text` / `--pf-ink`: headings and primary body text.
- `text-muted` / `--pf-muted`: helper text, secondary copy, and captions.
- `text-subtle` / `--pf-subtle`: low-emphasis metadata and inactive states.
- `background` / `--pf-surface`: page background.
- `surface` / `--pf-panel`: white panels and inputs.
- `surface-muted` / `--pf-panel-muted`: tinted panels, hover rows, and quiet empty states.
- `border` / `--pf-line`: dividers, panel outlines, and input borders.
- `warning` / `--pf-warning`: billing limits and caution indicators.
- `danger` / `--pf-danger`: destructive/archive actions and real error states.

Do not introduce a second dominant accent color. If a new state is needed, derive it from the existing semantic colors and verify contrast.

## Typography

Use the system font stack everywhere. This keeps the app fast, familiar, and utilitarian. Headings are semibold, body text is regular, and labels use semibold weight. Letter spacing stays at `0`; do not use tight negative tracking or all-caps dashboard labels unless the surrounding UI already does.

Marketing pages may use larger display sizes, but product panels should stay compact. Inside cards, tables, modals, forms, and navigation, prefer small headings and strong labels over hero-scale type.

## Layout

Use `pf-shell` as the default page width container. Product screens should prioritize repeated work: filters near lists, row actions close to URLs, settings grouped by sitemap, and plan usage visible without becoming the page.

Marketing pages should reveal the product artifact in the first viewport and leave a hint of the next section visible. Avoid split-layout hero pages where the product is hidden in a decorative card; the review queue, digest, or dashboard itself should carry the story.

Use stable dimensions for toolbars, tables, icon buttons, counters, and repeated rows so dynamic content does not shift the layout. Long URLs must wrap cleanly and never overflow their container.

## Elevation & Depth

PageFresh is mostly flat. Convey hierarchy with borders, spacing, muted surfaces, and typography rather than heavy shadows. Panels should use a 1px border with `--pf-line`; tinted panels should use `--pf-panel-muted`.

Use shadows only for overlays, dropdowns, or modals where depth clarifies focus. Do not stack cards inside cards.

## Shapes

The shape language is soft but efficient:

- Standard buttons and inputs: 12px radius.
- Panels and major grouped surfaces: 16px radius.
- Small tags and status pills: full radius.
- Avoid oversized pill buttons for normal product actions.

Keep repeated components consistent. Do not introduce new radii unless the existing `rounded` tokens cannot express the state.

## Components

Use existing `pf-*` classes before adding new component styles.

- Primary buttons: one clear next action per surface, green/ink hover, visible focus ring.
- Secondary buttons: bordered white controls for cancel, filter, navigation, and low-risk actions.
- Inputs: `pf-input` with visible labels and helper text where the expected value is not obvious.
- Badges: client labels, plan/status metadata, and compact classifications.
- Panels: individual tools, lists, forms, and modals only. Page sections should not become nested card stacks.
- Tables/lists: URLs are the core data. Keep URL text readable, row actions nearby, and status columns compact.

Destructive actions should use red text/background treatment and clear labels such as `Archive`, never vague icon-only controls.

## Motion

Marketing pages can use short entrance and hover motion when it clarifies the product artifact. Product UI motion should stay between 150 and 250ms, be tied to state changes, and avoid drawing attention away from review work.

All motion must respect `prefers-reduced-motion`. Do not add decorative looping animation, parallax, or animated background effects.

## Do's and Don'ts

Do:

- Show the maintenance loop clearly.
- Keep dashboard and settings screens dense enough for repeated use.
- Use the PageFresh green for actions, state, and orientation.
- Preserve keyboard focus, readable labels, and reduced-motion behavior.
- Match new templates to the existing `pf-*` component vocabulary.

Don't:

- Build generic SaaS hero sections, decorative icon-card grids, or blue-template dashboards.
- Add decorative blobs, bokeh, heavy gradients, or motion that distracts from maintenance work.
- Use AI/generative imagery when the user needs to inspect actual product state.
- Hide core sitemap, client, queue, digest, billing, or review information behind marketing copy.
- Let long URLs, email addresses, or client labels overflow controls or table cells.
