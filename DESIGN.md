# Design

## Overview

PageFresh uses a calm maintenance-product visual system: high-contrast ink, a deep green brand anchor, soft green status accents, and compact app surfaces. Marketing pages should make the sitemap review loop obvious in the first viewport. Authenticated app screens stay restrained, with the accent reserved for actions, status, and orientation.

## Color

Use OKLCH tokens in CSS. The palette is anchored by a practical green brand color with neutral blue-gray text and borders.

```css
:root {
  --pf-ink: oklch(0.19 0.028 250);
  --pf-muted: oklch(0.42 0.035 250);
  --pf-line: oklch(0.88 0.018 250);
  --pf-surface: oklch(0.985 0.006 250);
  --pf-panel: oklch(1 0 0);
  --pf-panel-muted: oklch(0.96 0.012 250);
  --pf-brand: oklch(0.51 0.14 166);
  --pf-brand-dark: oklch(0.38 0.12 166);
  --pf-brand-soft: oklch(0.92 0.05 166);
  --pf-warning: oklch(0.58 0.14 72);
  --pf-danger: oklch(0.52 0.16 26);
}
```

## Typography

Marketing surfaces use the system stack with strong weight contrast and readable display sizes. Product surfaces use the same family for speed and consistency. Avoid oversized display type inside app panels, and keep letter spacing at zero.

## Layout

Marketing should show the product artifact and leave a hint of the next section visible in the first viewport. App screens use a compact top shell, focused form surfaces, and data-first content regions.

## Components

Buttons use 10 to 12px radii, never oversized pill shapes for standard app actions. Cards and panels use light borders or flat tinted surfaces, not paired heavy shadows. Status pills use semantic colors with readable text. Tables keep row actions close to the URL data.

## Motion

Marketing can use short entrance and hover motion. Product UI motion should be 150 to 250ms and state-based only. All motion must respect `prefers-reduced-motion`.
