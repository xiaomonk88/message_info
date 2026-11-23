---
name: Ethereal Admin
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#464555'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#5c5f61'
  on-secondary: '#ffffff'
  secondary-container: '#e0e3e5'
  on-secondary-container: '#626567'
  tertiary: '#7e3000'
  on-tertiary: '#ffffff'
  tertiary-container: '#a44100'
  on-tertiary-container: '#ffd2be'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#e0e3e5'
  secondary-fixed-dim: '#c4c7c9'
  on-secondary-fixed: '#191c1e'
  on-secondary-fixed-variant: '#444749'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
    letterSpacing: 0.02em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding-desktop: 40px
  container-padding-mobile: 20px
  gutter: 24px
  section-gap: 64px
  element-gap: 16px
---

## Brand & Style

The design system is centered on the concept of "Breathing Space & Clarity." It is an ultra-minimalist framework designed for high-end administrative interfaces where cognitive load must be minimized to allow for precise decision-making. 

The aesthetic is rooted in **Minimalism** with a focus on extreme whitespace, high-contrast typography, and a "borderless" philosophy. It evokes a sense of calm authority and premium quality. The target audience is executive-level users and data analysts who require a sophisticated, distraction-free environment. Visual hierarchy is established through scale and tonal shifts rather than decorative elements or heavy borders.

## Colors

The palette is intentionally restrained to maintain the "Breathing Space" narrative. 

- **Primary (Deep Indigo):** Used sparingly for key actions, active states, and critical indicators. It provides a sharp, sophisticated point of focus against the neutral backdrop.
- **Background (#F8FAFC):** An extremely light, cool grey that differentiates the application frame from the content surfaces.
- **Surface (#FFFFFF):** Pure white is reserved for cards, modals, and input areas to create a "floating" effect.
- **Neutral (#0F172A):** A deep navy-black used for primary text to ensure maximum readability and a high-contrast, premium feel.

Functional colors (success, warning, error) should follow a desaturated, professional profile to avoid clashing with the Deep Indigo accent.

## Typography

This design system utilizes **Inter** exclusively to leverage its systematic, highly-legible characteristics. 

- **Headlines:** Feature generous letter spacing and significant vertical margins to emphasize the "airy" concept. Large display sizes use subtle negative letter-spacing for a modern, "tight" editorial look, while medium headers use increased tracking to promote openness.
- **Body Text:** Optimised for long-form reading with a line height of 1.5–1.6.
- **Labels:** Small labels use uppercase with increased tracking (5%) to differentiate them from body text without requiring additional weight or color.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy for dashboard content, centered within a fluid application shell. 

- **Desktop:** A 12-column grid with a maximum content width of 1440px. Gutters are kept wide (24px) to maintain the airy aesthetic.
- **Spacing Rhythm:** Based on an 8px base unit. Section-level vertical spacing is intentionally aggressive (64px+) to force a "one thought at a time" user flow.
- **Margins:** Large outer margins (40px on desktop) act as a frame, isolating the content from the edges of the browser to reinforce the premium, gallery-like feel.

## Elevation & Depth

To maintain the "borderless" and "ultra-minimalist" aesthetic, this design system avoids traditional heavy shadows and thick borders.

- **Tonal Layers:** Depth is primarily communicated through color shifts. The `#F8FAFC` background provides a base, while `#FFFFFF` surfaces sit on top.
- **Ambient Shadows:** Where elevation is strictly necessary (e.g., active modals or floating menus), use extremely diffused, low-opacity shadows: `0 20px 50px rgba(0, 0, 0, 0.04)`. These should feel like natural light falling on a soft surface.
- **Interaction:** Hover states should be indicated by subtle shifts in surface color (e.g., White to a 1% Indigo tint) rather than a shadow increase.

## Shapes

The shape language is consistently **Soft**. 

All primary UI containers, including cards and input fields, utilize a 12px (`0.75rem`) corner radius. This softens the high-contrast typography and ensures the "premium" feel doesn't become too clinical or sharp. Larger components like main content areas or modal overlays should use 24px (`1.5rem`) to emphasize their prominence.

## Components

- **Buttons:** Primary buttons use the Deep Indigo background with white text. Ghost buttons use no border, only Deep Indigo text, and a very subtle Indigo-tinted background on hover.
- **Input Fields:** Borderless design. Fields are defined by the white surface against the light grey background, or a very light 1px stroke (#E2E8F0) only when appearing on white backgrounds. Focused states use a 2px Deep Indigo bottom-border or subtle inner glow.
- **Cards:** No borders. Shadows are avoided in favor of the color contrast between the card (#FFFFFF) and the page background (#F8FAFC). Padding inside cards should be generous (min 32px).
- **Chips/Badges:** Small, 12px rounded shapes with low-saturation backgrounds. The text should be semi-bold and high-contrast.
- **Lists:** Clean lines with no dividers. Vertical rhythm and subtle hover backgrounds provide the structure.
- **Navigation:** Vertical sidebar with icons only or icons + text. Active states are marked by a small Indigo vertical pill next to the label, rather than a full-width background highlight.